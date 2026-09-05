import json
from datetime import datetime, timedelta
from app.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.article import Article, Category, Tag, ArticleTag
from app.models.links import InternalLink, ExternalLink, RelatedPost
from app.models.media import Media
from app.models.automation import Keyword, GenerationJob
from app.models.settings import SiteSetting, SystemLog
from app.services.image_service import ImageService
from app.services.seo_engine import SEOEngine
from app.config import settings

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. Admin User
    existing_admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
    if not existing_admin:
        pwd_hash, salt = User.hash_password(settings.ADMIN_PASSWORD)
        admin = User(
            email=settings.ADMIN_EMAIL,
            name="TrendBlogo Chief Editor",
            password_hash=pwd_hash,
            salt=salt,
            role="admin"
        )
        db.add(admin)
        print(f"Created admin account: {settings.ADMIN_EMAIL}")

    # 2. Categories
    categories_data = [
        {"name": "AI & Automation", "slug": "ai-and-automation", "description": "Cutting-edge artificial intelligence, workflow automation, and algorithmic content systems.", "color": "#6366F1", "icon": "cpu"},
        {"name": "Content Strategy & SEO", "slug": "content-strategy-seo", "description": "Architectural SEO, keyword intent mapping, and high-performance search distribution.", "color": "#06B6D4", "icon": "search"},
        {"name": "Productivity & Remote Work", "slug": "productivity-remote-work", "description": "Modern tools, team operational cadence, and asynchronous collaboration workflows.", "color": "#10B981", "icon": "zap"},
        {"name": "Digital Marketing", "slug": "digital-marketing", "description": "High-leverage growth engines, omnichannel syndication, and measurable audience acquisition.", "color": "#F59E0B", "icon": "trending-up"},
    ]
    cat_map = {}
    for cat in categories_data:
        existing = db.query(Category).filter(Category.slug == cat["slug"]).first()
        if not existing:
            new_cat = Category(**cat)
            db.add(new_cat)
            db.flush()
            cat_map[cat["slug"]] = new_cat
        else:
            cat_map[cat["slug"]] = existing

    # 3. Tags
    tags_list = ["Content Automation", "AI Writing", "SEO Architecture", "Productivity Tools", "Search Intent", "Workflow Optimization"]
    tag_map = {}
    for t_name in tags_list:
        slug = t_name.lower().replace(" ", "-")
        existing_t = db.query(Tag).filter(Tag.slug == slug).first()
        if not existing_t:
            new_t = Tag(name=t_name, slug=slug)
            db.add(new_t)
            db.flush()
            tag_map[slug] = new_t
        else:
            tag_map[slug] = existing_t

    # 4. Default Site Settings
    default_settings = [
        ("site_name", "TrendBlogo", "general", "Platform display name"),
        ("site_tagline", "Turn Keywords Into High-Quality Blog Content Automatically", "general", "Hero headline & site tagline"),
        ("site_description", "TrendBlogo is an enterprise-grade AI content automation platform designed for modern digital publications and SEO growth.", "seo", "Global meta description"),
        ("contact_email", "support@trendblogo.com", "general", "Official support contact email"),
        ("editorial_review_required", "true", "general", "Enforce editorial check before live publishing"),
        ("openai_model", "gpt-4o-mini", "api", "Default OpenAI chat model"),
        ("image_provider", "auto", "api", "Image generation engine provider"),
        ("allow_guest_submissions", "true", "general", "Enable public guest post submissions"),
        ("cookie_consent_enabled", "true", "legal", "Display interactive cookie preference banner")
    ]
    for key, val, cat, desc in default_settings:
        if not db.query(SiteSetting).filter(SiteSetting.key == key).first():
            db.add(SiteSetting(key=key, value=val, category=cat, description=desc))

    db.commit()

    # 5. Seed 3 High-Quality Published Articles
    articles_seed = [
        {
            "keyword": "ai content automation",
            "slug": "ai-content-automation-complete-guide",
            "title": "The Complete Guide to AI Content Automation in 2026",
            "cat_slug": "ai-and-automation",
            "summary": "Discover how modern digital publishers scale organic search visibility with automated content pipelines, semantic clustering, and editorial quality controls.",
            "read_time": 6,
            "sections": [
                {"h2": "The Evolution of Algorithmic Editorial Pipelines", "h3_list": ["From Primitive Templates to Neural Synthesis", "Architectural Prerequisites"]},
                {"h2": "Core Components of Modern Content Automation", "h3_list": ["Intent-Driven Keyword Topology", "Structured Markdown Compilation"]},
                {"h2": "Quality Governance and Heading Hierarchy Standards", "h3_list": ["Plain-Text Heading Requirements", "Multi-Pass Fact and Readability Auditing"]},
                {"h2": "Long-Term Indexation and Organic Growth Trajectories", "h3_list": ["Topical Authority Clustering", "Sustainable Performance Metrics"]}
            ]
        },
        {
            "keyword": "best productivity apps",
            "slug": "best-productivity-apps-for-teams",
            "title": "10 Best Productivity Apps for Modern Teams in 2026",
            "cat_slug": "productivity-remote-work",
            "summary": "An exhaustive, benchmarked evaluation of the premier task managers, asynchronous collaboration hubs, and cognitive focus platforms for distributed teams.",
            "read_time": 7,
            "sections": [
                {"h2": "Defining Next-Generation Team Productivity", "h3_list": ["The Asynchronous Shift", "Tool Sprawl vs Integrated Workspaces"]},
                {"h2": "Top Ranked Productivity Suites and Benchmarks", "h3_list": ["Cognitive Workflow Engines", "Knowledge Architecture Platforms"]},
                {"h2": "Implementation Blueprint for High-Growth Workflows", "h3_list": ["Reducing Context-Switching Penalties", "Automating Repetitive Telemetry"]},
                {"h2": "Balancing Synchronous Cadence with Deep Work", "h3_list": ["Focus Time Safeguards", "Continuous Alignment Reviews"]}
            ]
        },
        {
            "keyword": "seo tools for digital publishers",
            "slug": "seo-tools-for-digital-publishers",
            "title": "Modern SEO Tools for Digital Publishers: Architectural Guide",
            "cat_slug": "content-strategy-seo",
            "summary": "A comprehensive review of the modern SEO tool stack designed to audit search intent, streamline structured data, and eliminate keyword cannibalization.",
            "read_time": 6,
            "sections": [
                {"h2": "The Modern SEO Infrastructure Stack", "h3_list": ["Semantic Crawling Algorithms", "Entity Resolution Platforms"]},
                {"h2": "Intent Identification and Semantic Cannibalization", "h3_list": ["Query Clustering Mechanics", "Disambiguating SERP Ambiguity"]},
                {"h2": "Structured Data and Schema.org Implementations", "h3_list": ["Article Schema Generation", "Automated XML Sitemap Orchestration"]},
                {"h2": "Continuous Technical Auditing and Monitoring", "h3_list": ["Core Web Vitals Telemetry", "Dynamic Internal Link Distribution"]}
            ]
        }
    ]

    for item in articles_seed:
        existing_art = db.query(Article).filter(Article.slug == item["slug"]).first()
        if existing_art:
            continue

        cat = cat_map[item["cat_slug"]]
        
        # Generate 4 images (1 featured + 3 in-article)
        images = ImageService.create_article_images(
            keyword=item["keyword"],
            title=item["title"],
            outline_sections=item["sections"],
            slug=item["slug"]
        )

        featured = images["featured"]
        img1 = images["image_1"]
        img2 = images["image_2"]
        img3 = images["image_3"]

        # Body markdown adhering strictly to rule: NO links in H2-H5 headings!
        body_md = f"""Modern digital publishing has reached an inflection point where scale without quality is suicidal, and quality without automation is unsustainable. Understanding **{item['keyword']}** provides digital teams with the leverage needed to publish authoritative, deeply researched articles with minimal operational friction.

## {item['sections'][0]['h2']}

At its core, a sustainable strategy begins by establishing clear architectural boundaries. Instead of generating fragmented, unstructured text, modern practitioners orchestrate multi-step editorial workflows that mirror senior human editors.

### {item['sections'][0]['h3_list'][0]}

When evaluating workflow maturity, the primary objective is eliminating mechanical friction. You can also explore our foundational guide to [ai content automation](/blog/ai-content-automation-complete-guide) to understand how neural pipelines maintain high stylistic fidelity across hundreds of published assets.

### {item['sections'][0]['h3_list'][1]}

Key architectural pillars include:

- **Entity Preservation:** Maintaining factual continuity and strict terminology across all subtopics.
- **Topical Hierarchy:** Enforcing clean H2, H3, and H4 structures without superficial fluff.
- **Standardized References:** Aligning definitions with recognized industry authorities like the [World Wide Web Consortium (W3C)](https://www.w3.org/standards/).

![{img1['alt']}]({img1['url']})
*{img1['caption']}*

## {item['sections'][1]['h2']}

To consistently rank in competitive organic landscapes, publications must map each section directly to explicit user search intent.

### {item['sections'][1]['h3_list'][0]}

By categorizing search queries into informational, navigational, and commercial buckets, the generation pipeline can adjust tone, depth, and structural templates accordingly. Teams adopting [best productivity apps](/blog/best-productivity-apps-for-teams) frequently discover that automated taxonomy tagging saves countless editorial hours.

### {item['sections'][1]['h3_list'][1]}

Effective schema integration and link distribution ensure that search engines can easily parse topic relationships and index key findings efficiently.

![{img2['alt']}]({img2['url']})
*{img2['caption']}*

## {item['sections'][2]['h2']}

Maintaining editorial trust requires automated quality control guardrails operating before any post is published.

### {item['sections'][2]['h3_list'][0]}

A critical rule in high-performance SEO is maintaining plain-text heading tags. Headings serve as landmark semantic anchors for both screen readers and web spiders. Placing hyperlinks inside headings dilutes topical clarity and degrades accessibility metrics.

### {item['sections'][2]['h3_list'][1]}

Every article produced through TrendBlogo passes through a comprehensive multi-pass quality control audit, checking reading ease, keyword density, and schema completeness. For technical reference, consult the [MDN Web Docs](https://developer.mozilla.org/) on semantic accessibility.

![{img3['alt']}]({img3['url']})
*{img3['caption']}*

## {item['sections'][3]['h2']}

As search engines continue to prioritize verified topical authority and direct user value, digital publishers must adopt resilient, future-ready infrastructure.

- **Automated Anti-Cannibalization:** Proactively detecting thematic overlap before content generation.
- **Contextual In-Article Imagery:** Providing bespoke visual assets that directly complement specific section discussions.
- **Structured JSON-LD:** Ensuring rich snippets and knowledge graph entity recognition.

## Frequently Asked Questions About {item['keyword'].title()}

### How does TrendBlogo ensure generated articles remain original and human-readable?
TrendBlogo uses a modular generation pipeline where keyword intent, structural outline, section content, and quality auditing are executed in dedicated steps rather than a single generic prompt.

### Why are hyperlinks prohibited inside headings?
Headings must remain pure semantic landmarks. Hyperlinks inside H2-H5 headings harm user readability, create accessibility barriers for assistive devices, and disrupt search engine topic extraction.

### How many images should accompany an in-depth article?
TrendBlogo standardizes on exactly 4 contextually generated visual assets: 1 wide featured banner plus 3 bespoke in-article illustrations placed across key sections.

## Summary and Next Steps

Implementing **{item['keyword']}** with discipline and automated governance unlocks unmatched publishing velocity while elevating editorial standards. Start by cataloging your primary keyword opportunities, eliminate topical overlap, and leverage structured pipelines to deliver enduring value to your audience."""

        # Enforce clean headings strictly
        from app.services.link_engine import LinkEngine
        clean_body = LinkEngine.sanitize_headings(body_md)

        import markdown as md_lib
        html = md_lib.markdown(clean_body, extensions=["fenced_code", "tables", "toc", "sane_lists"])
        word_count = len(clean_body.split())

        seo_meta = SEOEngine.generate_metadata(
            keyword=item["keyword"],
            title=item["title"],
            summary=item["summary"],
            slug=item["slug"],
            featured_image=featured["url"]
        )

        art = Article(
            title=item["title"],
            slug=item["slug"],
            primary_keyword=item["keyword"],
            secondary_keywords="content strategy, editorial automation, SEO growth",
            search_intent="informational",
            template_type="ultimate_guide",
            summary=item["summary"],
            content=clean_body,
            html_content=html,
            featured_image=featured["url"],
            featured_image_alt=featured["alt"],
            featured_image_caption=featured["caption"],
            image_1_url=img1["url"],
            image_1_alt=img1["alt"],
            image_1_caption=img1["caption"],
            image_2_url=img2["url"],
            image_2_alt=img2["alt"],
            image_2_caption=img2["caption"],
            image_3_url=img3["url"],
            image_3_alt=img3["alt"],
            image_3_caption=img3["caption"],
            category_id=cat.id,
            author_name="TrendBlogo Editorial Staff",
            status="published",
            published_at=datetime.utcnow() - timedelta(days=len(articles_seed) - articles_seed.index(item)),
            word_count=word_count,
            reading_time=item["read_time"],
            seo_title=seo_meta["seo_title"],
            meta_description=seo_meta["meta_description"],
            canonical_url=seo_meta["canonical_url"],
            og_title=seo_meta["og_title"],
            og_description=seo_meta["og_description"],
            quality_score=96.5,
            quality_report=json.dumps({"is_passed": True, "score": 96.5, "warnings": []})
        )
        db.add(art)
        db.flush()

        art.schema_json = SEOEngine.generate_schema_json(art)

        # Connect Tags
        for t_slug in ["content-automation", "seo-architecture"]:
            if t_slug in tag_map:
                db.add(ArticleTag(article_id=art.id, tag_id=tag_map[t_slug].id))

        # Media records
        for img_info in [featured, img1, img2, img3]:
            db.add(Media(
                filename=img_info["filename"],
                file_path=img_info.get("file_path", ""),
                url=img_info["url"],
                media_type="image/svg+xml",
                alt_text=img_info["alt"],
                caption=img_info.get("caption", ""),
                prompt=img_info.get("prompt", ""),
                article_id=art.id
            ))

        print(f"Seeded article: {art.title} (#{art.id})")

    # 6. Sample Queued Keywords
    sample_keywords = [
        ("remote work productivity tips", "informational"),
        ("email marketing automation platforms", "commercial"),
        ("how to conduct technical seo audit", "how_to")
    ]
    for kw_text, intent in sample_keywords:
        if not db.query(Keyword).filter(Keyword.keyword == kw_text).first():
            db.add(Keyword(keyword=kw_text, search_intent=intent, status="queued", priority=1))

    db.commit()
    db.close()
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
