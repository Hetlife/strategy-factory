"""CE-1-04: profile-aware health_check -- stale ledger, duplicate dates,
disabled-profile handling, and the default profile's real-repo behaviour.

No network. Synthetic ledgers live in a temp root laid out like the repo
(factory_state/<profile>/ledger.json) with a temp profiles/ directory.
"""
import contextlib
import datetime
import io
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tools import health_check as hc  # noqa: E402

# Wed 2026-10-07 (a weekday) and Sun 2026-10-04 (a weekend day)
WED = datetime.date(2026, 10, 7)
SUN = datetime.date(2026, 10, 4)


def ledger(dates, name="c1"):
    return {"registry": {name: {}},
            "contestants": {name: {"history": [[d, 0.0, 1.0] for d in dates]}}}


class HealthCheckProfileTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name
        self.pdir = os.path.join(self.root, "profiles")
        os.makedirs(self.pdir)
        self.profile("crypto_paper", enabled=True, weekends=True)
        self.profile("fx_paper", enabled=True, weekends=False)
        self.profile("dormant", enabled=False, weekends=False)

    def profile(self, name, enabled, weekends):
        with open(os.path.join(self.pdir, name + ".json"), "w") as fh:
            json.dump({"enabled": enabled, "trades_weekends": weekends,
                       "MACRO_PROXIES": []}, fh)

    def write_ledger(self, profile, data):
        d = os.path.join(self.root, "factory_state", profile)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "ledger.json"), "w") as fh:
            json.dump(data, fh)

    def stale(self, profile, today, data=None):
        return hc.check_stale_ledger(profile, ledger_data=data, today=today,
                                     profiles_dir=self.pdir, root=self.root)

    # -- duplicate dates ---------------------------------------------------
    def test_duplicate_date_in_non_default_profile_is_warning(self):
        res = hc.check_duplicate_dates(
            "crypto_paper", ledger_data=ledger(["2026-10-01", "2026-10-02", "2026-10-02"]))
        self.assertEqual([lvl for lvl, _ in res], ["warning"])
        self.assertIn("1 duplicate", res[0][1])

    def test_duplicate_date_in_equity_is_info_with_count(self):
        res = hc.check_duplicate_dates(
            "equity_nse", ledger_data=ledger(["2026-10-01", "2026-10-01", "2026-10-01"]))
        self.assertEqual([lvl for lvl, _ in res], ["info"])
        self.assertIn("2 duplicate", res[0][1])

    # -- stale ledger ------------------------------------------------------
    def test_stale_weekday_ledger_is_warning(self):
        # Wed 10-07, last row Fri 10-02 is 5 days behind -> stale
        res = self.stale("fx_paper", WED, ledger(["2026-10-02"]))
        self.assertEqual([lvl for lvl, _ in res], ["warning"])

    def test_weekday_ledger_over_a_weekend_is_fine(self):
        # Sunday: reference weekday is Fri 10-02; last row Fri -> 0 days
        self.assertEqual(self.stale("fx_paper", SUN, ledger(["2026-10-02"])), [])
        # Tue 10-06 after a Fri row: 4 days, still inside the limit
        self.assertEqual(self.stale("fx_paper", datetime.date(2026, 10, 6),
                                    ledger(["2026-10-02"])), [])

    def test_stale_weekend_profile_is_warning(self):
        res = self.stale("crypto_paper", SUN, ledger(["2026-10-01"]))   # 3 days
        self.assertEqual([lvl for lvl, _ in res], ["warning"])
        self.assertEqual(self.stale("crypto_paper", SUN, ledger(["2026-10-02"])), [])

    # -- clean ledger --------------------------------------------------------
    def test_clean_synthetic_ledger_has_no_findings(self):
        data = ledger(["2026-10-01", "2026-10-02", "2026-10-03"])
        self.assertEqual(self.stale("crypto_paper", SUN, data), [])
        self.assertEqual(hc.check_duplicate_dates("crypto_paper", ledger_data=data), [])
        self.write_ledger("crypto_paper", data)
        res = hc.run_all(profile="crypto_paper", profiles_dir=self.pdir,
                         root=self.root, today=SUN)
        # only the documented registry-drift-skipped note may appear
        self.assertEqual([lvl for lvl, _ in res if lvl != "info"], [])

    # -- missing ledger ----------------------------------------------------
    def test_missing_ledger_disabled_is_info_only(self):
        res = hc.run_all(profile="dormant", profiles_dir=self.pdir, root=self.root)
        self.assertEqual([lvl for lvl, _ in res], ["info"])

    def test_missing_ledger_enabled_is_warning(self):
        res = hc.run_all(profile="fx_paper", profiles_dir=self.pdir, root=self.root)
        self.assertEqual([lvl for lvl, _ in res], ["warning"])

    def test_run_all_flags_duplicates_and_staleness_together(self):
        self.write_ledger("fx_paper", ledger(["2026-09-01", "2026-09-01"]))
        res = hc.run_all(profile="fx_paper", profiles_dir=self.pdir,
                         root=self.root, today=WED)
        self.assertEqual(sorted({lvl for lvl, _ in res} - {"info"}), ["warning"])
        self.assertEqual(sum(1 for lvl, _ in res if lvl == "warning"), 2)

    # -- CLI / default profile ---------------------------------------------
    def run_main(self, argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = hc.main(argv)
        return rc, out.getvalue()

    def test_default_profile_output_on_real_repo(self):
        # pin "today" to the real ledger's own last date so this test does not
        # start failing merely because a branch checkout's ledger ages
        with open(os.path.join(ROOT, "factory_state", "ledger.json")) as fh:
            last = hc._ledger_last_update_date(json.load(fh))
        pinned = datetime.date(*map(int, last.split("-")))
        orig = hc._utc_today
        hc._utc_today = lambda: pinned
        self.addCleanup(setattr, hc, "_utc_today", orig)
        rc0, out0 = self.run_main([])
        rc1, out1 = self.run_main(["--profile", "equity_nse"])
        self.assertEqual((rc0, out0), (rc1, out1))      # flag changes nothing
        self.assertEqual(rc0, 0)
        self.assertNotIn("[WARNING]", out0)
        self.assertNotIn("[ERROR]", out0)
        self.assertIn("phantom day(s)", out0)           # the existing info line

    def test_unknown_profile_exits_2(self):
        rc, out = self.run_main(["--profile", "no_such_profile"])
        self.assertEqual(rc, 2)
        self.assertIn("unknown profile", out)


if __name__ == "__main__":
    unittest.main()
