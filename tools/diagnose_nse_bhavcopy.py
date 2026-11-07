"""
One-off diagnostic (CE-6-02): can a GitHub Actions runner fetch NSE's official
end-of-day cash-market bhavcopy (UDiFF format)?

NSE often blocks cloud IPs. If Actions can fetch the file, the data archive
needs no second writer; if not, a fetch from the Lucy-den host becomes an
option to discuss (docs/capital_engine/DATA_ARCHIVE.md).

For each of the last 5 weekdays before today (NSE holidays are NOT excluded --
a 404 on a holiday is expected and counts as neutral) it makes ONE request to
the documented archive URL pattern
  https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip
and prints: URL, HTTP status, content length, whether the zip opens, the CSV
header line, and the row count. The download is held in memory only; nothing is
written to disk or to the repo.

Politeness limits: browser-like User-Agent, 20 s timeout, at most 8 requests in
total, a timeout/network error is retried at most once per run (not per date).

Per-date outcome:
  OK         200, zip opens, CSV has >= 1 data row
  NOT_FOUND  404 (holiday or file not posted yet; neutral)
  BLOCKED    401/403/429, timeout, network error, 200 that is not a valid zip
             (e.g. an HTML challenge page), or any other HTTP status

VERDICT line (last line of output):
  REACHABLE  >= 1 OK and no BLOCKED
  MIXED      >= 1 OK and >= 1 BLOCKED
  BLOCKED    no OK at all (if every date was NOT_FOUND a note says the URL
             pattern or the date choice is suspect, not the network)

USAGE: python tools/diagnose_nse_bhavcopy.py [--today YYYY-MM-DD]
Read-only: prints, writes nothing. Exits 0 whatever the verdict (it is a
measurement); exits 2 only on bad arguments.
"""
import argparse
import csv
import datetime as dt
import io
import socket
import sys
import urllib.error
import urllib.request
import zipfile

URL_TEMPLATE = ("https://nsearchives.nseindia.com/content/cm/"
                "BhavCopy_NSE_CM_0_0_0_{ymd}_F_0000.csv.zip")
USER_AGENT = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TIMEOUT_S = 20
N_DATES = 5
MAX_REQUESTS = 8
MAX_RETRIES = 1  # total across the run, timeouts/network errors only
MAX_BODY_BYTES = 20 * 1024 * 1024

BLOCK_STATUSES = {401, 403, 429}


def build_url(d):
    """URL for the cash-market bhavcopy of date `d` (datetime.date)."""
    return URL_TEMPLATE.format(ymd=d.strftime("%Y%m%d"))


def last_weekdays(today, n=N_DATES):
    """The `n` weekdays (Mon-Fri) strictly before `today`, most recent first.
    Holidays are deliberately ignored."""
    out = []
    d = today
    while len(out) < n:
        d -= dt.timedelta(days=1)
        if d.weekday() < 5:
            out.append(d)
    return out


