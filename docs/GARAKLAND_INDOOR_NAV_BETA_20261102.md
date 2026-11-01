# GARAKLAND 가락몰 실내지도 베타 · 개발·검수 기록

**작성:** 2026-11-02 KST  
**브랜치:** feature/garakland-indoor-map-20261102  
**출시 정책:** 베타 미리보기부터 검수. 공개 운영 출시는 관리 주체 도면/점포 현장 대조 후 승인.

## 현장자료 판독

- 사진 제공: 사용자 촬영 가락몰 3관·5관 층별 안내판, 1층·B1층 실내 안내도, 지상 1층 피난 안내도, 건물 외관·점포 사진.
- 층 분류: B3 고객 주차, B2 축산부산물/가공/주차, B1 과일·채소·먹거리광장, 1F 수산·건어·축산·회센터, 2F 종합식품·주방용품·식자재, 3F 식당·건어물 관련 상가.
- 사진에서 판독되는 3관·5관 매장 14곳은 명칭+관+층만 기록. **호실, 실제 점포 구획, 영업 상태, 실내 좌표는 검증되지 않음.**
- 관의 정확한 건물 연결 좌표, 장애인 접근 동선, 출입 가능 시간, 계단과 승강기 정확한 위치도 미검증.
- 응급피난 지도 사진은 건물의 복잡한 외곽을 이해하는 참고로만 사용. 서비스의 안전·피난 경로로 전환하지 않음.

## 추가 공개자료 조사

2026년 2월 카카오맵은 가락몰을 포함한 시장 실내지도를 제공한다고 발표함.
공식 보도자료: https://www.kakaocorp.com/page/detail/11930
서울시농수산식품공사 가락몰 점포 정보: https://www.garak.co.kr/homepage/M0000212/market/findStore.do

**데이터 재사용 권한 확인 필요:** 카카오맵이 제공하는 정확한 실내 도면/점포좌표를 복제·스크래핑하지 않음. 실제 도면은 저작권자/관리자에게 허용을 받은 SVG/PDF/DWG 원본으로 확보해야 함.

## 구현한 화면

- \`/indoor-map.html\` — 층별 백화점형 UI (B3~3F), 3/4/5관 필터, 업종 및 매장명 검색, 개략 모양의 SVG 지도, 색상 범례.
- 14개 안내판 수록 명칭, 필터링·선택 시 관·층 자동 전환.
- 관·층 수동 출발점에서 목적 관·층으로 이동 순서를 보여주는 **개략적 텍스트 안내**. 실제 최단 경로·거리·시간·GPS·비상 안내 기능 없음.
- 키보드로 구역 선택 및 시력보조 텍스트, 모바일 반응형 지도, 확대·축소.
- 기존 \`/map.html\` 실외 지도, \`/market.html\`과 웹 브랜드 메뉴에서 접근 가능.

## 실제 납품용 매장 좌표 등록 설계

store: id, name, hall, floor, category, roomNo, polygonId, entranceNodeId, coordinateStatus (unverified/approximate/verified), sourceId, verifiedAt
floor: hallId, floorId, referenceDocumentId, referenceScale, localOriginXY, mapTransformMatrix, validFrom
edge: fromNode, toNode, lengthMeters, travelMode (walk/wheelchair/elevator/escalator), accessibility, verifiedAt
poi: floorId, type, anchorNodeId, polygon, sourceId, reviewedAt
도면 좌표와 GPS는 분리 저장. 최초에는 구역 개략도만 사용; 승인된 층별 벡터 도면이 입수되면 해당 층의 geometry만 교체.

## 우선 추가 검증

1. [P0] 실제 관리 주체 원본/사용 승인, 3~5관·모든 층 실측 도면.
2. [P0] 매장별 실제 위치, 현 위치 마커/호실 및 상가 번호 현장 확인.
3. [P0] 출입구·승강기·연결통로 실제 경로 네트워크, 계단·배리어프리 별도.
4. [P1] 관리 콘솔에서 검수 완료된 매장만 위치 핀 게시.
5. [P1] 운영 DB의 floor_id/hall_id/coordinate_status 매핑과 시범 매장 충돌 방지.
6. [P1] 모바일 Android WebView, iOS Safari 및 저성능 안드로이드 실제 기기 테스트.

## 실행 및 증빙

\`\`\`sh
node tests/indoor_nav.test.mjs
python scripts/web_quality_gate.py
python -m pip install playwright
python -m playwright install chromium
python tests/browser_indoor_qa.py
\`\`\`

브라우저 테스트는 6개 층/3개 화면 크기에서 층 전환, 관 필터, 검색, 길안내 안내 및 확대로 검증하고 12장 스크린샷 보관. 실제 API/DB/고객 개인정보를 사용하지 않음.
