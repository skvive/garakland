/* All merchants, prices and coupons below are DEMO fixtures, not verified market listings. */
window.GARAK_BRAND_DATA = {
  shops:[
    {id:'demo-sea',name:'바다마루 수산',category:'수산',building:'수산 구역',floor:'1층',room:'시연 S-01',photo:'assets/editorial/seafood.webp',subphoto:'assets/demo/sea-hero.png',intro:'싱싱한 제철 해산물과 한 끼의 즐거움을 소개하는 수산 매장 시연 사례입니다.',address:'서울 송파구 양재대로 932',lat:null,lng:null,verified:false,blog:'',products:[{name:'제철 생선 꾸러미',price:22000},{name:'모둠 해산물',price:29000}],coupon:'c-sea'},
    {id:'demo-fruit',name:'색동과일',category:'청과',building:'청과 구역',floor:'1층',room:'시연 P-02',photo:'assets/editorial/fruit.webp',subphoto:'assets/demo/fruit-hero.png',intro:'계절마다 바뀌는 과일과 산지 이야기를 사진과 함께 전하는 청과 매장 시연 사례입니다.',address:'서울 송파구 양재대로 932',lat:null,lng:null,verified:false,blog:'',products:[{name:'제철 과일 컵',price:7500},{name:'과일 선물상자',price:18000}],coupon:'c-fruit'},
    {id:'demo-meat',name:'고기공방',category:'축산',building:'축산 구역',floor:'1층',room:'시연 M-03',photo:'assets/editorial/meat.webp',subphoto:'assets/demo/meat-hero.png',intro:'정육 관리와 제철 장보기를 테마로 구성한 축산 매장 시연 사례입니다.',address:'서울 송파구 양재대로 932',lat:null,lng:null,verified:false,blog:'',products:[{name:'불고기 식사용 팩',price:12900},{name:'국거리 한 팩',price:21000}],coupon:'c-meat'},
    {id:'demo-kitchen',name:'가락한상 키친',category:'먹거리',building:'가락몰 테마존',floor:'2층',room:'시연 K-04',photo:'assets/editorial/kitchen.webp',subphoto:'assets/demo/kitchen-hero.png',intro:'시장 먹거리의 매력을 보여주기 위한 가상 식당이며 실제 영업 중인 상점이 아닙니다.',address:'서울 송파구 양재대로 932',lat:null,lng:null,verified:false,blog:'',products:[{name:'든든 한상',price:13900},{name:'시장 국밥',price:9900}],coupon:'c-kitchen'}
  ],
  coupons:[
    {id:'c-sea',shopId:'demo-sea',title:'수산 장보기 할인 체험권',benefit:'3,000원 할인',minimum:30000,description:'3만 원 이상 장보기 조건을 가정한 시연 쿠폰'},
    {id:'c-fruit',shopId:'demo-fruit',title:'제철 과일 체험 쿠폰',benefit:'10% 할인',minimum:0,description:'시연용 10% 혜택'},
    {id:'c-meat',shopId:'demo-meat',title:'축산 한상 체험 쿠폰',benefit:'5,000원 할인',minimum:50000,description:'5만 원 이상 구매를 가정한 시연 쿠폰'},
    {id:'c-kitchen',shopId:'demo-kitchen',title:'한상 방문 체험 쿠폰',benefit:'2,000원 할인',minimum:0,description:'시연용 방문 쿠폰'}
  ],
  events:[
    {id:1,tag:'제철',type:'청과',title:'제철 과일 탐험 주간',subtitle:'과일·원산지 이야기를 살펴보는 가상 프로모션',image:'assets/editorial/fruit.webp',date:'시연 행사',shop:'demo-fruit'},
    {id:2,tag:'체험',type:'수산',title:'우리 바다 한상 발견',subtitle:'수산물 손질과 추천 메뉴를 소개하는 이벤트 시안',image:'assets/editorial/seafood.webp',date:'시연 행사',shop:'demo-sea'},
    {id:3,tag:'먹거리',type:'먹거리',title:'가락한상 시장 미식 산책',subtitle:'가게에서 메뉴까지 탐험하는 가상 코스',image:'assets/editorial/kitchen.webp',date:'시연 행사',shop:'demo-kitchen'},
    {id:4,tag:'상인',type:'축산',title:'상인이 직접 소개하는 한우',subtitle:'상인 스토리·추천 메뉴·쿠폰을 묶은 시안',image:'assets/editorial/meat.webp',date:'시연 행사',shop:'demo-meat'}
  ]
};
