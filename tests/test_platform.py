import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.article import Article, Category
from app.services.link_engine import LinkEngine
from app.services.image_service import ImageService
from app.services.quality_control import QualityControl
from app.services.duplicate_checker import DuplicateChecker
from app.services.keyword_analyzer import KeywordAnalyzer

client = TestClient(app)

def test_heading_link_purity_sanitization():
    """
    CRITICAL RULE: Headings (H2-H5) must NEVER contain hyperlinks.
    """
    dirty_md = """# Main Title
## [Best AI Tools](https://example.com) for Automation
This is a body paragraph that can have a [valid body link](https://trendblogo.com).

### Key Features of <a href="http://badlink.com">Analytics Suite</a>
Another body sentence.

## Clean Heading Without Links
Clean content."""

    cleaned_md = LinkEngine.sanitize_headings(dirty_md)
    lines = cleaned_md.split("\n")
    
    # Check that H2 and H3 headings have no links
    h2_line = [l for l in lines if l.startswith("## ")][0]
    assert "[" not in h2_line
    assert "https://example.com" not in h2_line
    assert "Best AI Tools for Automation" in h2_line

    h3_line = [l for l in lines if l.startswith("### ")][0]
    assert "<a" not in h3_line
    assert "Analytics Suite" in h3_line

    # Verify body link was preserved
    assert "[valid body link](https://trendblogo.com)" in cleaned_md

def test_four_images_generation():
    """
    CRITICAL RULE: Exactly 1 featured image + 3 in-content images = 4 images total.
    """
    sections = [
        {"h2": "Section One Overview", "h3_list": ["Subtopic A"]},
        {"h2": "Section Two Architecture", "h3_list": ["Subtopic B"]},
        {"h2": "Section Three Benchmarks", "h3_list": ["Subtopic C"]}
    ]
    images = ImageService.create_article_images(
        keyword="automated seo tools",
        title="10 Best Automated SEO Tools for High-Growth Publications",
        outline_sections=sections,
        slug="test-automated-seo-tools"
    )

    assert "featured" in images
    assert "image_1" in images
    assert "image_2" in images
    assert "image_3" in images

    # Exactly 4 images total
    assert len(images["all_images"]) == 4

    # Verify attributes
    for key in ["featured", "image_1", "image_2", "image_3"]:
        img = images[key]
        assert img["url"].startswith("/static/uploads/")
        assert img["alt"] != ""
        assert img["filename"].endswith(".svg")

def test_anti_cannibalization_checker():
    db = SessionLocal()
    # Test checking for an existing seeded keyword
    result = DuplicateChecker.check(db, "ai content automation")
    assert result["has_collision"] is True
    assert result["risk_level"] in ["high", "moderate"]

    # Test checking for a unique new keyword
    unique_result = DuplicateChecker.check(db, "quantum cryptography for deep space satellites")
    assert unique_result["has_collision"] is False
    assert unique_result["risk_level"] == "none"
    db.close()

def test_quality_control_audit():
    # Create a realistic 600+ word test article
    p1 = "Understanding modern cloud systems requires structured engineering discipline and strategic architectural foresight across all operational parameters. " * 15
    p2 = "Evaluating throughput, latency, and fault-tolerance boundaries allows engineering teams to eliminate bottlenecks before rolling out production workloads. " * 15
    p3 = "By establishing continuous telemetry monitoring, teams ensure high indexation velocity and resilient infrastructure uptime across distributed regions. " * 15
    valid_content = f"""# Test Title
## Foundations of Modern Cloud Systems
{p1}

## Implementation Metrics
{p2}

## Production Deployment Tactics
{p3}

## Frequently Asked Questions About Modern Cloud Systems
Q: What is key? A: Structured benchmarks.
"""

    report = QualityControl.audit(
        keyword="modern cloud systems",
        title="Mastering Modern Cloud Systems",
        content=valid_content,
        featured_image="/static/uploads/test-featured.svg",
        in_content_images=[
            {"url": "/img1.svg", "alt": "Alt 1"},
            {"url": "/img2.svg", "alt": "Alt 2"},
            {"url": "/img3.svg", "alt": "Alt 3"}
        ],
        internal_links_count=1,
        external_links_count=1
    )

    assert report["heading_links_found"] == 0
    assert report["score"] >= 80.0
    assert report["is_passed"] is True

