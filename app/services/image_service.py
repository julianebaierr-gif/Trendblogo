import os
import re
import random
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from app.config import settings

class ImageService:
    THEME_PALETTES = [
        {"bg1": "#1E1B4B", "bg2": "#312E81", "accent": "#818CF8", "glow": "#C7D2FE", "name": "indigo_nebula"},
        {"bg1": "#0F172A", "bg2": "#1E293B", "accent": "#38BDF8", "glow": "#7DD3FC", "name": "slate_cyan"},
        {"bg1": "#141E30", "bg2": "#243B55", "accent": "#2DD4BF", "glow": "#99F6E4", "name": "teal_flow"},
        {"bg1": "#18181B", "bg2": "#27272A", "accent": "#A855F7", "glow": "#E9D5FF", "name": "violet_deep"},
        {"bg1": "#0C1A30", "bg2": "#1D3557", "accent": "#457B9D", "glow": "#A8DADC", "name": "blue_arctic"},
    ]

    @classmethod
    def generate_image_prompts(cls, keyword: str, title: str, outline_sections: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Creates exactly 4 prompt specs:
        1. Featured/Hero Image
        2. In-Article Image #1
        3. In-Article Image #2
        4. In-Article Image #3
        """
        prompts = []
        
        # 1. Featured Image
        prompts.append({
            "type": "featured",
            "section_title": "Hero Overview",
            "prompt": f"A clean, modern, ultra-sharp 3D isometric concept illustration of {keyword}, futuristic digital dashboard, glowing network nodes, gradient lighting, minimalist tech aesthetic, 8k resolution, suitable for tech editorial banner.",
            "alt_text": f"Comprehensive guide to {keyword} - TrendBlogo featured illustration",
            "caption": f"Strategic overview of modern {keyword} workflows and technological architecture."
        })

        # Section 1 Image
        sec1_title = outline_sections[0]["h2"] if len(outline_sections) > 0 else f"{keyword} Fundamentals"
        prompts.append({
            "type": "in_article_1",
            "section_title": sec1_title,
            "prompt": f"Minimalist modern illustration representing {sec1_title}, modular components, clean typography accents, blue and purple gradient color scheme, high contrast, professional digital publication graphic.",
            "alt_text": f"{sec1_title} - Architectural components and foundational principles",
            "caption": f"Core operational components and foundational framework."
        })

        # Section 2 Image
        sec2_title = outline_sections[1]["h2"] if len(outline_sections) > 1 else f"Optimizing {keyword}"
        prompts.append({
            "type": "in_article_2",
            "section_title": sec2_title,
            "prompt": f"High-tech analytical visualization showing {sec2_title}, data metrics, glowing telemetry graphs, isometric cloud integration, modern dark UI styling, sleek aesthetic.",
            "alt_text": f"{sec2_title} - Performance benchmarks and analytical comparison",
            "caption": f"Comparative performance analysis and execution efficiency metrics."
        })

        # Section 3 Image
        sec3_title = outline_sections[2]["h2"] if len(outline_sections) > 2 else f"Advanced {keyword} Implementation"
        prompts.append({
            "type": "in_article_3",
            "section_title": sec3_title,
            "prompt": f"Futuristic blueprint concept representing {sec3_title}, automated pipeline lines, smart nodes, cybernetic productivity icons, crisp vector style, vibrant neon accents.",
            "alt_text": f"{sec3_title} - Execution blueprint and workflow integration",
            "caption": f"Production deployment blueprint and long-term scaling considerations."
        })

        return prompts

    @classmethod
    def get_active_credentials(cls, db: Optional[Any] = None) -> Tuple[str, str]:
        from app.models.settings import SiteSetting
        api_key = ""
        provider = "auto"
        if db:
            try:
                s_key = db.query(SiteSetting).filter(SiteSetting.key == "openai_api_key").first()
                if s_key and s_key.value and s_key.value.strip():
                    api_key = s_key.value.strip()
                s_prov = db.query(SiteSetting).filter(SiteSetting.key == "image_provider").first()
                if s_prov and s_prov.value and s_prov.value.strip():
                    provider = s_prov.value.strip()
            except Exception:
                pass

        
        if not api_key:
            try:
                from app.database import SessionLocal
                with SessionLocal() as session:
                    s_key = session.query(SiteSetting).filter(SiteSetting.key == "openai_api_key").first()
                    if s_key and s_key.value and s_key.value.strip():
                        api_key = s_key.value.strip()
                    s_prov = session.query(SiteSetting).filter(SiteSetting.key == "image_provider").first()
                    if s_prov and s_prov.value and s_prov.value.strip():
                        provider = s_prov.value.strip()
            except Exception:
                pass
                
        if not api_key:
            api_key = (settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")).strip()
        if provider == "auto" and settings.IMAGE_GENERATION_PROVIDER != "auto":
            provider = settings.IMAGE_GENERATION_PROVIDER
            
        return api_key, provider

    @classmethod
    def create_article_images(
        cls,
        keyword: str,
        title: str,
        outline_sections: List[Dict[str, Any]],
        slug: str,
        db: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Generates exactly 4 images (1 featured + 3 in-article).
        Uses OpenAI DALL-E if API key is provided and enabled, otherwise generates high-aesthetic vector SVGs.
        """
        prompt_specs = cls.generate_image_prompts(keyword, title, outline_sections)
        results = {}
        api_key, provider = cls.get_active_credentials(db)

        for idx, spec in enumerate(prompt_specs):
            img_type = spec["type"]
            image_generated = False
            filename = f"{slug}-{img_type}.svg"
            file_path = settings.UPLOADS_DIR / filename
            rel_url = f"/static/uploads/{filename}"

            # If user configured OpenAI DALL-E and provided API key
            if api_key and provider in ("openai", "dall-e-3", "dall-e-2", "auto"):
                try:
                    from openai import OpenAI
                    import base64
                    client = OpenAI(api_key=api_key, timeout=30.0)
                    model_to_use = "dall-e-3" if provider in ("openai", "dall-e-3") else "dall-e-2"
                    img_prompt = spec["prompt"][:950]
                    img_resp = client.images.generate(
                        model=model_to_use,
                        prompt=img_prompt,
                        n=1,
                        size="1024x1024",
                        response_format="b64_json"
                    )
                    b64_data = img_resp.data[0].b64_json
                    img_bytes = base64.b64decode(b64_data)
                    png_filename = f"{slug}-{img_type}.png"
                    png_path = settings.UPLOADS_DIR / png_filename
                    with open(png_path, "wb") as f_png:
                        f_png.write(img_bytes)
                    
                    filename = png_filename
                    file_path = png_path
                    rel_url = f"/static/uploads/{png_filename}"
                    image_generated = True
                except Exception as e_dalle:
                    print(f"DALL-E image generation notice ({img_type}): {e_dalle}. Falling back to procedural vector graphic.")

            # Fallback to high-aesthetic procedural vector SVG
            if not image_generated:
                filename = f"{slug}-{img_type}.svg"
                file_path = settings.UPLOADS_DIR / filename
                rel_url = f"/static/uploads/{filename}"
                palette = cls.THEME_PALETTES[idx % len(cls.THEME_PALETTES)]
                svg_content = cls._render_vector_image(
                    title=spec["section_title"],
                    subtitle=keyword.upper(),
                    img_type=img_type,
                    palette=palette,
                    idx=idx
                )
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(svg_content)

            results[img_type] = {
                "url": rel_url,
                "file_path": str(file_path),
                "filename": filename,
                "alt": spec["alt_text"],
                "caption": spec["caption"],
                "prompt": spec["prompt"]
            }

        return {
            "featured": results["featured"],
            "image_1": results["in_article_1"],
            "image_2": results["in_article_2"],
            "image_3": results["in_article_3"],
            "all_images": results
        }

    @classmethod
    def _render_vector_image(cls, title: str, subtitle: str, img_type: str, palette: Dict[str, str], idx: int) -> str:
        width = 1200
        height = 630 if img_type == "featured" else 675
        
        clean_title = re.sub(r"[^a-zA-Z0-9\s:,-]", "", title)[:52]
        if len(title) > 52:
            clean_title += "..."

        # Unique motifs for each image
        motif_svg = cls._get_motif_svg(idx, palette)

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" fill="none">
  <defs>
    <linearGradient id="bgGrad_{idx}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{palette['bg1']}" />
      <stop offset="100%" stop-color="{palette['bg2']}" />
    </linearGradient>
    <linearGradient id="accGrad_{idx}" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{palette['accent']}" />
      <stop offset="100%" stop-color="{palette['glow']}" />
    </linearGradient>
    <filter id="blurFilter_{idx}" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="60" result="blur" />
    </filter>
    <pattern id="grid_{idx}" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255, 255, 255, 0.05)" stroke-width="1" />
    </pattern>
  </defs>

  <!-- Background Base -->
  <rect width="{width}" height="{height}" fill="url(#bgGrad_{idx})" />
  <rect width="{width}" height="{height}" fill="url(#grid_{idx})" />

  <!-- Ambient Glow Orbs -->
  <circle cx="200" cy="180" r="180" fill="{palette['accent']}" opacity="0.22" filter="url(#blurFilter_{idx})" />
  <circle cx="1000" cy="450" r="220" fill="{palette['glow']}" opacity="0.18" filter="url(#blurFilter_{idx})" />

  <!-- Thematic Center Illustration Graphic -->
  <g transform="translate(620, 100)">
    {motif_svg}
  </g>

  <!-- Content Banner / Overlay Card -->
  <g transform="translate(80, 160)">
    <!-- Category Badge -->
    <rect x="0" y="0" width="220" height="38" rx="8" fill="rgba(255, 255, 255, 0.08)" stroke="rgba(255, 255, 255, 0.15)" />
    <circle cx="24" cy="19" r="6" fill="{palette['accent']}" />
    <text x="40" y="24" font-family="system-ui, -apple-system, sans-serif" font-size="13" font-weight="700" letter-spacing="1.5" fill="{palette['glow']}">{subtitle}</text>

    <!-- Main Title -->
    <text x="0" y="90" font-family="system-ui, -apple-system, sans-serif" font-size="38" font-weight="800" fill="#FFFFFF" letter-spacing="-0.5">{clean_title}</text>
    
    <!-- Meta details -->
    <text x="0" y="145" font-family="system-ui, -apple-system, sans-serif" font-size="16" font-weight="500" fill="rgba(255, 255, 255, 0.65)">TrendBlogo Intelligence ? Automated Editorial Architecture</text>

    <!-- Visual Indicator Line -->
    <rect x="0" y="180" width="120" height="4" rx="2" fill="url(#accGrad_{idx})" />
  </g>

  <!-- Watermark / Brand Badge -->
  <g transform="translate(80, {height - 70})">
    <rect x="0" y="0" width="150" height="32" rx="6" fill="rgba(15, 23, 42, 0.6)" stroke="rgba(255, 255, 255, 0.1)" />
    <text x="14" y="20" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="700" fill="#F8FAFC">TrendBlogo AI</text>
  </g>
