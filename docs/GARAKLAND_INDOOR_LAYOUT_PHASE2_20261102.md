# 가락몰 실내 길안내 2차 개발 · 승인 도면 온보딩 설계

기준: 2026-11-02 · 기존 \`/indoor-map.html\` 6개 층·3/4/5관 베타를 보존한 별도 작업 브랜치.

## 2차 구현
- **\`/indoor-layout-lab.html\` 도면 검수 작업대**: 로컬 브라우저에서 JSON(최대 1MB) 가져오기, 구역·점포 폴리곤·출입구·동선 노드 표시, 좌표판 클릭으로 임시 점포 위치 초안 작성, JSON 초안 내려받기. 업로드한 파일은 서버에 전송하지 않음.
- \`indoor/layout-schema.mjs\`: 관, 층, 도면 외곽, 점포와 출입구 XY, 이동 노드, 실측 간선 및 출처 정보의 일관성을 검사.
- 승인용 원본 도면/현장 실측 여부, 사용권 근거번호, 검토자/날짜, 개별 지오메트리의 검증 상태를 별개 필드로 보관. **안내판 사진과 시연 도면만으로는 공개 승인 불가**.
- 그래프의 길찾기는 **출처와 각 지오메트리 모두 검증 완료된 입력에서만** 실행. 실측거리 합계 기준 Dijkstra 최단거리(층 내), 휠체어 옵션에서 계단·에스컬레이터 제외.
- 실제 배송/피난/실내 위치 측정이 아님. 다층 승강기 연결, 관 간 경로, 계단 운영 상태, 소요시간은 추가 자료 필요.
- 관리 작업대는 배포된 HTML에서 접근 가능하지만 업로드/파일 내보내기는 로컬 클라이언트 기능만 구현. 운영 데이터베이스 및 고객 제출에는 영향이 없음.

## 도면 JSON 표준
- 필수 \`schemaVersion: 1\`, \`hall: "3" | "4" | "5"\`, \`floor: "B3" | ... | "3F"\`
- \`source\`: \`id\`, \`title\`, \`kind\`(illustrative, signboard-photo, owner-authorized-drawing, on-site-survey), \`status\`(draft, reviewed, approved), \`permissionRef\`, \`reviewer\`, \`reviewDate\`.
- \`outline\`: 도면 외곽 [[x,y], ...] (x/y 각각 0~100 정규화).
- \`shops\`: \`id,name,category,polygon:[[x,y],...],verified:boolean\`. GPS나 지번과는 별도.
- \`entrances\`: \`id,label,xy:[x,y],verified\`.
- \`nodes\`: \`id,type,xy,verified\`. 타입 passage/entry/stairs/elevator/escalator.
- \`edges\`: \`id,from,to,mode,lengthMeters,verified\`. 경로 간선은 등록되기 전 실제 길이 확인 필요.
- 공개 승인 판정은 **검증 로직의 서식 판정일 뿐**, 업로더가 임의 기입한 승인 데이터의 진위를 확인해 주지 않음. 독립된 관리 주체 사용권·원본 확인 및 운영 담당자의 서명이 별도로 필요.
- 다운로드/편집한 데이터는 항상 \`draft\`로 내려가며 검증 플래그가 초기화됨. 운영 게시 API는 구현하지 않음.

## 현장 사진과 사용권
참고 파일: 첨부한 가락몰 3관·5관 층별 안내판, 1F/B1 안내판, 외관 및 상점 사진. 별도 Google Drive의 내부 소스 폴더에서 보관.
이 중 안내판에 나오는 텍스트와 범주를 베타에 활용. **공식 피난 안내도 이미지를 그대로 상용 지도에 공개·복제하지 않음**.
도면 관리 주체의 정식 전자 도면 PDF/DWG/SVG 및 배포·가공 허가를 받은 뒤 위치를 대조해야 함.

## 납품 전 남은 개발
1. 허가받은 실측 원본을 이용한 건물 외곽·구역 폴리곤 편집/승인 API.
2. 점포 번호·층·관/호실 + 계약·영업 상태 소스 대조, 운영 DB 연동, 승인 이력.
3. 승강기·출입 가능 시간·배리어프리 검증 등 다층 그래프 구축.
4. 실제 사용자 위치(건물 위치 비콘/BLE·QR 기준점) 권한 동의 및 정확도 안내.
5. 공식 교통·안전 경로와 별도 검토. 긴급대피 안내로 사용 금지.
6. 고객 인수용 Android 실기기, iOS Safari, 접근성, 장애 대응 테스트.

## 로컬 검증
\`\`\`bash
node tests/indoor_nav.test.mjs
node tests/indoor_layout_schema.test.mjs
python scripts/web_quality_gate.py
python tests/browser_indoor_qa.py # Playwright Chromium 필요
\`\`\`
기능별 테스트는 합성 예제만 사용하며 실제 승인 도면·점포 위치를 꾸며 넣지 않음.
