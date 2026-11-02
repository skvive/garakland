# 가락몰 실내지도 4단계: 매장 명부·호실 검수 및 시연용 위치 매핑

2026-11-02 / `feature/garakland-indoor-map-20261102`

신규 `/indoor-tenant-lab.html`는 매장명부 CSV·텍스트 불러오기, 안내판 출처 기반 14개 매장 표기명 대조, 중복 이름/호실·필드·출처 검사, 관·층 필터·검색, 임시 지도 좌표 선택, 검수 전 JSON·CSV 파일 내보내기 기능을 제공합니다.

사용되는 CSV 열: `shop_id,name,hall,floor,room,category,source_ref`. `hall`은 3/4/5, `floor`는 B3/B2/B1/1F/2F/3F. 호실이 없으면 공란이며 미확인으로 표시합니다. `shop_id`는 고유 영문 ID, `source_ref`는 확인자료 식별자입니다. 예시는 `indoor/tenant-template.csv` 참조.

안내판에서 확인한 14개 명칭은 매장 입점/영업/호실/정확 위치의 증명이 아닙니다. 기존 관·층 시연 도면은 실측이 아닌 상대좌표 개략도입니다. 파일을 로컬로 가져오더라도 도면은 강제로 초안 상태가 되고 새 점포는 `verified:false`, `coordinateStatus:unverified`로 표시합니다. CSV로부터 실제 좌표를 추정하거나 공개 DB에 쓰지 않습니다.

로컬 데이터 검수의 주요 차단조건: 1MB/5000행 상한, 불완전한 따옴표, 헤더/열 누락, 중복 shop_id, 같은 관·층 이름 중복, 호실 중복, 잘못된 관·층·좌표, 영업/소유권 검증 누락. CSV 출력 시 수식 주입도 완화합니다.

검증:
```
node tests/indoor_tenant_onboarding.test.mjs
node tests/indoor_layout_schema.test.mjs
python scripts/web_quality_gate.py
python tests/browser_indoor_qa.py
```

**최종 운영 전 필수:** 가락몰 관리 주체가 승인한 최신 층별 도면 사용권, 실매장 호실·출입문 현장 대조, 승강기 및 층간 연결 검증, 서버측 이중 승인 및 수정 기록, 실기기 접근성 검수. 이 도구의 CSV나 승인 상태 필드는 실제 운영 배포 승인의 대체물이 아닙니다.

**배포 범위:** 기존 프로덕션과 `master` 원본 미변경. Draft PR과 Vercel Preview로만 검증.
