// TrendBlogo Main JS
document.addEventListener("DOMContentLoaded", () => {
  // 1. Mobile Menu Drawer
  const mobileMenuBtn = document.getElementById("mobile-menu-btn");
  const mobileMenu = document.getElementById("mobile-menu");
  const closeMobileMenuBtn = document.getElementById("close-mobile-menu");

  if (mobileMenuBtn && mobileMenu) {
    mobileMenuBtn.addEventListener("click", () => {
      mobileMenu.classList.remove("hidden");
    });
    if (closeMobileMenuBtn) {
      closeMobileMenuBtn.addEventListener("click", () => {
        mobileMenu.classList.add("hidden");
      });
    }
  }

  // 2. Search Modal
  const searchModal = document.getElementById("search-modal");
  const openSearchBtns = document.querySelectorAll(".open-search-modal");
  const closeSearchBtn = document.getElementById("close-search-modal");
  const searchInput = document.getElementById("modal-search-input");
  const searchSuggestions = document.getElementById("search-suggestions");

  function openSearch() {
    if (searchModal) {
      searchModal.classList.remove("hidden");
      if (searchInput) {
        setTimeout(() => searchInput.focus(), 100);
      }
    }
  }

  function closeSearch() {
    if (searchModal) {
      searchModal.classList.add("hidden");
    }
  }

  openSearchBtns.forEach(btn => btn.addEventListener("click", openSearch));
  if (closeSearchBtn) closeSearchBtn.addEventListener("click", closeSearch);

  // Keyboard shortcut: '/' opens search, 'Escape' closes
  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) {
      e.preventDefault();
      openSearch();
    }
    if (e.key === "Escape") {
      closeSearch();
    }
  });

  // Debounced search suggestions
  let debounceTimeout;
  if (searchInput && searchSuggestions) {
    searchInput.addEventListener("input", (e) => {
      clearTimeout(debounceTimeout);
      const query = e.target.value.trim();
      if (query.length < 2) {
        searchSuggestions.innerHTML = "";
        searchSuggestions.classList.add("hidden");
        return;
      }
      debounceTimeout = setTimeout(async () => {
        try {
          const res = await fetch(`/api/search/suggest?q=${encodeURIComponent(query)}`);
          const items = await res.json();
          if (items.length > 0) {
            searchSuggestions.innerHTML = items.map(item => `
              <a href="/blog/${item.slug}" class="flex items-center p-3 hover:bg-slate-50 rounded-lg transition">
                <img src="${item.image}" alt="" class="w-12 h-8 rounded object-cover mr-3 bg-slate-100 flex-shrink-0" />
                <div class="truncate">
                  <div class="font-semibold text-slate-800 text-sm truncate">${item.title}</div>
                  <div class="text-xs text-indigo-600">View article &rarr;</div>
                </div>
              </a>
            `).join("");
            searchSuggestions.classList.remove("hidden");
          } else {
            searchSuggestions.innerHTML = `<div class="p-3 text-sm text-slate-500">No articles found matching "${query}"</div>`;
            searchSuggestions.classList.remove("hidden");
          }
        } catch (err) {
          console.error("Suggestion fetch failed", err);
        }
      }, 250);
    });
  }

  // 3. Cookie Consent Banner
  const cookieBanner = document.getElementById("cookie-consent-banner");
  const acceptCookiesBtn = document.getElementById("accept-cookies-btn");
  const declineCookiesBtn = document.getElementById("decline-cookies-btn");

  if (cookieBanner) {
    const hasConsented = localStorage.getItem("trendblogo_cookie_consent");
    if (!hasConsented) {
      setTimeout(() => cookieBanner.classList.remove("translate-y-full"), 600);
    }
    if (acceptCookiesBtn) {
      acceptCookiesBtn.addEventListener("click", () => {
        localStorage.setItem("trendblogo_cookie_consent", "all");
        cookieBanner.classList.add("translate-y-full");
      });
    }
    if (declineCookiesBtn) {
      declineCookiesBtn.addEventListener("click", () => {
        localStorage.setItem("trendblogo_cookie_consent", "essential");
        cookieBanner.classList.add("translate-y-full");
      });
    }
  }

  // 4. Share Link Copy Toast
  const copyLinkBtns = document.querySelectorAll(".copy-share-link");
  copyLinkBtns.forEach(btn => {
    btn.addEventListener("click", async () => {
      const url = btn.dataset.url || window.location.href;
      try {
        await navigator.clipboard.writeText(url);
        const origText = btn.innerHTML;
        btn.innerHTML = `? Copied!`;
        btn.classList.add("bg-emerald-600", "text-white");
        setTimeout(() => {
          btn.innerHTML = origText;
          btn.classList.remove("bg-emerald-600", "text-white");
        }, 2000);
      } catch (err) {
        console.error("Copy failed", err);
      }
    });
  });
});
