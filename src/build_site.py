"""
build_site.py — data/products.json → docs/index.html
"""
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_FILE = ROOT / "data" / "products.json"
OUT_FILE  = ROOT / "docs" / "index.html"

KST = timezone(timedelta(hours=9))

STAGE_CONFIG = {
    "대유행":   {"color": "#e25f48", "bg": "#fff1ee", "dot": "🔥"},
    "유행":     {"color": "#cf8d2e", "bg": "#fff8ee", "dot": "📈"},
    "피크":     {"color": "#c9624f", "bg": "#fff1ee", "dot": "⚡"},
    "시즌 피크":{"color": "#4d83c7", "bg": "#eef4ff", "dot": "☀️"},
    "상승 중":  {"color": "#4d83c7", "bg": "#eef4ff", "dot": "🌱"},
    "초기 신호":{"color": "#9a6fc7", "bg": "#f5f0ff", "dot": "👀"},
}

def prob_color(p):
    if p >= 85: return "#e25f48"
    if p >= 70: return "#cf8d2e"
    if p >= 55: return "#4d83c7"
    return "#9a6fc7"

def stars(p):
    n = round(p / 20)
    return "★" * n + "☆" * (5 - n)

def card_html(p):
    sc   = STAGE_CONFIG.get(p["stage"], {"color": "#888", "bg": "#f5f5f5", "dot": "•"})
    col  = prob_color(p["korea_trend_prob"])
    img_block = ""
    if p.get("image_url"):
        img_block = f"""
        <img class="card-img"
          src="{p['image_url']}"
          alt="{p['name']}"
          onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
        <div class="card-img-placeholder" style="display:none">{p.get('image_emoji','📦')}</div>"""
    else:
        img_block = f"""
        <div class="card-img-placeholder">{p.get('image_emoji','📦')}</div>"""

    tags_html = "".join(
        f'<span class="tag">{t}</span>' for t in p.get("tags", [])
    )

    src = p.get("sourcing", {})
    links_html = ""
    if src.get("aliexpress"):
        links_html += f'<a class="src-link ali" href="{src["aliexpress"]}" target="_blank">AliExpress</a>'
    if src.get("taobao"):
        links_html += f'<a class="src-link taobao" href="{src["taobao"]}" target="_blank">Taobao</a>'
    if src.get("naver"):
        links_html += f'<a class="src-link naver" href="{src["naver"]}" target="_blank">네이버 쇼핑</a>'
    kw1688 = src.get("search_1688", "")
    if kw1688:
        url1688 = f"https://s.1688.com/selloffer/offer_search.htm?keywords={kw1688.replace(' ', '+')}"
        links_html += f'<a class="src-link s1688" href="{url1688}" target="_blank">1688</a>'

    return f"""
    <div class="card" data-stage="{p['stage_class']}" data-prob="{p['korea_trend_prob']}">
      <div class="card-top">{img_block}</div>
      <div class="card-body">
        <div class="card-header-row">
          <div>
            <div class="card-name">{p['name']}</div>
            <div class="card-cn">{p.get('name_cn','')}</div>
          </div>
          <div class="stage-badge" style="background:{sc['bg']};color:{sc['color']}">{sc['dot']} {p['stage']}</div>
        </div>

        <div class="prob-section">
          <div class="prob-row">
            <span class="prob-label">한국 유행 가능성</span>
            <span class="stars">{stars(p['korea_trend_prob'])}</span>
            <span class="prob-pct" style="color:{col}">{p['korea_trend_prob']}%</span>
          </div>
          <div class="prob-track">
            <div class="prob-fill" style="width:{p['korea_trend_prob']}%;background:{col}"></div>
          </div>
        </div>

        <div class="info-rows">
          <div class="info-row"><span class="info-key">카테고리</span><span>{p['category']}</span></div>
          <div class="info-row"><span class="info-key">유행 패턴</span><span>{p.get('origin_pattern','')}</span></div>
          <div class="info-row"><span class="info-key">유행 시기</span><span>{p.get('trend_period','')}</span></div>
          <div class="info-row"><span class="info-key">소싱 가격대</span><span>{p.get('price_range','')}</span></div>
          {"<div class='info-row'><span class='info-key'>중국어 감점</span><span style='color:#c9624f;font-weight:700'>" + str(p.get('china_label_penalty',0)) + "점</span></div>" if p.get('china_label_penalty',0) < 0 else ""}
        </div>

        <div class="why-box">
          <div class="why-label">왜 한국에서 뜰까?</div>
          <div class="why-text">{p.get('why_korea','')}</div>
        </div>

        <div class="evidence-box">
          <div class="evidence-label">근거</div>
          <div class="evidence-text">{p.get('evidence','')}</div>
        </div>

        <div class="tags-row">{tags_html}</div>

        <div class="src-links">{links_html}</div>

        <div class="added-date">등록일 {p.get('added_date','')}</div>
      </div>
    </div>"""