def test_public_pages():
    # Home
    res = client.get("/")
    assert res.status_code == 200
    assert "TrendBlogo" in res.text
    assert "Turn Keywords Into" in res.text

    # Blog list
    res = client.get("/blog")
    assert res.status_code == 200
    assert "Editorial Archives" in res.text

    # Informational & Legal Pages
    pages = ["/about", "/contact", "/guest-posting", "/privacy-policy", "/terms-and-conditions", "/disclaimer", "/cookie-policy", "/categories"]
    for p in pages:
        r = client.get(p)
        assert r.status_code == 200, f"Page {p} returned {r.status_code}"

    # Sitemap and Robots
    res_sitemap = client.get("/sitemap.xml")
    assert res_sitemap.status_code == 200
    assert "urlset" in res_sitemap.text

    res_robots = client.get("/robots.txt")
    assert res_robots.status_code == 200
    assert "Disallow: /admin" in res_robots.text

    res_rss = client.get("/rss.xml")
    assert res_rss.status_code == 200
    assert "<rss" in res_rss.text

def test_single_article_page():
    db = SessionLocal()
    art = db.query(Article).filter(Article.status == "published").first()
    db.close()
    assert art is not None

    res = client.get(f"/blog/{art.slug}")
    assert res.status_code == 200
    assert art.title in res.text
    assert art.featured_image in res.text
    assert "Related Knowledge" in res.text

def test_admin_auth_and_dashboard():
    # Unauthenticated access redirects to /admin/login
    res = client.get("/admin", follow_redirects=False)
    assert res.status_code in [302, 303, 307]
    assert "/admin/login" in res.headers.get("location", "")

    # Login
    res_login = client.post("/admin/login", data={"email": "admin@trendblogo.com", "password": "Admin123!"}, follow_redirects=False)
    assert res_login.status_code == 303
    cookies = res_login.cookies
    assert "tb_session" in cookies

    # Access dashboard with cookie
    res_dash = client.get("/admin", cookies=cookies)
    assert res_dash.status_code == 200
    assert "System Overview" in res_dash.text
    assert "Total Articles" in res_dash.text

def test_api_keyword_analyze_and_generate():
    # Test keyword analysis
    res_an = client.post("/api/keywords/analyze", json={"keyword": "best productivity tools"})
    assert res_an.status_code == 200
    data_an = res_an.json()
    assert "search_intent" in data_an
    assert "outline" in data_an

    # Test full generation pipeline via API
    res_gen = client.post("/api/articles/generate", json={
        "keyword": "enterprise workflow automation",
        "secondary_keywords": "scalability, cicd, devops",
        "tone": "informative",
        "target_word_count": 1200,
        "publish_mode": "published"
    })
    assert res_gen.status_code == 200
    data_gen = res_gen.json()
    assert data_gen["success"] is True
    assert "slug" in data_gen
    assert data_gen["quality_score"] >= 80.0

    # Verify generated article is live
    res_live = client.get(f"/blog/{data_gen['slug']}")
    assert res_live.status_code == 200
    assert data_gen["title"] in res_live.text


def test_guest_post_submission():
    res = client.post("/guest-posting", data={
        "author_name": "Test Contributor",
        "email": "contributor@example.com",
        "website": "https://contributor.io",
        "topic_category": "AI & Automation",
        "proposed_title": "Novel Approaches to Vector Embeddings",
        "article_outline": "H2: Vector Spaces\nH3: Cosine Distance\nH2: Performance",
        "author_bio": "AI Engineer",
        "message": "Excited to share insights.",
        "agreed": "true"
    })
    assert res.status_code == 200
    assert "Proposal Submitted" in res.text or "has been received" in res.text

def test_contact_form_submission():
    res = client.post("/contact", data={
        "name": "Sarah Connor",
        "email": "sarah@resistance.org",
        "subject": "Platform Partnership",
        "message": "Inquiring about syndication rights for TrendBlogo articles."
    })
    assert res.status_code == 200
    assert "Message Received" in res.text or "Thank you" in res.text

