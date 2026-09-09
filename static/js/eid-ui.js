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

// Paint feedback before starting native Django navigation. Fetch-based
// workflows keep their existing request and loading controls.
(() => {
  const progress = document.getElementById("page-progress");
  const status = document.getElementById("page-loading-status");
  const message = document.getElementById("page-loading-message");
  if (!progress || !status || !message) return;
  let active = null;
  let pendingForm = null;
  let previousBusy = null;
  let previousDisabled = null;
  let timers = [];
  let frame = null;
  const submitting = new WeakSet();

  function afterPaint(action) {
    if (document.hidden) {
      action();
      return;
    }
    frame = requestAnimationFrame(() => {
      frame = requestAnimationFrame(() => {
        frame = null;
        action();
      });
    });
  }

  function reset() {
    cancelAnimationFrame(frame);
    frame = null;
    timers.forEach(clearTimeout);
    timers = [];
    if (active) {
      active.classList.remove("is-page-loading");
      for (const [name, value] of [
        ["aria-busy", previousBusy],
        ["aria-disabled", previousDisabled],
      ]) {
        if (value === null) active.removeAttribute(name);
        else active.setAttribute(name, value);
      }
    }
    active = pendingForm = null;
    progress.hidden = status.hidden = true;
    status.classList.remove("is-slow");
    message.textContent = "";
  }

  function start(element, label, form = null) {
    reset();
    active = element;
    pendingForm = form;
    if (active) {
      previousBusy = active.getAttribute("aria-busy");
      previousDisabled = active.getAttribute("aria-disabled");
      active.classList.add("is-page-loading");
      active.setAttribute("aria-busy", "true");
      // Do not set disabled: the browser must still send the submitter's value.
      active.setAttribute("aria-disabled", "true");
    }
    progress.hidden = false;
    message.textContent = label;
    // Fast responses only need the bar/button; avoid flashing an extra panel.
    timers.push(
      setTimeout(() => {
        status.hidden = false;
      }, 350),
    );
    timers.push(
      setTimeout(() => {
        message.textContent = form
          ? "正在提交，请勿重复操作…"
          : "加载时间较长，请稍候…";
        status.classList.add("is-slow");
      }, 8000),
    );
    // A cancelled download or failed navigation may leave this document alive.
    // Recover the controls without automatically retrying a request.
    timers.push(
      setTimeout(() => {
        reset();
        status.hidden = false;
        status.classList.add("is-slow");
        message.textContent = form
          ? "提交结果尚未确认，请先查看申请记录。"
          : "页面响应较慢，请检查网络后重试。";
        timers.push(setTimeout(reset, 6000));
      }, 30000),
    );
  }

  // Block only a repeated activation of the current control. Other links remain
  // usable, so the user can choose a different destination while waiting.
  document.addEventListener(
    "click",
    (event) => {
      if (
        event.button !== 0 ||
        event.metaKey ||
        event.ctrlKey ||
        event.shiftKey ||
        event.altKey
      )
        return;
      if (
        active &&
        event.target instanceof Element &&
        active.contains(event.target)
      ) {
        event.preventDefault();
        event.stopImmediatePropagation();
      }
    },
    true,
  );

  document.addEventListener("click", (event) => {
    if (
      event.defaultPrevented ||
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    )
      return;
    if (!(event.target instanceof Element)) return;
    const element = event.target.closest("a[href], [data-page-loading]");
    if (!element || element.closest("[data-no-page-loading]")) return;
    if (element.matches("[data-bs-toggle], [data-bs-dismiss]")) return;
    if (element instanceof HTMLAnchorElement) {
      if (
        element.hasAttribute("download") ||
        (element.target && element.target.toLowerCase() !== "_self")
      )
        return;
      const url = new URL(element.href, location.href);
      if (!["http:", "https:"].includes(url.protocol)) return;
      if (
        url.origin === location.origin &&
        url.pathname === location.pathname &&
        url.search === location.search &&
        url.hash
      )
        return;
    }
    if (
      !(element instanceof HTMLAnchorElement) &&
      !element.hasAttribute("data-page-reload")
    )
      return;
    event.preventDefault();
    start(element, element.dataset.pageLoading || "正在打开页面…");
    afterPaint(() => {
      if (element instanceof HTMLAnchorElement) location.assign(element.href);
      else location.reload();
    });
  });

  document.addEventListener("submit", (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) return;
    if (submitting.delete(form)) return;
    if (pendingForm === form) {
      event.preventDefault();
      return;
    }
    if (event.defaultPrevented || form.closest("[data-no-page-loading]"))
      return;
    const button = event.submitter;
    const target = button?.getAttribute("formtarget") || form.target;
    const method = button?.getAttribute("formmethod") || form.method;
    if (
      (target && target.toLowerCase() !== "_self") ||
      method.toLowerCase() === "dialog"
    )
      return;
    event.preventDefault();
    start(
      button,
      method.toLowerCase() === "get" ? "正在加载结果…" : "正在提交，请稍候…",
      form,
    );
    afterPaint(() => {
      submitting.add(form);
      try {
        form.requestSubmit(button || undefined);
      } finally {
        submitting.delete(form);
      }
    });
  });

  window.addEventListener("pageshow", reset);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") reset();
  });
})();
