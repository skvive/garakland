/* GARAKLAND / shared public navigation - unified with brand/app.js header. */
(function () {
  'use strict';
  var path = window.location.pathname || '/';
  if (path.slice(-1) === '/' && path !== '/') path = path.slice(0, -1);
  var menu = [
    ['/','홈','home'],
    ['/map.html','3D 시장지도','map'],
    ['/stores.html','매장 찾기','stores'],
    ['/coupons.html','쿠폰·상품권','coupons'],
    ['/events.html','이벤트','events'],
    ['/market-guide.html','시장 이야기','guide'],
    ['/merchant-center.html','상인센터','merchant'],
    ['/indoor-map.html','▤ 입체 실내지도 베타','indoor'],
    ['/lotteworld-next.html','🎡 롯데월드 다음 코스','lotte'],
    ['/ar-quest.html','✦ AR 탐험 베타','ar'],
    ['/project.html','사업 소개','project'],
    ['/culture.html','문화·행사','culture'],
    ['/commerce.html','온라인 유통','commerce'],
    ['/mypage.html','마이페이지','mypage'],
    ['/login.html','로그인','login']
  ];
  function activeFromPath() {
    if (path === '/' || path === '/index.html' || path === '/home.html') return 'home';
    if (path === '/store.html') return 'stores';
    if (path === '/market.html') return 'coupons';
    if (path === '/market-map.html') return 'map';
    for (var i = 0; i < menu.length; i++) {
      if (menu[i][0] === path) return menu[i][2];
    }
    return '';
  }
  function start() {
    /* Brand pages already render the same full header; never duplicate it. */
    if (document.body.hasAttribute('data-page') && document.getElementById('app')) return;
    if (document.getElementById('garakland-global-header')) return;
    var active = activeFromPath();
    var root = document.createElement('div');
    root.id = 'garakland-global-header';
    root.className = 'glsh-shell';
    root.innerHTML =
      '<div class="glsh-notice">가락시장의 미래를 연결하는 가락랜드 <span>· 시장 탐험 · 문화·관광 · 온라인 유통 실증 제안</span></div>' +
      '<header class="glsh-header" aria-label="가락랜드 공통 상단 메뉴">' +
        '<div class="glsh-head-inner">' +
          '<a class="glsh-logo" href="/" aria-label="가락랜드 홈">' +
            '<img src="/assets/brand/garakland-wordmark-header-v3.webp" alt="가락랜드" width="295" height="82">' +
          '</a>' +
          '<form class="glsh-search" action="/stores.html" method="get" role="search">' +
            '<label class="glsh-sr-only" for="glsh-search-field">매장 또는 상품 검색</label>' +
            '<input id="glsh-search-field" name="q" type="search" autocomplete="off" placeholder="매장, 상품, 시장 체험을 찾아보세요">' +
            '<button type="submit" aria-label="매장 검색">⌕</button>' +
          '</form>' +
          '<div class="glsh-head-actions">' +
            '<a href="/coupons.html" aria-label="내 쿠폰">🎟️</a>' +
            '<a href="/mypage.html?tab=favorites" aria-label="찜한 매장">♡</a>' +
          '</div>' +
        '</div>' +
        '<nav class="glsh-nav" aria-label="가락랜드 통합 메뉴"><div class="glsh-nav-inner">' +
          menu.map(function (m) {
            var current = m[2] === active;
            return '<a href="' + m[0] + '"' + (m[2] === 'login' ? ' id="authLinkGlobal"' : '') + (current ? ' class="glsh-active-link" aria-current="page"' : '') + '>' + m[1] + '</a>';
          }).join('') +
        '</div></nav>' +
      '</header>';
    document.body.insertBefore(root, document.body.firstChild);
    document.body.classList.add('glsh-active');
    import('/auth/banner.mjs').then(m => m.mountAuthLink('authLinkGlobal')).catch(() => {});
    document.body.dataset.glMobileNav = 'off';
    /* The map's settings button must remain interactive after hiding its legacy nav. */
    if (path === '/map.html') {
      var settings = document.getElementById('settingsBtn');
      var actions = root.querySelector('.glsh-head-actions');
      if (settings && actions) {
        settings.classList.add('glsh-map-settings');
        actions.insertBefore(settings, actions.firstChild);
      }
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();