# 설치 & 배포 가이드

이 파일을 따라하면 VSCode 없이 매주 월/목 자동으로 업데이트되는 웹사이트가 만들어집니다.

---

## 1단계 — GitHub 저장소 만들기

1. [github.com](https://github.com) 로그인
2. 우측 상단 **+** → **New repository** 클릭
3. 설정:
   - Repository name: `china-trend-tracker`
   - Public (GitHub Pages 무료 사용에 필요)
   - README 추가 **체크 해제**
4. **Create repository** 클릭

---

## 2단계 — 이 폴더를 GitHub에 올리기

VSCode 터미널에서 (이 폴더 기준):

```bash
cd "c:\Users\trbb8\OneDrive\Desktop\AI, 코딩, BAI 소모임\BAI-workspace-main\10-projects\china-trend-tracker"
git init
git add .
git commit -m "init: 트렌드 트래커 초기 설정"
git branch -M main
git remote add origin https://github.com/[내 깃허브 아이디]/china-trend-tracker.git
git push -u origin main
```

> `[내 깃허브 아이디]` 부분을 실제 GitHub 아이디로 바꿔주세요.

---

## 3단계 — API 키 등록 (GitHub Secrets)

GitHub 저장소 페이지 → **Settings** → 왼쪽 메뉴 **Secrets and variables** → **Actions** → **New repository secret**

아래 3개를 각각 추가:

| Secret 이름 | 값 | 얻는 곳 |
|---|---|---|
| `ANTHROPIC_API_KEY` | sk-ant-... | [console.anthropic.com](https://console.anthropic.com) |
| `NAVER_CLIENT_ID` | 영문+숫자 | 아래 참고 |
| `NAVER_CLIENT_SECRET` | 영문+숫자 | 아래 참고 |

### 네이버 API 키 발급 (무료)
1. [developers.naver.com](https://developers.naver.com) → 로그인
2. **Application 등록** → 앱 이름 입력
3. **검색** API 사용 신청
4. Client ID, Client Secret 복사

---

## 4단계 — GitHub Pages 활성화

저장소 **Settings** → 왼쪽 메뉴 **Pages** → Source: **Deploy from a branch** → Branch: `main` / folder: `/docs` → **Save**

몇 분 후 `https://[내 깃허브 아이디].github.io/china-trend-tracker` 에서 웹사이트 확인!

---

## 5단계 — 첫 수동 실행 (테스트)

저장소 **Actions** 탭 → **트렌드 데이터 자동 업데이트** → **Run workflow** 클릭

실행이 완료(초록 체크)되면 웹사이트가 업데이트됩니다.

---

## 이후에는?

- **아무것도 안 해도** 매주 월요일, 목요일 오전 9시(KST)에 자동 업데이트됩니다.
- 제품을 직접 추가하고 싶을 때: `data/products.json`을 편집 후 push → 자동으로 웹사이트 반영
- 웹사이트 주소는 4단계에서 확인한 URL입니다.

---

## 비용 안내

| 항목 | 비용 |
|---|---|
| GitHub Actions | **무료** (월 2,000분, 이 프로젝트는 약 2분/회) |
| GitHub Pages | **무료** |
| 네이버 API | **무료** |
| Anthropic API (Claude) | 실행당 약 **0.01~0.05달러** (월 8회 × 0.05달러 = 약 500원) |
