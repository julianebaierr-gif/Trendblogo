import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, Query, Form
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from app.database import get_db
from app.config import settings
from app.models.article import Article, Category, Tag, ArticleTag
from app.models.user import User
from app.models.inquiries import ContactMessage, GuestPostSubmission
from app.models.settings import SiteSetting, HomepageSection
from app.services.link_engine import LinkEngine
from app.services.seo_engine import SEOEngine

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))

def get_common_context(db: Session, request: Request) -> dict:
    categories = db.query(Category).all()
    recent_posts = db.query(Article).filter(Article.status == "published").order_by(desc(Article.published_at)).limit(4).all()
    site_name = db.query(SiteSetting).filter(SiteSetting.key == "site_name").first()
    site_desc = db.query(SiteSetting).filter(SiteSetting.key == "site_description").first()
    return {
        "request": request,
        "categories": categories,
        "recent_posts": recent_posts,
        "site_name": site_name.value if site_name else "TrendBlogo",
        "site_desc": site_desc.value if site_desc else "The Journal of Technology, Digital Economy & Innovation",
        "base_url": settings.BASE_URL,
        "current_year": datetime.utcnow().year,
        "current_date_str": datetime.utcnow().strftime("%A, %B %d, %Y")
    }

@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    ctx = get_common_context(db, request)
    all_articles = db.query(Article).filter(Article.status == "published").order_by(desc(Article.published_at)).limit(20).all()
    featured_post = all_articles[0] if all_articles else None
    latest_posts = all_articles[1:] if len(all_articles) > 1 else []
    total_articles = len(all_articles)
    
    sections = db.query(HomepageSection).filter(HomepageSection.is_enabled == True).order_by(HomepageSection.sort_order).all()
    sections_map = {s.section_key: s for s in sections}

    ctx.update({
        "featured_post": featured_post,
        "latest_posts": latest_posts,
        "all_articles": all_articles,
        "total_articles": total_articles,
        "sections": sections,
        "sections_map": sections_map,
        "title": "TrendBlogo — Modern Journal & Technology Magazine",
        "meta_desc": "Explore top guides, independent reviews, and comprehensive articles published on TrendBlogo."
    })
    return templates.TemplateResponse(request=request, name="index.html", context=ctx)


@router.get("/about", response_class=HTMLResponse)
def about(request: Request, db: Session = Depends(get_db)):
    ctx = get_common_context(db, request)
    ctx.update({
        "title": "About Us — Independent Testing & Reviews | TrendBlogo",
        "meta_desc": "Meet the real team behind TrendBlogo. Led by Alex Rivera, we test footwear, everyday tech, and lifestyle gear with 100% independent integrity."
    })
    return templates.TemplateResponse(request=request, name="about.html", context=ctx)

@router.get("/contact", response_class=HTMLResponse)
def contact(request: Request, db: Session = Depends(get_db)):
    ctx = get_common_context(db, request)
    contact_email = db.query(SiteSetting).filter(SiteSetting.key == "contact_email").first()
    ctx.update({
        "title": "Contact Us ? TrendBlogo Support & Inquiries",
        "meta_desc": "Get in touch with the TrendBlogo editorial and support team for inquiries, feedback, or enterprise collaboration.",
        "contact_email_val": contact_email.value if contact_email else "support@trendblogo.com"
    })
    return templates.TemplateResponse(request=request, name="contact.html", context=ctx)

