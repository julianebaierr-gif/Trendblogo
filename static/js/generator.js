// TrendBlogo 15-Step Generator Wizard
document.addEventListener("DOMContentLoaded", () => {
  const wizardForm = document.getElementById("generator-form");
  if (!wizardForm) return;

  const keywordInput = document.getElementById("wizard-keyword");
  const secondaryKeywordsInput = document.getElementById("wizard-secondary-keywords");
  const categorySelect = document.getElementById("wizard-category");
  const toneSelect = document.getElementById("wizard-tone");
  const templateSelect = document.getElementById("wizard-template");
  const wordCountInput = document.getElementById("wizard-word-count");
  const publishModeSelect = document.getElementById("wizard-publish-mode");

  const btnAnalyze = document.getElementById("btn-wizard-analyze");
  const btnGenerateNow = document.getElementById("btn-wizard-generate");
  
  const stepConfig = document.getElementById("step-config");
  const stepAnalysis = document.getElementById("step-analysis");
  const stepProgress = document.getElementById("step-progress");
  const stepReview = document.getElementById("step-review");

  const intentBadge = document.getElementById("analysis-intent-badge");
  const templateBadge = document.getElementById("analysis-template-badge");
  const collisionAlert = document.getElementById("collision-alert");
  const collisionText = document.getElementById("collision-text");
  const outlineList = document.getElementById("analysis-outline-list");

  const progressStatusText = document.getElementById("progress-status-text");
  const progressBar = document.getElementById("generation-progress-bar");
  const progressPercent = document.getElementById("progress-percent");

  // Review screen elements
  const reviewTitle = document.getElementById("review-title");
  const reviewScore = document.getElementById("review-score");
  const reviewScoreBadge = document.getElementById("review-score-badge");
  const reviewWordCount = document.getElementById("review-word-count");
  const reviewFeaturedImg = document.getElementById("review-featured-img");
  const reviewArticleLink = document.getElementById("review-article-link");
  const reviewEditLink = document.getElementById("review-edit-link");

  // 1. Analyze Step
  if (btnAnalyze) {
    btnAnalyze.addEventListener("click", async () => {
      const kw = keywordInput.value.trim();
      if (!kw) {
        alert("Please enter a primary keyword first.");
        keywordInput.focus();
        return;
      }

      btnAnalyze.disabled = true;
      btnAnalyze.innerHTML = `<span class="animate-spin inline-block mr-2">&#9696;</span> Analyzing Keyword...`;

      try {
        // Fetch Intent & Outline
        const resAnalyze = await fetch("/api/keywords/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ keyword: kw })
        });
        const analysisData = await resAnalyze.json();

        // Fetch Duplicate / Cannibalization Check
        const resDup = await fetch("/api/keywords/check-duplicate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ keyword: kw })
        });
        const dupData = await resDup.json();

        // Populate Analysis UI
        if (intentBadge) intentBadge.textContent = (analysisData.search_intent || "Informational").toUpperCase();
        if (templateBadge) templateBadge.textContent = (analysisData.template_type || "Ultimate Guide").replace("_", " ").toUpperCase();
        
        if (templateSelect) {
          templateSelect.value = analysisData.template_type || "ultimate_guide";
        }

        // Handle Cannibalization Warnings
        if (dupData.has_collision) {
          collisionAlert.classList.remove("hidden");
          collisionText.innerHTML = `<strong>Topical Overlap Alert:</strong> ${dupData.warnings.join(" ")}`;
        } else {
          collisionAlert.classList.add("hidden");
        }

        // Render Outline Preview
        if (outlineList && analysisData.outline) {
          outlineList.innerHTML = analysisData.outline.map((sec, i) => `
            <div class="p-3 bg-slate-50 border border-slate-200 rounded-lg text-sm">
              <div class="font-bold text-slate-800">H2: ${sec.h2}</div>
              ${sec.h3_list && sec.h3_list.length > 0 ? `
                <div class="mt-1 pl-4 text-xs text-slate-500 space-y-0.5">
                  ${sec.h3_list.map(h3 => `<div>&bull; H3: ${h3}</div>`).join("")}
                </div>
              ` : ""}
            </div>
          `).join("");
        }

        stepAnalysis.classList.remove("hidden");
        btnAnalyze.classList.add("hidden");
      } catch (err) {
        alert("Failed to analyze keyword: " + err.message);
      } finally {
        btnAnalyze.disabled = false;
        btnAnalyze.innerHTML = `Analyze Keyword & Intent &rarr;`;
      }
    });
  }

  // 2. Generate Step
  if (btnGenerateNow) {
    btnGenerateNow.addEventListener("click", async () => {
      const kw = keywordInput.value.trim();
      if (!kw) return;

      stepConfig.classList.add("hidden");
      stepAnalysis.classList.add("hidden");
      stepProgress.classList.remove("hidden");

      const payload = {
        keyword: kw,
        secondary_keywords: secondaryKeywordsInput.value.trim(),
        category_id: categorySelect.value ? parseInt(categorySelect.value) : null,
        tone: toneSelect.value,
        template_type: templateSelect.value,
        target_word_count: parseInt(wordCountInput.value) || 1500,
        publish_mode: publishModeSelect.value
      };

      // Animate progress simulation while worker executes
      let curProgress = 15;
      const progressTimer = setInterval(() => {
        if (curProgress < 88) {
          curProgress += 4;
          progressBar.style.width = curProgress + "%";
          progressPercent.textContent = curProgress + "%";
          if (curProgress === 35) progressStatusText.textContent = "Synthesizing deep article content & plain-text headings...";
          if (curProgress === 55) progressStatusText.textContent = "Injecting contextual internal and authoritative external links...";
          if (curProgress === 75) progressStatusText.textContent = "Rendering 4 bespoke visual assets (1 featured + 3 in-article)...";
          if (curProgress === 85) progressStatusText.textContent = "Generating Schema.org JSON-LD & running quality audit...";
        }
      }, 400);

      try {
        const res = await fetch("/api/articles/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        clearInterval(progressTimer);

        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || "Generation failed.");
        }

        const data = await res.json();

        // 100% Complete
        progressBar.style.width = "100%";
        progressPercent.textContent = "100%";
        progressStatusText.textContent = "Generation complete! Rendering review...";

        setTimeout(() => {
          stepProgress.classList.add("hidden");
          stepReview.classList.remove("hidden");

          reviewTitle.textContent = data.title;
          reviewScore.textContent = `${data.quality_score}/100`;
          reviewWordCount.textContent = `${data.word_count} words`;
          if (reviewFeaturedImg) reviewFeaturedImg.src = data.featured_image;
          if (reviewArticleLink) reviewArticleLink.href = data.url;
          if (reviewEditLink) reviewEditLink.href = `/admin/articles/${data.article_id}/edit`;
        }, 600);

      } catch (err) {
        clearInterval(progressTimer);
        alert("Generation Error: " + err.message);
        stepProgress.classList.add("hidden");
        stepConfig.classList.remove("hidden");
      }
    });
  }
});
