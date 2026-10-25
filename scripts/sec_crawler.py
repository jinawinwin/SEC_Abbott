"""Download Abbott Laboratories (and SEC-filing peer) data from SEC EDGAR.

SEC fair-access policy requires a User-Agent that declares who is calling,
e.g. "Your Name your.email@example.com". Set it via the SEC_USER_AGENT
environment variable (a GitHub Actions secret in CI).
"""
import json
import os
import shutil
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CONFIG = json.loads((ROOT / "config" / "company.json").read_text(encoding="utf-8"))

USER_AGENT = os.environ.get("SEC_USER_AGENT") or "SEC_Abbott-dashboard jinawinwin@users.noreply.github.com"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"})


def get_json(url):
    for attempt in range(4):
        resp = SESSION.get(url, timeout=60)
        if resp.status_code == 200:
            time.sleep(0.15)  # stay well under SEC's 10 requests/second limit
            return resp.json()
        if resp.status_code in (429, 500, 502, 503):
            time.sleep(2 ** attempt)
            continue
        raise RuntimeError(f"{url} -> HTTP {resp.status_code}")
    raise RuntimeError(f"{url} -> gave up after retries")


UNIT_NAMES = {"USD": "USD", "shares": "shares", "USD/shares": "USD/shares"}  # by measure local name


def parse_instance(xml_bytes, filed, form):
    """Parse a filing's XBRL instance into the companyfacts shape (us-gaap, no dimensions)."""
    root = ET.fromstring(xml_bytes)
    ns_x, ns_gaap = "{http://www.xbrl.org/2003/instance}", None
    for el in root.iter():
        if el.tag.startswith("{http://fasb.org/us-gaap/"):
            ns_gaap = el.tag.split("}")[0] + "}"
            break
    contexts = {}
    for ctx in root.iter(f"{ns_x}context"):
        if ctx.find(f"{ns_x}entity/{ns_x}segment") is not None or ctx.find(f"{ns_x}scenario") is not None:
            continue
        p = ctx.find(f"{ns_x}period")
        inst, start, end = p.find(f"{ns_x}instant"), p.find(f"{ns_x}startDate"), p.find(f"{ns_x}endDate")
        contexts[ctx.get("id")] = {"end": inst.text.strip()} if inst is not None else {"start": start.text.strip(), "end": end.text.strip()}
    units = {}
    for u in root.iter(f"{ns_x}unit"):
        measures = [m.text.strip().split(":")[-1] for m in u.iter(f"{ns_x}measure")]
        units[u.get("id")] = "/".join(measures)
    out = {}
    if not ns_gaap:
        return out
    for el in root:
        if not el.tag.startswith(ns_gaap) or el.get("contextRef") not in contexts or not (el.text or "").strip():
            continue
        unit = UNIT_NAMES.get(units.get(el.get("unitRef"), ""))
        if not unit:
            continue
        try:
            val = float(el.text)
        except ValueError:
            continue
        fact = dict(contexts[el.get("contextRef")], val=int(val) if val.is_integer() and unit != "USD/shares" else val, filed=filed, form=form)
        out.setdefault(el.tag[len(ns_gaap):], {"units": {}})["units"].setdefault(unit, []).append(fact)
    return out


def fetch_recent_filings(facts, subs, limit=4):
    """companyfacts can lag behind EDGAR; read newer 10-K/10-Q filings straight from their XBRL instance."""
    out_dir = RAW / "filings"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    covered = max((f["end"] for c in facts["facts"].get("us-gaap", {}).values() for u in c["units"].values()
                   for f in u if f.get("form") in ("10-K", "10-Q")), default="")
    recent = subs["filings"]["recent"]
    cik = int(subs["cik"])
    todo = [i for i in range(len(recent["form"]))
            if recent["form"][i] in ("10-K", "10-Q") and recent["reportDate"][i] > covered][:limit]
    for i in todo:
        acc = recent["accessionNumber"][i]
        base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}"
        try:
            items = get_json(f"{base}/index.json")["directory"]["item"]
            name = next(x["name"] for x in items if x["name"].endswith("_htm.xml"))
            resp = SESSION.get(f"{base}/{name}", timeout=60)
            resp.raise_for_status()
        except (RuntimeError, StopIteration, requests.RequestException) as exc:
            print(f"filing {acc}: skipped ({exc})", file=sys.stderr)
            continue
        parsed = parse_instance(resp.content, recent["filingDate"][i], recent["form"][i])
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{acc}.json").write_text(json.dumps(parsed), encoding="utf-8")
        print(f"filing {acc} ({recent['form'][i]} {recent['reportDate'][i]}): {len(parsed)} concepts from XBRL instance")


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    cik = CONFIG["company"]["cik"]

    facts = get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
    (RAW / "companyfacts.json").write_text(json.dumps(facts), encoding="utf-8")
    print(f"companyfacts: {len(facts['facts'].get('us-gaap', {}))} us-gaap concepts")

    subs = get_json(f"https://data.sec.gov/submissions/CIK{cik}.json")
    (RAW / "submissions.json").write_text(json.dumps(subs), encoding="utf-8")
    print(f"submissions: {subs['name']} {subs['tickers']}")

    fetch_recent_filings(facts, subs)

    # Peers: keep only the us-gaap concepts the analysis needs, to keep the repo small.
    from analyze import PEER_CONCEPTS  # noqa: E402  (shared concept list)

    peer_dir = RAW / "peers"
    peer_dir.mkdir(exist_ok=True)
    for peer in CONFIG["peers"]:
        if not peer.get("sec_cik"):
            continue
        try:
            pf = get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{peer['sec_cik']}.json")
        except RuntimeError as exc:
            print(f"peer {peer['ticker']}: {exc}", file=sys.stderr)
            continue
        gaap = pf["facts"].get("us-gaap", {})
        slim = {"entityName": pf.get("entityName"), "facts": {k: gaap[k] for k in PEER_CONCEPTS if k in gaap}}
        (peer_dir / f"{peer['ticker']}.json").write_text(json.dumps(slim), encoding="utf-8")
        print(f"peer {peer['ticker']}: {len(slim['facts'])} concepts")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