@router.post("/contact", response_class=HTMLResponse)
def submit_contact(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    subject: str = Form(...),
    message: str = Form(...),
    spam_honey: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    ctx = get_common_context(db, request)
    if spam_honey: # Simple honeypot spam protection
        ctx["success"] = True
        return templates.TemplateResponse(request=request, name="contact.html", context=ctx)

    msg = ContactMessage(name=name.strip(), email=email.strip(), subject=subject.strip(), message=message.strip())
    db.add(msg)
    db.commit()

    ctx.update({
        "title": "Contact Us ? Message Received",
        "meta_desc": "Thank you for contacting TrendBlogo.",
        "success_msg": "Thank you! Your message has been received. Our team will review it and respond promptly."
    })
    return templates.TemplateResponse(request=request, name="contact.html", context=ctx)

    return templates.TemplateResponse(request=request, name="contact.html", context=ctx)

@router.get("/editorial-policy", response_class=HTMLResponse)
def editorial_policy(request: Request, db: Session = Depends(get_db)):
    ctx = get_common_context(db, request)
    ctx.update({
        "title": "Editorial Policy & Benchmarking Standards | TrendBlogo",
        "meta_desc": "TrendBlogo's independent editorial policy, rigorous hardware benchmarking methodology, zero-conflict disclosure, and AI ethics statement."
    })
    return templates.TemplateResponse(request=request, name="editorial_policy.html", context=ctx)

@router.get("/corrections-policy", response_class=HTMLResponse)
def corrections_policy(request: Request, db: Session = Depends(get_db)):
    ctx = get_common_context(db, request)
    ctx.update({
        "title": "Corrections & Updates Policy | TrendBlogo",
        "meta_desc": "Review TrendBlogo's transparent protocol for fact-checking updates, correction notices, and errata disclosures across our technology reporting."
    })
    return templates.TemplateResponse(request=request, name="corrections_policy.html", context=ctx)

@router.get("/sitemap", response_class=HTMLResponse)
def html_sitemap(request: Request, db: Session = Depends(get_db)):
    ctx = get_common_context(db, request)
    categories = db.query(Category).all()
    articles = db.query(Article).filter(Article.status == "published").order_by(desc(Article.published_at)).limit(100).all()
    ctx.update({
        "categories": categories,
        "articles": articles,
        "title": "HTML Sitemap & Content Index | TrendBlogo",
        "meta_desc": "Complete index and directory of all technology sections, topics, tutorials, and policy documentation across TrendBlogo."
    })
    return templates.TemplateResponse(request=request, name="sitemap.html", context=ctx)

@router.get("/author/{slug}", response_class=HTMLResponse)
def author_profile(slug: str, request: Request, page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    ctx = get_common_context(db, request)
    author_user = db.query(User).filter(User.slug == slug).first()
    
    # Query articles written by this author (or matching author_slug)
    query = db.query(Article).filter(
        Article.status == "published",
        or_(Article.author_slug == slug, Article.author_name.ilike(f"%{slug.replace('-', ' ')}%"))
    ).order_by(desc(Article.published_at))
    
    total = query.count()
    per_page = 9
    total_pages = max(1, (total + per_page - 1) // per_page)
    articles = query.offset((page - 1) * per_page).limit(per_page).all()

    author_name = author_user.name if author_user else slug.replace("-", " ").title()
    author_bio = author_user.bio if author_user else "Contributing technology analyst and researcher at TrendBlogo."
    author_role = author_user.title_designation if author_user else "Senior Technology Contributor"

    ctx.update({
        "author": author_user,
        "author_name": author_name,
        "author_bio": author_bio,
        "author_role": author_role,
        "author_slug": slug,
        "articles": articles,
        "page": page,
        "total_pages": total_pages,
        "total_count": total,
        "title": f"{author_name} — Author Profile & Articles | TrendBlogo",
        "meta_desc": f"Explore technology analysis, software architecture breakdowns, and hardware reviews written by {author_name} on TrendBlogo."
    })
    return templates.TemplateResponse(request=request, name="author.html", context=ctx)

@router.get("/guest-posting", response_class=HTMLResponse)
def guest_posting(request: Request, db: Session = Depends(get_db)):
    ctx = get_common_context(db, request)
    ctx.update({
        "title": "Guest Posting Guidelines — Write for TrendBlogo",
        "meta_desc": "Explore TrendBlogo's editorial criteria, submission benchmarks, and contributor guidelines."
    })
    return templates.TemplateResponse(request=request, name="guest_posting.html", context=ctx)

@router.post("/guest-posting", response_class=HTMLResponse)
def submit_guest_post(
    request: Request,
    author_name: str = Form(...),
    email: str = Form(...),
    website: Optional[str] = Form(None),
    proposed_title: str = Form(...),
    topic_category: str = Form(...),
    article_outline: str = Form(...),
    author_bio: Optional[str] = Form(None),
    message: Optional[str] = Form(None),
    spam_honey: Optional[str] = Form(None),
    agreed: Optional[bool] = Form(False),
    db: Session = Depends(get_db)
):
    ctx = get_common_context(db, request)
    if spam_honey:
        ctx["success_msg"] = "Proposal submitted."
        return templates.TemplateResponse(request=request, name="guest_posting.html", context=ctx)

    submission = GuestPostSubmission(
        author_name=author_name.strip(),
        email=email.strip(),
        website=website.strip() if website else None,
        proposed_title=proposed_title.strip(),
        topic_category=topic_category.strip(),
        article_outline=article_outline.strip(),
        author_bio=author_bio.strip() if author_bio else None,
        message=message.strip() if message else None,
        agreed_to_guidelines=bool(agreed)
    )
    db.add(submission)
    db.commit()

    ctx.update({
        "title": "Guest Posting Guidelines — Proposal Submitted",
        "meta_desc": "Your guest post submission has been received by TrendBlogo.",
        "success_msg": "Your guest post proposal has been received! Our editorial board reviews submissions weekly."
    })
    return templates.TemplateResponse(request=request, name="guest_posting.html", context=ctx)



@router.get("/privacy-policy", response_class=HTMLResponse)
def privacy_policy(request: Request, db: Session = Depends(get_db)):
    ctx = get_common_context(db, request)
    ctx.update({
        "title": "Privacy Policy ? TrendBlogo Data Protection",
        "meta_desc": "TrendBlogo Privacy Policy covering data collection, cookie usage, analytics, AI API processing, user rights, and security safeguards."
    })
    return templates.TemplateResponse(request=request, name="privacy.html", context=ctx)

@router.get("/terms-and-conditions", response_class=HTMLResponse)
def terms_conditions(request: Request, db: Session = Depends(get_db)):
    ctx = get_common_context(db, request)
    ctx.update({
        "title": "Terms & Conditions ? TrendBlogo",
        "meta_desc": "Review the terms, acceptable use policies, intellectual property rights, and user agreements for the TrendBlogo platform."
    })
    return templates.TemplateResponse(request=request, name="terms.html", context=ctx)

@router.get("/disclaimer", response_class=HTMLResponse)
def disclaimer(request: Request, db: Session = Depends(get_db)):
    ctx = get_common_context(db, request)
    ctx.update({
        "title": "Disclaimer ? AI Content & Factual Verification",
        "meta_desc": "TrendBlogo disclaimer outlining the informational nature of AI-generated content, verification obligations, and third-party references."
    })
    return templates.TemplateResponse(request=request, name="disclaimer.html", context=ctx)

@router.get("/cookie-policy", response_class=HTMLResponse)
def cookie_policy(request: Request, db: Session = Depends(get_db)):
    ctx = get_common_context(db, request)
    ctx.update({
        "title": "Cookie Policy & Preferences ? TrendBlogo",
        "meta_desc": "Understand how TrendBlogo utilizes essential, functional, and analytics cookies, and manage your cookie preferences."
    })
    return templates.TemplateResponse(request=request, name="cookies.html", context=ctx)

@router.get("/blog", response_class=HTMLResponse)
def blog_list(
    request: Request,
    page: int = Query(1, ge=1),
    sort: str = Query("latest"),
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    ctx = get_common_context(db, request)
    query = db.query(Article).filter(Article.status == "published")

    active_category = None
    if category:
        active_category = db.query(Category).filter(Category.slug == category).first()
        if active_category:
            query = query.filter(Article.category_id == active_category.id)

    active_tag = None
    if tag:
        active_tag = db.query(Tag).filter(Tag.slug == tag).first()
        if active_tag:
            query = query.join(ArticleTag).filter(ArticleTag.tag_id == active_tag.id)

    if q:
        kw = f"%{q.strip()}%"
        query = query.filter(or_(Article.title.ilike(kw), Article.summary.ilike(kw), Article.primary_keyword.ilike(kw)))

    if sort == "popular":
        query = query.order_by(desc(Article.view_count))
    else:
        query = query.order_by(desc(Article.published_at))

    total = query.count()
    per_page = 9
    total_pages = max(1, (total + per_page - 1) // per_page)
    articles = query.offset((page - 1) * per_page).limit(per_page).all()

    ctx.update({
        "articles": articles,
        "page": page,
        "total_pages": total_pages,
        "total_count": total,
        "active_category": active_category,
        "active_tag": active_tag,
        "search_query": q,
        "sort": sort,
        "title": f"Blog ? Latest Articles & Insights ({page}/{total_pages}) | TrendBlogo",
        "meta_desc": "Explore high-quality, actionable articles on AI automation, SEO architecture, modern software workflows, and digital productivity."
    })
    return templates.TemplateResponse(request=request, name="blog/list.html", context=ctx)

@router.get("/blog/{slug}", response_class=HTMLResponse)
def article_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Increment view count
    article.view_count = (article.view_count or 0) + 1
    db.commit()

    ctx = get_common_context(db, request)
    related_posts = LinkEngine.get_related_posts(db, article.id, article.category_id, limit=4)

    ctx.update({
        "article": article,
        "related_posts": related_posts,
        "title": article.seo_title or f"{article.title} | TrendBlogo",
        "meta_desc": article.meta_description or article.summary,
        "canonical_url": article.canonical_url,
        "og_image": article.featured_image,
        "schema_json": article.schema_json or SEOEngine.generate_schema_json(article)
    })
    return templates.TemplateResponse(request=request, name="blog/detail.html", context=ctx)

@router.get("/categories", response_class=HTMLResponse)
def categories_list(request: Request, db: Session = Depends(get_db)):
    ctx = get_common_context(db, request)
    categories = db.query(Category).all()
    # Add count for each
    cat_counts = []
    for c in categories:
        count = db.query(Article).filter(Article.category_id == c.id, Article.status == "published").count()
        cat_counts.append({"category": c, "count": count})

    ctx.update({
        "categories_with_counts": cat_counts,
        "title": "All Topic Categories | TrendBlogo",
        "meta_desc": "Browse articles by topic across AI & Automation, Content Strategy & SEO, Productivity, and Digital Marketing."
    })
    return templates.TemplateResponse(request=request, name="blog/categories.html", context=ctx)

@router.get("/category/{slug}", response_class=HTMLResponse)
def category_detail(slug: str, request: Request, page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.slug == slug).first()
    if not category and slug == "tech":
        category = db.query(Category).filter(Category.slug.in_(["tech", "tech-news", "ai"])).first()
        if not category:
            category = Category(
                name="Tech",
                slug="tech",
                description="Comprehensive technology reporting, systems engineering, and hardware reviews.",
                color="#2563EB"
            )
            db.add(category)
            db.commit()
            db.refresh(category)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    ctx = get_common_context(db, request)
    query = db.query(Article).filter(Article.category_id == category.id, Article.status == "published").order_by(desc(Article.published_at))
    total = query.count()
    per_page = 9
    total_pages = max(1, (total + per_page - 1) // per_page)
    articles = query.offset((page - 1) * per_page).limit(per_page).all()

    ctx.update({
        "category": category,
        "articles": articles,
        "page": page,
        "total_pages": total_pages,
        "total_count": total,
        "title": f"{category.name} Articles | TrendBlogo",
        "meta_desc": category.description or f"Discover top-tier articles and guides on {category.name} published on TrendBlogo."
    })
    return templates.TemplateResponse(request=request, name="blog/category.html", context=ctx)

@router.get("/search", response_class=HTMLResponse)
def search_view(request: Request, q: str = Query("", alias="q"), db: Session = Depends(get_db)):
    ctx = get_common_context(db, request)
    query_str = q.strip()
    articles = []
    if query_str:
        pattern = f"%{query_str}%"
        articles = db.query(Article).filter(
            Article.status == "published",
            or_(
                Article.title.ilike(pattern),
                Article.summary.ilike(pattern),
                Article.content.ilike(pattern),
                Article.primary_keyword.ilike(pattern)
            )
        ).order_by(desc(Article.published_at)).limit(20).all()

    ctx.update({
        "query": query_str,
        "results": articles,
        "result_count": len(articles),
        "title": f"Search Results for '{query_str}' | TrendBlogo" if query_str else "Search Articles | TrendBlogo",
        "meta_desc": f"Explore search results for '{query_str}' on TrendBlogo."
    })
    return templates.TemplateResponse(request=request, name="search.html", context=ctx)

@router.get("/sitemap.xml")
def sitemap(db: Session = Depends(get_db)):
    xml_content = SEOEngine.generate_sitemap_xml(db)
    return Response(content=xml_content, media_type="application/xml")

@router.get("/robots.txt")
def robots():
    txt_content = SEOEngine.generate_robots_txt()
    return Response(content=txt_content, media_type="text/plain")

@router.get("/rss.xml")
def rss_feed(db: Session = Depends(get_db)):
    articles = db.query(Article).filter(Article.status == "published").order_by(desc(Article.published_at)).limit(20).all()
    base = settings.BASE_URL
    rss_items = []
    for a in articles:
        rss_items.append(f"""
    <item>
      <title><![CDATA[{a.title}]]></title>
      <link>{base}/blog/{a.slug}</link>
      <guid isPermaLink="true">{base}/blog/{a.slug}</guid>
      <pubDate>{a.published_at.strftime("%a, %d %b %Y %H:%M:%S GMT") if a.published_at else ""}</pubDate>
      <description><![CDATA[{a.summary}]]></description>
    </item>""")
    
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>TrendBlogo ? AI Content Automation &amp; Publishing</title>
    <link>{base}</link>
    <description>Turn Keywords Into High-Quality Blog Content Automatically.</description>
    <language>en-us</language>
    <atom:link href="{base}/rss.xml" rel="self" type="application/rss+xml"/>
    {''.join(rss_items)}
  </channel>
</rss>"""
    return Response(content=xml, media_type="application/xml")
