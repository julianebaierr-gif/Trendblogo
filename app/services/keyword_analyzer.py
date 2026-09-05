import re
from typing import Dict, Any, List

class KeywordAnalyzer:
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

        return {
            "primary_keyword": keyword.strip(),
            "secondary_keywords": secondary_keywords or [],
            "search_intent": intent,
            "template_type": template,
            "target_audience": audience,
            "suggested_slug": slug,
            "outline": outline
        }

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
