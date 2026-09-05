# TrendBlogo ? AI-Powered Content Automation & Publishing Platform

TrendBlogo is an enterprise-grade blogging automation platform and content publishing system that transforms keywords into complete, SEO-optimized, human-readable articles.

---

## Key Features

- **Brand Identity & Modern SaaS UI**:
  - Original vector brand identity (`logo.svg`, `logo-dark.svg`, `favicon.svg`).
  - Responsive design with Tailwind CSS, Plus Jakarta Sans & Inter typography, Lucide icons, and mobile navigation drawer.

- **15-Step Automated Pipeline**:
  - Keyword Analysis & Search Intent Identification (Informational, Commercial, How-To)
  - Anti-Cannibalization & Semantic Overlap Detection
  - Structured Heading Hierarchy Generation (H2?H5)
  - **Zero Heading Links Rule**: Enforces plain-text only for all H2?H5 headings; links appear naturally within body copy only.
  - **4 Contextual Visual Assets**: Exactly 1 wide featured banner + 3 in-article section illustrations (4 images total) per post with SEO alt text and captions.
  - Contextual Internal Linking Engine (scans existing database posts for natural semantic placement)
  - Authoritative External Linking Engine (citations to W3C, MDN, Wikipedia, official docs)
  - Automated Schema.org JSON-LD Structured Data (`Article`, `BreadcrumbList`, `Organization`)
  - Automated Quality Control Audit (Flesch readability score, keyword density, heading structure, alt-text presence)
  - Instant Publishing, Scheduling (with configurable delay), or Draft storage.

- **Dual-Engine AI & Image Generation**:
  - Direct OpenAI API integration (`gpt-4o-mini`, `gpt-4o`, DALL-E 3) via secure server-side environment variables.
  - Built-in high-fidelity procedural generation fallback for both structured long-form text and custom thematic vector SVG illustrations, ensuring 100% out-of-the-box reliability.

- **Complete Public Web Pages**:
  - Homepage with interactive pipeline visualizer, feature matrix, live preview, and FAQ
  - Blog archive with search, category filtering chips, sorting (Latest, Most Viewed), and pagination
  - Single article view with breadcrumbs, 4 visual assets, contextual links, related posts, and schema markup
  - Category archives (`/categories` and `/category/{slug}`)
  - Site-wide search (`/search?q=...`) with debounced autocomplete API (`/api/search/suggest`)
  - Informational & Legal: About Us, Contact Us, Guest Posting with submission form, Privacy Policy, Terms & Conditions, Disclaimer, and Cookie Policy with interactive consent center
  - Technical SEO: `/sitemap.xml`, `/robots.txt`, and `/rss.xml`

- **SaaS Admin Dashboard (`/admin`)**:
  - Secure session-based authentication (default: `admin@trendblogo.com` / `Admin123!`)
  - Overview metrics (total articles, published, drafts, scheduled, keywords, images, failed jobs, API calls)
  - 15-step interactive keyword generation wizard
  - Automation queue for batch keyword ingestion with auto-runner and retry controls
  - Content editor with live Heading Hierarchy Inspector, side-by-side Markdown preview, and 4-images manager
  - Media library with copyable URLs
  - Link intelligence audit tables
  - Inquiries manager for contact messages and guest post proposal reviews
  - System audit logs with level filtering

---

## Getting Started

### Prerequisites
- Python 3.10+ (Tested on Python 3.14)

### Installation

1. Clone repository:
```bash
git clone https://github.com/julianebaierr-gif/Trendblogo.git
cd Trendblogo
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
copy .env.example .env
```
*(Optionally add your `OPENAI_API_KEY` in `.env` if you want to use OpenAI models)*

4. Run the application:
```bash
python run.py
```

- Public Website: `http://127.0.0.1:8000`
- Admin Console: `http://127.0.0.1:8000/admin`
  - Email: `admin@trendblogo.com`
  - Password: `Admin123!`

---

## Running Tests

Execute the automated test suite with pytest:

```bash
python -m pytest tests/test_platform.py -v
```

All 12 test suites verify:
- Strict heading link purity (0 hyperlinks in H2?H5)
- Generation of exactly 4 visual assets (1 featured + 3 body)
- Anti-cannibalization detection
- Quality control scoring
- Public routes and single article views
- Admin authentication and full editorial workflows
- API generation endpoints

---

## License

All rights reserved &copy; 2026 TrendBlogo.
