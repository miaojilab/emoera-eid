(() => {
  const toggle = document.querySelector(".menu-toggle");
  const menu = document.querySelector("#eid-menu");
  toggle?.addEventListener("click", () => {
    const open = toggle.getAttribute("aria-expanded") !== "true";
    toggle.setAttribute("aria-expanded", String(open));
    toggle.setAttribute("aria-label", open ? "收起导航" : "展开导航");
    menu.classList.toggle("is-open", open);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document
        .querySelectorAll(".nav-dropdown[open]")
        .forEach((el) => el.removeAttribute("open"));
      if (menu?.classList.contains("is-open")) {
        menu.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.setAttribute("aria-label", "展开导航");
        toggle.focus();
      }
    }
  });
  document.querySelectorAll(".needs-validation").forEach((form) =>
    form.addEventListener("submit", (e) => {
      if (!form.checkValidity()) {
        e.preventDefault();
        e.stopPropagation();
        form.querySelector(":invalid")?.focus();
      }
      form.classList.add("was-validated");
    }),
  );
})();