def test_search_and_category_archives():
    res_search = client.get("/search?q=automation")
    assert res_search.status_code == 200
    assert "Results for" in res_search.text

    res_cat = client.get("/category/ai-and-automation")
    assert res_cat.status_code == 200
    assert "AI &amp; Automation" in res_cat.text or "Automation" in res_cat.text

def test_admin_full_workflow():
    # Login as admin
    res_login = client.post("/admin/login", data={"email": "admin@trendblogo.com", "password": "Admin123!"}, follow_redirects=False)
    cookies = res_login.cookies

    # Batch Add Keywords to Queue
    res_batch = client.post("/admin/queue/batch-add", data={
        "raw_keywords": "quantum machine learning\nedge computing architectures",
        "publish_mode": "draft"
    }, cookies=cookies, follow_redirects=False)
    assert res_batch.status_code == 303

    # Check Queue View
    res_queue = client.get("/admin/queue", cookies=cookies)
    assert res_queue.status_code == 200
    assert "quantum machine learning" in res_queue.text

    # Check Media View
    res_media = client.get("/admin/media", cookies=cookies)
    assert res_media.status_code == 200
    assert "Visual Assets Gallery" in res_media.text

    # Check Links View
    res_links = client.get("/admin/links", cookies=cookies)
    assert res_links.status_code == 200
    assert "Link Intelligence" in res_links.text

    # Check Guest Posts View
    res_gp = client.get("/admin/guest-posts", cookies=cookies)
    assert res_gp.status_code == 200
    assert "Test Contributor" in res_gp.text

    # Check Messages View
    res_msg = client.get("/admin/messages", cookies=cookies)
    assert res_msg.status_code == 200
    assert "Sarah Connor" in res_msg.text

    # Update Settings
    res_set = client.post("/admin/settings", data={
        "site_name": "TrendBlogo Enterprise",
        "site_tagline": "Autonomous Content Publishing Engine",
        "site_description": "Enterprise SEO publishing platform.",
        "contact_email": "editorial@trendblogo.com",
        "openai_model": "gpt-4o-mini",
        "image_provider": "auto"
    }, cookies=cookies, follow_redirects=False)
    assert res_set.status_code == 303

    # Check Logs View
    res_logs = client.get("/admin/logs", cookies=cookies)
    assert res_logs.status_code == 200
    assert "System &" in res_logs.text

def test_openai_api_key_configuration_and_tester():
    # Login as admin
    res_login = client.post("/admin/login", data={"email": "admin@trendblogo.com", "password": "Admin123!"}, follow_redirects=False)
    cookies = res_login.cookies

    # Test key endpoint with empty key
    res_empty = client.post("/admin/api/test-openai-key", json={"api_key": ""}, cookies=cookies)
    assert res_empty.status_code == 200
    data_empty = res_empty.json()
    assert data_empty["success"] is False
    assert "empty" in data_empty["message"].lower()

    # Save a custom OpenAI key and model via settings
    test_key = "sk-proj-test1234567890abcdefghijklmnopqrstuvwxyz"
    res_save = client.post("/admin/settings", data={
        "site_name": "TrendBlogo AI",
        "site_tagline": "AI Generated Content",
        "site_description": "Powered by OpenAI ChatGPT & DALL-E",
        "contact_email": "admin@trendblogo.com",
        "openai_api_key": test_key,
        "openai_model": "gpt-4o",
        "image_provider": "auto"
    }, cookies=cookies, follow_redirects=False)
    assert res_save.status_code == 303

    # Check that settings page displays the configured key
    res_settings = client.get("/admin/settings", cookies=cookies)
    assert res_settings.status_code == 200
    assert test_key in res_settings.text
    assert "API Key Active" in res_settings.text

    # Verify AIGenerator dynamically detects this active key
    from app.services.ai_generator import AIGenerator
    with SessionLocal() as db:
        resolved_key = AIGenerator.get_active_api_key(db)
        resolved_model = AIGenerator.get_active_model(db)
        assert resolved_key == test_key
        assert resolved_model == "gpt-4o"


