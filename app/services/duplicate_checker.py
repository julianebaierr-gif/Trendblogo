import re
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.article import Article

class DuplicateChecker:
    @classmethod
    def check(cls, db: Session, keyword: str, current_article_id: int = None) -> Dict[str, Any]:
        kw_clean = keyword.strip().lower()
        target_tokens = set(re.findall(r"\w+", kw_clean))
        
        query = db.query(Article)
        if current_article_id:
            query = query.filter(Article.id != current_article_id)
        articles = query.all()

        exact_matches = []
        similar_articles = []

        for art in articles:
            art_kw = (art.primary_keyword or "").strip().lower()
            art_title = (art.title or "").strip().lower()
            
            # Exact keyword match
            if art_kw == kw_clean:
                exact_matches.append({
                    "id": art.id,
                    "title": art.title,
                    "slug": art.slug,
                    "keyword": art.primary_keyword,
                    "match_type": "exact_keyword"
                })
                continue

            # Token overlap similarity
            art_tokens = set(re.findall(r"\w+", art_kw + " " + art_title))
            intersection = target_tokens.intersection(art_tokens)
            if target_tokens and len(intersection) >= max(2, int(len(target_tokens) * 0.65)):
                similarity_ratio = len(intersection) / max(len(target_tokens), 1)
                similar_articles.append({
                    "id": art.id,
                    "title": art.title,
                    "slug": art.slug,
                    "keyword": art.primary_keyword,
                    "similarity": round(similarity_ratio * 100, 1)
                })

        has_exact = len(exact_matches) > 0
        has_similar = len(similar_articles) > 0
        risk_level = "high" if has_exact else ("moderate" if has_similar else "none")

        warnings = []
        if has_exact:
            warnings.append(f"An existing article already targets the exact keyword '{keyword}'. Consider targeting a distinct secondary intent or updating the existing post.")
        if has_similar:
            warnings.append(f"Found {len(similar_articles)} potentially overlapping article(s) that might cause keyword cannibalization.")

        return {
            "keyword": keyword,
            "risk_level": risk_level,
            "has_collision": has_exact or has_similar,
            "warnings": warnings,
            "exact_matches": exact_matches,
            "similar_articles": similar_articles
        }
