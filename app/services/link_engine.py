import re
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from app.models.article import Article

class LinkEngine:
    AUTHORITATIVE_SOURCES = [
        {"domain": "wikipedia.org", "name": "Wikipedia", "pattern": r"\b(history|overview|definition|encyclopedia)\b", "url": "https://en.wikipedia.org/wiki/"},
        {"domain": "w3.org", "name": "World Wide Web Consortium (W3C)", "pattern": r"\b(standards|accessibility|web standards|protocols)\b", "url": "https://www.w3.org/standards/"},
        {"domain": "developer.mozilla.org", "name": "MDN Web Docs", "pattern": r"\b(web development|javascript|apis|browser standards)\b", "url": "https://developer.mozilla.org/"},
        {"domain": "nist.gov", "name": "National Institute of Standards and Technology", "pattern": r"\b(cybersecurity|encryption|data security|compliance)\b", "url": "https://www.nist.gov/"},
        {"domain": "github.com", "name": "GitHub Open Source", "pattern": r"\b(open source|repository|codebase|developer tools)\b", "url": "https://github.com/topics/"},
        {"domain": "hbr.org", "name": "Harvard Business Review", "pattern": r"\b(leadership|management|productivity strategy|business scale)\b", "url": "https://hbr.org/"},
        {"domain": "acm.org", "name": "Association for Computing Machinery", "pattern": r"\b(computing algorithms|machine learning research|computational models)\b", "url": "https://www.acm.org/"}
    ]

    @classmethod
    def sanitize_headings(cls, markdown_content: str) -> str:
        """
        CRITICAL RULE: Headings (H2-H5) must NEVER contain hyperlinks.
        Strips any [text](url) or <a href="...">text</a> from lines starting with #.
        """
        lines = markdown_content.split("\n")
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("##"):
                # Strip markdown link: [Anchor](url) -> Anchor
                line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
                # Strip HTML link: <a ...>Anchor</a> -> Anchor
                line = re.sub(r"<a\b[^>]*>(.*?)</a>", r"\1", line, flags=re.IGNORECASE)
            cleaned_lines.append(line)
        return "\n".join(cleaned_lines)

    @classmethod
    def inject_internal_links(cls, db: Session, content: str, current_article_id: int = None, max_links: int = 3) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Scans existing published articles and weaves natural internal links into body paragraphs.
        NEVER touches headings or lines starting with #.
        """
        query = db.query(Article).filter(Article.status == "published")
        if current_article_id:
            query = query.filter(Article.id != current_article_id)
        existing_articles = query.all()

        if not existing_articles:
            return content, []

        inserted_links = []
        lines = content.split("\n")
        new_lines = []

        used_target_ids = set()

        for line in lines:
            # Skip headings, quotes, code fences, image tags
            if (line.strip().startswith("#") or 
                line.strip().startswith("!") or 
                line.strip().startswith("```") or 
                line.strip().startswith(">") or 
                len(line.strip()) < 40 or 
                len(inserted_links) >= max_links):
                new_lines.append(line)
                continue

            # Attempt to find a natural keyword phrase match for an existing article
            modified_line = line
            for art in existing_articles:
                if art.id in used_target_ids or len(inserted_links) >= max_links:
                    continue

                kw = art.primary_keyword.strip()
                if not kw or len(kw) < 4:
                    continue

                # Search case-insensitively for keyword without already being part of a link
                pattern = rf"(?<!\[)(?<!/)\b({re.escape(kw)})\b(?![^\[]*\])(?![^\(]*\))"
                match = re.search(pattern, modified_line, flags=re.IGNORECASE)
                if match:
                    matched_text = match.group(1)
                    replacement = f"[{matched_text}](/blog/{art.slug})"
                    modified_line = modified_line[:match.start()] + replacement + modified_line[match.end():]
                    
                    inserted_links.append({
                        "target_article_id": art.id,
                        "title": art.title,
                        "slug": art.slug,
                        "anchor": matched_text,
                        "target_url": f"/blog/{art.slug}"
                    })
                    used_target_ids.add(art.id)
                    break # One link per paragraph max

            new_lines.append(modified_line)

        return "\n".join(new_lines), inserted_links

    @classmethod
    def inject_external_links(cls, content: str, topic_keyword: str, max_links: int = 2) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Injects authoritative external references into body sentences.
        NEVER touches headings.
        """
        inserted_links = []
        lines = content.split("\n")
        new_lines = []

        available_sources = list(cls.AUTHORITATIVE_SOURCES)
        
        for line in lines:
            if (line.strip().startswith("#") or 
                line.strip().startswith("!") or 
                line.strip().startswith("```") or 
                len(line.strip()) < 50 or 
                len(inserted_links) >= max_links):
                new_lines.append(line)
                continue

            modified_line = line
            for src in list(available_sources):
                if len(inserted_links) >= max_links:
                    break
                match = re.search(src["pattern"], modified_line, flags=re.IGNORECASE)
                if match and not "[" in modified_line:
                    matched_text = match.group(1)
                    target_url = src["url"]
                    replacement = f"[{matched_text}]({target_url}){{:target=\"_blank\" rel=\"noopener noreferrer\"}}"
                    modified_line = modified_line[:match.start()] + replacement + modified_line[match.end():]
                    
                    inserted_links.append({
                        "domain": src["domain"],
                        "name": src["name"],
                        "anchor": matched_text,
                        "url": target_url
                    })
                    available_sources.remove(src)
                    break

            new_lines.append(modified_line)

        return "\n".join(new_lines), inserted_links

    @classmethod
    def get_related_posts(cls, db: Session, article_id: int, category_id: int = None, limit: int = 4) -> List[Dict[str, Any]]:
        """
        Finds 3 to 6 contextually related articles based on category and topic proximity.
        """
        query = db.query(Article).filter(
            Article.status == "published",
            Article.id != article_id
        )

        same_category_posts = []
        if category_id:
            same_category_posts = query.filter(Article.category_id == category_id).limit(limit).all()

        other_posts = []
        if len(same_category_posts) < limit:
            remaining = limit - len(same_category_posts)
            exclude_ids = [p.id for p in same_category_posts] + [article_id]
            other_posts = query.filter(~Article.id.in_(exclude_ids)).limit(remaining).all()

        all_related = same_category_posts + other_posts
        
        results = []
        for post in all_related:
            results.append({
                "id": post.id,
                "title": post.title,
                "slug": post.slug,
                "excerpt": post.summary or (post.content[:160] + "..."),
                "featured_image": post.featured_image,
                "category": post.category.name if post.category else "Technology",
                "category_slug": post.category.slug if post.category else "technology",
                "published_at": post.published_at.strftime("%B %d, %Y") if post.published_at else "Recently",
                "reading_time": post.reading_time
            })
        return results
