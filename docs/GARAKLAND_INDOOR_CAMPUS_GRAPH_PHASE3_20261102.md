# 가락몰 실내지도 3단계 · 다층/관 연결 그래프 개발 · 2026-11-02

## 이번 단계 실구현

- `indoor/campus-graph.mjs`: 관·층별 승인 도면 JSON을 결합해 노드를 namespace(`hall:floor:node`)로 격리, 확인된 승강기·계단 층 이동 및 관 연결 경로 데이터의 필드/근거 검수.
- `indoor-campus-lab.html` + `indoor/campus-lab.mjs`: 로컬 JSON 업로드, 관·층별 토폴로지(실제 평면도가 아님), 출발/도착 노드 선택, 옵션별 경로 실험 및 승인 초안 내보내기.
- `tests/indoor_campus_graph.test.mjs`: 가상의 3개 층 예시로 층간 엘리베이터/계단, 관 연결, 한 방향 경로, 휠체어 모드, 증빙 누락, 실측 권한 누락을 검사.
- `tests/browser_indoor_qa.py`: 전체 층별 안내와 기존 도면 편집기 외에 새 다층 검수 UI를 실제 Chromium에서 클릭 및 화면 캡처.
- 앞서 완성한 `/indoor-map.html`과 `/indoor-layout-lab.html`의 기존 기능, `master` 및 운영 사이트는 변경하지 않음.

## 다층 그래프 형식

```json
{
  "schemaVersion": 1,
  "publication": "disabled",
  "floors": [
    { "schemaVersion": 1, "hall": "5", "floor": "1F", "source": {},
      "outline": [], "shops": [], "nodes": [], "edges": [], "entrances": [] }
  ],
  "transfers": [
    {
      "id": "transfer-approved-id",
      "from": {"hall":"5","floor":"1F","node":"node-elevator"},
      "to": {"hall":"5","floor":"2F","node":"node-elevator"},
      "mode": "elevator",
      "lengthMeters": 0,
      "accessible": true,
      "bidirectional": true,
      "verified": false,
      "evidenceId": "survey-reference",
      "sourceKind": "survey"
    }
  ]
}
```

위 JSON은 **형식 예시**이고, 길이 0 / 빈 도면 / 미검증 연결은 실제로 검증 오류가 되어 계산되지 않습니다. 실제값이나 실제 매장 위치를 나타내지 않습니다.

## 승인 검증 및 제한

- 모든 참여 층의 도면 출처/허가/검토자와 점포·경로 노드/간선이 검증 완료된 형식이어야 내부 계산 실행.
- 서로 다른 층은 같은 관의 동일 이동수단 노드(엘리베이터↔엘리베이터 등)만 연결. 다른 관 사이 연결은 같은 층의 보행으로만 연결.
- 휠체어 옵션에서 계단·에스컬레이터 제외. **이것만으로 실제 무장애 접근성이 보장되는 것은 아님.** 출입폭·경사·운행 여부는 추가 검증 필수.
- 업로드 파일의 승인 필드는 누구나 작성할 수 있으므로 **클라이언트 서식 검사만으로 법적 사용권/실측 진위를 확인하지 못함**. 운영 공개 API는 개발하지 않았으며 `publication: disabled`와 독립 담당자의 승인 절차가 필요.
- 테스트 예제의 거리·점포·허가 정보는 가상값임을 화면에 표시. 정식 지도·안전·피난·교통 안내로 사용 금지.
- 도면 좌표 0~100은 내부 상대좌표이며 GIS 위치·실내 현 위치를 추정하지 않음.

## 다음 실제 데이터 필요조건

1. 관리주체 승인 원본층 도면(SVG, DWG, PDF)을 층·관별로 수령.
2. 출입구/계단/승강기/에스컬레이터 위치 및 층간 연결지점 현장 측량.
3. 실제 입점업체/호실/영업 상태, 무장애 동선, 출입 제한사항 확인.
4. 관리자 이중 승인과 해시/변경 이력 저장, 외부 접근 권한 검사.
5. Android 실제 기기와 브라우저 접근성 검수 후 공개 릴리스 판단.

## 검증

```sh
node tests/indoor_nav.test.mjs
node tests/indoor_layout_schema.test.mjs
node tests/indoor_campus_graph.test.mjs
python scripts/web_quality_gate.py
python tests/browser_indoor_qa.py
```

모든 검증은 테스트 환경과 명확히 표시된 합성 그래프를 사용하며 실운영 상인 DB/결제·알림/현재위치 데이터는 조회·수정하지 않습니다.
