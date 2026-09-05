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

    # Fast-exit if already seeded
    try:
        if db.query(Article).count() > 0:
            db.close()
            return
    except Exception:
        pass

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
    db.close()
    print("Database essential bootstrap completed (clean slate, zero mock articles).")

if __name__ == "__main__":
    seed_database()