def build():
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    products = data["products"]
    meta     = data["meta"]
    now_kst  = datetime.now(KST).strftime("%Y년 %m월 %d일 %H:%M")

    # Stats
    total       = len(products)
    viral_count = sum(1 for p in products if p["korea_trend_prob"] >= 80)
    avg_prob    = round(sum(p["korea_trend_prob"] for p in products) / total) if total else 0

    stage_order = ["대유행", "피크", "유행", "시즌 피크", "상승 중", "초기 신호"]
    products_sorted = sorted(
        products,
        key=lambda p: (stage_order.index(p["stage"]) if p["stage"] in stage_order else 99,
                       -p["korea_trend_prob"])
    )

    cards = "\n".join(card_html(p) for p in products_sorted)

    filter_stages = sorted(set(p["stage"] for p in products))
    filter_btns = '<button class="filter-btn active" data-stage="all">전체</button>\n'
    for s in stage_order:
        if s in filter_stages:
            filter_btns += f'<button class="filter-btn" data-stage="{next(p["stage_class"] for p in products if p["stage"]==s)}">{s}</button>\n'

    html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>중국 → 한국 트렌드 트래커</title>
  <style>
    :root {{
      --bg: #f7f5ef;
      --ink: #222426;
      --muted: #687078;
      --line: #d8d2c4;
      --panel: #ffffff;
      --accent: #c9624f;
      --accent2: #4d83c7;
      --green: #1a7f4b;
      --shadow: 0 4px 24px rgba(34,36,38,0.10);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--ink);
      font-family: "Pretendard","Apple SD Gothic Neo","Segoe UI",Arial,sans-serif;
      line-height: 1.6;
      font-size: 15px;
    }}
    a {{ color: var(--accent2); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}

    /* ── Header ── */
    .site-header {{
      background: var(--ink);
      color: #fff;
      padding: 40px 24px 32px;
    }}
    .header-inner {{ max-width: 1200px; margin: 0 auto; }}
    .header-tag {{
      display: inline-block;
      background: rgba(255,255,255,0.15);
      border-radius: 4px;
      padding: 3px 10px;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.08em;
      margin-bottom: 14px;
    }}
    .site-header h1 {{ font-size: clamp(24px,4vw,40px); font-weight: 800; line-height: 1.15; margin-bottom: 8px; }}
    .header-sub {{ color: #b0b8c1; font-size: 14px; margin-bottom: 20px; }}
    .header-stats {{
      display: flex; flex-wrap: wrap; gap: 16px;
    }}
    .stat-pill {{
      background: rgba(255,255,255,0.10);
      border-radius: 999px;
      padding: 6px 16px;
      font-size: 13px;
    }}
    .stat-pill strong {{ color: #fff; }}

    /* ── Main ── */
    main {{ max-width: 1200px; margin: 0 auto; padding: 32px 20px 80px; }}

    /* ── Update bar ── */
    .update-bar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 12px;
      background: var(--panel);
      border-radius: 10px;
      padding: 14px 20px;
      margin-bottom: 28px;
      box-shadow: var(--shadow);
      font-size: 13px;
      color: var(--muted);
    }}
    .update-bar .schedule {{
      display: flex; align-items: center; gap: 8px;
    }}
    .schedule-dot {{
      width: 8px; height: 8px; background: #34c759; border-radius: 50%;
      box-shadow: 0 0 0 3px rgba(52,199,89,0.25);
    }}

    /* ── Filters ── */
    .filters {{
      display: flex; flex-wrap: wrap; gap: 8px;
      margin-bottom: 24px;
    }}
    .filter-btn {{
      background: var(--panel);
      border: 1.5px solid var(--line);
      border-radius: 999px;
      padding: 6px 16px;
      font-size: 13px;
      cursor: pointer;
      transition: all 0.15s;
      color: var(--muted);
    }}
    .filter-btn:hover {{ border-color: var(--ink); color: var(--ink); }}
    .filter-btn.active {{
      background: var(--ink); border-color: var(--ink); color: #fff;
    }}
    .sort-select {{
      margin-left: auto;
      background: var(--panel);
      border: 1.5px solid var(--line);
      border-radius: 8px;
      padding: 6px 12px;
      font-size: 13px;
      cursor: pointer;
    }}

    /* ── Cards grid ── */
    .cards-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 24px;
    }}

    /* ── Card ── */
    .card {{
      background: var(--panel);
      border-radius: 16px;
      overflow: hidden;
      box-shadow: var(--shadow);
      display: flex;
      flex-direction: column;
      transition: transform 0.18s, box-shadow 0.18s;
    }}
    .card:hover {{ transform: translateY(-4px); box-shadow: 0 8px 32px rgba(34,36,38,0.15); }}
    .card.hidden {{ display: none; }}

    .card-top {{ position: relative; }}
    .card-img {{
      width: 100%; height: 200px;
      object-fit: cover; display: block;
    }}
    .card-img-placeholder {{
      width: 100%; height: 200px;
      background: linear-gradient(135deg,#f0ebe3,#e4ddd4);
      display: flex; align-items: center; justify-content: center;
      font-size: 56px;
    }}

    .card-body {{ padding: 20px; flex: 1; display: flex; flex-direction: column; gap: 12px; }}

    .card-header-row {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }}
    .card-name {{ font-size: 17px; font-weight: 700; line-height: 1.3; }}
    .card-cn {{ font-size: 12px; color: var(--muted); margin-top: 2px; }}

    .stage-badge {{
      font-size: 11px; font-weight: 700;
      padding: 4px 10px; border-radius: 999px;
      white-space: nowrap; flex-shrink: 0;
    }}

    .prob-section {{ display: flex; flex-direction: column; gap: 5px; }}
    .prob-row {{ display: flex; align-items: center; gap: 8px; }}
    .prob-label {{ font-size: 12px; color: var(--muted); }}
    .stars {{ color: #f4b942; font-size: 13px; letter-spacing: 1px; }}
    .prob-pct {{ font-size: 14px; font-weight: 700; margin-left: auto; }}
    .prob-track {{ height: 5px; background: #ede9e2; border-radius: 999px; }}
    .prob-fill {{ height: 5px; border-radius: 999px; transition: width 0.4s; }}

    .info-rows {{ display: flex; flex-direction: column; gap: 4px; }}
    .info-row {{ display: grid; grid-template-columns: 80px 1fr; font-size: 13px; }}
    .info-key {{ color: var(--muted); }}

    .why-box, .evidence-box {{
      background: #faf8f4;
      border-radius: 8px;
      padding: 12px 14px;
      font-size: 13px;
      line-height: 1.65;
    }}
    .why-label, .evidence-label {{
      font-size: 11px; font-weight: 700; letter-spacing: 0.05em;
      color: var(--muted); margin-bottom: 5px;
    }}
    .evidence-box {{ background: #f0f4ff; }}
    .evidence-text {{ color: #444; font-size: 12.5px; }}

    .tags-row {{ display: flex; flex-wrap: wrap; gap: 5px; }}
    .tag {{
      font-size: 11px; padding: 3px 9px;
      background: #ede9e2; border-radius: 999px; color: var(--muted);
    }}

    .src-links {{ display: flex; flex-wrap: wrap; gap: 7px; }}
    .src-link {{
      display: inline-flex; align-items: center;
      font-size: 12px; font-weight: 600;
      padding: 5px 12px; border-radius: 8px;
      border: 1.5px solid var(--line);
      color: var(--ink); background: var(--bg);
      transition: background 0.15s;
    }}
    .src-link:hover {{ background: #eee; text-decoration: none; }}
    .src-link.ali    {{ border-color: #ff6000; color: #ff6000; }}
    .src-link.taobao {{ border-color: #ff4400; color: #ff4400; }}
    .src-link.naver  {{ border-color: #03c75a; color: #1a7f4b; }}
    .src-link.s1688  {{ border-color: #e3262e; color: #e3262e; }}

    .added-date {{ font-size: 11px; color: #bbb; margin-top: auto; padding-top: 4px; }}

    /* ── No results ── */
    .no-results {{
      grid-column: 1/-1;
      text-align: center;
      padding: 60px 20px;
      color: var(--muted);
    }}

    /* ── Footer ── */
    footer {{
      text-align: center;
      color: var(--muted);
      font-size: 12px;
      border-top: 1px solid var(--line);
      padding: 28px 20px;
    }}

    /* ── 지표 설명 버튼 ── */
    .criteria-btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--ink);
      color: #fff;
      border: none;
      border-radius: 999px;
      padding: 6px 16px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: opacity 0.15s;
    }}
    .criteria-btn:hover {{ opacity: 0.82; }}

    /* ── 모달 오버레이 ── */
    .modal-backdrop {{
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(22,24,26,0.55);
      backdrop-filter: blur(3px);
      z-index: 1000;
      align-items: flex-start;
      justify-content: center;
      padding: 40px 16px 40px;
      overflow-y: auto;
    }}
    .modal-backdrop.open {{ display: flex; }}

    .modal {{
      background: var(--panel);
      border-radius: 18px;
      width: 100%;
      max-width: 680px;
      box-shadow: 0 24px 64px rgba(22,24,26,0.28);
      overflow: hidden;
      animation: slideUp 0.22s ease;
    }}
    @keyframes slideUp {{
      from {{ transform: translateY(24px); opacity: 0; }}
      to   {{ transform: translateY(0);    opacity: 1; }}
    }}

    .modal-header {{
      background: var(--ink);
      color: #fff;
      padding: 22px 28px 18px;
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
    }}
    .modal-header h2 {{ font-size: 18px; font-weight: 800; line-height: 1.25; }}
    .modal-header p  {{ color: #b0b8c1; font-size: 13px; margin-top: 5px; }}
    .modal-close {{
      background: rgba(255,255,255,0.14);
      border: none;
      color: #fff;
      width: 32px; height: 32px;
      border-radius: 50%;
      font-size: 18px;
      cursor: pointer;
      flex-shrink: 0;
      display: flex; align-items: center; justify-content: center;
      transition: background 0.15s;
    }}
    .modal-close:hover {{ background: rgba(255,255,255,0.25); }}

    .modal-body {{ padding: 24px 28px 32px; display: flex; flex-direction: column; gap: 20px; }}

    /* 가중치 요약 바 */
    .weight-summary {{
      background: #faf8f4;
      border-radius: 12px;
      padding: 16px 20px;
    }}
    .weight-summary h3 {{ font-size: 13px; font-weight: 700; color: var(--muted); margin-bottom: 12px; letter-spacing: 0.04em; }}
    .weight-bars {{ display: flex; flex-direction: column; gap: 7px; }}
    .wb-row {{ display: grid; grid-template-columns: 160px 1fr 36px; align-items: center; gap: 10px; font-size: 12.5px; }}
    .wb-label {{ color: var(--ink); font-weight: 500; }}
    .wb-track {{ height: 8px; background: #e8e3da; border-radius: 999px; overflow: hidden; }}
    .wb-fill  {{ height: 8px; border-radius: 999px; }}
    .wb-pct   {{ font-size: 12px; font-weight: 700; text-align: right; }}

    /* 지표 카드 */
    .indicator-list {{ display: flex; flex-direction: column; gap: 12px; }}
    .ind-card {{
      border: 1.5px solid var(--line);
      border-radius: 12px;
      overflow: hidden;
    }}
    .ind-head {{
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 16px;
      cursor: pointer;
      user-select: none;
      background: #fafaf8;
      transition: background 0.12s;
    }}
    .ind-head:hover {{ background: #f3f0e8; }}
    .ind-num {{
      width: 26px; height: 26px;
      background: var(--ink);
      color: #fff;
      border-radius: 50%;
      font-size: 11px;
      font-weight: 700;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0;
    }}
    .ind-title {{ flex: 1; }}
    .ind-name  {{ font-size: 14px; font-weight: 700; }}
    .ind-meta  {{ font-size: 11.5px; color: var(--muted); margin-top: 1px; }}
    .ind-badge {{
      font-size: 12px; font-weight: 700;
      padding: 3px 10px;
      border-radius: 999px;
      white-space: nowrap;
    }}
    .ind-chevron {{ font-size: 12px; color: var(--muted); transition: transform 0.18s; }}
    .ind-card.open .ind-chevron {{ transform: rotate(180deg); }}

    .ind-body {{
      display: none;
      padding: 0 16px 16px;
      font-size: 13px;
      line-height: 1.65;
    }}
    .ind-card.open .ind-body {{ display: block; }}

    .ind-why {{
      background: #f0f4ff;
      border-radius: 8px;
      padding: 10px 13px;
      margin-bottom: 10px;
      font-size: 12.5px;
      color: #2a4a7a;
      border-left: 3px solid #4d83c7;
    }}
    .score-table {{ width: 100%; border-collapse: collapse; font-size: 12.5px; margin-top: 6px; }}
    .score-table th {{ background: #f0ece4; padding: 6px 10px; text-align: left; font-weight: 600; color: var(--muted); font-size: 11px; }}
    .score-table td {{ padding: 6px 10px; border-bottom: 1px solid #f0ece4; }}
    .score-table tr:last-child td {{ border-bottom: none; }}
    .s-pts {{ font-weight: 700; color: var(--accent); }}

    /* 점수→확률 */
    .prob-map {{
      background: #faf8f4;
      border-radius: 12px;
      padding: 16px 20px;
    }}
    .prob-map h3 {{ font-size: 13px; font-weight: 700; color: var(--muted); margin-bottom: 10px; }}
    .prob-map-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }}
    .pm-item {{
      display: flex; align-items: center; gap: 8px;
      background: var(--panel); border-radius: 8px; padding: 8px 12px;
      font-size: 12.5px;
    }}
    .pm-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}

    /* 타이밍 보정 */
    .timing-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
    .tm-item {{
      display: flex; align-items: center; gap: 8px;
      background: #faf8f4; border-radius: 8px; padding: 8px 12px; font-size: 12.5px;
    }}
    .tm-badge {{
      font-size: 11px; font-weight: 700; padding: 2px 7px;
      border-radius: 4px; white-space: nowrap;
    }}
    .tm-neg {{ background: #fff1ee; color: #c9624f; }}
    .tm-pos {{ background: #eef8f0; color: #1a7f4b; }}

    @media (max-width: 600px) {{
      .cards-grid {{ grid-template-columns: 1fr; }}
      .modal-body {{ padding: 20px 18px 28px; }}
      .wb-row {{ grid-template-columns: 120px 1fr 36px; }}
      .prob-map-grid, .timing-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>

<div class="site-header">
  <div class="header-inner">
    <div class="header-tag">TREND TRACKER · 자동 업데이트</div>
    <h1>중국 → 한국<br>트렌드 제품 트래커</h1>
    <p class="header-sub">중국에서 먼저 유행하고 한국에 상륙 예정인 제품을 추적합니다. 매주 월·목 자동 업데이트.</p>
    <div class="header-stats">
      <div class="stat-pill">추적 제품 <strong>{total}개</strong></div>
      <div class="stat-pill">유행 가능성 80%↑ <strong>{viral_count}개</strong></div>
      <div class="stat-pill">평균 가능성 <strong>{avg_prob}%</strong></div>
    </div>
  </div>
</div>

<main>
  <div class="update-bar">
    <div class="schedule">
      <div class="schedule-dot"></div>
      <span>자동 업데이트: 매주 <strong>월요일 · 목요일</strong> 오전 9시 (KST)</span>
    </div>
    <span>마지막 업데이트: <strong>{now_kst}</strong></span>
  </div>

  <div class="filters">
    {filter_btns}
    <button class="criteria-btn" id="open-criteria">📊 지표 설명</button>
    <select class="sort-select" id="sort-select">
      <option value="default">정렬: 유행 단계순</option>
      <option value="prob-desc">유행 가능성 높은 순</option>
      <option value="prob-asc">유행 가능성 낮은 순</option>
      <option value="newest">최신 등록순</option>
    </select>
  </div>

  <div class="cards-grid" id="cards-grid">
    {cards}
    <div class="no-results hidden" id="no-results">해당 조건의 제품이 없습니다.</div>
  </div>
</main>

<footer>
  데이터 출처: 네이버 검색, 중국 마케팅 분석, 샤오홍슈·더우인 트렌드 종합 분석<br>
  소싱 링크는 키워드 기반이며 가격·재고는 변동될 수 있습니다. 최종 확인은 직접 플랫폼에서 해주세요.<br><br>
  마지막 빌드: {now_kst}
</footer>

<!-- ══════════ 지표 설명 모달 ══════════ -->
<div class="modal-backdrop" id="modal-backdrop">
  <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">

    <div class="modal-header">
      <div>
        <h2 id="modal-title">📊 유행 가능성 채점 기준</h2>
        <p>한국 유행 가능성(%) 산출에 사용되는 지표와 가중치입니다. (가점 6개 + 보정 1개 + <span style="color:#ff9f8a">감점 1개</span>)<br>
           매주 월·목 자동 업데이트 시 이 기준으로 Claude AI가 신규 제품을 채점합니다.</p>
      </div>
      <button class="modal-close" id="close-modal" aria-label="닫기">✕</button>
    </div>

    <div class="modal-body">

      <!-- 가중치 요약 바 -->
      <div class="weight-summary">
        <h3>가중치 한눈에 보기</h3>
        <div class="weight-bars">
          <div class="wb-row">
            <span class="wb-label">① 중국 플랫폼 바이럴</span>
            <div class="wb-track"><div class="wb-fill" style="width:25%;background:#e25f48"></div></div>
            <span class="wb-pct" style="color:#e25f48">25%</span>
          </div>
          <div class="wb-row">
            <span class="wb-label">② 한·중 트렌드 시차</span>
            <div class="wb-track"><div class="wb-fill" style="width:20%;background:#cf8d2e"></div></div>
            <span class="wb-pct" style="color:#cf8d2e">20%</span>
          </div>
          <div class="wb-row">
            <span class="wb-label">③ 네이버 검색 신호</span>
            <div class="wb-track"><div class="wb-fill" style="width:5%;background:#687078"></div></div>
            <span class="wb-pct" style="color:#687078">5%</span>
          </div>
          <div class="wb-row">
            <span class="wb-label">④ 한국 문화 적합성</span>
            <div class="wb-track"><div class="wb-fill" style="width:25%;background:#4d83c7"></div></div>
            <span class="wb-pct" style="color:#4d83c7">25%</span>
          </div>
          <div class="wb-row">
            <span class="wb-label">⑤ 제품 확산력</span>
            <div class="wb-track"><div class="wb-fill" style="width:15%;background:#9a6fc7"></div></div>
            <span class="wb-pct" style="color:#9a6fc7">15%</span>
          </div>
          <div class="wb-row">
            <span class="wb-label">⑥ 소싱 환경</span>
            <div class="wb-track"><div class="wb-fill" style="width:10%;background:#1a7f4b"></div></div>
            <span class="wb-pct" style="color:#1a7f4b">10%</span>
          </div>
          <div class="wb-row">
            <span class="wb-label">⑦ 타이밍 보정</span>
            <div class="wb-track"><div class="wb-fill" style="width:8%;background:#aaa;opacity:0.5"></div></div>
            <span class="wb-pct" style="color:#aaa">±보정</span>
          </div>
          <div class="wb-row" style="border-top:1px dashed #e8e3da;padding-top:8px;margin-top:2px">
            <span class="wb-label" style="color:#c9624f">⑧ 중국어 표기 감점</span>
            <div class="wb-track" style="background:#fde8e4"><div class="wb-fill" style="width:15%;background:#c9624f"></div></div>
            <span class="wb-pct" style="color:#c9624f">최대 −15</span>
          </div>
        </div>
      </div>

      <!-- 지표별 상세 (아코디언) -->
      <div class="indicator-list">

        <!-- 지표 1 -->
        <div class="ind-card" data-idx="0">
          <div class="ind-head">
            <div class="ind-num">1</div>
            <div class="ind-title">
              <div class="ind-name">중국 플랫폼 바이럴 강도</div>
              <div class="ind-meta">샤오홍슈 · 더우인 · 글로벌 틱톡 조회수</div>
            </div>
            <span class="ind-badge" style="background:#fff1ee;color:#e25f48">25점</span>
            <span class="ind-chevron">▼</span>
          </div>
          <div class="ind-body">
            <div class="ind-why">
              중국 SNS 바이럴 → 한국 상륙의 시차는 보통 <strong>6개월~1년</strong>입니다.
              즉, 지금 중국에서 폭발하고 있는 제품이 내년 한국 소품샵에 깔릴 가능성이 높아요.
              가장 빠른 <strong>선행 지표</strong>이기 때문에 가중치를 최고로 설정했습니다.
            </div>
            <table class="score-table">
              <tr><th>조건</th><th>점수</th></tr>
              <tr><td>샤오홍슈 1억↑ / 더우인 해시태그 10억↑</td><td class="s-pts">25점</td></tr>
              <tr><td>조회수 1,000만↑</td><td class="s-pts">18점</td></tr>
              <tr><td>조회수 100만↑</td><td class="s-pts">12점</td></tr>
              <tr><td>조회수 10만↑</td><td class="s-pts">6점</td></tr>
              <tr><td>확인 불가 / 초기 단계</td><td class="s-pts">3점</td></tr>
            </table>
          </div>
        </div>

        <!-- 지표 2 -->
        <div class="ind-card" data-idx="1">
          <div class="ind-head">
            <div class="ind-num">2</div>
            <div class="ind-title">
              <div class="ind-name">한국-중국 트렌드 시차</div>
              <div class="ind-meta">중국 유행 중 + 한국 미진입 여부</div>
            </div>
            <span class="ind-badge" style="background:#fff8ee;color:#cf8d2e">20점</span>
            <span class="ind-chevron">▼</span>
          </div>
          <div class="ind-body">
            <div class="ind-why">
              소싱 골든타임 판단 지표입니다. <strong>다이소에 입점되기 직전 1~3개월</strong>이
              마진이 가장 높은 구간이에요. 중국 피크 + 한국 미진입 상태일 때
              가장 높은 점수를 주는 이유입니다.
            </div>
            <table class="score-table">
              <tr><th>상태</th><th>점수</th></tr>
              <tr><td>중국 피크 + 한국 미진입</td><td class="s-pts">20점</td></tr>
              <tr><td>중국 피크 + 한국 초기 신호</td><td class="s-pts">14점</td></tr>
              <tr><td>글로벌 동시 발화</td><td class="s-pts">8점</td></tr>
              <tr><td>이미 한국에서도 유행 중</td><td class="s-pts">4점</td></tr>
              <tr><td>한국 포화 · 다이소 입점</td><td class="s-pts">1점</td></tr>
            </table>
          </div>
        </div>

        <!-- 지표 3 -->
        <div class="ind-card" data-idx="2">
          <div class="ind-head">
            <div class="ind-num">3</div>
            <div class="ind-title">
              <div class="ind-name">네이버 검색·쇼핑 신호</div>
              <div class="ind-meta">블로그 게시물 수 · 검색량 증가율</div>
            </div>
            <span class="ind-badge" style="background:#f2f2f2;color:#687078">5점</span>
            <span class="ind-chevron">▼</span>
          </div>
          <div class="ind-body">
            <div class="ind-why">
              네이버 검색량은 유행이 <strong>이미 시작된 뒤에야</strong> 올라가는
              후행 지표입니다. 선행 탐지가 목적인 이 시스템에서는 낮은 가중치(5%)를 부여해
              참고 정도로만 활용합니다. 검색량이 이미 높다면 소싱 기회가
              줄어든 신호로 읽을 수도 있어요.
            </div>
            <table class="score-table">
              <tr><th>조건</th><th>점수</th></tr>
              <tr><td>블로그 월 500건↑ + 검색량 전월비 200%↑</td><td class="s-pts">5점</td></tr>
              <tr><td>블로그 100건↑ 또는 검색량 100%↑</td><td class="s-pts">3점</td></tr>
              <tr><td>블로그 10~100건</td><td class="s-pts">2점</td></tr>
              <tr><td>거의 없음 (초기)</td><td class="s-pts">1점</td></tr>
            </table>
          </div>
        </div>

        <!-- 지표 4 -->
        <div class="ind-card" data-idx="3">
          <div class="ind-head">
            <div class="ind-num">4</div>
            <div class="ind-title">
              <div class="ind-name">한국 소비자 문화 적합성</div>
              <div class="ind-meta">귀여움 · SNS 친화성 · 가성비 · 채널 적합성</div>
            </div>
            <span class="ind-badge" style="background:#eef4ff;color:#4d83c7">25점</span>
            <span class="ind-chevron">▼</span>
          </div>
          <div class="ind-body">
            <div class="ind-why">
              같은 중국 유행 제품이라도 한국에서 터지는 것과 안 터지는 것이 갈리는
              핵심 이유가 여기에 있습니다. 한국 시장은 <strong>"귀엽고 + SNS에 올리기 좋고 +
              저렴하면"</strong> 폭발적으로 퍼지는 구조예요. 가중치를 25%로 높인 이유입니다.
              아래 5개 항목을 해당하는 만큼 합산합니다.
            </div>
            <table class="score-table">
              <tr><th>항목</th><th>점수</th></tr>
              <tr><td>귀여운 · 아기자기 · 감성 비주얼</td><td class="s-pts">+8점</td></tr>
              <tr><td>SNS 인증샷 · 숏폼 영상 소재 적합</td><td class="s-pts">+7점</td></tr>
              <tr><td>가성비 (원가 대비 체감 가치 높음)</td><td class="s-pts">+5점</td></tr>
              <tr><td>기존 한국 유행의 연장선 (예: 말랑이→두쫀쿠)</td><td class="s-pts">+3점</td></tr>
              <tr><td>다이소·소품샵 채널로 유통 가능</td><td class="s-pts">+2점</td></tr>
            </table>
          </div>
        </div>

        <!-- 지표 5 -->
        <div class="ind-card" data-idx="4">
          <div class="ind-head">
            <div class="ind-num">5</div>
            <div class="ind-title">
              <div class="ind-name">제품 확산력 (가격 · 비주얼)</div>
              <div class="ind-meta">소비자가 기준 충동구매 허들</div>
            </div>
            <span class="ind-badge" style="background:#f5f0ff;color:#9a6fc7">15점</span>
            <span class="ind-chevron">▼</span>
          </div>
          <div class="ind-body">
            <div class="ind-why">
              <strong>1만 원 미만 제품은 SNS 바이럴만으로 폭발적으로 퍼집니다.</strong>
              "이거 사야 해?" 고민 없이 바로 구매로 이어지기 때문이에요.
              가격대가 확산 속도에 직결되므로 15%로 상향했습니다.
              단, 라부부처럼 팬덤이 형성된 수집 아이템은 고가여도 예외 보정이 적용됩니다.
            </div>
            <table class="score-table">
              <tr><th>소비자가</th><th>점수</th></tr>
              <tr><td>1만 원 미만 (충동구매 가능)</td><td class="s-pts">15점</td></tr>
              <tr><td>1~3만 원</td><td class="s-pts">10점</td></tr>
              <tr><td>3~10만 원</td><td class="s-pts">6점</td></tr>
              <tr><td>10만 원 초과</td><td class="s-pts">2점</td></tr>
              <tr><td>수집 아이템 · 팬덤 형성 시 보정</td><td class="s-pts">+3점</td></tr>
            </table>
          </div>
        </div>

        <!-- 지표 6 -->
        <div class="ind-card" data-idx="5">
          <div class="ind-head">
            <div class="ind-num">6</div>
            <div class="ind-title">
              <div class="ind-name">소싱 환경</div>
              <div class="ind-meta">1688 · 알리익스프레스 소싱 가능성 · IP 이슈</div>
            </div>
            <span class="ind-badge" style="background:#eef8f0;color:#1a7f4b">10점</span>
            <span class="ind-chevron">▼</span>
          </div>
          <div class="ind-body">
            <div class="ind-why">
              아이디어가 좋아도 실제로 소싱이 안 되면 의미가 없습니다.
              또한 IP·특허 문제가 있으면 통관 단계에서 막히거나
              리스크가 발생할 수 있어요. <strong>40점 미만 제품은 목록에 올리지 않습니다.</strong>
            </div>
            <table class="score-table">
              <tr><th>조건</th><th>점수</th></tr>
              <tr><td>1688·알리 대량 소싱 가능 + IP 문제 없음</td><td class="s-pts">10점</td></tr>
              <tr><td>소싱 가능하나 MOQ 높거나 배송 복잡</td><td class="s-pts">6점</td></tr>
              <tr><td>IP·특허 불확실</td><td class="s-pts">4점</td></tr>
              <tr><td>소싱 불가 (특허 브랜드만 존재)</td><td class="s-pts">0점</td></tr>
            </table>
          </div>
        </div>

        <!-- 지표 8 (감점) -->
        <div class="ind-card" data-idx="7" style="border-color:#f5cdc7">
          <div class="ind-head" style="background:#fff8f7">
            <div class="ind-num" style="background:#c9624f">8</div>
            <div class="ind-title">
              <div class="ind-name">중국어 표기·브랜드 노출 감점</div>
              <div class="ind-meta">포장·제품의 중국어·중국 브랜드 노출 정도</div>
            </div>
            <span class="ind-badge" style="background:#fff1ee;color:#c9624f">최대 −15점</span>
            <span class="ind-chevron">▼</span>
          </div>
          <div class="ind-body">
            <div class="ind-why" style="border-left-color:#c9624f;background:#fff8f7;color:#7a2a2a">
              한국 소비자는 제품·포장에 중국어가 대놓고 적혀 있거나
              <strong>중국 브랜드임이 한눈에 보이면 호감도가 낮아집니다.</strong>
              "메이드 인 차이나"는 용인하더라도, 패키징이 중국어로 가득하면
              선뜻 구매를 꺼리는 경향이 있어요.
              이 지표는 이 시스템의 <strong>유일한 감점 지표</strong>입니다.
            </div>
            <table class="score-table">
              <tr><th>조건</th><th>감점</th></tr>
              <tr><td>포장·제품에 중국어 없음, 브랜드 중립</td><td class="s-pts" style="color:#1a7f4b">0점</td></tr>
              <tr><td>영문 브랜드이나 포장에 중국어 소량 표기</td><td class="s-pts" style="color:#cf8d2e">−5점</td></tr>
              <tr><td>포장에 중국어 상당량 또는 중국 브랜드 로고 노출</td><td class="s-pts" style="color:#c9624f">−10점</td></tr>
              <tr><td>완전 중국어 제품·패키징 또는 중국 대표 브랜드 (팝마트 등)</td><td class="s-pts" style="color:#e25f48">−15점</td></tr>
            </table>
          </div>
        </div>

      </div><!-- /indicator-list -->

      <!-- 점수 → 확률 변환 -->
      <div class="prob-map">
        <h3>최종 점수 → 유행 가능성 % 변환</h3>
        <div class="prob-map-grid">
          <div class="pm-item"><div class="pm-dot" style="background:#e25f48"></div><span><strong>85~95%</strong> — 대유행 / 피크</span></div>
          <div class="pm-item"><div class="pm-dot" style="background:#cf8d2e"></div><span><strong>70~84%</strong> — 유행 / 상승 중</span></div>
          <div class="pm-item"><div class="pm-dot" style="background:#4d83c7"></div><span><strong>55~69%</strong> — 초기 신호</span></div>
          <div class="pm-item"><div class="pm-dot" style="background:#9a6fc7"></div><span><strong>40~54%</strong> — 관망</span></div>
          <div class="pm-item" style="grid-column:1/-1"><div class="pm-dot" style="background:#ddd"></div><span><strong>40점 미만</strong> — 목록 제외 (확산 가능성 낮음)</span></div>
        </div>
      </div>

      <!-- 타이밍 보정 -->
      <div>
        <h3 style="font-size:13px;color:var(--muted);font-weight:700;margin-bottom:10px;">⑦ 타이밍 보정 (합산 점수에 가감)</h3>
        <div class="timing-grid">
          <div class="tm-item"><span class="tm-badge tm-neg">−15</span><span>다이소 입점 확인 (경쟁 과열)</span></div>
          <div class="tm-item"><span class="tm-badge tm-pos">+5</span><span>소품샵 초기 입점 단계 (골든타임)</span></div>
          <div class="tm-item"><span class="tm-badge tm-pos">+8</span><span>연예인 · 인플루언서 착용 확인</span></div>
          <div class="tm-item"><span class="tm-badge tm-pos">+5</span><span>계절 · 시즌 맞물림</span></div>
        </div>
      </div>

    </div><!-- /modal-body -->
  </div><!-- /modal -->
</div><!-- /modal-backdrop -->

<script>
/* ── 지표 설명 모달 ── */
const backdrop  = document.getElementById("modal-backdrop");
const openBtn   = document.getElementById("open-criteria");
const closeBtn  = document.getElementById("close-modal");

openBtn.addEventListener("click", () => backdrop.classList.add("open"));
closeBtn.addEventListener("click", () => backdrop.classList.remove("open"));
backdrop.addEventListener("click", e => {{ if (e.target === backdrop) backdrop.classList.remove("open"); }});
document.addEventListener("keydown", e => {{ if (e.key === "Escape") backdrop.classList.remove("open"); }});

/* 아코디언 */
document.querySelectorAll(".ind-head").forEach(head => {{
  head.addEventListener("click", () => {{
    const card = head.closest(".ind-card");
    card.classList.toggle("open");
  }});
}});

/* ── 필터 & 정렬 ── */
const grid  = document.getElementById("cards-grid");
const cards = Array.from(grid.querySelectorAll(".card"));
const noRes = document.getElementById("no-results");
let currentStage = "all";
let currentSort  = "default";

document.querySelectorAll(".filter-btn").forEach(btn => {{
  btn.addEventListener("click", () => {{
    document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentStage = btn.dataset.stage;
    render();
  }});
}});

document.getElementById("sort-select").addEventListener("change", e => {{
  currentSort = e.target.value;
  render();
}});

function render() {{
  let visible = cards.filter(c => {{
    if (currentStage === "all") return true;
    return c.dataset.stage === currentStage;
  }});

  if (currentSort === "prob-desc") {{
    visible.sort((a,b) => +b.dataset.prob - +a.dataset.prob);
  }} else if (currentSort === "prob-asc") {{
    visible.sort((a,b) => +a.dataset.prob - +b.dataset.prob);
  }} else if (currentSort === "newest") {{
    visible.reverse();
  }}

  cards.forEach(c => c.classList.add("hidden"));
  visible.forEach(c => c.classList.remove("hidden"));
  noRes.classList.toggle("hidden", visible.length > 0);

  // Re-append in sorted order
  visible.forEach(c => grid.appendChild(c));
  grid.appendChild(noRes);
}}
</script>
</body>
</html>"""

    OUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Built: {OUT_FILE}  ({len(products)} products)")

if __name__ == "__main__":
    build()
