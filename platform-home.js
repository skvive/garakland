/** Home spotlight — load today's offers from v5 API */
(function () {
  const grid = document.getElementById("homeOffers");
  if (!grid) return;
  const photo = (r) => {
    const t = (r.category || "").toLowerCase();
    if (t.includes("수산")) return "/assets/v5/seafood.webp";
    if (t.includes("축")) return "/assets/v5/meat.webp";
    if (t.includes("청과")) return "/assets/v5/fruit.webp";
    return "/assets/v5/market.webp";
  };
  const won = (n) => Number(n).toLocaleString("ko-KR") + "원";
  fetch("/api/v5/public")
    .then((r) => {
      if (!r.ok) throw new Error("offline");
      return r.json();
    })
    .then((data) => {
      const offers = (data.offers || []).filter((o) => o.is_active !== false).slice(0, 4);
      if (!offers.length) {
        grid.innerHTML =
          '<p class="empty">특가를 불러오지 못했습니다. <a href="/market.html">특가 페이지</a>에서 확인해 주세요.</p>';
        return;
      }
      grid.innerHTML = offers
        .map(
          (o) => `<a class="offer-card" href="/market.html#deals">
<img src="${photo(o)}" alt="">
<div class="body"><b>${escapeHtml(o.item || "오늘의 특가")}</b>
<p class="price"><s>${won(o.original_price)}</s><em>${won(o.offer_price)}</em></p></div></a>`
        )
        .join("");
    })
    .catch(() => {
      grid.innerHTML =
        '<p class="empty">서버 연결 후 특가가 표시됩니다. <a href="/market.html">특가 페이지 ↗</a></p>';
    });
  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/"/g, "&quot;");
  }
})();
