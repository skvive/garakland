import { getMemberSession, memberRequest, signOut } from './member-client.mjs';

let root = null;
const shops = window.GARAK_BRAND_DATA?.shops || [];
const coupons = window.GARAK_BRAND_DATA?.coupons || [];
let state = { favorites: [], coupons: [], demoOnly: true };
let user = null;
let activeTab = 'coupons';

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
function formatName(value) {
  const name = String(value || '').trim();
  return name ? name.slice(0, 32) : '가락랜드 회원';
}
function status(message, danger = false) {
  const line = root?.querySelector('[data-member-status]');
  if (line) { line.textContent = message; line.dataset.danger = String(danger); }
}
function render() {
  if (!root || !user) return;
  const name = formatName(user.name || user.email?.split('@')[0]);
  root.innerHTML = 
    '<div class="mp-identity"><div class="mp-avatar" aria-hidden="true">G</div><div>' +
      '<span class="mp-eyebrow">MY GARAKLAND</span><h2>' + esc(name) + '님, 환영합니다.</h2>' +
      '<p>내가 저장한 업소와 시연 쿠폰은 로그인한 회원 계정에만 연결됩니다.</p>' +
    '</div></div>' +
    '<div class="mp-stats" aria-label="회원 저장 현황">' +
      '<div><strong>' + state.coupons.length + '</strong><span>내 쿠폰</span></div>' +
      '<div><strong>' + state.favorites.length + '</strong><span>찜한 업소</span></div>' +
      '<div><strong>회원</strong><span>로그인 상태</span></div>' +
    '</div>' +
    '<p class="mp-info" role="note">현재 등록된 할인 쿠폰과 업소는 <b>서비스 체험용 시연 데이터</b>입니다. 실제 할인·발급·결제·현장 사용은 제공되지 않습니다.</p>' +
    '<div class="mp-tabs" role="tablist" aria-label="마이페이지 메뉴">' +
      [['coupons','🎟️ 내 쿠폰'],['favorites','♡ 찜한 업소'],['profile','⚙ 계정 정보']].map(([key,label]) =>
      '<button role="tab" type="button" data-member-tab="' + key + '" aria-selected="' + String(activeTab === key) + '" class="' + (activeTab === key ? 'selected' : '') + '">' + label + '</button>').join('') +
    '</div><div class="mp-content" id="member-content" role="tabpanel"></div>' +
    '<p class="mp-status" data-member-status role="status" aria-live="polite"></p>';
  const main = root.querySelector('#member-content');
  if (activeTab === 'coupons') {
    const items = state.coupons.map(id => {
      const c = coupons.find(item => item.id === id);
      const shop = c && shops.find(s => s.id === c.shopId);
      if (!c) return '';
      return '<article class="mp-item"><div class="mp-card-symbol">🎟️</div><div class="mp-item-copy">' +
        '<span class="mp-eyebrow">시연 쿠폰 · 실제 사용 불가</span><h3>' + esc(c.title) + '</h3>' +
        '<strong>' + esc(c.benefit) + '</strong><p>' + esc(shop?.name || '시연 업소') + ' · ' + esc(c.description) + '</p>' +
        '<div class="mp-actions"><a href="/store.html?id=' + encodeURIComponent(c.shopId) + '">업소 안내</a>' +
        '<button data-member-remove-coupon="' + esc(c.id) + '">지갑에서 제외</button></div></div></article>';
    }).filter(Boolean);
    main.innerHTML = '<div class="mp-section-head"><h3>내 쿠폰 지갑</h3><a href="/coupons.html">쿠폰 더 살펴보기 ↗</a></div>' +
      (items.length ? '<div class="mp-list">' + items.join('') + '</div>' :
      '<div class="mp-empty"><div>🎟️</div><h3>아직 저장한 쿠폰이 없습니다.</h3><p>시연용 쿠폰을 살펴보고 내 지갑에 담아보세요.</p><a href="/coupons.html">쿠폰 둘러보기</a></div>');
  } else if (activeTab === 'favorites') {
    const items = state.favorites.map(id => {
      const shop = shops.find(s => s.id === id);
      if (!shop) return '<article class="mp-item"><div class="mp-card-symbol">♡</div><div class="mp-item-copy"><h3>' +
        esc(id) + '</h3><p>등록된 업소 정보가 아직 없습니다.</p><button data-member-remove-favorite="' + esc(id) + '">저장 해제</button></div></article>';
      return '<article class="mp-item"><img class="mp-store-photo" src="/' + esc(shop.photo.replace(/^\/+/,'')) + '" alt="' + esc(shop.category) + ' 시연 이미지"><div class="mp-item-copy">' +
        '<span class="mp-eyebrow">시연 업소 · ' + esc(shop.category) + '</span><h3>' + esc(shop.name) + '</h3><p>' + esc(shop.intro) + '</p>' +
        '<div class="mp-actions"><a href="/store.html?id=' + encodeURIComponent(shop.id) + '">업소 상세</a>' +
        '<button data-member-remove-favorite="' + esc(id) + '">즐겨찾기 해제</button></div></div></article>';
    });
    main.innerHTML = '<div class="mp-section-head"><h3>찜한 업소</h3><a href="/stores.html">업소 더 찾기 ↗</a></div>' +
      (items.length ? '<div class="mp-list">' + items.join('') + '</div>' :
      '<div class="mp-empty"><div>♡</div><h3>저장한 업소가 없습니다.</h3><p>가락시장을 둘러보며 마음에 드는 업소를 찜해 보세요.</p><a href="/stores.html">매장 찾기</a></div>');
  } else {
    main.innerHTML = '<div class="mp-section-head"><h3>내 계정</h3></div>' +
      '<div class="mp-profile"><div><span>회원명</span><strong>' + esc(name) + '</strong></div>' +
      '<div><span>로그인 이메일</span><strong>' + esc(user.email || '-') + '</strong></div>' +
      '<div><span>인증 서비스</span><strong>Neon Auth (Google·이메일)</strong></div>' +
      '<p>개인정보와 로그인 관리는 Neon Auth를 사용합니다. 비밀번호는 가락랜드 서버에 보관하지 않습니다.</p>' +
      '<button class="mp-signout" data-member-signout>로그아웃</button></div>';
  }
}
async function load() {
  if (!root) return;
  root.innerHTML = '<div class="mp-loading">회원 정보를 확인하고 있습니다…</div>';
  try {
    const session = await Promise.race([getMemberSession(), new Promise((_, reject) => setTimeout(() => reject(new Error('인증 확인 시간이 초과됐습니다. 다시 시도해 주세요.')), 9000))]);
    if (!session?.user?.id) {
      root.innerHTML = '<div class="mp-empty"><div>🔒</div><h2>로그인 후 이용할 수 있습니다.</h2>' +
        '<p>Google 계정으로 가입하면 쿠폰과 찜한 업소를 회원별로 보관할 수 있습니다.</p>' +
        '<a href="/login.html?next=%2Fmypage.html">Google 로그인·회원가입</a></div>';
      return;
    }
    user = session.user;
    state = await memberRequest('/api/member/state');
    render();
    const tab = new URLSearchParams(location.search).get('tab');
    if (['coupons','favorites','profile'].includes(tab)) { activeTab = tab; render(); }
  } catch (error) {
    root.innerHTML = '<div class="mp-empty"><div>!</div><h2>회원 정보를 불러오지 못했습니다.</h2>' +
      '<p>' + esc(error?.message || '네트워크 상태를 확인해 주세요.') + '</p>' +
      '<button class="mp-retry">다시 시도</button><a href="/login.html">로그인 화면</a></div>';
  }
}
function boot() {
  root = document.getElementById('member-panel');
  if (!root) return;
  root.addEventListener('click', async (event) => {
  const tab = event.target.closest('[data-member-tab]');
  if (tab) { activeTab = tab.dataset.memberTab; render(); return; }
  if (event.target.closest('.mp-retry')) { await load(); return; }
  if (event.target.closest('[data-member-signout]')) {
    try { await signOut(); location.href = '/'; } catch (error) { status(error.message, true); } return;
  }
  const favorite = event.target.closest('[data-member-remove-favorite]');
  const coupon = event.target.closest('[data-member-remove-coupon]');
  if (favorite || coupon) {
    const button = favorite || coupon; button.disabled = true;
    try {
      state = await memberRequest(favorite ? '/api/member/favorites' : '/api/member/coupons', {
        action: 'remove', ...(favorite ? { storeId: favorite.dataset.memberRemoveFavorite } : { couponId: coupon.dataset.memberRemoveCoupon })
      });
      render(); status('회원 계정에서 저장 해제했습니다.');
    } catch (error) { button.disabled = false; status(error.message, true); }
  }
  });
  load();
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
else boot();
