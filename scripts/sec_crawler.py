"""Download Abbott Laboratories (and SEC-filing peer) data from SEC EDGAR.

SEC fair-access policy requires a User-Agent that declares who is calling,
e.g. "Your Name your.email@example.com". Set it via the SEC_USER_AGENT
environment variable (a GitHub Actions secret in CI).
"""
import json
import os
import sys
import time
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


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    cik = CONFIG["company"]["cik"]

    facts = get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
    (RAW / "companyfacts.json").write_text(json.dumps(facts), encoding="utf-8")
    print(f"companyfacts: {len(facts['facts'].get('us-gaap', {}))} us-gaap concepts")

    subs = get_json(f"https://data.sec.gov/submissions/CIK{cik}.json")
    (RAW / "submissions.json").write_text(json.dumps(subs), encoding="utf-8")
    print(f"submissions: {subs['name']} {subs['tickers']}")

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
