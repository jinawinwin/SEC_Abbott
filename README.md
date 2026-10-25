<p align="center">
  <a href="https://jinawinwin.github.io/SEC_Abbott/"><img src="assets/dashboard-badge.svg" alt="🔗 대시보드 바로가기" height="72"></a>
</p>

<p align="center">
  <a href="https://jinawinwin.github.io/SEC_Abbott/"><img src="https://img.shields.io/badge/🔗_대시보드_바로가기-0a4a78?style=for-the-badge" alt="🔗 대시보드 바로가기"></a>
  <a href="https://github.com/jinawinwin/SEC_Abbott/actions/workflows/update-data.yml"><img src="https://github.com/jinawinwin/SEC_Abbott/actions/workflows/update-data.yml/badge.svg" alt="Update SEC data"></a>
</p>

# Abbott Laboratories (NYSE: ABT) — SEC EDGAR 재무 대시보드

SEC EDGAR XBRL API에서 **Abbott Laboratories**의 재무 데이터를 크롤링해 저장하고, 연간·반기·분기 실적을 분석해
GitHub Pages 대시보드로 배포하는 저장소입니다. 데이터는 **매월 1일·5일** GitHub Actions가 자동으로 갱신합니다.

**대시보드:** https://jinawinwin.github.io/SEC_Abbott/

## 기업 개요

| 항목 | 내용 |
|---|---|
| 기업명 | Abbott Laboratories |
| 티커 | **ABT** (NYSE) |
| SEC CIK | 0000001800 |
| GICS Sector | Health Care |
| GICS Industry Group | Health Care Equipment & Services |
| GICS Industry | Health Care Equipment & Supplies |
| GICS Sub-Industry | Health Care Equipment |
| 본사 | Abbott Park, Illinois, USA |
| 설립 | 1888 |
| 회계연도 말 | 12월 31일 |
| 사업 부문 | Medical Devices · Diagnostic Products · Nutritional Products · Established Pharmaceutical Products |
| 특징 | S&P 500, Dividend King (50년 이상 연속 배당 증액) |

## 대시보드 구성

1. **기업 개요** — 티커, GICS Sector / Industry Group / Industry / Sub-Industry, SIC, 사업 부문
2. **핵심 KPI** — 최근 회계연도 매출·순이익·영업이익률·희석 EPS·FCF, 최근 분기 매출 YoY
3. **시각화** — 연간 매출·순이익, 수익성(마진) 추이, 손익 Waterfall, 분기 매출·YoY, 반기(H1 vs H2) 비교,
   현금흐름·주주환원, 비용 구조(도넛), 재무상태, EPS·DPS
4. **재무 수치 테이블** — **Annual / Half-year / Quarterly** 3개 테이블 (손익·수익성·재무상태·현금흐름·주당지표)
5. **글로벌 Peer 비교 테이블**
6. **플로팅 다운로드 패널 (우측)** — **PDF**: 대시보드 화면을 PDF로 저장 · **Excel**: 클릭 시 기간(연간/반기/분기)과
   회계연도 범위를 선택해 `.xlsx` 다운로드

## Global Peer Firms

SEC 제출 기업은 최근 회계연도 10-K 기준(자동 갱신), 해외 상장사(IFRS·비SEC 제출)는 정성 정보만 제공합니다.

