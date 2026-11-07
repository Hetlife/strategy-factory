"""Entry-day cost must reach the promotion statistics (Het-authorized, 2026-10-12).

Audit finding, verified in part: update() charged the entry-day cost to equity but
accumulated sum_ret / sum_sq / days_in_market only `if s["positions"]` -- i.e. only
on days a position was ALREADY held. On the day a position is first opened,
positions is still empty, so the cost reached equity but never the statistics that
report() feeds to promotion_check() as expectancy and Sharpe.

These tests run the REAL update() (not a replica of its accumulation rules) on a
temp copy of factory.py with a seeded synthetic panel and a monkeypatched
fetch_prices. No network; the real factory_state/ is never written.

The strategy is a controllable enter/hold/exit cycle, so the expected statistics can
be derived independently from the ledger's own recorded daily returns.
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

N_HISTORY, N_NEW, SEED = 300, 40, 20261012
CYCLE = 5            # in market on 3 of every 5 sessions -> 8 separate entries in 40 days
HELD_PHASES = (1, 2, 3)
NAME = "test_enter_exit_cycle"


class EntryDayCostInStats(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self.tmp = tempfile.mkdtemp(prefix="entry_cost_")
        os.chdir(self.tmp)
        os.makedirs("factory_state")
        self.f = _load_factory_copy(self.tmp)
        self.panel = make_panel(list(self.f.ALL_TICKERS), N_HISTORY, N_NEW, SEED,
                                benchmark=self.f.BENCHMARK)
        self.ticker = [t for t in self.panel.columns
                       if t not in self.f.MACRO_PROXIES and t != self.f.BENCHMARK][0]

        ticker = self.ticker

        def sig_cycle(px, p):
            return {ticker: 1.0} if (len(px) % CYCLE) in HELD_PHASES else {}

        self.f.IMPLS["test_cycle"] = sig_cycle
        st = self.f.load_state()
        st["registry"][NAME] = dict(fn="test_cycle")
        self.f.save_state(st)

        for k in range(1, N_NEW + 1):
            self.f.fetch_prices = lambda k=k: self.panel.iloc[:N_HISTORY + k].copy()
            with contextlib.redirect_stdout(io.StringIO()):
                self.f.update()
        led = json.load(open(os.path.join(self.tmp, "factory_state", "ledger.json")))
        self.s = led["contestants"][NAME]
        self.nets = [r[1] for r in self.s["history"]]

    def tearDown(self):
        os.chdir(self._cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_there_really_are_several_entries(self):
        """Guard the test itself: it only means something if the strategy entered
        many times, each entry day carrying a cost that equity sees."""
        entry_days = [n for n in self.nets if n < 0 and abs(n) < 0.01]
        self.assertGreaterEqual(self.s["trades"], 8)
        self.assertGreaterEqual(len(entry_days), 6, self.nets)

    def test_sum_ret_matches_every_booked_day(self):
        """sum_ret must equal the sum of ALL booked daily net returns. Days with no
        position at either end have net exactly 0, so the only way the totals can
        disagree is an exposed day -- the entry day -- being left out. Before the fix
        this was short by one entry cost (~0.11%) per entry, i.e. ~0.9% over 8
        entries, against a tolerance of 0.01% (history rows are rounded to 6dp)."""
        self.assertAlmostEqual(self.s["sum_ret"], sum(self.nets), delta=1e-4)

    def test_sum_sq_matches_every_booked_day(self):
        self.assertAlmostEqual(self.s["sum_sq"], sum(n * n for n in self.nets), delta=1e-6)

    def test_days_in_market_counts_exposed_days_including_entry(self):
        """Every active day -- held, entered or exited -- has a nonzero net on this
        random panel; idle days have exactly 0.0. days_in_market must count the former."""
        active = sum(1 for n in self.nets if n != 0.0)
        self.assertEqual(self.s["days_in_market"], active)

    def test_statistics_agree_with_equity(self):
        """The compounding of the booked series must reproduce equity, and the mean
        the gate sees must be the mean of that same series over its own days."""
        eq = 1.0
        for n in self.nets:
            eq *= (1 + n)
        self.assertAlmostEqual(self.s["equity"], eq, delta=1e-4)
        gate_mean = self.s["sum_ret"] / max(self.s["days_in_market"], 1)
        active = [n for n in self.nets if n != 0.0]
        self.assertAlmostEqual(gate_mean, sum(active) / len(active), delta=1e-6)

    def test_exit_day_still_counted_once(self):
        """Regression guard for the other edge: widening the condition must not
        double-count the exit day (positions non-empty, targets empty)."""
        active = sum(1 for n in self.nets if n != 0.0)
        self.assertLessEqual(self.s["days_in_market"], active)


if __name__ == "__main__":
    unittest.main()
