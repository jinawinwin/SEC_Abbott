"""Turn raw SEC XBRL company facts into annual / half-year / quarterly datasets.

Outputs
  data/annual.csv, data/half_year.csv, data/quarterly.csv
  data/abbott_financials.xlsx
  docs/data/dashboard.json   (consumed by the GitHub Pages dashboard)
"""
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CONFIG = json.loads((ROOT / "config" / "company.json").read_text(encoding="utf-8"))

# metric -> ordered list of us-gaap concepts (first concept with a value wins)
FLOW = {
    "revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet", "SalesRevenueGoodsNet"],
    "cogs": ["CostOfGoodsAndServicesSold", "CostOfRevenue", "CostOfGoodsSold",
             "CostOfGoodsAndServiceExcludingDepreciationDepletionAndAmortization"],
    "amortization": ["AmortizationOfIntangibleAssets"],
    "rnd": ["ResearchAndDevelopmentExpense", "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost"],
    "sga": ["SellingGeneralAndAdministrativeExpense"],
    "operating_income": ["OperatingIncomeLoss"],
    "pretax_income": ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
                      "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"],
    "income_tax": ["IncomeTaxExpenseBenefit"],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "eps_basic": ["EarningsPerShareBasic"],
    "eps_diluted": ["EarningsPerShareDiluted"],
    "dps": ["CommonStockDividendsPerShareDeclared", "CommonStockDividendsPerShareCashPaid"],
    "shares_diluted": ["WeightedAverageNumberOfDilutedSharesOutstanding"],
    "ocf": ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"],
    "dividends_paid": ["PaymentsOfDividendsCommonStock", "PaymentsOfDividends"],
    "buybacks": ["PaymentsForRepurchaseOfCommonStock"],
    "dna": ["DepreciationDepletionAndAmortization", "DepreciationAmortizationAndAccretionNet"],
}
INSTANT = {
    "cash": ["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"],
    "inventory": ["InventoryNet"],
    "current_assets": ["AssetsCurrent"],
    "goodwill": ["Goodwill"],
    "total_assets": ["Assets"],
    "current_liabilities": ["LiabilitiesCurrent"],
    "total_liabilities": ["Liabilities"],
    "liabilities_and_equity": ["LiabilitiesAndStockholdersEquity"],
    "equity_incl_nci": ["StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
    "equity": ["StockholdersEquity"],
    "long_term_debt": ["LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations"],
    "short_term_borrowings": ["ShortTermBorrowings", "CommercialPaper"],
    "current_debt": ["LongTermDebtCurrent", "LongTermDebtAndCapitalLeaseObligationsCurrent"],
}
# Averages can't be derived by subtracting year-to-date figures.
NO_DERIVE = {"shares_diluted"}

PEER_CONCEPTS = sorted({c for k in ("revenue", "operating_income", "net_income", "rnd", "ocf", "capex") for c in FLOW[k]}
                       | {c for k in ("total_assets", "equity") for c in INSTANT[k]})

# Display metadata: key -> (label, section, kind)
METRICS = [
    ("revenue", "매출액 (Revenue)", "손익계산서", "usd"),
    ("cogs", "매출원가 (Cost of products sold)", "손익계산서", "usd"),
    ("gross_profit", "매출총이익 (Gross profit)", "손익계산서", "usd"),
    ("rnd", "연구개발비 (R&D)", "손익계산서", "usd"),
    ("sga", "판매관리비 (SG&A)", "손익계산서", "usd"),
    ("amortization", "무형자산상각 (Amortization)", "손익계산서", "usd"),
    ("operating_income", "영업이익 (Operating income)", "손익계산서", "usd"),
    ("pretax_income", "세전이익 (Pre-tax income)", "손익계산서", "usd"),
    ("income_tax", "법인세 (Income tax)", "손익계산서", "usd"),
    ("net_income", "순이익 (Net income)", "손익계산서", "usd"),
    ("revenue_yoy", "매출 성장률 YoY", "수익성·성장", "pct"),
    ("net_income_yoy", "순이익 성장률 YoY", "수익성·성장", "pct"),
    ("gross_margin", "매출총이익률", "수익성·성장", "pct"),
    ("operating_margin", "영업이익률", "수익성·성장", "pct"),
    ("net_margin", "순이익률", "수익성·성장", "pct"),
    ("rnd_ratio", "R&D / 매출", "수익성·성장", "pct"),
    ("effective_tax_rate", "유효세율", "수익성·성장", "pct"),
    ("roe", "ROE (연환산)", "수익성·성장", "pct"),
    ("roa", "ROA (연환산)", "수익성·성장", "pct"),
    ("cash", "현금성자산 (Cash & equivalents)", "재무상태표", "usd"),
    ("inventory", "재고자산 (Inventory)", "재무상태표", "usd"),
    ("current_assets", "유동자산 (Current assets)", "재무상태표", "usd"),
    ("goodwill", "영업권 (Goodwill)", "재무상태표", "usd"),
    ("total_assets", "자산총계 (Total assets)", "재무상태표", "usd"),
    ("current_liabilities", "유동부채 (Current liabilities)", "재무상태표", "usd"),
    ("total_liabilities", "부채총계 (Total liabilities)", "재무상태표", "usd"),
    ("total_debt", "총차입금 (Total debt)", "재무상태표", "usd"),
    ("net_debt", "순차입금 (Net debt)", "재무상태표", "usd"),
    ("equity", "자본총계 (Shareholders' equity)", "재무상태표", "usd"),
    ("current_ratio", "유동비율", "재무상태표", "x"),
    ("debt_to_equity", "부채비율 (Debt / Equity)", "재무상태표", "x"),
    ("ocf", "영업활동현금흐름 (Operating CF)", "현금흐름표", "usd"),
    ("capex", "설비투자 (CapEx)", "현금흐름표", "usd"),
    ("fcf", "잉여현금흐름 (FCF)", "현금흐름표", "usd"),
    ("dividends_paid", "배당금 지급 (Dividends paid)", "현금흐름표", "usd"),
    ("buybacks", "자사주 매입 (Buybacks)", "현금흐름표", "usd"),
    ("dna", "감가상각비 (D&A)", "현금흐름표", "usd"),
    ("fcf_margin", "FCF 마진", "현금흐름표", "pct"),
    ("eps_basic", "기본 EPS (Basic)", "주당지표", "per_share"),
    ("eps_diluted", "희석 EPS (Diluted)", "주당지표", "per_share"),
    ("dps", "주당배당금 (DPS)", "주당지표", "per_share"),
    ("payout_ratio", "배당성향 (DPS / Diluted EPS)", "주당지표", "pct"),
    ("shares_diluted", "희석 가중평균 주식수", "주당지표", "shares"),
]


def d(s):
    return date.fromisoformat(s)


def load_concepts(gaap, concepts):
    """Return list of facts (dicts with start/end/val/filed) for each concept, latest filing wins."""
    out = {}
    for c in concepts:
        node = gaap.get(c)
        if not node:
            continue
        best = {}
        for unit_facts in node["units"].values():
            for f in unit_facts:
                key = (f.get("start"), f["end"])
                if key not in best or f["filed"] > best[key]["filed"]:
                    best[key] = f
        out[c] = [{"start": d(k[0]) if k[0] else None, "end": d(k[1]), "val": v["val"], "form": v.get("form")}
                  for k, v in best.items()]
    return out


def find_duration(facts_by_concept, concepts, start, end, tol=7):
    for c in concepts:
        for f in facts_by_concept.get(c, []):
            if f["start"] and abs((f["start"] - start).days) <= tol and abs((f["end"] - end).days) <= tol:
                return f["val"]
    return None


def find_instant(facts_by_concept, concepts, end, tol=7):
    for c in concepts:
        for f in facts_by_concept.get(c, []):
            if f["start"] is None and abs((f["end"] - end).days) <= tol:
                return f["val"]
    return None


def sub(a, b):
    return None if a is None or b is None else a - b


def add(*xs):
    return None if any(x is None for x in xs) else sum(xs)


def div(a, b):
    return None if a is None or b in (None, 0) else a / b


def month_end(y, m):
    nxt = date(y + (m == 12), m % 12 + 1, 1)
    return nxt - timedelta(days=1)


def build_periods(facts):
    flow_facts = {k: load_concepts(facts, v) for k, v in FLOW.items()}
    inst_facts = {k: load_concepts(facts, v) for k, v in INSTANT.items()}

    years = sorted({f["end"].year for fs in flow_facts["revenue"].values() for f in fs if f["start"]})
    q_ends = [(3, 31), (6, 30), (9, 30), (12, 31)]

    def dur(metric, s, e):
        return find_duration(flow_facts[metric], FLOW[metric], s, e)

    annual, half, quarterly = [], [], []
    for y in years:
        jan1 = date(y, 1, 1)
        ytd_end = [date(y, m, dd) for m, dd in q_ends]
        q_start = [date(y, m, 1) for m in (1, 4, 7, 10)]

        def flows(metric):
            fy = dur(metric, jan1, ytd_end[3])
            ytd = [dur(metric, jan1, e) for e in ytd_end]
            ytd[3] = fy
            qs = []
            for k in range(4):
                v = dur(metric, q_start[k], ytd_end[k])
                if v is None and metric not in NO_DERIVE:
                    v = ytd[0] if k == 0 else sub(ytd[k], ytd[k - 1])
                qs.append(v)
            h1 = ytd[1]
            if h1 is None and metric not in NO_DERIVE:
                h1 = add(qs[0], qs[1])
            h2 = dur(metric, date(y, 7, 1), ytd_end[3])
            if h2 is None and metric not in NO_DERIVE:
                h2 = sub(fy, h1) if fy is not None else add(qs[2], qs[3])
            return fy, [h1, h2], qs

        per_metric = {m: flows(m) for m in FLOW}
        inst = lambda m, e: find_instant(inst_facts[m], INSTANT[m], e)  # noqa: E731

        def row(label, ptype, start, end, getter, months):
            r = {"period": label, "type": ptype, "fiscal_year": y, "start": start.isoformat(), "end": end.isoformat(), "months": months}
            for m in FLOW:
                r[m] = getter(m)
            for m in INSTANT:
                r[m] = inst(m, end)
            return r

        fy_row = row(f"FY{y}", "annual", jan1, ytd_end[3], lambda m: per_metric[m][0], 12)
        if fy_row["revenue"] is not None:
            annual.append(fy_row)
        for i, (s, e) in enumerate([(jan1, ytd_end[1]), (date(y, 7, 1), ytd_end[3])]):
            r = row(f"{y} H{i + 1}", "half", s, e, lambda m, i=i: per_metric[m][1][i], 6)
            if r["revenue"] is not None:
                half.append(r)
        for k in range(4):
            r = row(f"{y} Q{k + 1}", "quarter", q_start[k], ytd_end[k], lambda m, k=k: per_metric[m][2][k], 3)
            if r["revenue"] is not None:
                quarterly.append(r)
    return annual, half, quarterly


def enrich(rows):
    """Add derived metrics (margins, leverage, returns, YoY growth) in place."""
    for i, r in enumerate(rows):
        if r["total_liabilities"] is None:
            eq_all = r["equity_incl_nci"] if r["equity_incl_nci"] is not None else r["equity"]
            r["total_liabilities"] = sub(r["liabilities_and_equity"], eq_all)
        r["gross_profit"] = sub(r["revenue"], r["cogs"])
        r["gross_margin"] = div(r["gross_profit"], r["revenue"])
        r["operating_margin"] = div(r["operating_income"], r["revenue"])
        r["net_margin"] = div(r["net_income"], r["revenue"])
        r["rnd_ratio"] = div(r["rnd"], r["revenue"])
        r["effective_tax_rate"] = div(r["income_tax"], r["pretax_income"])
        r["fcf"] = sub(r["ocf"], r["capex"])
        r["fcf_margin"] = div(r["fcf"], r["revenue"])
        debt_parts = [r[k] for k in ("long_term_debt", "short_term_borrowings", "current_debt") if r[k] is not None]
        r["total_debt"] = sum(debt_parts) if debt_parts else None
        r["net_debt"] = sub(r["total_debt"], r["cash"])
        r["debt_to_equity"] = div(r["total_debt"], r["equity"])
        r["current_ratio"] = div(r["current_assets"], r["current_liabilities"])
        r["payout_ratio"] = div(r["dps"], r["eps_diluted"])
        annualize = 12 / r["months"]
        prev = rows[i - 1] if i >= 1 else None
        avg_eq = (r["equity"] + prev["equity"]) / 2 if prev and r["equity"] and prev["equity"] else r["equity"]
        avg_as = (r["total_assets"] + prev["total_assets"]) / 2 if prev and r["total_assets"] and prev["total_assets"] else r["total_assets"]
        r["roe"] = div(r["net_income"] * annualize if r["net_income"] is not None else None, avg_eq)
        r["roa"] = div(r["net_income"] * annualize if r["net_income"] is not None else None, avg_as)
        yoy = None
        for j in range(i - 1, -1, -1):  # match the same period label one year earlier
            if rows[j]["fiscal_year"] == r["fiscal_year"] - 1 and rows[j]["period"][4:] == r["period"][4:] and rows[j]["type"] == r["type"]:
                yoy = rows[j]
                break
        if r["type"] == "annual":
            yoy = rows[i - 1] if i >= 1 and rows[i - 1]["fiscal_year"] == r["fiscal_year"] - 1 else None
        r["revenue_yoy"] = div(sub(r["revenue"], yoy["revenue"]) if yoy else None, yoy["revenue"] if yoy else None)
        ni_prev = yoy["net_income"] if yoy else None
        r["net_income_yoy"] = div(sub(r["net_income"], ni_prev), abs(ni_prev) if ni_prev else None)
    return rows


def peer_summary(peer):
    path = RAW / "peers" / f"{peer['ticker']}.json"
    base = {k: peer[k] for k in ("name", "ticker", "exchange", "country", "gics_sub_industry", "overlap")}
    base.update({"sec_filer": bool(peer.get("sec_cik")), "fy_end": None, "revenue": None, "operating_income": None,
                 "net_income": None, "net_margin": None, "operating_margin": None, "rnd_ratio": None,
                 "fcf": None, "total_assets": None, "revenue_yoy": None})
    if not path.exists():
        return base
    gaap = json.loads(path.read_text(encoding="utf-8"))["facts"]

    def annual_series(metric):
        facts = load_concepts(gaap, FLOW[metric])
        series = {}
        for c in FLOW[metric]:
            for f in facts.get(c, []):
                if f["start"] and 350 <= (f["end"] - f["start"]).days <= 380:
                    series.setdefault(f["end"], f["val"])
        return series

    rev = annual_series("revenue")
    if not rev:
        return base
    latest = max(rev)
    prior = [e for e in rev if 350 <= (latest - e).days <= 380]

    def at(metric):
        s = annual_series(metric)
        return next((v for e, v in s.items() if abs((e - latest).days) <= 7), None)

    assets = load_concepts(gaap, INSTANT["total_assets"])
    ta = next((f["val"] for fs in assets.values() for f in fs if f["start"] is None and abs((f["end"] - latest).days) <= 7), None)
    base.update({
        "fy_end": latest.isoformat(),
        "revenue": rev[latest],
        "operating_income": at("operating_income"),
        "net_income": at("net_income"),
        "fcf": sub(at("ocf"), at("capex")),
        "total_assets": ta,
        "revenue_yoy": div(sub(rev[latest], rev[prior[0]]), rev[prior[0]]) if prior else None,
    })
    base["net_margin"] = div(base["net_income"], base["revenue"])
    base["operating_margin"] = div(base["operating_income"], base["revenue"])
    base["rnd_ratio"] = div(at("rnd"), base["revenue"])
    return base


def update_readme_peers(peers):
    """Rewrite the peer table between the README markers so it tracks each data refresh."""
    readme = ROOT / "README.md"
    if not readme.exists():
        return
    text = readme.read_text(encoding="utf-8")
    start, end = "<!-- PEERS:START -->", "<!-- PEERS:END -->"
    if start not in text or end not in text:
        return
    bn = lambda v: f"${v / 1e9:,.1f}B" if v is not None else "—"  # noqa: E731
    pc = lambda v: f"{v * 100:.1f}%" if v is not None else "—"  # noqa: E731
    lines = ["| 기업 | 티커 | 국가 | GICS Sub-Industry | 경쟁·중첩 영역 | FY 말 | 매출액 | 영업이익률 | 순이익률 |",
             "|---|---|---|---|---|---|---:|---:|---:|"]
    for p in peers:
        name = f"**{p['name']}**" if p.get("is_self") else p["name"]
        fy = p["fy_end"][:7] if p.get("fy_end") else ("—" if p["sec_filer"] else "비SEC·IFRS")
        lines.append(f"| {name} | {p['ticker']} ({p['exchange']}) | {p['country']} | {p['gics_sub_industry']} | {p['overlap']} | {fy} | "
                     f"{bn(p['revenue'])} | {pc(p['operating_margin'])} | {pc(p['net_margin'])} |")
    head, rest = text.split(start, 1)
    tail = rest.split(end, 1)[1]
    readme.write_text(f"{head}{start}\n" + "\n".join(lines) + f"\n{end}{tail}", encoding="utf-8")


def clean(v):
    if isinstance(v, float) and v != v:
        return None
    return v


def main():
    facts = json.loads((RAW / "companyfacts.json").read_text(encoding="utf-8"))["facts"]["us-gaap"]
    subs = json.loads((RAW / "submissions.json").read_text(encoding="utf-8"))
    annual, half, quarterly = build_periods(facts)
    enrich(annual)
    enrich(half)
    enrich(quarterly)

    keys = [m[0] for m in METRICS]
    meta_cols = ["period", "type", "fiscal_year", "start", "end"]
    frames = {}
    for name, rows in (("annual", annual), ("half_year", half), ("quarterly", quarterly)):
        df = pd.DataFrame(rows)[meta_cols + keys]
        df.to_csv(ROOT / "data" / f"{name}.csv", index=False, encoding="utf-8-sig")
        frames[name] = df

    labels = {m[0]: m[1] for m in METRICS}
    with pd.ExcelWriter(ROOT / "data" / "abbott_financials.xlsx", engine="openpyxl") as xw:
        for sheet, name in (("Annual", "annual"), ("Half-year", "half_year"), ("Quarterly", "quarterly")):
            frames[name].rename(columns=labels).to_excel(xw, sheet_name=sheet, index=False)

    recent = subs["filings"]["recent"]
    filings = [
        {"form": recent["form"][i], "filing_date": recent["filingDate"][i], "report_date": recent["reportDate"][i],
         "url": f"https://www.sec.gov/Archives/edgar/data/{int(subs['cik'])}/{recent['accessionNumber'][i].replace('-', '')}/{recent['primaryDocument'][i]}"}
        for i in range(len(recent["form"])) if recent["form"][i] in ("10-K", "10-Q")
    ][:8]

    company = dict(CONFIG["company"])
    company.update({
        "sec_name": subs.get("name"),
        "sic": subs.get("sic"),
        "sic_description": subs.get("sicDescription"),
        "state_of_incorporation": subs.get("stateOfIncorporation"),
        "tickers": subs.get("tickers"),
        "exchanges": subs.get("exchanges"),
    })

    def records(rows):
        return [{k: clean(r.get(k)) for k in meta_cols + keys} for r in rows]

    out = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "source": "SEC EDGAR XBRL API (companyfacts, submissions)",
            "latest_period": quarterly[-1]["period"] if quarterly else None,
            "latest_filing": filings[0] if filings else None,
        },
        "company": company,
        "metrics": [{"key": k, "label": lbl, "section": sec, "kind": kind} for k, lbl, sec, kind in METRICS],
        "annual": records(annual),
        "half_year": records(half),
        "quarterly": records(quarterly),
        "filings": filings,
        "peers": [peer_summary(p) for p in CONFIG["peers"]],
    }
    abt = dict(out["annual"][-1]) if out["annual"] else {}
    out["peers"].insert(0, {
        "name": company["name"], "ticker": company["ticker"], "exchange": company["exchange"], "country": "USA",
        "gics_sub_industry": company["gics_sub_industry"], "overlap": "— (기준 기업)", "sec_filer": True, "is_self": True,
        "fy_end": abt.get("end"), "revenue": abt.get("revenue"), "operating_income": abt.get("operating_income"),
        "net_income": abt.get("net_income"), "net_margin": abt.get("net_margin"), "operating_margin": abt.get("operating_margin"),
        "rnd_ratio": abt.get("rnd_ratio"), "fcf": abt.get("fcf"), "total_assets": abt.get("total_assets"), "revenue_yoy": abt.get("revenue_yoy"),
    })
    dest = ROOT / "docs" / "data"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "dashboard.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "data" / "peers.json").write_text(json.dumps(out["peers"], ensure_ascii=False, indent=1), encoding="utf-8")
    update_readme_peers(out["peers"])
    print(f"annual={len(annual)} half={len(half)} quarterly={len(quarterly)} latest={out['meta']['latest_period']}")


if __name__ == "__main__":
    main()
