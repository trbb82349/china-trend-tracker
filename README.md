# 중국 → 한국 트렌드 제품 트래커

중국에서 먼저 유행하고 한국 상륙 가능성이 높은 제품을 추적하는 자동 업데이트 웹사이트.

## 빠른 시작

배포 방법은 [notes/setup-guide.md](notes/setup-guide.md) 참고.

## 파일 구조

```
china-trend-tracker/
├── data/
│   └── products.json       ← 제품 데이터 (여기를 직접 편집해도 됨)
├── src/
│   ├── collect.py          ← 네이버+Claude로 신규 제품 탐지
│   └── build_site.py       ← JSON → HTML 변환
├── docs/
│   └── index.html          ← 웹사이트 (자동 생성, GitHub Pages 제공)
├── .github/
│   └── workflows/
│       └── update.yml      ← 매주 월/목 자동 실행
└── notes/
    └── setup-guide.md      ← 배포 가이드
```

## 업데이트 주기

매주 **월요일, 목요일** 오전 9시 (KST) 자동 실행.
- 네이버 블로그에서 중국 유행 트렌드 검색
- Claude AI가 신규 제품 후보 분석
- HTML 자동 재빌드 후 GitHub Pages 반영

## 수동으로 제품 추가하기

`data/products.json`을 열어서 products 배열에 아이템 추가 후 저장. GitHub에 push하면 바로 반영.

## 필요 API 키

- Anthropic API Key (claude.ai 계정)
- 네이버 검색 API (developers.naver.com, 무료)
