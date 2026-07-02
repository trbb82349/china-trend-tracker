"""
collect.py — 네이버 API + Claude API로 신규 유행 제품 탐지 후 products.json 업데이트
GitHub Actions에서 매주 월/목 자동 실행됨.

필요한 환경변수 (GitHub Secrets):
  ANTHROPIC_API_KEY
  NAVER_CLIENT_ID
  NAVER_CLIENT_SECRET
"""
import json
import os
import re
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST      = timezone(timedelta(hours=9))
ROOT     = Path(__file__).parent.parent
DATA_FILE = ROOT / "data" / "products.json"

NAVER_ID     = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

SEARCH_QUERIES = [
    "중국 유행 제품 한국",
    "알리익스프레스 요즘 인기 제품",
    "샤오홍슈 트렌드 한국",
    "중국 감성 소품 유행",
    "틱톡 유행 중국 제품",
    "중국 직구 인기 아이템 2026",
    "알리 핫템 요즘",
]


# ──────────────────────────────────────────────
# Naver API
# ──────────────────────────────────────────────

def naver_search(query: str, display: int = 10) -> list[dict]:
    if not NAVER_ID or not NAVER_SECRET:
        print(f"  [SKIP] 네이버 API 키 없음: {query}")
        return []
    url = "https://openapi.naver.com/v1/search/blog.json?" + urllib.parse.urlencode({
        "query": query, "display": display, "sort": "date"
    })
    req = urllib.request.Request(url, headers={
        "X-Naver-Client-Id": NAVER_ID,
        "X-Naver-Client-Secret": NAVER_SECRET,
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read())
            return data.get("items", [])
    except Exception as e:
        print(f"  [ERROR] 네이버 검색 실패 ({query}): {e}")
        return []

def clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


# ──────────────────────────────────────────────
# Claude API
# ──────────────────────────────────────────────

def call_claude(prompt: str) -> str:
    if not ANTHROPIC_KEY:
        print("  [SKIP] Anthropic API 키 없음")
        return "[]"
    import urllib.request
    body = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            data = json.loads(res.read())
            return data["content"][0]["text"]
    except Exception as e:
        print(f"  [ERROR] Claude API 실패: {e}")
        return "[]"


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    today = datetime.now(KST).strftime("%Y-%m-%d")
    print(f"[collect.py] 실행: {today}")

    # 1. 기존 데이터 로드
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    existing_ids = {p["id"] for p in data["products"]}
    existing_names = [p["name"] for p in data["products"]]
    print(f"  기존 제품: {len(existing_ids)}개")

    # 2. 네이버 블로그 검색
    raw_snippets = []
    for q in SEARCH_QUERIES:
        items = naver_search(q, display=5)
        for item in items:
            title = clean_html(item.get("title", ""))
            desc  = clean_html(item.get("description", ""))
            raw_snippets.append(f"제목: {title}\n내용: {desc}")
        if items:
            print(f"  검색 완료: '{q}' → {len(items)}건")

    if not raw_snippets:
        print("  검색 결과 없음. products.json 유지.")
        data["meta"]["last_updated"] = today
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return

    snippets_text = "\n---\n".join(raw_snippets[:30])

    # 3. Claude에게 분석 요청
    prompt = f"""당신은 중국→한국 트렌드 소싱 전문가입니다.

아래 네이버 블로그 검색 결과를 분석해서,
한국에서 새롭게 유행할 가능성이 있는 **중국 소싱 가능 제품**을 찾아주세요.
단, 화장품(앰플, 세럼, 미백, 에센스 등 바르는 스킨케어)은 제외합니다.

**이미 추적 중인 제품 (추가 불필요):**
{json.dumps(existing_names, ensure_ascii=False)}

**검색 결과:**
{snippets_text}

---
**한국 유행 가능성(korea_trend_prob) 채점 기준 — 반드시 아래 기준으로 점수를 합산하세요.**

[지표1] 중국 플랫폼 바이럴 강도 — 최대 25점
  샤오홍슈·더우인·글로벌 틱톡 조회수 기준:
  - 1억↑ 또는 더우인 해시태그 10억↑ → 25점
  - 1000만↑ → 18점
  - 100만↑ → 12점
  - 10만↑ → 6점
  - 확인 불가·초기 → 3점

[지표2] 한국-중국 트렌드 시차 — 최대 20점
  - 중국 피크 + 한국 미진입 → 20점
  - 중국 피크 + 한국 초기 신호 → 14점
  - 글로벌 동시 발화 → 8점
  - 이미 한국에서도 유행 중 → 4점
  - 한국에서 포화·다이소 입점 → 1점

[지표3] 네이버 검색·쇼핑 신호 — 최대 5점
  - 블로그 월 500건↑ + 검색량 전월비 200%↑ → 5점
  - 블로그 100건↑ 또는 검색량 100%↑ → 3점
  - 블로그 10~100건 → 2점
  - 거의 없음 → 1점

[지표4] 한국 소비자 문화 적합성 — 최대 25점 (해당 항목 합산)
  - 귀여운·아기자기·감성 비주얼 → +8점
  - SNS 인증샷·숏폼 영상 소재 적합 → +7점
  - 가성비 (원가 대비 체감 가치 높음) → +5점
  - 기존 한국 유행의 연장선 (예: 말랑이→두쫀쿠) → +3점
  - 다이소·소품샵 채널로 유통 가능 → +2점

[지표5] 제품 확산력 (가격·비주얼) — 최대 15점
  소비자가 기준:
  - 1만 원 미만 → 15점
  - 1~3만 원 → 10점
  - 3~10만 원 → 6점
  - 10만 원 초과 → 2점
  (수집 아이템·팬덤 형성 시 +3점 보정 가능)

[지표6] 소싱 환경 — 최대 10점
  - 1688·알리 대량 소싱 가능 + IP 문제 없음 → 10점
  - 소싱 가능하나 MOQ 높거나 복잡 → 6점
  - IP·특허 불확실 → 4점
  - 소싱 불가 → 0점

[지표8] 중국어 표기·브랜드 노출 감점 (마이너스)
  한국 소비자는 제품·포장에 중국어가 대놓고 있거나 중국 브랜드임이 각인되면 호감도가 낮아짐.
  - 포장·제품에 중국어 없음, 브랜드 중립 → 0점
  - 영문 브랜드이나 포장에 중국어 소량 표기 → -5점
  - 포장에 중국어 상당량 또는 중국 브랜드 로고 노출 → -10점
  - 완전 중국어 제품·패키징 또는 중국 대표 브랜드(팝마트 등) → -15점

[타이밍 보정] 위 합산값에 추가:
  - 다이소 입점 확인 → -15점
  - 국내 소품샵 초기 입점 단계 → +5점
  - 연예인·인플루언서 착용 확인 → +8점
  - 계절·시즌 맞물림 → +5점

최종 korea_trend_prob = min(지표1~6 합산 + 지표8 + 보정값, 95)
40점 미만 제품은 목록에 추가하지 마세요.
---

위 검색 결과에서 아직 목록에 없는 신규 제품을 최대 3개 찾아 JSON 배열로 반환하세요.
결과가 없으면 빈 배열 []을 반환하세요.

반드시 아래 JSON 형식을 정확히 지켜주세요:
[
  {{
    "id": "영어-소문자-하이픈",
    "name": "한국어 제품명",
    "name_cn": "중국어 제품명",
    "category": "카테고리",
    "stage": "초기 신호",
    "stage_class": "early",
    "korea_trend_prob": 55,
    "image_url": "",
    "image_emoji": "🎁",
    "origin_pattern": "중국 선행",
    "trend_period": "2026년 하반기",
    "price_range": "미확인",
    "why_korea": "한국에서 유행할 이유 (지표4 한국 문화 적합성 위주로 서술)",
    "evidence": "블로그 검색에서 발견된 근거",
    "sourcing": {{
      "aliexpress": "https://www.aliexpress.com/wholesale?SearchText=키워드",
      "taobao": "",
      "naver": "https://search.shopping.naver.com/search/all?query=한국어키워드",
      "search_1688": "중국어키워드"
    }},
    "tags": ["태그1", "태그2"],
    "added_date": "{today}",
    "china_label_penalty": 0
  }}
]

china_label_penalty는 지표8 기준으로 0, -5, -10, -15 중 하나를 선택하세요.
JSON만 반환하고 다른 텍스트는 쓰지 마세요."""

    print("  Claude 분석 중...")
    response = call_claude(prompt)

    # 4. 파싱
    try:
        # JSON 블록만 추출
        match = re.search(r"\[.*\]", response, re.DOTALL)
        if match:
            new_products = json.loads(match.group())
        else:
            new_products = []
    except json.JSONDecodeError as e:
        print(f"  [WARN] JSON 파싱 실패: {e}")
        new_products = []

    # 5. 중복 제거 후 추가
    added = 0
    for prod in new_products:
        if prod.get("id") and prod["id"] not in existing_ids:
            data["products"].append(prod)
            existing_ids.add(prod["id"])
            added += 1
            print(f"  신규 추가: {prod['name']}")

    if added == 0:
        print("  신규 제품 없음.")

    # 6. 저장
    data["meta"]["last_updated"] = today
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  저장 완료. 총 {len(data['products'])}개")


if __name__ == "__main__":
    main()
