"""CE-0-04: phantom-day guard in factory.update().

Runs on a temp copy of factory.py with a seeded synthetic panel and a
monkeypatched fetch_prices -- no network, and the real factory_state/ is
never written. A phantom row mimics what fetch_prices() produces on an NSE
holiday: every NSE ticker NaN -> .ffill() -> exactly unchanged, while Brent
(a MACRO_PROXY) still moves.
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from synthetic_panel import make_panel  # noqa: E402
from test_golden_master import _load_factory_copy  # noqa: E402

N_HISTORY, N_NEW, SEED = 300, 8, 20261004


class PhantomGuard(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self.tmp = tempfile.mkdtemp(prefix="phantom_guard_")
        os.chdir(self.tmp)
        os.makedirs("factory_state")
        self.f = _load_factory_copy(self.tmp)
        self.panel = make_panel(list(self.f.ALL_TICKERS), N_HISTORY, N_NEW, SEED,
                                benchmark=self.f.BENCHMARK)
        self.macro = list(self.f.MACRO_PROXIES)
        self.nse = [t for t in self.panel.columns if t not in self.macro]

    def tearDown(self):
        os.chdir(self._cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_update(self, panel):
        self.f.fetch_prices = lambda: panel.copy()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.f.update()
        return out.getvalue()

    def recorded_dates(self):
        led = json.load(open(os.path.join(self.tmp, "factory_state", "ledger.json")))
        return [r[0] for s in led["contestants"].values() for r in s["history"]]

    def market_log_dates(self):
        return sorted(json.load(open(self.f.MARKET_LOG_PATH)))

    def stale_row(self, panel, i):
        """Row i as fetch_prices() yields it on a holiday / not-yet-posted day:
        NSE tickers NaN then ffilled, Brent still moving."""
        p = panel.copy()
        p.iloc[i, [p.columns.get_loc(t) for t in self.nse]] = float("nan")
        return p.ffill()

    def test_holiday_row_is_not_recorded_and_next_real_day_is(self):
        h = N_HISTORY + 3                       # 4th new row becomes the holiday
        full = self.stale_row(self.panel.iloc[:N_HISTORY + 6], h)
        hday = str(full.index[h].date())
        for n in (1, 2, 3):
            self.run_update(full.iloc[:N_HISTORY + n])
        out = self.run_update(full.iloc[:h + 1])    # panel now ends on the holiday
        self.assertIn("PHANTOM SKIPPED: " + hday, out)
        self.assertIn("treating as no new session", out)
        self.assertNotIn(hday, self.recorded_dates())
        self.assertNotIn(hday, self.market_log_dates())
        self.assertEqual(len(set(self.recorded_dates())), 3)
        out = self.run_update(full.iloc[:h + 2])    # next real session arrives
        nday = str(full.index[h + 1].date())
        self.assertNotIn("PHANTOM", out)
        self.assertIn(nday, self.recorded_dates())
        self.assertNotIn(hday, self.recorded_dates())
        # return into the selected row is the real one-step return, not 0
        entry = json.load(open(self.f.MARKET_LOG_PATH))[nday]
        t = self.nse[0]
        self.assertAlmostEqual(entry[t]["ret"],
                               round(full[t].iloc[h + 1] / full[t].iloc[h] - 1, 6), places=6)

    def test_late_data_row_recorded_exactly_once_on_next_cycle(self):
        d = N_HISTORY + 2                       # row D: stale at cycle k
        stale = self.stale_row(self.panel.iloc[:d + 1], d)
        dday = str(self.panel.index[d].date())
        self.run_update(self.panel.iloc[:N_HISTORY + 1])
        self.run_update(self.panel.iloc[:N_HISTORY + 2])
        out = self.run_update(stale)                # cycle k: D phantom
        self.assertIn("PHANTOM SKIPPED: " + dday, out)
        self.assertNotIn(dday, self.recorded_dates())
        self.run_update(self.panel.iloc[:d + 1])    # cycle k+1: D now populated
        self.assertEqual(self.recorded_dates().count(dday),
                         len(json.load(open(os.path.join(
                             self.tmp, "factory_state", "ledger.json")))["contestants"]))
        self.assertEqual(self.market_log_dates().count(dday), 1)
        out = self.run_update(self.panel.iloc[:d + 1])  # replay: idempotence still holds
        self.assertIn("Arena update SKIPPED", out)

    def test_no_real_row_writes_nothing(self):
        flat = self.panel.iloc[:5].copy()
        for t in self.nse:
            flat[t] = 100.0
        out = self.run_update(flat)
        self.assertIn("no real", out)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "factory_state", "ledger.json")))
        self.assertFalse(os.path.exists(self.f.MARKET_LOG_PATH))


if __name__ == "__main__":
    unittest.main()
