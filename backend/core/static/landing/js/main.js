
(() => {
  "use strict";

  const toggle = document.querySelector(".menu-toggle");
  const nav = document.querySelector("#main-nav");

  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    });

    nav.querySelectorAll("a").forEach(link => {
      link.addEventListener("click", () => {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.setAttribute("aria-label", "Open menu");
      });
    });

    document.addEventListener("keydown", event => {
      if (event.key === "Escape") {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.setAttribute("aria-label", "Open menu");
      }
    });
  }

  // Program CTAs reuse the existing enquiry page.
  // Store selected program only in the current URL.
  // Claude Code should map this to a verified Django route.
  document.querySelectorAll("[data-program]").forEach(link => {
    link.addEventListener("click", event => {
      const program = link.dataset.program;
      const enquiry = document.querySelector("#enquire");
      if (enquiry) {
        event.preventDefault();
        enquiry.scrollIntoView({ behavior: "smooth" });
        const cta = enquiry.querySelector(".btn");
        if (cta) {
          const url = new URL(cta.getAttribute("href"), window.location.href);
          url.searchParams.set("program", program);
          cta.setAttribute("href", url.pathname + url.search);
        }
      }
    });
  });
})();
