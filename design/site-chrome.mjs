/** Shared mobile nav + optional header active state (design v1.0) */
const TABS = [
  { id: "home", href: "/", icon: "🧭", label: "홈" },
  { id: "explore", href: "/index.html", icon: "🗺️", label: "탐험" },
  { id: "market", href: "/market.html", icon: "🎟️", label: "특가" },
  { id: "map", href: "/map.html", icon: "📍", label: "지도" },
  { id: "wallet", href: "/market.html#wallet", icon: "💳", label: "지갑" },
];

function activeFromBody() {
  return document.body.dataset.glActive || "home";
}

function markHeaderLinks(active) {
  document.querySelectorAll(".gl-site-nav a[data-gl-nav]").forEach((a) => {
    a.classList.toggle("gl-nav-active", a.dataset.glNav === active);
  });
}

function injectMobileNav(active) {
  if (document.body.dataset.glMobileNav === "off") return;
  let nav = document.querySelector(".gl-mobile-nav");
  if (!nav) {
    nav = document.createElement("nav");
    nav.className = "gl-mobile-nav";
    nav.setAttribute("aria-label", "모바일 메뉴");
    document.body.appendChild(nav);
  }
  nav.innerHTML = TABS.map(
    (t) =>
      `<a href="${t.href}" class="${t.id === active ? "gl-nav-active" : ""}" data-gl-tab="${t.id}">${t.icon}<small>${t.label}</small></a>`
  ).join("");
  document.body.classList.add("gl-has-mobile-nav");
}

const active = activeFromBody();
markHeaderLinks(active);
injectMobileNav(active);
