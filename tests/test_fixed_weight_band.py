"""CE-2-02b: band rebalancing for fn == "fixed_weight". No network.

Pure-helper tests (a)-(f) call factory.fixed_weight_next directly; the 40-cycle
test runs a shield_nse temp copy of factory.py on the seeded synthetic panel.
"""
import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
from synthetic_panel import make_panel  # noqa: E402
from test_shield_profile import load_copy, TARGET, N_HISTORY, N_CYCLES, SEED  # noqa: E402
import factory  # noqa: E402

CASH = "LIQUIDCASE.NS"
BAND = 0.05
FLAT = {t: 0.0 for t in TARGET}


def step(cur, rets, rebalance, cash=CASH, target=TARGET):
    return factory.fixed_weight_next(cur, pd.Series(rets), target, BAND, rebalance, cash=cash)[0]


def turnover(a, b):
    return sum(abs(a.get(t, 0) - b.get(t, 0)) for t in set(a) | set(b))


class Helper(unittest.TestCase):
    def test_a_first_day_enters_target(self):
        self.assertEqual(step({}, FLAT, False), TARGET)
        self.assertEqual(step({}, FLAT, True), TARGET)

    def test_b_small_drift_on_rebalance_day_no_trade(self):
        out = step(dict(TARGET), {**FLAT, "NIFTYBEES.NS": 0.05}, True)
        self.assertGreater(turnover(out, TARGET), 0)            # it drifted ...
        self.assertLess(max(abs(out[t] - TARGET[t]) for t in TARGET), BAND)  # ... under the band
        self.assertAlmostEqual(sum(out.values()), 1.0, places=12)
        self.assertGreater(out["NIFTYBEES.NS"], 0.20)
        self.assertNotEqual(out, TARGET)

    def test_c_big_drift_on_non_rebalance_day_no_trade(self):
        out = step(dict(TARGET), {**FLAT, "NIFTYBEES.NS": 0.60}, False)
        self.assertGreater(abs(out["NIFTYBEES.NS"] - 0.20), BAND)
        self.assertNotEqual(out, TARGET)
        self.assertAlmostEqual(sum(out.values()), 1.0, places=12)

    def test_d_big_drift_on_rebalance_day_goes_to_target(self):
        out = step(dict(TARGET), {**FLAT, "NIFTYBEES.NS": 0.60}, True)
        self.assertEqual(out, TARGET)
        # turnover as update() computes it, vs the drifted pre-trade weights
        drifted = step(dict(TARGET), {**FLAT, "NIFTYBEES.NS": 0.60}, False)
        self.assertGreater(turnover(out, drifted), 0.01)

    def test_e_never_two_rebalances_in_one_iso_week(self):
        rng = np.random.default_rng(7)
        days = pd.bdate_range("2026-01-05", periods=60)
        cur, per_week = {}, {}
        for d in days:
            rets = {t: float(rng.normal(0, 0.12)) for t in TARGET}   # huge drifts
            new = step(cur, rets, d.weekday() == 4)
            if cur and new == TARGET and turnover(new, cur) > 1e-9:
                # a rebalance is a jump to exactly TARGET from a non-target state
                per_week[d.isocalendar()[:2]] = per_week.get(d.isocalendar()[:2], 0) + 1
                self.assertEqual(d.weekday(), 4)
            cur = new
        self.assertGreater(len(per_week), 5)
        self.assertTrue(all(n == 1 for n in per_week.values()), per_week)

    def test_f_cash_ticker_missing_holds_and_warns(self):
        cur = {"LIQUIDCASE.NS": 0.45, "LTGILTBEES.NS": 0.15, "GOLDBEES.NS": 0.2, "NIFTYBEES.NS": 0.2}
        no_cash = {t: 1 / 3 for t in TARGET if t != CASH}
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            out = step(cur, {**FLAT, "NIFTYBEES.NS": 0.6}, True, target=no_cash)
        self.assertEqual(out, cur)
        self.assertIn("WARNING", buf.getvalue())
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(step({}, FLAT, True, target=no_cash), {})  # day 1: nothing entered


class FortyCycle(unittest.TestCase):
    def test_turnover_only_on_rebalance_days(self):
        cwd, tmp = os.getcwd(), tempfile.mkdtemp(prefix="fwband_")
        saved = {k: sys.modules.pop(k) for k in list(sys.modules)
                 if k == "agents" or k.startswith("agents.")}
        try:
            os.chdir(tmp)
            sys.modules["agents"] = None
            f = load_copy(tmp, "shield_nse")
            panel = make_panel(list(f.ALL_TICKERS), N_HISTORY, N_CYCLES, SEED,
                               {2: {"NIFTYBEES.NS": 0.60}, 12: {"GOLDBEES.NS": 0.60}},
                               benchmark=f.BENCHMARK)
            cur, turns = [N_HISTORY], []
            f.fetch_prices = lambda: panel.iloc[:cur[0]].copy()
            real_rtc = f.round_trip_cost

            def spy(turn, tickers_sold, effective_capital):
                turns.append(turn)          # one call per contestant per update
                return real_rtc(turn, tickers_sold, effective_capital)
            f.round_trip_cost = spy
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                for i in range(N_CYCLES):
                    cur[0] = N_HISTORY + i + 1
                    f.update()
                f.report()
            report_out = out.getvalue()
            print("\n----- shield_nse 40-cycle report() output -----\n" + report_out)
            self.assertEqual(len(turns), 2 * N_CYCLES)
            core = turns[0::2]              # registry order: shield_core first
            dates = panel.index[N_HISTORY:N_HISTORY + N_CYCLES]
            traded = [(d, t) for d, t in zip(dates, core) if t > 1e-9]
            self.assertAlmostEqual(core[0], 1.0, places=9)       # day-1 entry
            rebal = traded[1:]
            self.assertGreater(len(rebal), 0, "synthetic run never rebalanced")
            self.assertLess(len(rebal), len(dates) - 1)          # not every day
            for d, t in rebal:
                self.assertEqual(d.weekday(), 4, f"{d.date()} traded on a non-Friday")
            print("turnover > 0 on:", [(str(d.date()), round(t, 4)) for d, t in traded])
            con = f.load_state()["contestants"]["shield_core"]
            self.assertEqual(con["trades"], len([1 for _, t in traded if t > 0.01]))
            self.assertIn("shield_core", report_out)
        finally:
            os.chdir(cwd)
            sys.modules.pop("agents", None)
            sys.modules.update(saved)
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