<!-- PEERS:START -->
| 기업 | 티커 | 국가 | GICS Sub-Industry | 경쟁·중첩 영역 | FY 말 | 매출액 | 영업이익률 | 순이익률 |
|---|---|---|---|---|---|---:|---:|---:|
| **Abbott Laboratories** | ABT (NYSE) | USA | Health Care Equipment | — (기준 기업) | 2025-12 | $44.3B | 18.2% | 14.7% |
| Medtronic plc | MDT (NYSE) | Ireland / USA | Health Care Equipment | 당뇨(CGM·인슐린펌프), 심혈관·구조적 심장, 신경조절 | 2026-04 | $36.4B | 17.8% | 0.0% |
| Boston Scientific | BSX (NYSE) | USA | Health Care Equipment | 전기생리(EP), 구조적 심장, 혈관중재, 신경조절 | 2025-12 | $20.1B | 18.0% | 14.4% |
| Stryker | SYK (NYSE) | USA | Health Care Equipment | 신경혈관, 의료기기 전반 | 2025-12 | $25.1B | 19.5% | 12.9% |
| Becton, Dickinson and Co. | BDX (NYSE) | USA | Health Care Equipment | 진단(미생물·분자), 의료기기 | 2025-09 | $21.8B | 11.8% | 7.7% |
| Edwards Lifesciences | EW (NYSE) | USA | Health Care Equipment | 구조적 심장(TAVR·승모판 수리) | 2025-12 | $6.1B | 20.8% | 17.7% |
| GE HealthCare | GEHC (NASDAQ) | USA | Health Care Equipment | 진단 영상·환자 모니터링 | 2025-12 | $20.6B | 13.4% | 10.1% |
| Baxter International | BAX (NYSE) | USA | Health Care Equipment | 병원용 의료제품·임상영양 | 2025-12 | $11.2B | -2.7% | -8.5% |
| Johnson & Johnson | JNJ (NYSE) | USA | Pharmaceuticals | MedTech(심혈관·EP·수술), 헬스케어 대형주 | 2025-12 | $94.2B | — | 28.5% |
| Danaher | DHR (NYSE) | USA | Life Sciences Tools & Services | 진단(Beckman Coulter, Cepheid, Radiometer) | 2025-12 | $24.6B | 19.1% | 14.7% |
| Thermo Fisher Scientific | TMO (NYSE) | USA | Life Sciences Tools & Services | 특수진단, 생명과학 도구 | 2025-12 | $44.6B | 17.4% | 15.1% |
| Roche Holding | ROG (SIX Swiss) | Switzerland | Pharmaceuticals | 진단(세계 1위 IVD), 당뇨 관리 | 비SEC·IFRS | — | — | — |
| Siemens Healthineers | SHL (XETRA) | Germany | Health Care Equipment | 검체·현장진단(IVD), 영상진단 | 비SEC·IFRS | — | — | — |
| Koninklijke Philips | PHIA / PHG (Euronext Amsterdam / NYSE) | Netherlands | Health Care Equipment | 환자 모니터링, 영상유도 치료 | 비SEC·IFRS | — | — | — |
| Terumo | 4543 (TSE) | Japan | Health Care Equipment | 심혈관 중재, 혈액·세포 기술 | 비SEC·IFRS | — | — | — |
| Nestlé (Nestlé Health Science) | NESN (SIX Swiss) | Switzerland | Packaged Foods & Meats | 영유아·성인 영양(분유, 의료영양) | 비SEC·IFRS | — | — | — |
<!-- PEERS:END -->

## 저장소 구조

```
├── config/company.json          # 기업 개요(GICS 등)와 Peer 목록
├── scripts/
│   ├── sec_crawler.py           # SEC EDGAR API 크롤러 (companyfacts, submissions, peers)
│   └── analyze.py               # 연간/반기/분기 데이터셋·파생지표·Excel·대시보드 JSON 생성
├── data/
│   ├── raw/                     # SEC 원본 JSON
│   ├── annual.csv · half_year.csv · quarterly.csv
│   ├── abbott_financials.xlsx   # 3개 시트(Annual / Half-year / Quarterly)
│   └── peers.json
├── docs/                        # GitHub Pages 대시보드 (index.html, assets/, data/dashboard.json)
└── .github/workflows/update-data.yml   # 매월 1일·5일 자동 업데이트 에이전트
```

## 데이터 처리 방법

- 출처: `https://data.sec.gov/api/xbrl/companyfacts/CIK0000001800.json`, `.../submissions/CIK0000001800.json`
- 같은 기간의 값이 여러 공시에 있으면 **가장 최근 제출본(재작성 반영)** 을 사용합니다.
- **분기**: 3개월 값이 있으면 그대로, 없으면 누적(YTD) 차감. **Q4 = 연간 − 9개월 누적**
- **반기**: H1 = 6개월 누적, **H2 = 연간 − H1**
- 파생 지표: 매출총이익·마진, 영업/순이익률, R&D 비중, 유효세율, ROE·ROA(연환산), FCF, 순차입금, 부채비율, 유동비율, 배당성향, YoY 성장률
- 매출원가는 Abbott 공시 기준(무형자산상각 제외)이며, 차감 방식으로 산출한 분기·반기 EPS는 근사치입니다.

## 자동 업데이트 (Agent)

`.github/workflows/update-data.yml` 이 **매월 1일과 5일 09:00 KST** 에 실행되어
SEC 크롤링 → 분석 → `data/`, `docs/data/`, README Peer 테이블을 갱신하고 변경 사항을 커밋합니다.
커밋이 올라가면 GitHub Pages 대시보드도 자동으로 다시 배포됩니다. Actions 탭에서 **Run workflow** 로 수동 실행도 가능합니다.

> SEC는 User-Agent에 연락처를 요구합니다. 저장소 **Settings → Secrets and variables → Actions** 에
> `SEC_USER_AGENT` (예: `Your Name your.email@example.com`) 를 등록하면 해당 값을 사용합니다.

## 로컬 실행

```bash
pip install -r requirements.txt
SEC_USER_AGENT="Your Name your.email@example.com" python scripts/sec_crawler.py
python scripts/analyze.py
python -m http.server 8000 --directory docs
```

---
데이터: SEC EDGAR · 본 저장소는 정보 제공 목적이며 투자 권유가 아닙니다.
