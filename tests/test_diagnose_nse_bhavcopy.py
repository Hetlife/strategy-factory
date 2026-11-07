"""CE-6-02: URL builder, weekday selection, result formatter. No network."""
import datetime as dt
import io
import os
import sys
import unittest
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import diagnose_nse_bhavcopy as d  # noqa: E402


def make_zip(rows=3, name="bhav.csv", header="TradDt,TckrSymb,ClsPric"):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        body = header + "\n" + "".join(f"2026-10-06,SYM{i},{100+i}\n"
                                       for i in range(rows))
        zf.writestr(name, body)
    return buf.getvalue()


D = dt.date(2026, 10, 6)
U = d.build_url(D)


class TestUrl(unittest.TestCase):
    def test_exact_url(self):
        self.assertEqual(
            d.build_url(dt.date(2026, 10, 6)),
            "https://nsearchives.nseindia.com/content/cm/"
            "BhavCopy_NSE_CM_0_0_0_20261006_F_0000.csv.zip")

    def test_zero_padding(self):
        self.assertIn("20260105", d.build_url(dt.date(2026, 1, 5)))


class TestWeekdays(unittest.TestCase):
    def test_midweek(self):  # Wed 2026-11-04 -> Tue, Mon, Fri, Thu, Wed
        got = d.last_weekdays(dt.date(2026, 11, 4))
        self.assertEqual(got, [dt.date(2026, 11, 3), dt.date(2026, 11, 2),
                               dt.date(2026, 10, 30), dt.date(2026, 10, 29),
                               dt.date(2026, 10, 28)])

    def test_saturday_today(self):  # Sat 2026-11-07
        got = d.last_weekdays(dt.date(2026, 11, 7))
        self.assertEqual(got[0], dt.date(2026, 11, 6))
        self.assertEqual(len(got), 5)

    def test_no_weekends_and_today_excluded(self):
        for day in range(1, 29):
            today = dt.date(2026, 10, day)
            got = d.last_weekdays(today)
            self.assertTrue(all(x.weekday() < 5 and x < today for x in got))
            self.assertEqual(len(set(got)), 5)


class TestMakeResult(unittest.TestCase):
    def test_200_ok(self):
        r = d.make_result(D, U, 200, make_zip(3), None)
        self.assertEqual(r["outcome"], "OK")
        self.assertTrue(r["zip_opens"])
        self.assertEqual(r["rows"], 3)
        self.assertEqual(r["header"], "TradDt,TckrSymb,ClsPric")
        self.assertGreater(r["length"], 0)

    def test_403(self):
        r = d.make_result(D, U, 403, None, None)
        self.assertEqual(r["outcome"], "BLOCKED")
        self.assertIn("403", r["note"])

    def test_404_neutral(self):
        self.assertEqual(d.make_result(D, U, 404, None, None)["outcome"],
                         "NOT_FOUND")

    def test_timeout(self):
        r = d.make_result(D, U, None, None, "timeout")
        self.assertEqual(r["outcome"], "BLOCKED")
        self.assertEqual(r["note"], "timeout")

    def test_200_but_html_not_zip(self):
        r = d.make_result(D, U, 200, b"<html>Access Denied</html>", None)
        self.assertEqual(r["outcome"], "BLOCKED")
        self.assertFalse(r["zip_opens"])

    def test_200_zip_without_csv(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("readme.txt", "x")
        r = d.make_result(D, U, 200, buf.getvalue(), None)
        self.assertEqual(r["outcome"], "BLOCKED")

    def test_200_header_only_csv(self):
        r = d.make_result(D, U, 200, make_zip(0), None)
        self.assertEqual(r["outcome"], "BLOCKED")

    def test_500_unexpected(self):
        self.assertEqual(d.make_result(D, U, 500, None, None)["outcome"],
                         "BLOCKED")


def res(outcome):
    return {"outcome": outcome}


class TestVerdict(unittest.TestCase):
    def test_reachable(self):
        self.assertEqual(d.compute_verdict([res("OK"), res("NOT_FOUND")]),
                         "REACHABLE")

    def test_mixed(self):
        self.assertEqual(d.compute_verdict([res("OK"), res("BLOCKED")]), "MIXED")

    def test_blocked(self):
        self.assertEqual(d.compute_verdict([res("BLOCKED")] * 5), "BLOCKED")

    def test_all_404_is_blocked_with_note(self):
        rs = [d.make_result(D, U, 404, None, None) for _ in range(5)]
        self.assertEqual(d.compute_verdict(rs), "BLOCKED")
        self.assertIn("suspect the URL pattern", d.format_report(rs))


class TestFormatter(unittest.TestCase):
    def test_mixed_report(self):
        rs = [d.make_result(D, U, 200, make_zip(2), None),
              d.make_result(D, U, 403, None, None),
              d.make_result(D, U, 404, None, None),
              d.make_result(D, U, None, None, "timeout")]
        out = d.format_report(rs)
        self.assertIn("OK", out)
        self.assertIn("NOT_FOUND", out)
        self.assertIn("timeout", out)
        self.assertIn(U, out)
        self.assertIn("CSV header: TradDt,TckrSymb,ClsPric", out)
        self.assertEqual(out.splitlines()[-1], "VERDICT: MIXED")


class TestRun(unittest.TestCase):
    def test_five_requests_no_network(self):
        calls = []

        def fake(url):
            calls.append(url)
            return 200, make_zip(1), None
        rs = d.run(dt.date(2026, 11, 4), fetch=fake)
        self.assertEqual(len(calls), 5)
        self.assertEqual(len(set(calls)), 5)
        self.assertEqual(d.compute_verdict(rs), "REACHABLE")

    def test_retry_at_most_once_per_run(self):
        calls = []

        def fake(url):
            calls.append(url)
            return None, None, "timeout"
        rs = d.run(dt.date(2026, 11, 4), fetch=fake)
        self.assertEqual(len(calls), 6)  # 5 dates + exactly 1 retry
        self.assertLessEqual(len(calls), d.MAX_REQUESTS)
        self.assertEqual(d.compute_verdict(rs), "BLOCKED")

    def test_http_errors_not_retried(self):
        calls = []

        def fake(url):
            calls.append(url)
            return 403, None, None
        d.run(dt.date(2026, 11, 4), fetch=fake)
        self.assertEqual(len(calls), 5)


if __name__ == "__main__":
    unittest.main()


class HonestUserAgent(unittest.TestCase):
    def test_user_agent_is_not_a_browser_and_has_no_contact_details(self):
        import tools.diagnose_nse_bhavcopy as m
        ua = m.USER_AGENT
        self.assertNotIn("Mozilla", ua)
        self.assertNotIn("Chrome", ua)
        self.assertNotIn("@", ua)
        self.assertIn("strategy-factory", ua)