def fetch_one(url, timeout=TIMEOUT_S):
    """One GET. Returns (status, body, error). Never raises on HTTP/network
    problems. status is an int or None; error is a short string or None."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                               "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(MAX_BODY_BYTES), None
    except urllib.error.HTTPError as e:
        return e.code, None, None
    except (socket.timeout, TimeoutError):
        return None, None, "timeout"
    except urllib.error.URLError as e:
        if isinstance(e.reason, (socket.timeout, TimeoutError)):
            return None, None, "timeout"
        return None, None, f"network: {e.reason}"
    except Exception as e:  # keep the diagnostic alive; report what happened
        return None, None, f"error: {type(e).__name__}"


def inspect_zip(body):
    """Open a zip held in memory. Returns (ok, header_line, rows, err)."""
    try:
        with zipfile.ZipFile(io.BytesIO(body)) as zf:
            names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if not names:
                return False, "", 0, "zip has no .csv member"
            with zf.open(names[0]) as fh:
                text = io.TextIOWrapper(fh, encoding="utf-8", errors="replace",
                                        newline="")
                header = text.readline().rstrip("\r\n")
                rows = sum(1 for r in csv.reader(text) if r)
            return True, header, rows, None
    except zipfile.BadZipFile:
        return False, "", 0, "not a valid zip"
    except Exception as e:
        return False, "", 0, f"zip error: {type(e).__name__}"


def make_result(date, url, status, body, error):
    """Classify one fetch into a result dict (pure; fake inputs are fine)."""
    res = {"date": date, "url": url, "status": status, "error": error,
           "length": len(body) if body is not None else None,
           "zip_opens": None, "header": "", "rows": None, "note": ""}
    if error is not None:
        res["outcome"] = "BLOCKED"
        res["note"] = error
    elif status == 200:
        ok, header, rows, err = inspect_zip(body or b"")
        res["zip_opens"] = ok
        if ok and rows >= 1:
            res.update(outcome="OK", header=header, rows=rows)
        elif ok:
            res.update(outcome="BLOCKED", header=header, rows=rows,
                       note="zip opens but CSV has no data rows")
        else:
            res.update(outcome="BLOCKED", note=f"200 but {err}")
    elif status == 404:
        res["outcome"] = "NOT_FOUND"
        res["note"] = "holiday or not posted yet"
    elif status in BLOCK_STATUSES:
        res["outcome"] = "BLOCKED"
        res["note"] = f"HTTP {status}"
    else:
        res["outcome"] = "BLOCKED"
        res["note"] = f"unexpected HTTP status {status}"
    return res


def compute_verdict(results):
    ok = sum(1 for r in results if r["outcome"] == "OK")
    blocked = sum(1 for r in results if r["outcome"] == "BLOCKED")
    if ok and not blocked:
        return "REACHABLE"
    if ok:
        return "MIXED"
    return "BLOCKED"


def format_report(results):
    """Human-readable summary table + detail lines + final VERDICT line."""
    lines = []
    lines.append(f"{'date':<11} {'status':<7} {'length':>9} {'zip':<5} "
                 f"{'rows':>6}  outcome    note")
    for r in results:
        status = "-" if r["status"] is None else str(r["status"])
        length = "-" if r["length"] is None else str(r["length"])
        zp = "-" if r["zip_opens"] is None else ("yes" if r["zip_opens"] else "no")
        rows = "-" if r["rows"] is None else str(r["rows"])
        lines.append(f"{r['date']!s:<11} {status:<7} {length:>9} {zp:<5} "
                     f"{rows:>6}  {r['outcome']:<10} {r['note']}")
    lines.append("")
    for r in results:
        lines.append(f"URL {r['date']}: {r['url']}")
        if r["header"]:
            lines.append(f"  CSV header: {r['header']}")
    lines.append("")
    counts = {k: sum(1 for r in results if r["outcome"] == k)
              for k in ("OK", "NOT_FOUND", "BLOCKED")}
    lines.append("counts: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    if results and counts["NOT_FOUND"] == len(results):
        lines.append("note: every date was 404 -- suspect the URL pattern or the "
                     "date choice, not a network block.")
    lines.append(f"VERDICT: {compute_verdict(results)}")
    return "\n".join(lines)


def run(today, fetch=fetch_one):
    """Fetch the last N weekdays (injectable `fetch` for tests). Hard cap of
    MAX_REQUESTS requests; at most MAX_RETRIES retries, timeouts/network only."""
    results = []
    requests_made = 0
    retries_left = MAX_RETRIES
    for d in last_weekdays(today):
        url = build_url(d)
        if requests_made >= MAX_REQUESTS:
            break
        status, body, error = fetch(url)
        requests_made += 1
        if error is not None and retries_left > 0 and requests_made < MAX_REQUESTS:
            retries_left -= 1
            status, body, error = fetch(url)
            requests_made += 1
        results.append(make_result(d, url, status, body, error))
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--today", help="override today's date (YYYY-MM-DD)")
    args = ap.parse_args(argv)
    try:
        today = (dt.date.fromisoformat(args.today) if args.today
                 else dt.datetime.now(dt.timezone.utc).date())
    except ValueError:
        print("bad --today value, expected YYYY-MM-DD")
        return 2
    results = run(today)
    print(format_report(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
