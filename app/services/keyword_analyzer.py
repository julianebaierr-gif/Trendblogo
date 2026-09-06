import re
import hashlib
from typing import Dict, Any, List

class KeywordAnalyzer:
    CATEGORY_KEYWORDS = {
        "Health": [
            "health", "fitness", "diet", "nutrition", "workout", "weight", "wellness",
            "mental", "sleep", "medical", "doctor", "yoga", "exercise", "supplement",
            "skincare", "skin", "muscle", "disease", "pain", "therapy", "remedy",
            "cardio", "gut", "immune", "organic", "calorie", "fasting", "longevity"
        ],
        "Tech": [
            "tech", "ai", "artificial intelligence", "software", "hardware", "app",
            "code", "coding", "python", "javascript", "developer", "cloud", "server",
            "computer", "laptop", "phone", "gadget", "cybersecurity", "automation",
            "api", "database", "devops", "robotics", "machine learning", "crypto",
            "blockchain", "data", "network", "digital", "algorithm", "saas", "seo"
        ],
        "News": [
            "news", "breaking", "update", "report", "election", "politics", "global",
            "summit", "policy", "regulation", "market", "inflation", "economy",
            "crisis", "press", "announcement", "conference", "treaty"
        ],
        "Lifestyle": [
            "lifestyle", "travel", "home", "routine", "productivity", "habit",
            "decor", "interior", "fashion", "style", "mindful", "remote work",
            "hobbies", "relationships", "family", "parenting", "cooking", "recipe",
            "coffee", "minimalism", "budget", "living", "life"
        ]
    }

    INTENT_KEYWORDS = {
        "transactional": ["buy", "discount", "pricing", "cost", "cheap", "deal", "order", "coupon"],
        "commercial": ["best", "top", "review", "vs", "versus", "comparison", "alternative", "recommended"],
        "how_to": ["how to", "step by step", "guide", "tutorial", "build", "create", "setup", "install"],
        "informational": ["what is", "why", "benefits", "strategies", "tips", "types", "examples", "guide"]
    }


    @classmethod
    def analyze(cls, keyword: str, secondary_keywords: List[str] = None) -> Dict[str, Any]:
        kw_clean = keyword.strip().lower()
        
        # Determine intent
        intent = "informational"
        for potential_intent, triggers in cls.INTENT_KEYWORDS.items():
            if any(trigger in kw_clean for trigger in triggers):
                intent = potential_intent
                break
        
        # Determine template
        if "best" in kw_clean or "top" in kw_clean or "list" in kw_clean:
            template = "listicle"
        elif "vs" in kw_clean or "versus" in kw_clean or "comparison" in kw_clean:
            template = "comparison"
        elif "how to" in kw_clean or "tutorial" in kw_clean:
            template = "how_to"
        elif "review" in kw_clean:
            template = "review"
        else:
            template = "ultimate_guide"

        # Determine target audience
        audience = "Tech-forward professionals, entrepreneurs, and digital teams"
        if any(w in kw_clean for w in ["beginner", "student", "starter"]):
            audience = "Beginners and learners looking for actionable fundamentals"
        elif any(w in kw_clean for w in ["enterprise", "scale", "architect", "developer"]):
            audience = "Enterprise leaders, developers, and technical decision-makers"

        # Generate structured heading outline
        outline = cls._generate_outline(keyword, intent, template)

        # Generate clean slug
        slug = re.sub(r"[^a-zA-Z0-9\s-]", "", kw_clean)
        slug = re.sub(r"[\s_]+", "-", slug).strip("-")

        # Detect suggested category
        detected_category = cls.detect_category_name(keyword)

        return {
            "primary_keyword": keyword.strip(),
            "secondary_keywords": secondary_keywords or [],
            "search_intent": intent,
            "template_type": template,
            "target_audience": audience,
            "suggested_slug": slug,
            "suggested_category": detected_category,
            "outline": outline
        }

    @classmethod
    def detect_category_name(cls, keyword: str) -> str:
        kw = keyword.lower().strip()
        
        # 1. Exact word boundary match
        for cat_name, triggers in cls.CATEGORY_KEYWORDS.items():
            if any(re.search(r"\b" + re.escape(tr) + r"\b", kw) for tr in triggers):
                return cat_name
                
        # 2. Substring match
        for cat_name, triggers in cls.CATEGORY_KEYWORDS.items():
            if any(tr in kw for tr in triggers):
                return cat_name

        # 3. Dynamic smart category extraction if noun present
        stop_words = {"best", "top", "guide", "tutorial", "tips", "review", "for", "the", "and", "with", "from", "how", "what"}
        words = [w for w in re.findall(r"[a-zA-Z]+", kw) if len(w) > 3 and w not in stop_words]
        if words:
            candidate = words[0].capitalize()
            if len(candidate) <= 15:
                return candidate

        return "Tech"

    @classmethod
    def resolve_or_create_category(cls, db, keyword: str):
        from app.models.article import Category
        cat_name = cls.detect_category_name(keyword)

        # Look up existing category by name
        cat = db.query(Category).filter(Category.name.ilike(cat_name.strip())).first()
        if cat:
            return cat

        # Check by slug
        clean_slug = re.sub(r"[^a-zA-Z0-9-]", "", cat_name.lower().replace(" ", "-")).strip("-")
        cat = db.query(Category).filter(Category.slug == clean_slug).first()
        if cat:
            return cat

        # Auto-create the category if not found!
        colors = ["#2563EB", "#10B981", "#DC2626", "#8B5CF6", "#F59E0B", "#06B6D4", "#EC4899"]
        color_idx = int(hashlib.md5(cat_name.encode()).hexdigest(), 16) % len(colors)

        new_cat = Category(
            name=cat_name,
            slug=clean_slug,
            description=f"Curated analysis, dispatches, and tactical frameworks exploring {cat_name.lower()}.",
            color=colors[color_idx]
        )
        db.add(new_cat)
        db.commit()
        db.refresh(new_cat)
        return new_cat

    @classmethod
    def _generate_outline(cls, keyword: str, intent: str, template: str) -> List[Dict[str, Any]]:
        kw_cap = keyword.title()
        
        if template == "listicle":
            return [
                {
                    "h2": f"Understanding {kw_cap}: An Industry Overview",
                    "h3_list": ["The Evolution of Current Solutions", "Key Selection Criteria"]
                },
                {
                    "h2": f"Top Recommended Options for {kw_cap}",
                    "h3_list": ["Feature Breakdown & Core Capabilities", "Performance Benchmarks & Usability"]
                },
                {
                    "h2": f"Implementation Blueprint and Integration Strategies",
                    "h3_list": ["Step-by-Step Setup Guide", "Avoiding Common Pitfalls"]
                },
                {
                    "h2": f"Comparative Evaluation and Value Matrix",
                    "h3_list": ["Cost vs ROI Analysis", "Long-Term Scalability Factors"]
                },
                {
                    "h2": f"Frequently Asked Questions About {kw_cap}",
                    "h3_list": []
                },
                {
                    "h2": "Final Takeaways and Expert Recommendation",
                    "h3_list": []
                }
            ]
        elif template == "comparison":
            return [
                {
                    "h2": f"Executive Summary: {kw_cap}",
                    "h3_list": ["Core Philosophy and Architecture", "Target Use Cases"]
                },
                {
                    "h2": "Feature-by-Feature Deep Dive",
                    "h3_list": ["Efficiency and Productivity Gains", "User Experience and Learning Curve"]
                },
                {
                    "h2": "Pricing, Licensing, and Total Cost of Ownership",
                    "h3_list": ["Direct Costs vs Hidden Overheads", "Resource Allocation"]
                },
                {
                    "h2": "Decision Framework: Which Solution Fits Your Workflow?",
                    "h3_list": ["When to Choose Option A", "When to Choose Option B"]
                },
                {
                    "h2": f"Frequently Asked Questions About {kw_cap}",
                    "h3_list": []
                },
                {
                    "h2": "Final Verdict",
                    "h3_list": []
                }
            ]
        else: # Ultimate Guide / How-To
            return [
                {
                    "h2": f"Foundations of {kw_cap}",
                    "h3_list": ["Core Principles and Definitions", "Why It Matters in Today's Digital Landscape"]
                },
                {
                    "h2": f"Strategic Framework for Mastering {kw_cap}",
                    "h3_list": ["Key Architecture & Components", "Workflow Optimization Tactics"]
                },
                {
                    "h2": f"Best Practices and Practical Execution",
                    "h3_list": ["Actionable Step-by-Step Methodology", "Quality Assurance and Monitoring"]
                },
                {
                    "h2": "Advanced Tactics and Emerging Trends",
                    "h3_list": ["Automation & Efficiency Multipliers", "Future-Proofing Your Approach"]
                },
                {
                    "h2": f"Frequently Asked Questions About {kw_cap}",
                    "h3_list": []
                },
                {
                    "h2": "Summary and Next Steps",
                    "h3_list": []
                }
            ]
