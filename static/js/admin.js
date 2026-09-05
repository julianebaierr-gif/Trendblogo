// TrendBlogo Admin JS
document.addEventListener("DOMContentLoaded", () => {
  // Mobile sidebar toggle
  const sidebar = document.getElementById("admin-sidebar");
  const toggleBtn = document.getElementById("admin-sidebar-toggle");
  if (sidebar && toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("-translate-x-full");
    });
  }

  // Live Markdown preview in Editor
  const markdownTextarea = document.getElementById("editor-content");
  const previewPane = document.getElementById("editor-preview");
  const headingList = document.getElementById("editor-heading-check");

  if (markdownTextarea && previewPane) {
    function updatePreview() {
      const text = markdownTextarea.value;
      // Extract headings for hierarchy audit
      if (headingList) {
        const lines = text.split("\n");
        const headings = [];
        let hasLinksInHeadings = false;

        lines.forEach(line => {
          const trimmed = line.trim();
          if (trimmed.startsWith("##")) {
            const level = trimmed.indexOf(" ");
            const title = trimmed.substring(level).trim();
            const hasLink = /\[.*?\]\(.*?\)|<a\b/i.test(title);
            if (hasLink) hasLinksInHeadings = true;
            headings.push({ level: level > 0 ? level : 2, title, hasLink });
          }
        });

        if (headings.length === 0) {
          headingList.innerHTML = `<div class="text-xs text-amber-600">No H2-H5 headings found yet.</div>`;
        } else {
          headingList.innerHTML = headings.map(h => `
            <div class="flex items-center text-xs py-1 ${h.hasLink ? 'text-red-600 font-bold' : 'text-slate-600'}">
              <span class="inline-block w-8 font-mono font-bold text-indigo-600">H${h.level}</span>
              <span class="truncate flex-1">${h.title}</span>
              ${h.hasLink ? '<span class="ml-2 text-red-500 font-bold text-[10px] bg-red-50 px-1 rounded">HYPERLINK FORBIDDEN</span>' : '<span class="text-emerald-500 text-[10px]">? Plain text</span>'}
            </div>
          `).join("");
        }
      }
    }

    markdownTextarea.addEventListener("input", updatePreview);
    updatePreview();
  }

  // Copy to clipboard buttons in media & links
  document.querySelectorAll(".copy-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const text = btn.dataset.copy;
      if (text) {
        await navigator.clipboard.writeText(text);
        const orig = btn.innerText;
        btn.innerText = "Copied!";
        setTimeout(() => btn.innerText = orig, 1500);
      }
    });
  });
});
