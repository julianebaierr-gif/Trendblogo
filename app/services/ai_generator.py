import json
import re
import os
import markdown
from typing import Dict, Any, List, Optional
from app.config import settings
from app.services.keyword_analyzer import KeywordAnalyzer

class AIGenerator:
    @classmethod
    def generate_article(
        cls,
        keyword: str,
        secondary_keywords: List[str] = None,
        search_intent: str = "informational",
        tone: str = "informative",
        language: str = "English",
        target_word_count: int = 1500,
        template_type: str = "ultimate_guide",
        category_name: str = "Technology"
    ) -> Dict[str, Any]:
        """
        Executes the AI article generation pipeline.
        Uses OpenAI if API key is provided, otherwise utilizes the high-depth native generator.
        """
        secondary_keywords = secondary_keywords or []
        
        # Step 1: Keyword Analysis & Intent Outline
        analysis = KeywordAnalyzer.analyze(keyword, secondary_keywords)
        outline = analysis["outline"]
        suggested_slug = analysis["suggested_slug"]

        # Step 2: Generate Title
        title = cls._generate_title(keyword, search_intent, template_type)

        # Step 3: Check OpenAI availability
        content_markdown = None
        if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY.strip()) > 10:
            try:
                content_markdown = cls._generate_with_openai(
                    keyword=keyword,
                    secondary_keywords=secondary_keywords,
                    title=title,
                    search_intent=search_intent,
                    tone=tone,
                    language=language,
                    target_word_count=target_word_count,
                    template_type=template_type,
                    outline=outline
                )
            except Exception as e:
                print(f"OpenAI Generation error: {e}. Falling back to native high-depth generator.")

        if not content_markdown:
            content_markdown = cls._generate_native(
                keyword=keyword,
                secondary_keywords=secondary_keywords,
                title=title,
                search_intent=search_intent,
                tone=tone,
                template_type=template_type,
                outline=outline
            )

        # Enforce strict plain text on all H2-H5 headings (NO hyperlinks in headings)
        content_markdown = cls._enforce_clean_headings(content_markdown)

        # Render HTML
        html_content = markdown.markdown(
            content_markdown,
            extensions=["fenced_code", "tables", "toc", "sane_lists"]
        )

        word_count = len(re.findall(r"\w+", content_markdown))
        reading_time = max(1, round(word_count / 220))

        summary = cls._generate_summary(keyword, title, content_markdown)

        return {
            "title": title,
            "slug": suggested_slug,
            "summary": summary,
            "markdown": content_markdown,
            "html": html_content,
            "word_count": word_count,
            "reading_time": reading_time,
            "outline": outline,
            "search_intent": search_intent,
            "template_type": template_type
        }

    @classmethod
    def _generate_title(cls, keyword: str, intent: str, template: str) -> str:
        kw_title = keyword.strip().title()
        if template == "listicle":
            return f"10 Best {kw_title}: Tested and Ranked for Maximum Impact"
        elif template == "comparison":
            return f"{kw_title}: An In-Depth Side-by-Side Comparison"
        elif template == "how_to":
            return f"How to Master {kw_title}: Step-by-Step Implementation Guide"
        elif template == "review":
            return f"Comprehensive {kw_title} Review: Capabilities, Pricing, and Performance"
        else:
            return f"The Complete Guide to {kw_title}: Strategic Insights & Execution"

    @classmethod
    def _enforce_clean_headings(cls, markdown_text: str) -> str:
        """
        CRITICAL REQUIREMENT:
        Never place anchor links, internal links, or external hyperlinks inside H2, H3, H4, or H5 headings.
        Headings must contain plain text only.
        """
        lines = markdown_text.split("\n")
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                # Strip markdown links: [Anchor](url) -> Anchor
                line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
                # Strip HTML links: <a href="...">Anchor</a> -> Anchor
                line = re.sub(r"<a\b[^>]*>(.*?)</a>", r"\1", line, flags=re.IGNORECASE)
            cleaned_lines.append(line)
        return "\n".join(cleaned_lines)

    @classmethod
    def _generate_summary(cls, keyword: str, title: str, content: str) -> str:
        first_para = ""
        for block in content.split("\n\n"):
            clean = block.strip()
            if clean and not clean.startswith("#") and not clean.startswith("!"):
                first_para = clean
                break
        if first_para and len(first_para) > 60:
            return first_para[:180] + ("..." if len(first_para) > 180 else "")
        return f"Explore our comprehensive analysis and strategic guide to {keyword}. Discover proven techniques, operational frameworks, and actionable recommendations."

    @classmethod
    def _generate_with_openai(cls, **kwargs) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        prompt = f"""You are an elite technology journalist and SEO specialist writing for TrendBlogo.
Generate a comprehensive, high-value, deeply researched article.

Primary Keyword: {kwargs['keyword']}
Secondary Keywords: {', '.join(kwargs.get('secondary_keywords', []))}
Target Title: {kwargs['title']}
Search Intent: {kwargs['search_intent']}
Tone: {kwargs['tone']}
Language: {kwargs['language']}
Target Word Count: {kwargs['target_word_count']} words

CRITICAL MANDATORY RULES:
1. Never place any anchor links or hyperlinks inside any H2, H3, H4, or H5 headings. Headings MUST be plain text only.
2. Structure the article with natural H2 and H3 headings.
3. Include real actionable insights, structured lists, and comparison points.
4. Avoid generic introductions ("In today's fast paced world...").
5. Do NOT fabricate fake statistics or fake quotes.
6. Insert exactly three in-content image placement markers in appropriate sections:
   <!-- IN_CONTENT_IMAGE_1 -->
   <!-- IN_CONTENT_IMAGE_2 -->
   <!-- IN_CONTENT_IMAGE_3 -->
7. Include a detailed FAQ section at the end.
8. Output pure Markdown.
"""

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional editorial AI for TrendBlogo that produces structured, clean Markdown."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=3500
        )
        return response.choices[0].message.content

    @classmethod
    def _generate_native(
        cls,
        keyword: str,
        secondary_keywords: List[str],
        title: str,
        search_intent: str,
        tone: str,
        template_type: str,
        outline: List[Dict[str, Any]]
    ) -> str:
        kw = keyword.strip()
        kw_cap = kw.title()
        
        sec_kw_str = ", ".join(secondary_keywords) if secondary_keywords else "digital transformation, automation efficiency, strategic optimization"
        
        sections = []
        
        # Introduction
        sections.append(f"""In modern digital workflows, **{kw}** has transitioned from an emerging competitive advantage into an indispensable operational imperative. Organizations and practitioners striving to maintain high standards of efficiency must navigate an increasingly crowded landscape of tools, methodologies, and architectural decisions.

This strategic analysis provides an end-to-end blueprint for mastering {kw}. Whether evaluating technical adoption, workflow consolidation, or performance enhancement, the frameworks detailed below deliver tangible benchmarks and repeatable outcomes.""")

        # Section 1
        h2_1 = outline[0]["h2"]
        h3_1_1 = outline[0]["h3_list"][0] if outline[0]["h3_list"] else "Core Capabilities"
        h3_1_2 = outline[0]["h3_list"][1] if len(outline[0]["h3_list"]) > 1 else "Operational Principles"

        sections.append(f"""## {h2_1}

Navigating {kw} requires a clear understanding of the architectural primitives that govern modern deployments. When teams approach this domain without a structured methodology, they frequently encounter fragmented workflows, redundant tool stacks, and inconsistent output.

### {h3_1_1}

At its foundation, effective implementation hinges on modularity and predictability. Rather than treating {kw} as an isolated process, forward-looking practitioners integrate it directly into existing continuous delivery and feedback systems. By establishing well-defined boundary conditions and inputs, you ensure that every iteration yields measurable value.

### {h3_1_2}

Key parameters to calibrate during initial planning include:

- **System Compatibility:** Ensuring seamless data handoffs between upstream assets and downstream consumers.
- **Latency and Throughput:** Balancing thorough analytical depth with rapid execution turnaround.
- **Maintainability:** Structuring configurations and workflows so that cross-functional team members can audit and refine them without specialized friction.

<!-- IN_CONTENT_IMAGE_1 -->
""")

        # Section 2
        h2_2 = outline[1]["h2"]
        h3_2_1 = outline[1]["h3_list"][0] if outline[1]["h3_list"] else "Key Execution Metrics"
        h3_2_2 = outline[1]["h3_list"][1] if len(outline[1]["h3_list"]) > 1 else "Optimizing Workflows"

        sections.append(f"""## {h2_2}

To translate theoretical concepts into high-performing production routines, teams must establish objective evaluation criteria. Focusing on empirical benchmarks ensures that investments in {kw} directly translate into superior user experiences and operational resilience.

### {h3_2_1}

When auditing performance, track the following multidimensional factors:

1. **Precision and Accuracy:** Does the system consistently hit quality thresholds across diverse edge cases?
2. **Resource Efficiency:** What is the computational and human overhead required per delivered unit of work?
3. **Adaptability:** How gracefully does the workflow adapt when requirements evolve or underlying dependencies shift?

### {h3_2_2}

By implementing structured checkpoints throughout the lifecycle, teams can identify bottlenecks before they cascade into downstream deliverables. Incorporating automated linting, schema validation, and peer review establishes a resilient safety net.

<!-- IN_CONTENT_IMAGE_2 -->
""")

        # Section 3
        h2_3 = outline[2]["h2"]
        h3_3_1 = outline[2]["h3_list"][0] if outline[2]["h3_list"] else "Step-by-Step Implementation"
        h3_3_2 = outline[2]["h3_list"][1] if len(outline[2]["h3_list"]) > 1 else "Common Pitfalls to Avoid"

        sections.append(f"""## {h2_3}

Rolling out {kw} across dynamic environments requires methodical phased execution. The following phased framework has demonstrated consistent success across diverse industry sectors:

### {h3_3_1}

| Phase | Core Objective | Key Deliverable | Risk Mitigation |
| :--- | :--- | :--- | :--- |
| **Phase 1: Discovery** | Establish baseline metrics and identify friction points | Technical scoping document | Clear stakeholder alignment |
| **Phase 2: Prototyping** | Validate core assumptions in isolated sandbox | Functional MVP / POC | Controlled blast radius |
| **Phase 3: Rollout** | Phased deployment with automated telemetry | Production-ready pipeline | Immediate fallback triggers |
| **Phase 4: Optimization**| Ongoing iterative refinement and quality monitoring | Long-term performance report | Continuous telemetry auditing |

### {h3_3_2}

A frequent misstep is over-engineering early iterations. Teams often construct fragile abstractions before fully understanding their operational characteristics. Prioritize simple, readable, and well-instrumented solutions over opaque complexity.

<!-- IN_CONTENT_IMAGE_3 -->
""")

        # Section 4
        h2_4 = outline[3]["h2"]
        sections.append(f"""## {h2_4}

As technology ecosystems continue to mature, the discipline surrounding {kw} is being shaped by several key macro trends:

- **Automated Quality Governance:** Real-time feedback loops that verify output validity and standards compliance without manual gatekeeping.
- **Modular Ecosystem Interoperability:** Clean REST and event-driven interfaces allowing distinct platforms to orchestrate unified outcomes.
- **Context-Aware Personalization:** Utilizing localized intent signals to adapt deliverables to specific audience personas and use cases.

Integrating these forward-looking patterns into your current roadmap ensures that your operational assets remain resilient and future-proof.""")

        # FAQ Section
        sections.append(f"""## Frequently Asked Questions About {kw_cap}

### What is the most critical factor when starting with {kw}?
The most critical factor is defining explicit success criteria and baseline metrics before scaling execution. Understanding exactly what business or technical outcome you are optimizing prevents wasted effort and misalignment.

### How frequently should workflows around {kw} be audited?
A monthly review of primary metrics combined with a quarterly deep-dive into architectural dependencies ensures optimal performance and prevents technical drift.

### What are the primary pitfalls to avoid?
The two most common pitfalls are lack of standardization across team members and failure to implement automated quality control guardrails.""")

        # Conclusion
        sections.append(f"""## Summary and Key Takeaways

Mastering **{kw}** requires a deliberate combination of architectural clarity, disciplined execution, and continuous validation. By following the structured framework outlined in this guide, organizations can eliminate operational ambiguity, accelerate execution velocity, and deliver consistent, high-impact results.

Begin by assessing your current baseline against the benchmarks outlined above, identify the highest-leverage optimization targets, and iterate methodically.""")

        return "\n\n".join(sections)
