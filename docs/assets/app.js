(() => {
  "use strict";

  const $ = (sel) => document.querySelector(sel);
  const el = (tag, attrs = {}, html = "") => {
    const n = document.createElement(tag);
    Object.entries(attrs).forEach(([k, v]) => n.setAttribute(k, v));
    if (html) n.innerHTML = html;
    return n;
  };
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const isNum = (v) => typeof v === "number" && isFinite(v);

  // ---------- formatting ----------
  const nf0 = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
  const nf1 = new Intl.NumberFormat("en-US", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const nf2 = new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const bn = (v) => (isNum(v) ? v / 1e9 : null);
  const fmtBn = (v) => (isNum(v) ? `$${nf1.format(v / 1e9)}B` : "—");
  const fmtPct = (v, signed = false) => (isNum(v) ? `${signed && v > 0 ? "+" : ""}${nf1.format(v * 100)}%` : "—");
  const fmtCell = (v, kind) => {
    if (!isNum(v)) return "—";
    switch (kind) {
      case "usd": return nf0.format(v / 1e6);
      case "pct": return `${nf1.format(v * 100)}%`;
      case "x": return `${nf2.format(v)}x`;
      case "per_share": return `$${nf2.format(v)}`;
      case "shares": return nf0.format(v / 1e6);
      default: return nf2.format(v);
    }
  };
  const trend = (v) => (isNum(v) ? (v >= 0 ? `<span class="up">▲ ${fmtPct(v)}</span>` : `<span class="down">▼ ${fmtPct(Math.abs(v))}</span>`) : "");

  let DATA = null;
  const charts = [];

  // ---------- overview ----------
  function renderOverview() {
    const c = DATA.company;
    const m = DATA.meta;
    $("#co-name").textContent = c.name;
    $("#co-chips").innerHTML = [
      `<span class="chip"><b>${esc(c.exchange)}: ${esc(c.ticker)}</b></span>`,
      `<span class="chip">${esc(c.gics_sector)}</span>`,
      `<span class="chip">${esc(c.gics_sub_industry)}</span>`,
      `<span class="chip">CIK ${esc(c.cik)}</span>`,
    ].join("");
    const lf = m.latest_filing;
    $("#hero-meta").innerHTML = [
      `최신 반영 기간 <b>${esc(m.latest_period || "—")}</b>`,
      lf ? `최근 공시 <a href="${esc(lf.url)}" target="_blank" rel="noopener">${esc(lf.form)} (${esc(lf.filing_date)})</a>` : "",
      `데이터 갱신 ${esc(m.generated_at)}`,
      `출처: ${esc(m.source)}`,
    ].filter(Boolean).join("<br>");
    $("#co-desc").textContent = c.description;
    const segColors = ["--s1", "--s2", "--s3", "--s4"];
    $("#co-segments").innerHTML = (c.segments || [])
      .map((s, i) => `<span class="seg"><i style="background:var(${segColors[i % 4]})"></i>${esc(s)}</span>`).join("");
    const facts = [
      ["Ticker", `${esc(c.ticker)} <span style="color:var(--muted)">(${esc(c.exchange)})</span>`],
      ["GICS Sector", `<span class="gics">${esc(c.gics_sector)}</span>`],
      ["GICS Industry Group", esc(c.gics_industry_group)],
      ["GICS Industry", esc(c.gics_industry)],
      ["GICS Sub-Industry", `<span class="gics">${esc(c.gics_sub_industry)}</span>`],
      ["SEC SIC", c.sic ? `${esc(c.sic)} · ${esc(c.sic_description)}` : "—"],
      ["본사 (HQ)", esc(c.headquarters)],
      ["설립 (Founded)", esc(c.founded)],
      ["회계연도 말", esc(c.fiscal_year_end)],
      ["지수 / 특징", esc(c.index_membership)],
      ["웹사이트", `<a href="${esc(c.website)}" target="_blank" rel="noopener" style="color:var(--accent)">${esc(c.website.replace("https://", ""))}</a>`],
    ];
    $("#co-facts").innerHTML = facts.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
  }

  function renderKpis() {
    const A = DATA.annual, Q = DATA.quarterly;
    const fy = A[A.length - 1], pfy = A[A.length - 2] || {};
    const lq = Q[Q.length - 1];
    const epsYoy = isNum(fy.eps_diluted) && isNum(pfy.eps_diluted) && pfy.eps_diluted ? (fy.eps_diluted - pfy.eps_diluted) / Math.abs(pfy.eps_diluted) : null;
    const tiles = [
      [`매출액 · ${fy.period}`, fmtBn(fy.revenue), `${trend(fy.revenue_yoy)} YoY`],
      [`순이익 · ${fy.period}`, fmtBn(fy.net_income), `${trend(fy.net_income_yoy)} YoY`],
      [`영업이익률 · ${fy.period}`, fmtPct(fy.operating_margin), `순이익률 ${fmtPct(fy.net_margin)}`],
      [`희석 EPS · ${fy.period}`, isNum(fy.eps_diluted) ? `$${nf2.format(fy.eps_diluted)}` : "—", `${trend(epsYoy)} · DPS ${isNum(fy.dps) ? "$" + nf2.format(fy.dps) : "—"}`],
      [`잉여현금흐름 · ${fy.period}`, fmtBn(fy.fcf), `FCF 마진 ${fmtPct(fy.fcf_margin)}`],
      [`최근 분기 매출 · ${lq.period}`, fmtBn(lq.revenue), `${trend(lq.revenue_yoy)} YoY`],
    ];
    $("#kpis").innerHTML = tiles.map(([l, v, s]) =>
      `<div class="card kpi"><div class="k-label">${esc(l)}</div><div class="k-val">${v}</div><div class="k-sub">${s}</div></div>`).join("");
  }

  // ---------- charts ----------
  function legend(id, items) {
    const box = document.querySelector(`.legend[data-for="${id}"]`);
    if (box) box.innerHTML = items.map(([name, color, line]) => `<span><i class="${line ? "line" : ""}" style="background:${color}"></i>${esc(name)}</span>`).join("");
  }

  function baseOptions(unit) {
    const grid = css("--grid"), muted = css("--muted");
    const fmt = unit === "pct" ? (v) => `${nf1.format(v)}%` : unit === "ps" ? (v) => `$${nf2.format(v)}` : (v) => `$${nf1.format(v)}B`;
    return {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      animation: { duration: 400 },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: css("--surface"), titleColor: css("--text"), bodyColor: css("--text-2"),
          borderColor: css("--border"), borderWidth: 1, padding: 10, boxPadding: 4, usePointStyle: true,
          callbacks: { label: (ctx) => ` ${ctx.dataset.label}: ${ctx.parsed.y == null ? "—" : fmt(ctx.parsed.y)}` },
        },
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: muted, font: { size: 11 }, maxRotation: 0, autoSkipPadding: 12 }, border: { color: grid } },
        y: { grid: { color: grid }, border: { display: false }, ticks: { color: muted, font: { size: 11 }, callback: fmt } },
      },
    };
  }

  const barDs = (label, data, color, extra = {}) => ({
    label, data, backgroundColor: color, borderRadius: 4, borderSkipped: "start", maxBarThickness: 28,
    categoryPercentage: 0.72, barPercentage: 0.9, borderColor: css("--surface"), borderWidth: { left: 1, right: 1 }, ...extra,
  });
  const lineDs = (label, data, color, extra = {}) => ({
    label, data, borderColor: color, backgroundColor: color, borderWidth: 2, pointRadius: 0, pointHoverRadius: 5,
    pointHoverBorderWidth: 2, pointHoverBorderColor: css("--surface"), tension: 0.25, spanGaps: true, ...extra,
  });
  const make = (id, cfg) => charts.push(new Chart(document.getElementById(id), cfg));

  function renderCharts() {
    charts.splice(0).forEach((c) => c.destroy());
    const S = (n) => css(`--s${n}`);
    const A = DATA.annual, H = DATA.half_year, Q = DATA.quarterly;
    const years = A.map((r) => String(r.fiscal_year));

    // 1. annual revenue & net income
    make("c-annual", {
      type: "bar",
      data: { labels: years, datasets: [barDs("매출액", A.map((r) => bn(r.revenue)), S(1)), barDs("순이익", A.map((r) => bn(r.net_income)), S(2))] },
      options: (() => {
        const o = baseOptions("usd");
        o.plugins.tooltip.callbacks.afterBody = (items) => {
          const r = A[items[0].dataIndex];
          return isNum(r.revenue_yoy) ? [`매출 YoY ${fmtPct(r.revenue_yoy, true)} · 순이익률 ${fmtPct(r.net_margin)}`] : [];
        };
        return o;
      })(),
    });
    legend("c-annual", [["매출액", S(1)], ["순이익", S(2)]]);

    // 2. margins
    const pct = (k) => A.map((r) => (isNum(r[k]) ? r[k] * 100 : null));
    make("c-margin", {
      type: "line",
      data: { labels: years, datasets: [lineDs("매출총이익률", pct("gross_margin"), S(1)), lineDs("영업이익률", pct("operating_margin"), S(2)), lineDs("순이익률", pct("net_margin"), S(3))] },
      options: baseOptions("pct"),
    });
    legend("c-margin", [["매출총이익률", S(1), 1], ["영업이익률", S(2), 1], ["순이익률", S(3), 1]]);

    // 3. waterfall for latest FY
    const fy = A[A.length - 1];
    $("#wf-title").textContent = `손익 구조 Waterfall · ${fy.period}`;
    const steps = [["매출액", fy.revenue, "total"], ["매출원가", fy.cogs, "neg"], ["R&D", fy.rnd, "neg"], ["SG&A", fy.sga, "neg"], [["무형자산", "상각"], fy.amortization, "neg"]];
    const opex = steps.slice(1).reduce((s, x) => s + (isNum(x[1]) ? x[1] : 0), 0);
    const other = isNum(fy.operating_income) ? fy.revenue - opex - fy.operating_income : 0;
    if (Math.abs(other) > fy.revenue * 0.005) steps.push([["기타", "영업비용"], other, "neg"]);
    steps.push(["영업이익", fy.operating_income, "total"]);
    if (isNum(fy.net_income) && isNum(fy.operating_income)) steps.push([["영업외", "·법인세"], fy.operating_income - fy.net_income, "neg"]);
    steps.push(["순이익", fy.net_income, "total"]);
    let run = 0;
    const wf = steps.filter((s) => isNum(s[1])).map(([name, v, kind]) => {
      if (kind === "total") { run = v; return { name, range: [0, bn(v)], kind, v }; }
      const from = run; run -= v;
      return { name, range: [bn(run), bn(from)], kind: v >= 0 ? "neg" : "pos", v: -v };
    });
    const wfOpt = baseOptions("usd");
    wfOpt.interaction = { mode: "nearest", intersect: true };
    wfOpt.plugins.tooltip.callbacks = {
      label: (ctx) => { const s = wf[ctx.dataIndex]; return ` ${s.kind === "total" ? "" : s.v < 0 ? "−" : "+"}${fmtBn(Math.abs(s.v))} (매출 대비 ${fmtPct(Math.abs(s.v) / fy.revenue)})`; },
    };
    wfOpt.scales.x.ticks.autoSkip = false;
    wfOpt.scales.x.ticks.font = { size: 10.5 };
    make("c-waterfall", {
      type: "bar",
      data: { labels: wf.map((s) => s.name), datasets: [{ label: fy.period, data: wf.map((s) => s.range), backgroundColor: wf.map((s) => (s.kind === "total" ? S(1) : s.kind === "neg" ? S(8) : S(3))), borderRadius: 4, borderSkipped: false, maxBarThickness: 44 }] },
      options: wfOpt,
    });

    // 4. quarterly revenue (last 16 quarters)
    const q = Q.slice(-16);
    const qOpt = baseOptions("usd");
    qOpt.plugins.tooltip.callbacks.afterBody = (items) => {
      const r = q[items[0].dataIndex];
      return [`매출 YoY ${fmtPct(r.revenue_yoy, true)} · 영업이익률 ${fmtPct(r.operating_margin)}`];
    };
    make("c-quarter", {
      type: "bar",
      data: { labels: q.map((r) => r.period.replace(" ", " ")), datasets: [barDs("매출액", q.map((r) => bn(r.revenue)), S(1)), barDs("영업이익", q.map((r) => bn(r.operating_income)), S(3)), barDs("순이익", q.map((r) => bn(r.net_income)), S(2))] },
      options: qOpt,
    });
    legend("c-quarter", [["매출액", S(1)], ["영업이익", S(3)], ["순이익", S(2)]]);

    // 5. quarterly YoY
    const qy = Q.slice(-16).filter((r) => isNum(r.revenue_yoy));
    const yoyOpt = baseOptions("pct");
    yoyOpt.interaction = { mode: "nearest", intersect: false, axis: "x" };
    make("c-qyoy", {
      type: "bar",
      data: { labels: qy.map((r) => r.period), datasets: [barDs("매출 YoY", qy.map((r) => r.revenue_yoy * 100), qy.map((r) => (r.revenue_yoy >= 0 ? S(1) : S(8))), { borderSkipped: false })] },
      options: yoyOpt,
    });

    // 6. half-year comparison
    const hy = [...new Set(H.map((r) => r.fiscal_year))].slice(-10);
    const hv = (y, h) => { const r = H.find((x) => x.fiscal_year === y && x.period.endsWith(h)); return r ? bn(r.revenue) : null; };
    make("c-half", {
      type: "bar",
      data: { labels: hy.map(String), datasets: [barDs("H1 (1–6월)", hy.map((y) => hv(y, "H1")), S(1)), barDs("H2 (7–12월)", hy.map((y) => hv(y, "H2")), S(7))] },
      options: baseOptions("usd"),
    });
    legend("c-half", [["H1 (1–6월)", S(1)], ["H2 (7–12월)", S(7)]]);

    // 7. cash flow
    const a10 = A.slice(-10);
    make("c-cash", {
      type: "bar",
      data: {
        labels: a10.map((r) => String(r.fiscal_year)),
        datasets: [barDs("영업CF", a10.map((r) => bn(r.ocf)), S(1)), barDs("CapEx", a10.map((r) => bn(r.capex)), S(2)), barDs("FCF", a10.map((r) => bn(r.fcf)), S(3)), barDs("배당금", a10.map((r) => bn(r.dividends_paid)), S(4))],
      },
      options: baseOptions("usd"),
    });
    legend("c-cash", [["영업CF", S(1)], ["CapEx", S(2)], ["FCF", S(3)], ["배당금", S(4)]]);

    // 8. cost structure donut
    $("#cost-title").textContent = `비용 구조 · ${fy.period}`;
    const parts = [["매출원가", fy.cogs], ["R&D", fy.rnd], ["SG&A", fy.sga], ["무형자산상각", fy.amortization]];
    if (other > 0 && Math.abs(other) > fy.revenue * 0.005) parts.push(["기타 영업비용", other]);
    parts.push(["영업이익", fy.operating_income]);
    const pv = parts.filter((p) => isNum(p[1]) && p[1] > 0);
    const donutColors = [S(1), S(2), S(3), S(4), S(5), S(6)].slice(0, pv.length);
    make("c-cost", {
      type: "doughnut",
      data: { labels: pv.map((p) => p[0]), datasets: [{ data: pv.map((p) => p[1]), backgroundColor: donutColors, borderColor: css("--surface"), borderWidth: 2, hoverOffset: 6 }] },
      options: {
        responsive: true, maintainAspectRatio: false, cutout: "62%",
        plugins: {
          legend: { position: "right", labels: { color: css("--text-2"), usePointStyle: true, pointStyle: "rectRounded", padding: 12, font: { size: 12 },
            generateLabels: (chart) => chart.data.labels.map((l, i) => ({ text: `${l}  ${fmtPct(pv[i][1] / fy.revenue)}`, fillStyle: donutColors[i], strokeStyle: donutColors[i], fontColor: css("--text-2"), index: i })) } },
          tooltip: { callbacks: { label: (ctx) => ` ${ctx.label}: ${fmtBn(ctx.parsed)} (${fmtPct(ctx.parsed / fy.revenue)})` } },
        },
      },
    });

    // 9. balance sheet
    make("c-balance", {
      type: "line",
      data: {
        labels: years,
        datasets: [lineDs("자산총계", A.map((r) => bn(r.total_assets)), S(1)), lineDs("부채총계", A.map((r) => bn(r.total_liabilities)), S(2)), lineDs("자본총계", A.map((r) => bn(r.equity)), S(3)), lineDs("순차입금", A.map((r) => bn(r.net_debt)), S(7), { borderDash: [5, 4] })],
      },
      options: baseOptions("usd"),
    });
    legend("c-balance", [["자산총계", S(1), 1], ["부채총계", S(2), 1], ["자본총계", S(3), 1], ["순차입금 (점선)", S(7), 1]]);

    // 10. EPS & DPS
    make("c-eps", {
      type: "line",
      data: { labels: years, datasets: [lineDs("희석 EPS", A.map((r) => r.eps_diluted), S(1), { pointRadius: 3 }), lineDs("주당배당금", A.map((r) => r.dps), S(4), { pointRadius: 3 })] },
      options: baseOptions("ps"),
    });
    legend("c-eps", [["희석 EPS", S(1), 1], ["주당배당금 (DPS)", S(4), 1]]);
  }

  // ---------- tables ----------
  const KEY_ROWS = new Set(["revenue", "operating_income", "net_income", "fcf", "eps_diluted"]);

  function renderTable(tableId, rows, countId) {
    const cols = rows.slice().reverse();
    const metrics = DATA.metrics.filter((m) => cols.some((r) => isNum(r[m.key])));
    let html = `<thead><tr><th scope="col">항목 (Metric)</th>${cols.map((r, i) => `<th scope="col" class="${i === 0 ? "latest" : ""}">${esc(r.period)}</th>`).join("")}</tr></thead><tbody>`;
    let section = null;
    for (const m of metrics) {
      if (m.section !== section) {
        section = m.section;
        html += `<tr class="sec"><td>${esc(section)}</td><td colspan="${cols.length}"></td></tr>`;
      }
      html += `<tr class="${KEY_ROWS.has(m.key) ? "key" : ""}"><td class="lbl">${esc(m.label)}</td>${cols.map((r) => {
        const v = r[m.key];
        const cls = !isNum(v) ? "na" : v < 0 ? "neg" : "";
        return `<td class="${cls}">${fmtCell(v, m.kind)}</td>`;
      }).join("")}</tr>`;
    }
    $(`#${tableId}`).innerHTML = html + "</tbody>";
    $(`#${countId}`).textContent = cols.length ? `${cols.length}개 기간 · ${cols[cols.length - 1].period} – ${cols[0].period}` : "";
  }

  function renderPeers() {
    const P = DATA.peers;
    const maxRev = Math.max(...P.map((p) => p.revenue || 0));
    const head = ["기업 (Company)", "티커 / 거래소", "국가", "GICS Sub-Industry", "Abbott과 경쟁·중첩 영역", "회계연도 말", "매출액", "매출 YoY", "영업이익률", "순이익률", "R&D / 매출", "FCF", "자산총계"];
    const leftCols = new Set([0, 1, 2, 3, 4]);
    let html = `<thead><tr>${head.map((h, i) => `<th class="${leftCols.has(i) ? "l" : ""}">${h}</th>`).join("")}</tr></thead><tbody>`;
    for (const p of P) {
      const fin = isNum(p.revenue);
      const na = fin ? "—" : `<span class="badge-ifrs">${p.sec_filer ? "데이터 없음" : "비SEC·IFRS"}</span>`;
      html += `<tr class="${p.is_self ? "self" : ""}">
        <td class="l"><span class="tk">${esc(p.name)}</span></td>
        <td class="l">${esc(p.ticker)}<span class="sub">${esc(p.exchange)}</span></td>
        <td class="l">${esc(p.country)}</td>
        <td class="l">${esc(p.gics_sub_industry)}</td>
        <td class="l wrap-cell">${esc(p.overlap)}</td>
        <td>${p.fy_end ? esc(p.fy_end.slice(0, 7)) : na}</td>
        <td>${fin ? `<span class="bar-cell"><i style="width:${Math.max(4, (p.revenue / maxRev) * 70)}px"></i>${fmtBn(p.revenue)}</span>` : na}</td>
        <td class="${isNum(p.revenue_yoy) && p.revenue_yoy < 0 ? "down" : ""}">${fin ? fmtPct(p.revenue_yoy, true) : na}</td>
        <td>${fin ? fmtPct(p.operating_margin) : na}</td>
        <td>${fin ? fmtPct(p.net_margin) : na}</td>
        <td>${fin ? fmtPct(p.rnd_ratio) : na}</td>
        <td>${fin ? fmtBn(p.fcf) : na}</td>
        <td>${fin ? fmtBn(p.total_assets) : na}</td></tr>`;
    }
    $("#t-peers").innerHTML = html + "</tbody>";
  }

  function renderFooter() {
    const m = DATA.meta;
    $("#foot").innerHTML = `
      데이터 출처: <a href="https://www.sec.gov/edgar/browse/?CIK=${esc(DATA.company.cik)}" target="_blank" rel="noopener">SEC EDGAR</a> XBRL companyfacts API · 마지막 갱신 ${esc(m.generated_at)} · 매월 1일·5일 GitHub Actions로 자동 업데이트<br>
      Q4·H2 수치는 연간 10-K 값에서 누적(YTD) 값을 차감해 산출했으며, 현금흐름 분기 수치도 YTD 차감 방식입니다. EPS의 차감 산출치는 근사치입니다.
      매출원가는 무형자산상각 제외 기준(Abbott 공시 기준). GICS 분류는 MSCI/S&amp;P 기준이며 SEC 데이터에는 포함되지 않아 수동 기재했습니다.<br>
      본 대시보드는 정보 제공 목적이며 투자 권유가 아닙니다. · <a href="https://github.com/jinawinwin/SEC_Abbott" target="_blank" rel="noopener">GitHub repository</a>`;
  }

  // ---------- downloads ----------
  function setupDock() {
    const pop = $("#xl-pop"), btn = $("#btn-xlsx");
    const years = [...new Set([...DATA.annual, ...DATA.half_year, ...DATA.quarterly].map((r) => r.fiscal_year))].sort();
    const opts = years.map((y) => `<option value="${y}">${y}</option>`).join("");
    $("#yr-from").innerHTML = opts;
    $("#yr-to").innerHTML = opts;
    $("#yr-from").value = years[0];
    $("#yr-to").value = years[years.length - 1];

    const toggle = (open) => { pop.hidden = !open; btn.setAttribute("aria-expanded", String(open)); };
    btn.addEventListener("click", (e) => { e.stopPropagation(); toggle(pop.hidden); });
    document.addEventListener("click", (e) => { if (!pop.hidden && !pop.contains(e.target)) toggle(false); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") toggle(false); });

    const sync = () => { $("#xl-go").disabled = !pop.querySelectorAll("input[name=ptype]:checked").length; };
    pop.querySelectorAll("input[name=ptype]").forEach((i) => i.addEventListener("change", sync));
    $("#xl-go").addEventListener("click", () => { downloadExcel(); toggle(false); });
    $("#btn-pdf").addEventListener("click", downloadPdf);
  }

  function downloadExcel() {
    if (!window.XLSX) { alert("엑셀 라이브러리를 불러오지 못했습니다. 네트워크를 확인해 주세요."); return; }
    const types = [...document.querySelectorAll("input[name=ptype]:checked")].map((i) => i.value);
    let y0 = +$("#yr-from").value, y1 = +$("#yr-to").value;
    if (y0 > y1) [y0, y1] = [y1, y0];
    const names = { annual: "Annual", half_year: "Half-year", quarterly: "Quarterly" };
    const wb = XLSX.utils.book_new();
    const c = DATA.company;
    const info = [
      ["Company", c.name], ["Ticker", `${c.exchange}: ${c.ticker}`], ["CIK", c.cik],
      ["GICS Sector", c.gics_sector], ["GICS Industry", c.gics_industry], ["GICS Sub-Industry", c.gics_sub_industry],
      ["Fiscal years", `${y0} – ${y1}`], ["Units", "USD millions (per-share in USD, shares in millions, ratios in %)"],
      ["Source", DATA.meta.source], ["Generated", DATA.meta.generated_at],
    ];
    const wsInfo = XLSX.utils.aoa_to_sheet(info);
    wsInfo["!cols"] = [{ wch: 18 }, { wch: 70 }];
    XLSX.utils.book_append_sheet(wb, wsInfo, "Info");

    for (const t of types) {
      const rows = DATA[t].filter((r) => r.fiscal_year >= y0 && r.fiscal_year <= y1);
      const metrics = DATA.metrics.filter((m) => rows.some((r) => isNum(r[m.key])));
      const header = ["Period", "Start", "End", ...metrics.map((m) => m.label)];
      const aoa = [header, ...rows.map((r) => [r.period, r.start, r.end, ...metrics.map((m) => {
        const v = r[m.key];
        if (!isNum(v)) return null;
        return m.kind === "usd" || m.kind === "shares" ? Math.round(v / 1e4) / 100 : v;
      })])];
      const ws = XLSX.utils.aoa_to_sheet(aoa);
      metrics.forEach((m, j) => {
        const fmt = { usd: "#,##0", shares: "#,##0", pct: "0.0%", x: "0.00\"x\"", per_share: "$0.00" }[m.kind];
        for (let i = 1; i <= rows.length; i++) {
          const cell = ws[XLSX.utils.encode_cell({ r: i, c: j + 3 })];
          if (cell && fmt) cell.z = fmt;
        }
      });
      ws["!cols"] = header.map((h, i) => ({ wch: i < 3 ? 12 : Math.min(28, Math.max(12, h.length + 2)) }));
      ws["!freeze"] = { xSplit: 1, ySplit: 1 };
      XLSX.utils.book_append_sheet(wb, ws, names[t]);
    }
    XLSX.writeFile(wb, `Abbott_ABT_financials_${types.map((t) => names[t].replace("-", "")).join("_")}_${y0}-${y1}.xlsx`);
  }

  async function downloadPdf() {
    if (!window.html2pdf) { window.print(); return; }
    const btn = $("#btn-pdf");
    btn.disabled = true;
    btn.querySelector("span").textContent = "생성중";
    document.body.classList.add("pdf-mode");
    charts.forEach((c) => { c.options.animation = false; c.resize(); });
    try {
      await html2pdf().set({
        margin: [6, 6, 6, 6],
        filename: `Abbott_ABT_dashboard_${new Date().toISOString().slice(0, 10)}.pdf`,
        image: { type: "jpeg", quality: 0.95 },
        html2canvas: { scale: 2, useCORS: true, backgroundColor: css("--bg") || "#ffffff", windowWidth: 1320 },
        jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
        pagebreak: { mode: ["css", "legacy"], avoid: [".kpi", ".chart-card", ".overview", ".table-head", "tr"] },
      }).from($("#report")).save();
    } finally {
      document.body.classList.remove("pdf-mode");
      charts.forEach((c) => c.resize());
      btn.disabled = false;
      btn.querySelector("span").textContent = "PDF";
    }
  }

  // ---------- boot ----------
  async function boot() {
    const res = await fetch("data/dashboard.json", { cache: "no-store" });
    DATA = await res.json();
    renderOverview();
    renderKpis();
    renderTable("t-annual", DATA.annual, "t-annual-count");
    renderTable("t-half", DATA.half_year, "t-half-count");
    renderTable("t-quarter", DATA.quarterly, "t-quarter-count");
    renderPeers();
    renderFooter();
    setupDock();
    if (window.Chart) {
      Chart.defaults.font.family = '"Inter", "Noto Sans KR", system-ui, sans-serif';
      renderCharts();
      window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", renderCharts);
    }
  }

  boot().catch((err) => {
    console.error(err);
    document.querySelector("main").insertAdjacentHTML("afterbegin", `<div class="card" style="padding:20px;margin-bottom:16px">데이터를 불러오지 못했습니다: ${esc(err.message)}</div>`);
  });
})();