</svg>"""
        return svg

    @classmethod
    def _get_motif_svg(cls, idx: int, palette: Dict[str, str]) -> str:
        acc = palette["accent"]
        glow = palette["glow"]
        if idx == 0:  # Featured: Modern Isometric Platform + Growth Spark
            return f"""
            <polygon points="240,40 440,150 240,260 40,150" fill="rgba(255,255,255,0.04)" stroke="{acc}" stroke-width="2" />
            <polygon points="240,90 380,170 240,250 100,170" fill="rgba(255,255,255,0.08)" stroke="{glow}" stroke-width="1.5" />
            <line x1="240" y1="260" x2="240" y2="360" stroke="{acc}" stroke-width="2" stroke-dasharray="6,6" />
            <!-- Floating Data Cubes -->
            <rect x="180" y="100" width="50" height="50" rx="8" fill="{acc}" opacity="0.85" />
            <rect x="270" y="70" width="40" height="40" rx="6" fill="{glow}" opacity="0.9" />
            <circle cx="240" cy="150" r="16" fill="#FFFFFF" />
            <circle cx="240" cy="150" r="32" stroke="{glow}" stroke-width="2" opacity="0.6" />
            """
        elif idx == 1: # Section 1: Network Matrix Nodes
            return f"""
            <circle cx="200" cy="160" r="70" fill="none" stroke="{acc}" stroke-width="2" />
            <circle cx="360" cy="120" r="50" fill="none" stroke="{glow}" stroke-width="2" />
            <circle cx="280" cy="280" r="60" fill="none" stroke="{acc}" stroke-width="1.5" />
            <line x1="200" y1="160" x2="360" y2="120" stroke="{acc}" stroke-width="2" />
            <line x1="360" y1="120" x2="280" y2="280" stroke="{glow}" stroke-width="2" />
            <line x1="280" y1="280" x2="200" y2="160" stroke="{acc}" stroke-width="2" />
            <circle cx="200" cy="160" r="14" fill="{acc}" />
            <circle cx="360" cy="120" r="12" fill="{glow}" />
            <circle cx="280" cy="280" r="16" fill="#FFFFFF" />
            """
        elif idx == 2: # Section 2: Analytical Telemetry Charts
            return f"""
            <rect x="80" y="60" width="360" height="240" rx="14" fill="rgba(255,255,255,0.03)" stroke="{acc}" stroke-width="1.5" />
            <path d="M 110 240 L 170 190 L 230 210 L 290 130 L 350 160 L 410 90" fill="none" stroke="{glow}" stroke-width="4" stroke-linecap="round" />
            <circle cx="410" cy="90" r="6" fill="#FFFFFF" stroke="{acc}" stroke-width="2" />
            <line x1="110" y1="260" x2="410" y2="260" stroke="rgba(255,255,255,0.2)" stroke-width="2" />
            <rect x="140" y="210" width="24" height="50" rx="4" fill="{acc}" opacity="0.4" />
            <rect x="200" y="180" width="24" height="80" rx="4" fill="{acc}" opacity="0.6" />
            <rect x="260" y="140" width="24" height="120" rx="4" fill="{glow}" opacity="0.8" />
            <rect x="320" y="110" width="24" height="150" rx="4" fill="#FFFFFF" opacity="0.9" />
            """
        else: # Section 3: Smart Execution Pipeline
            return f"""
            <rect x="100" y="120" width="100" height="70" rx="10" fill="{acc}" opacity="0.85" />
            <rect x="250" y="120" width="100" height="70" rx="10" fill="{glow}" opacity="0.85" />
            <rect x="400" y="120" width="100" height="70" rx="10" fill="#FFFFFF" opacity="0.95" />
            <path d="M 200 155 L 250 155" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" />
            <path d="M 350 155 L 400 155" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" />
            <circle cx="150" cy="155" r="10" fill="#FFFFFF" />
            <circle cx="300" cy="155" r="10" fill="{acc}" />
            <circle cx="450" cy="155" r="10" fill="{glow}" />
            """
