#!/usr/bin/env python3
"""Original visitor-guide floor diagrams from publicly published Garak Mall floor uses."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "floorplans"
DATA = ROOT / "data" / "floorplans.json"
SOURCE = "서울시농수산식품공사 가락몰 매장검색 층별 안내"
SOURCE_URL = "https://www.garak.co.kr/homepage/M0000273/garak/list.do"
VERIFIED_AT = "2026-10-31"
W, H = 1200, 780
FONT = "Apple SD Gothic Neo, Malgun Gothic, Noto Sans KR, sans-serif"

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def rect(x, y, w, h, fill, label="", sub="", rx=14, ink="#16332b"):
    cx, cy = x + w / 2, y + h / 2
    t1 = f'<text x="{cx}" y="{cy - (8 if sub else 0)}" text-anchor="middle" font-size="20" font-weight="800" fill="{ink}">{esc(label)}</text>' if label else ""
    t2 = f'<text x="{cx}" y="{cy + 18}" text-anchor="middle" font-size="13" fill="#4d655c">{esc(sub)}</text>' if sub else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"/>{t1}{t2}'

def header(title, kicker):
    return f'''<text x="48" y="52" font-size="13" font-weight="800" letter-spacing="2" fill="#6e8a7a">{esc(kicker)}</text>
<text x="48" y="92" font-size="34" font-weight="800" fill="#16332b">{esc(title)}</text>
<text x="48" y="122" font-size="13" fill="#6e8a7a">공식 층별 안내 기반 모식도 · 실측 도면·개별 호실 좌표 아님</text>'''

def legend(items, x=48, y=720):
    parts = []
    xx = x
    for color, name in items:
        parts.append(f'<rect x="{xx}" y="{y}" width="16" height="16" rx="4" fill="{color}"/>')
        parts.append(f'<text x="{xx + 22}" y="{y + 13}" font-size="13" fill="#3d534a">{esc(name)}</text>')
        xx += 28 + len(name) * 13
    return "".join(parts)

def svg(body, title):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}">
  <rect width="{W}" height="{H}" fill="#f4f7f1"/>
  <rect x="24" y="24" width="1152" height="732" rx="28" fill="#fff" stroke="#d7e3d8"/>
  <g font-family="{FONT}">{body}</g>
</svg>
'''

def stack(title, kicker, rows, colors):
    body = [header(title, kicker)]
    top, left, row_h, gap = 160, 60, 86, 12
    for i, (fl, use) in enumerate(rows):
        y = top + i * (row_h + gap)
        body.append(rect(left, y, 140, row_h, "#16332b", fl, ink="#d6ef72"))
        body.append(rect(left + 154, y, 930, row_h, colors[i % len(colors)], use))
    body.append(legend(list(dict.fromkeys(zip(colors, [r[1] for r in rows]))), 60, 700))
    return "\n".join(body)

PLANS = []

def add(building, floor, name, body):
    fn = f"{building}-{floor.lower()}.svg"
    (OUT / fn).write_text(svg(body, name), encoding="utf-8")
    PLANS.append({
        "building": building,
        "floor": floor,
        "imageUrl": f"./assets/floorplans/{fn}",
        "verified": True,
        "width": W,
        "height": H,
        "source": SOURCE,
        "sourceUrl": SOURCE_URL,
        "verifiedAt": VERIFIED_AT,
        "kind": "official-guide"
    })

def sales_all():
    rows = [("3F", "식품·건어 관련 상가 · 전문식당가"), ("2F", "식자재 매장 · 수협/신협"), ("1F", "수산 · 건해 · 축산 · 젓갈"), ("B1", "청과(채소·과일) · 편의 · 식자재"), ("B2", "축산부산물 · 부류별 냉동창고")]
    cols = ["#f0c9d8", "#efe0b8", "#9ec9de", "#c5dd9a", "#e8b7a8"]
    add("sales", "all", "가락몰 판매동 층 구성", stack("가락몰 판매동", "SALES HALL", rows, cols))

def sales_1f():
    body = [header("판매동 1F · 수산 · 건해 · 축산", "SALES HALL / GROUND"),
            rect(56, 170, 500, 430, "#c5e4f3", "A · B · C", "수산"),
            rect(566, 170, 230, 430, "#efe0b8", "D", "건해"),
            rect(806, 170, 338, 430, "#f3c9c0", "E · F", "축산"),
            rect(80, 200, 120, 36, "#16332b", "북측 편의", ink="#fff"),
            rect(980, 200, 140, 36, "#16332b", "화장실", ink="#fff"),
            legend([("#c5e4f3", "수산"), ("#efe0b8", "건해"), ("#f3c9c0", "축산")], 56, 640)]
    add("sales", "1F", "판매동 1F", "\n".join(body))

def sales_b1():
    zones = ["A-1", "A-2", "B", "C-1", "C-2", "D", "E", "F-1", "F-2", "G-1", "G-2", "H-1", "H-2"]
    body = [header("판매동 B1 · 청과(채소·과일)", "SALES HALL / B1")]
    x = 56
    for i, z in enumerate(zones):
        w = 80 if "-" in z else 92
        body.append(rect(x, 200, w, 250, "#c5dd9a", z, "청과"))
        x += w + 6
    body.append(rect(56, 470, 220, 120, "#c9c4dc", "편의시설", "지하철 연결"))
    body.append(rect(286, 470, 220, 120, "#efe0b8", "식품/식자재"))
    body.append(legend([("#c5dd9a", "채소/과일"), ("#c9c4dc", "편의시설"), ("#efe0b8", "식품/식자재")], 56, 640))
    add("sales", "B1", "판매동 B1", "\n".join(body))

def sales_2f():
    body = [header("판매동 2F · 식자재 · 수협/신협", "SALES HALL / 2F"),
            rect(56, 180, 1088, 430, "#efe0b8", "A · B · C", "식품 / 식자재"),
            rect(120, 430, 180, 90, "#9dcfb3", "수협/신협"),
            rect(520, 430, 180, 90, "#9dcfb3", "수협/신협"),
            legend([("#efe0b8", "식품/식자재"), ("#9dcfb3", "수협/신협")], 56, 650)]
    add("sales", "2F", "판매동 2F", "\n".join(body))

def sales_3f():
    body = [header("판매동 3F · 전문식당가 · 식품상가", "SALES HALL / 3F")]
    labels = ["식당가", "식당가", "식당가", "식당가", "식당가", "식당가"]
    for i, lab in enumerate(labels):
        body.append(rect(56 + i * 186, 240, 174, 280, "#f0c9d8", lab))
    body.append(legend([("#f0c9d8", "전문식당가")], 56, 580))
    add("sales", "3F", "판매동 3F", "\n".join(body))

def sales_b2():
    body = [header("판매동 B2 · 축산부산물 · 냉동창고", "SALES HALL / B2"),
            rect(56, 180, 200, 160, "#efe0b8", "식품상가", "냉동창고"),
            rect(266, 180, 200, 160, "#efe0b8", "건어부류", "냉동창고"),
            rect(476, 180, 220, 160, "#efe0b8", "축산부류", "냉동창고"),
            rect(706, 180, 250, 160, "#efe0b8", "청과부류", "냉동·가공"),
            rect(966, 180, 178, 160, "#c5dd9a", "A구역", "축산"),
            rect(56, 360, 200, 160, "#c5e4f3", "수산부류", "냉동창고"),
            rect(266, 360, 200, 160, "#e8d4a8", "젓갈부류", "냉동창고"),
            rect(476, 360, 668, 160, "#f3c9c0", "축산부산물 시장"),
            legend([("#c5dd9a", "A구역 축산"), ("#efe0b8", "창고"), ("#f3c9c0", "축산")], 56, 560)]
    add("sales", "B2", "판매동 B2", "\n".join(body))

def pavilion(building, name, kicker, floors):
    rows = [(fl, use) for fl, use, *_ in floors]
    cols = [item[3] for item in floors]
    add(building, "all", f"{name} 층 구성", stack(name, kicker, rows, cols))
    for fl, use, note, color, blocks in floors:
        body = [header(f"{name} {fl} · {use}", kicker)]
        if len(blocks) == 1:
            body.append(rect(80, 180, 1040, 430, color, blocks[0], note))
        else:
            n = len(blocks)
            bw = (1040 - (n - 1) * 12) / n
            for i, b in enumerate(blocks):
                body.append(rect(80 + i * (bw + 12), 220, bw, 360, color, b, note if i == 0 else ""))
        body.append(legend([(color, use)], 80, 650))
        add(building, fl, f"{name} {fl}", "\n".join(body))

def theme5():
    # 1F 회센터 1–19 as a simplified numbered grid (official visitor map).
    body = [header("가락몰 5관 1F · 회센터", "THEME 05")]
    nums = list(range(1, 20))
    for i, n in enumerate(nums):
        col, row = i % 5, i // 5
        body.append(rect(90 + col * 200, 170 + row * 110, 186, 96, "#f7d7c4", str(n), "회센터" if i == 0 else ""))
    body.append(legend([("#f7d7c4", "회센터 1–19호")], 90, 640))
    add("theme5", "1F", "가락몰 5관 1F", "\n".join(body))
    pavilion_rest = [
        ("2F", "수산전문점 · 식당", "공식 안내: 식당/수산전문점", "#efe0b8", ["수산전문점", "식당"]),
        ("3F", "식당가", "테마 5관 식당", "#f0c9d8", ["식당가"]),
    ]
    add("theme5", "all", "가락몰 5관 층 구성", stack("가락몰 5관", "THEME 05",
        [("3F", "식당가"), ("2F", "수산전문점 · 식당"), ("1F", "회센터 1–19호")],
        ["#f0c9d8", "#efe0b8", "#f7d7c4"]))
    for fl, use, note, color, blocks in pavilion_rest:
        body = [header(f"가락몰 5관 {fl} · {use}", "THEME 05")]
        n = len(blocks)
        bw = (1040 - (n - 1) * 12) / n
        for i, b in enumerate(blocks):
            body.append(rect(80 + i * (bw + 12), 220, bw, 360, color, b, note if i == 0 else ""))
        add("theme5", fl, f"가락몰 5관 {fl}", "\n".join(body))

def wholesale(building, title, kicker, use, color, items):
    add(building, "all", title, stack(title, kicker, [("1F", use)], [color]))
    body = [header(f"{title} · {use}", kicker)]
    n = len(items)
    cols = 3
    for i, it in enumerate(items):
        r, c = divmod(i, cols)
        body.append(rect(80 + c * 360, 180 + r * 150, 340, 130, color, it))
    body.append(legend([(color, use)], 80, 680))
    add(building, "1F", title, "\n".join(body))

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    sales_all(); sales_b2(); sales_b1(); sales_1f(); sales_2f(); sales_3f()
    pavilion("theme1", "가락몰 1관", "THEME 01", [
        ("3F", "식품/식자재", "호실 블록", "#efe0b8", ["식자재 상가"]),
        ("2F", "식자재 매장", "1관 2층", "#efe0b8", ["식자재"]),
        ("1F", "식품/식자재", "부채꼴 테마동", "#efe0b8", ["식자재"]),
    ])
    pavilion("theme2", "가락몰 2관", "THEME 02", [
        ("3F", "식당가", "테마 2관 식당", "#f0c9d8", ["식당가"]),
        ("2F", "식자재 매장", "2관 2층", "#efe0b8", ["식자재"]),
        ("1F", "식자재 매장", "건냉·식품", "#efe0b8", ["식자재"]),
    ])
    pavilion("theme3", "가락몰 3관", "THEME 03", [
        ("3F", "식당가", "3관 3층", "#f0c9d8", ["식당가"]),
        ("2F", "마트 · 친환경", "새농 푸드마켓", "#c5dd9a", ["마트"]),
        ("1F", "식당가", "3관 1층", "#f0c9d8", ["식당가"]),
    ])
    pavilion("theme4", "가락몰 4관", "THEME 04", [
        ("3F", "식당가", "4관 3층", "#f0c9d8", ["식당가"]),
        ("2F", "식당가", "4관 2층", "#f0c9d8", ["식당가"]),
        ("1F", "식당가", "4관 1층", "#f0c9d8", ["식당가"]),
        ("B1", "먹거리광장", "지하철 연결 · 중앙홀", "#efe0b8", ["먹거리광장", "지하철 연결"]),
    ])
    theme5()
    pavilion("office", "가락몰 업무동", "CULTURE & SERVICES", [
        ("5F", "의료시설", "병원·편의", "#f3c9c0", ["의료시설"]),
        ("4F", "도서관 · 쿠킹스튜디오", "가락몰도서관", "#c5dd9a", ["도서관", "쿠킹스튜디오"]),
        ("3F", "보육시설", "업무동 3층", "#efe0b8", ["보육시설"]),
        ("2F", "컨벤션센터", "메인홀", "#c5e4f3", ["컨벤션"]),
        ("1F", "금융·편의", "민원실 · 은행 · 약국", "#c9c4dc", ["민원실", "농협은행", "약국·편의"]),
    ])
    wholesale("produce", "청과 도매구역", "WHOLESALE PRODUCE", "채소2동 등 청과 도매", "#c5dd9a",
              ["채소2동(현대화)", "무·배추·마늘 등 11품목", "기존 청과동 순환재건축"])
    wholesale("seafood", "수산 도매구역", "WHOLESALE SEAFOOD", "수산 도매 · 현대화 진행", "#9ec9de",
              ["수산 도매 거래", "수산동 신축 진행", "전 품목 도매"])
    DATA.write_text(json.dumps({
        "version": 2,
        "readme": "서울시농수산식품공사 가락몰 공식 층별 안내(매장검색)와 각 동 현황을 근거로 만든 방문자용 모식도입니다. 사용승인 실측 도면이 아니며 개별 호실 좌표를 보장하지 않습니다.",
        "plans": PLANS
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(PLANS)} plans")

if __name__ == "__main__":
    main()
