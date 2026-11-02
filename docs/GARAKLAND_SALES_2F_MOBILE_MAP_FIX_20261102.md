# 가락랜드 판매동 2F 반응형 지도 수정 · 2026-11-02

## 현장 화면 / 재현
사용자 제공 Android 캡처 `31890.jpg`, `31892.jpg`: `https://garakland.lexid.site/map.html` → `층별` → `판매동 2F`. 대형 지도 영역에 SVG가 가운데 1/3 폭으로 작게 나타나며 좌우 빈 공간이 과다. 상세 페이지의 `판매동 2F` 아래에는 기존 SVG와 등록 매장 목록이 표시됨.

## 실제 소스 확인
- `src/map-engine.js`: `renderFloorMap` 지도 영역과 층별 전환
- `src/studio-map.css`: `.floor-map-stage` 내부 flex 배치 및 이미지 크기
- `src/app.js`: `changeMapMode('floor')`, 매장 상세/층 전환
- `src/floorplans.js`: 검증 플래그의 층별 안내 이미지
- `data/floorplans.json`: 판매동 2F URL → `./assets/floorplans/sales-2f.svg`
- `assets/floorplans/sales-2f.svg`: 판매동 2F 식자재 및 수협/신협 개략도

## Drive 비교 자료
- `가락몰_현장사진_분석_20261101` 폴더 / `GARAKMALL_FIELD_PHOTO_DATA_20261101.xlsx`와 현장사진 ZIP: https://drive.google.com/drive/folders/1rkIYaXVNdHWVxqO6d41XuL4WvC1REFxS
- `20261031_024122_garakland_floorplans.txt` 이전 층별도면 작업 기록: https://drive.google.com/file/d/1lGh5Q2kc0gP493B-kS65Etnzlcqsa5wZ/view
- `GARAKLAND_INDOOR_BETA_DELIVERY_README_20261102.md` 베타 설명: https://drive.google.com/file/d/1JMLI8-OkVLuTc1DS2tRX7y8EIWJ2HYof/view

## 수정 내용
1. 플렉스 자식의 이미지 비율 제약으로 가로 폭이 압축되는 문제를 제거하고 **지도 전체 너비에 맞춰 SVG 표시**. 긴 지도는 영역 안에서 스크롤.
2. 새 창에서 **도면 원본 크게 보기** 제공.
3. 모바일 층 버튼의 터치 높이 보완 및 '실측 개별 호실 좌표 아님' 고지 유지.
4. 원본 SVG, 매장별 위치, DB/API, 기존 3D/지형 지도 기능은 수정하지 않음.

## 검증·출시 기준
- `python -m unittest discover -s tests -p test_floor_map_delivery.py`
- `python tests/browser_map_mode_qa.py` (Playwright): 2F 이미지 폭이 지도 가용폭의 최소 87%, 원본 링크, 브라우저 리소스 로딩, 모바일.
- 기존 전체 QA GitHub Actions 통과, Vercel 미리보기 확인 후 운영 배포.
- 실제 점포 호실·정밀 측량·무장애 경로 안내는 별도 승인 자료가 없으므로 배포하지 않음.
