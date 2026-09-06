import json
from datetime import datetime, timedelta
from app.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.article import Article, Category, Tag, ArticleTag
from app.models.links import InternalLink, ExternalLink, RelatedPost
from app.models.media import Media
from app.models.automation import Keyword, GenerationJob
from app.models.settings import SiteSetting, SystemLog, HomepageSection
from app.config import settings

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. Admin / Staff User
    existing_admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
    if not existing_admin:
        pwd_hash, salt = User.hash_password(settings.ADMIN_PASSWORD)
        admin = User(
            email=settings.ADMIN_EMAIL,
            name="TrendBlogo Tech Staff",
            slug="trendblogo-staff",
            title_designation="Senior Technology Editor",
            bio="Lead technology researcher covering foundation AI models, hardware benchmarks, systems architecture, and cybersecurity.",
            password_hash=pwd_hash,
            salt=salt,
            role="admin"
        )
        db.add(admin)
        print(f"Created admin account: {settings.ADMIN_EMAIL}")
    else:
        if not existing_admin.slug:
            existing_admin.slug = "trendblogo-staff"
            existing_admin.title_designation = "Senior Technology Editor"
            existing_admin.bio = "Lead technology researcher covering foundation AI models, hardware benchmarks, systems architecture, and cybersecurity."
            db.commit()

    # 2. Technology Categories
    tech_categories = [
        {"name": "Artificial Intelligence", "slug": "ai", "description": "Foundation LLMs, autonomous agent swarms, multimodal neural models, and machine learning research.", "color": "#6366F1", "icon": "cpu"},
        {"name": "Software & Apps", "slug": "software", "description": "Modern software engineering, open-source frameworks, devtools, and desktop applications.", "color": "#06B6D4", "icon": "code"},
        {"name": "Smartphones", "slug": "smartphones", "description": "Flagship smartphones, iOS and Android mobile architectures, silicon chips, and camera benchmarks.", "color": "#3B82F6", "icon": "smartphone"},
        {"name": "Laptops & Hardware", "slug": "hardware", "description": "Next-gen laptops, desktop silicon, GPUs, workstations, and high-performance hardware gear.", "color": "#EC4899", "icon": "laptop"},
        {"name": "Cybersecurity", "slug": "cybersecurity", "description": "Vulnerability research, zero-day threat telemetry, enterprise encryption, and privacy defense.", "color": "#EF4444", "icon": "shield"},
        {"name": "Cloud Computing & SaaS", "slug": "cloud-saas", "description": "Multi-cloud architecture, Kubernetes, microservices, enterprise SaaS, and infrastructure.", "color": "#8B5CF6", "icon": "cloud"},
        {"name": "How-To Guides", "slug": "how-to", "description": "Actionable step-by-step engineering tutorials, system configuration, and troubleshooting guides.", "color": "#10B981", "icon": "help-circle"},
        {"name": "Reviews & Comparisons", "slug": "reviews", "description": "Rigorous hardware testing, hands-on lab benchmarks, and side-by-side technology comparisons.", "color": "#F59E0B", "icon": "layers"},
        {"name": "Tech News", "slug": "tech-news", "description": "Breaking technology headlines, semiconductor industry shifts, and global digital policy.", "color": "#F43F5E", "icon": "newspaper"},
    ]

    for cat in tech_categories:
        existing = db.query(Category).filter(Category.slug == cat["slug"]).first()
        if not existing:
            # Check by name if slug changed
            existing_by_name = db.query(Category).filter(Category.name == cat["name"]).first()
            if existing_by_name:
                existing_by_name.slug = cat["slug"]
                existing_by_name.description = cat["description"]
                existing_by_name.icon = cat["icon"]
                existing_by_name.color = cat["color"]
            else:
                db.add(Category(**cat))

    # 3. Homepage Sections Configuration
    default_sections = [
        {"section_key": "featured", "title": "Featured Stories", "subtitle": "Lead investigations and technological breakthroughs", "sort_order": 1, "category_slug": None, "is_enabled": True},
        {"section_key": "trending", "title": "Trending Technology", "subtitle": "Real-time dispatches from across the tech landscape", "sort_order": 2, "category_slug": None, "is_enabled": True},
        {"section_key": "latest", "title": "Latest Dispatches", "subtitle": "Chronological stream of research reports and guides", "sort_order": 3, "category_slug": None, "is_enabled": True},
        {"section_key": "ai", "title": "Artificial Intelligence", "subtitle": "Foundation models, autonomous agents, and neural architectures", "sort_order": 4, "category_slug": "ai", "is_enabled": True},
        {"section_key": "smartphones", "title": "Smartphones & Mobile", "subtitle": "Silicon chips, cameras, ecosystem teardowns, and battery metrics", "sort_order": 5, "category_slug": "smartphones", "is_enabled": True},
        {"section_key": "software", "title": "Software & Cloud SaaS", "subtitle": "Modern devtools, enterprise platforms, and serverless stacks", "sort_order": 6, "category_slug": "software", "is_enabled": True},
        {"section_key": "cybersecurity", "title": "Cybersecurity Wire", "subtitle": "Zero-days, breach analysis, threat actors, and privacy defense", "sort_order": 7, "category_slug": "cybersecurity", "is_enabled": True},
        {"section_key": "howto", "title": "How-To Guides & Troubleshooting", "subtitle": "Actionable engineering workflows, fixes, and system optimization", "sort_order": 8, "category_slug": "how-to", "is_enabled": True},
        {"section_key": "reviews", "title": "Reviews & Tech Comparisons", "subtitle": "Rigorous hardware and benchmark comparisons", "sort_order": 9, "category_slug": "reviews", "is_enabled": True},
    ]

    for sec in default_sections:
        existing_sec = db.query(HomepageSection).filter(HomepageSection.section_key == sec["section_key"]).first()
        if not existing_sec:
            db.add(HomepageSection(**sec))

    # 4. Default Site Settings
    default_settings = [
        ("site_name", "TrendBlogo", "general", "Platform display name"),
        ("site_tagline", "Technology, Artificial Intelligence & Modern Systems Journal", "general", "Hero headline & site tagline"),
        ("site_description", "TrendBlogo is an authoritative technology publication covering artificial intelligence, software, hardware, cybersecurity, and digital infrastructure.", "seo", "Global meta description"),
        ("contact_email", "support@trendblogo.com", "general", "Official support contact email"),
        ("editorial_review_required", "true", "general", "Enforce editorial check before live publishing"),
        ("openai_model", "gpt-4o-mini", "api", "Default OpenAI chat model"),
        ("image_provider", "auto", "api", "Image generation engine provider"),
        ("cookie_consent_enabled", "true", "legal", "Display interactive cookie preference banner")
    ]
    for key, val, cat, desc in default_settings:
        existing_setting = db.query(SiteSetting).filter(SiteSetting.key == key).first()
        if not existing_setting:
            db.add(SiteSetting(key=key, value=val, category=cat, description=desc))
        else:
            if key in ["site_tagline", "site_description"]:
                existing_setting.value = val

    db.commit()
    db.close()
    print("Database essential bootstrap completed (technology taxonomy, homepage sections, clean slate).")

if __name__ == "__main__":
    seed_database()


