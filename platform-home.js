/** Home spotlight — market-aligned offer cards (v5 API) */
(function () {
  const grid = document.getElementById("homeOffers");
  if (!grid) return;
  grid.classList.add("cards");

  const photo = (r) => {
    if (r.image && String(r.image).startsWith("/assets/")) return r.image;
    const t = (r.category || "").toLowerCase();
    if (t.includes("수산")) return "/assets/v5/seafood.webp";
    if (t.includes("축")) return "/assets/v5/meat.webp";
    if (t.includes("청과")) return "/assets/v5/fruit.webp";
    return "/assets/v5/market.webp";
  };
  const won = (n) => Number(n).toLocaleString("ko-KR") + "원";
  const esc = (s) =>
    String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/"/g, "&quot;");

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
        .map((r) => {
          const disc =
            r.original_price && r.offer_price
              ? Math.round((1 - r.offer_price / r.original_price) * 100)
              : 0;
          return `<a class="card" href="/market.html#deals">
<img class="photo" src="${esc(photo(r))}" alt="AI 생성 ${esc(r.category || "시장")} 테마 이미지">
<div class="card-body">
<div class="card-top">
<span class="tag">${disc > 0 ? disc + "% 할인 · 한정 " + esc(r.limit_count || "—") + "장" : "오늘의 특가"}</span>
<span class="tag demo">${r.is_demo ? "가상 시연" : "상인 등록"}</span>
</div>
<h3>${esc(r.item || "오늘의 특가")}</h3>
<p class="desc">${esc(r.description || "특가 상세는 마켓 페이지에서 확인하세요.")}</p>
<div class="price"><strong>${won(r.offer_price)}</strong><s>${won(r.original_price)}</s></div>
<div class="shopline">${esc(r.shop_name || "가락랜드 시연 매장")}<br>${esc(r.building || "—")} · ${esc(r.floor || "—")} / ${esc(r.room || "—")} · ${r.verified_location ? "확인된 GPS" : "실점포 좌표 미확인"}</div>
<span class="card-cta">쿠폰 받기 →</span>
</div></a>`;
        })
        .join("");
    })
    .catch(() => {
      grid.innerHTML =
        '<p class="empty">서버 연결 후 특가가 표시됩니다. <a href="/market.html">특가 페이지 ↗</a></p>';
    });
})();
