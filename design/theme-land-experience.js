/* Garakland Theme Land guidance components.
 * All mascot images reuse the original transparent sticker shipped with the brand.
 * Inject only after the site's actual page content has mounted; no business actions are changed. */
(function(){
 'use strict';
 const MASCOT='/assets/brand/mascot-sticker.png';
 const pages={
  'index.html':{anchor:'.quick',position:'afterend',size:'tiny',title:'상점 탐험도 같이 해요!',copy:'가락한상은 가락랜드 쇼핑 코너의 상점 안내 친구입니다.',href:'/stores.html',cta:'쇼핑 상점 보기'},
  'home.html':{anchor:'.hero',position:'afterend',title:'가락랜드에서 어디부터 놀까요?',copy:'3D 지도부터 시장 쿠폰까지 — 공식 가락한상 캐릭터가 쇼핑과 탐방을 안내해요.',href:'/map.html',cta:'3D 지도 탐험'},
  'stores.html':{anchor:'#shop-section',position:'beforebegin',size:'tiny',title:'상점 방문 전에 확인하세요',copy:'소개되는 상점은 아직 시연 데이터입니다. 실제 협찬 여부는 확인 후 안내합니다.',href:'/merchant-center.html',cta:'협찬 안내'},
  'store.html':{anchor:'.detail-grid',position:'afterend',title:'이 상점의 이야기가 궁금하세요?',copy:'가락한상은 매장별 이야기와 혜택을 소개해요. 시연 정보와 실제 판매정보를 구분해 주세요.',href:'/stores.html',cta:'다른 매장 보기'},
  'coupons.html':{anchor:'.wallet-columns',position:'afterend',title:'쿠폰은 티켓처럼 모아보세요!',copy:'가락한상과 함께 즐기는 쇼핑 혜택. 현재 쿠폰은 시연용으로 실제 결제에 사용할 수 없어요.',href:'/stores.html',cta:'협찬 상점 찾기'},
  'events.html':{anchor:'#event-results',position:'afterend',title:'이달의 시장 탐험 미션!',copy:'즐거운 이벤트와 계절 먹거리를 살펴보세요. 실제 행사 개최 여부는 개별 확인이 필요해요.',href:'/map.html',cta:'시장 탐험 출발'},
  'merchant-center.html':{anchor:'.merchant-stats',position:'afterend',size:'tiny',title:'상인과 함께 만드는 가락랜드',copy:'우리 상점을 소개하고 쿠폰을 준비하는 파트너 운영 공간입니다.',href:'/ops.html',cta:'ERP 운영센터'},
  'market-guide.html':{anchor:'.gl-guide-values',position:'afterend',size:'tiny',title:'가락한상은 쇼핑 안내 친구!',copy:'가락랜드의 공식 메인은 테마랜드. 가락한상은 입점·협찬 상점 소개에만 함께합니다.',href:'/stores.html',cta:'쇼핑 상점 보기'},
  'market.html':{anchor:'.hero',position:'afterend',title:'오늘의 시장 할인 티켓',copy:'가락한상과 함께 시연 특가와 쿠폰을 구경해요. 실제 주문·결제 가능 여부는 별도 확인하세요.',href:'/stores.html',cta:'상점 구경하기'},
  'ar-quest.html':{anchor:'.hero',position:'afterend',title:'AR 탐험 스탬프를 모아봐요!',copy:'시장에서 발견한 이야기와 참여 미션을 모으는 테마랜드 체험이에요.',href:'/map.html',cta:'탐험 지도 보기'},
  'map.html':{anchor:'.map-foot',position:'afterend',size:'tiny',title:'건물 이름을 누르면 지도에 핀이!',copy:'모식도·위성·3D에서 선택 건물의 안내 위치를 확인하세요. 건물 핀은 근사 좌표입니다.',href:'/stores.html',cta:'매장 안내'},
  'hub.html':{anchor:'.hero',position:'afterend',size:'admin',title:'가락랜드 운영 투어',copy:'매장·쿠폰·이벤트·지도 모듈을 관리하는 내부 운영 화면입니다.',href:'/documents.html',cta:'운영 서류'},
  'ops.html':{anchor:'.hero',position:'afterend',size:'admin',title:'상인 파트너 운영 센터',copy:'계약·상품·정산은 실제 승인 전까지 시연 기능만 사용하세요.',href:'/merchant-center.html',cta:'파트너 안내'},
  'login.html':{anchor:'main, .login-card, .auth-card',position:'afterend',size:'tiny',title:'가락랜드에 오신 걸 환영해요',copy:'계정을 안전하게 보호하고 즐거운 시장 탐험을 이어가세요.',href:'/index.html',cta:'홈으로'},
  'documents.html':{anchor:'.filegrid, main',position:'afterend',size:'admin',title:'가락랜드 운영 자료실',copy:'입점·협찬 관련 자료는 시연 및 내부 검토용이며 실제 계약을 대신하지 않습니다.',href:'/merchant-center.html',cta:'상인센터'},
  'design_gallery.html':{anchor:'main, .grid',position:'afterend',size:'tiny',title:'테마랜드 디자인 전시관',copy:'가락랜드는 메인 브랜드, 가락한상은 동일한 원본 캐릭터로 유지합니다.',href:'/market-guide.html',cta:'브랜드 스토리'}
 };
 const tickets=[['🎡','3D 시장지도','/map.html'],['🛍️','매장 이야기','/stores.html'],['🎟️','이벤트·쿠폰','/coupons.html'],['✨','AR 탐험','/ar-quest.html']];
 function makeGuide(info){
  const el=document.createElement('aside');
  el.className='gl-park-guide'+(info.size?' gl-park-guide--'+info.size:'');
  el.setAttribute('aria-label','가락한상 마스코트 안내');
  el.innerHTML='<span class="gl-park-character"><img src="'+MASCOT+'" alt="공식 가락한상 마스코트: 머리에 생선과 게, 채소를 얹고 엄지를 든 상인" loading="lazy" width="74" height="77"></span>'+
  '<span class="gl-park-guide-copy"><small>GARAKLAND · THEME LAND GUIDE</small><b>'+info.title+'</b><p>'+info.copy+'</p></span>'+
  '<a class="gl-park-guide-link" href="'+info.href+'">'+info.cta+' ↗</a>';
  return el;
 }
 function addTickets(anchor){
  if(!anchor||document.querySelector('.gl-park-tickets'))return;
  const rail=document.createElement('nav');
  rail.className='gl-park-tickets';rail.setAttribute('aria-label','가락랜드 테마랜드 빠른 길');
  rail.innerHTML=tickets.map(t=>'<a href="'+t[2]+'"><span class="gl-park-ticket-icon" aria-hidden="true">'+t[0]+'</span><span>'+t[1]+' ↗</span></a>').join('');
  anchor.insertAdjacentElement('afterend',rail);
 }
 function mount(){
  const path=location.pathname.split('/').pop()||'index.html';
  const item=pages[path];
  if(!item||document.querySelector('.gl-park-guide[data-gl-injected="true"]'))return;
  const el=document.querySelector(item.anchor);
  if(!el)return;
  const card=makeGuide(item);
  card.dataset.glInjected='true';
  el.insertAdjacentElement(item.position,card);
  if(path==='index.html'||path==='home.html')addTickets(card);
 }
 if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',()=>setTimeout(mount,0));
 else setTimeout(mount,0);
})();
