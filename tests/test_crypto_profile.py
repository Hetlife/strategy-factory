"""CE-3-03: class B profile `crypto` + sig_trend_long_flat / sig_cash / VDA tax.

No network (fetch_prices is monkeypatched with a seeded, WEEKEND-INCLUSIVE
synthetic panel) and everything runs from a temp copy of factory.py +
profiles/ in a temp cwd, so the real factory_state/ is never written.
"""
import contextlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from profiles import load_profile  # noqa: E402
from tools import health_check  # noqa: E402

FROZEN = ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "LTC-USD",
          "LINK-USD", "XRP-USD", "AVAX-USD", "DOT-USD", "ADA-USD"]
N_HISTORY, N_CYCLES, SEED = 300, 60, 20261004
REG_NAMES = ({f"crypto_trend_{r}_{n}" for r in ("donchian", "sma") for n in (50, 100, 200)}
             | {"crypto_btc_benchmark", "crypto_cash_baseline"})


def load_copy(tmp, profile):
    shutil.copy(os.path.join(ROOT, "factory.py"), tmp)
    shutil.copytree(os.path.join(ROOT, "profiles"), os.path.join(tmp, "profiles"),
                    ignore=shutil.ignore_patterns("__pycache__"), dirs_exist_ok=True)
    saved = os.environ.pop("FACTORY_PROFILE", None)
    if profile:
        os.environ["FACTORY_PROFILE"] = profile
    try:
        spec = importlib.util.spec_from_file_location(
            "factory_cryptocopy_" + (profile or "default"),
            os.path.join(tmp, "factory.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        os.environ.pop("FACTORY_PROFILE", None)
        if saved is not None:
            os.environ["FACTORY_PROFILE"] = saved
    state = os.path.join(tmp, "factory_state")
    mod.STATE_DIR = state
    mod.PARAM_BANK_PATH = os.path.join(state, "parameter_bank.json")
    mod.ADVISOR_STATE_PATH = os.path.join(state, "advisor_state.json")
    mod.MARKET_LOG_PATH = os.path.join(state, "market_log.json")
    return mod


def crypto_panel(tickers, n_rows, seed=SEED, start="2026-01-01"):
    """Daily (7 days/week) random-walk panel with regime-switching drift so the
    trend rules actually flip. Every return is non-zero (no phantom days)."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start=start, periods=n_rows, freq="D")
    cols = {}
    for j, t in enumerate(sorted(tickers)):
        phase = rng.integers(0, 60)
        mu = np.where(((np.arange(n_rows) + phase) // 50) % 2 == 0, 0.004, -0.004)
        r = rng.normal(mu, 0.02)
        cols[t] = np.round(100.0 * (1 + j) * np.cumprod(1.0 + r), 4)
    return pd.DataFrame(cols, index=idx)


def three_coin_panel(kind, n=260, hi_vol_alt=False):
    """BTC-USD (low vol), A-USD, B-USD. kind in up / flat / down for A and B."""
    rng = np.random.default_rng(7)
    idx = pd.date_range("2026-01-01", periods=n, freq="D")
    drift = {"up": 0.004, "flat": 0.0, "down": -0.004}[kind]
    vol_a = 0.05 if hi_vol_alt else 0.01
    btc = 100 * np.cumprod(1 + rng.normal(drift, 0.01, n))
    a = 100 * np.cumprod(1 + rng.normal(drift, vol_a, n))
    b = 100 * np.cumprod(1 + rng.normal(drift, 0.01, n))
    return pd.DataFrame({"BTC-USD": btc, "A-USD": a, "B-USD": b}, index=idx)


class CryptoProfile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._cwd = os.getcwd()
        cls._tmp = tempfile.mkdtemp(prefix="crypto_test_")
        os.chdir(cls._tmp)
        cls._saved_agents = {k: sys.modules.pop(k) for k in list(sys.modules)
                             if k == "agents" or k.startswith("agents.")}
        sys.modules["agents"] = None     # keep report() inside the temp dir
        cls.f = f = load_copy(cls._tmp, "crypto")
        cls.panel = crypto_panel(f.ALL_TICKERS, N_HISTORY + N_CYCLES)
        cls.cursor = N_HISTORY
        f.fetch_prices = lambda: cls.panel.iloc[:cls.cursor].copy()
        cls.seeded = f.load_state()
        cls.prev_pos = {}
        cls.changes = []          # (date, weekday, contestant) where positions changed
        cls.update_out = io.StringIO()
        ledger_path = os.path.join(cls._tmp, "factory_state", "ledger.json")
        with contextlib.redirect_stdout(cls.update_out):
            for i in range(N_CYCLES):
                cls.cursor = N_HISTORY + i + 1
                f.update()
                led = json.load(open(ledger_path))
                day = cls.panel.index[cls.cursor - 1]
                for name, s in led["contestants"].items():
                    if s["positions"] != cls.prev_pos.get(name, {}):
                        cls.changes.append((str(day.date()), day.weekday(), name))
                    cls.prev_pos[name] = s["positions"]
        cls.pre_report = json.load(open(ledger_path))   # report() may reset a DEMOTEd paper entry
        cls.report_out = io.StringIO()
        with contextlib.redirect_stdout(cls.report_out):
            f.report()
        cls.ledger = json.load(open(ledger_path))

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls._cwd)
        sys.modules.pop("agents", None)
        sys.modules.update(cls._saved_agents)
        shutil.rmtree(cls._tmp, ignore_errors=True)

    # (a) signal on synthetic panels
    def _p(self, rule="sma", n=50):
        return {"fn": "trend_long_flat", "rule": rule, "lookback": n, "rebalance_weekday": 4}

    def test_a_uptrend_long_all_coins_gross_one_never_short(self):
        px = three_coin_panel("up")
        for rule in ("sma", "donchian"):
            w = self.f.sig_trend_long_flat(px, self._p(rule, 50))
            self.assertEqual(set(w), set(px.columns), rule)
            self.assertAlmostEqual(sum(w.values()), 1.0, places=12)
            self.assertTrue(all(0.0 < x <= 1.0 for x in w.values()))

    def test_a_falling_panel_is_flat(self):
        px = three_coin_panel("down")
        for rule in ("sma", "donchian"):
            self.assertEqual(self.f.sig_trend_long_flat(px, self._p(rule, 50)), {})

    def test_a_flat_panel_is_flat(self):
        # exactly constant prices: close == SMA == midpoint, strict '>' fails
        idx = pd.date_range("2026-01-01", periods=260, freq="D")
        px = pd.DataFrame({t: 100.0 for t in ("BTC-USD", "A-USD", "B-USD")}, index=idx)
        for rule in ("sma", "donchian"):
            self.assertEqual(self.f.sig_trend_long_flat(px, self._p(rule, 100)), {})

    def test_a_only_uptrending_coin_is_held(self):
        px = three_coin_panel("flat")
        px["B-USD"] = px["B-USD"] * np.linspace(1.0, 4.0, len(px))   # B trends up
        px["A-USD"] = px["A-USD"] * np.linspace(1.0, 0.25, len(px))  # A falls
        w = self.f.sig_trend_long_flat(px, self._p("sma", 50))
        self.assertIn("B-USD", w)
        self.assertNotIn("A-USD", w)
        self.assertAlmostEqual(sum(w.values()), 1.0, places=12)
        self.assertTrue(all(x >= 0 for x in w.values()))

    def test_a_double_vol_coin_gets_half_weight(self):
        n = 260
        idx = pd.date_range("2026-01-01", periods=n, freq="D")
        t = np.arange(n)
        alt = np.where((n - 1 - t) % 2 == 0, 1.0, -1.0)   # last day is the +side
        px = pd.DataFrame({
            "BTC-USD": 100 * 1.005 ** t * (1 + 0.004 * alt),
            "B-USD": 100 * 1.005 ** t * (1 + 0.004 * alt),
            "A-USD": 100 * 1.02 ** t * (1 + 0.05 * alt),     # much higher realised vol
        }, index=idx)
        vol = px.pct_change().iloc[-90:].std()
        self.assertGreater(vol["A-USD"], 2 * vol["BTC-USD"])
        for rule in ("sma", "donchian"):
            w = self.f.sig_trend_long_flat(px, self._p(rule, 50))
            self.assertEqual(set(w), set(px.columns), rule)
            # BTC and B full weight, A half weight (before normalising)
            self.assertAlmostEqual(w["A-USD"] / w["BTC-USD"], 0.5, places=12)
            self.assertAlmostEqual(w["B-USD"], w["BTC-USD"], places=12)
            self.assertAlmostEqual(sum(w.values()), 1.0, places=12)

    def test_a_too_few_rows_returns_empty(self):
        px = three_coin_panel("up", n=50)
        self.assertEqual(self.f.sig_trend_long_flat(px, self._p("sma", 50)), {})
        self.assertNotEqual(self.f.sig_trend_long_flat(
            three_coin_panel("up", n=51), self._p("sma", 50)), {})

    def test_a_sig_cash_is_empty(self):
        self.assertEqual(self.f.sig_cash(three_coin_panel("up"), {"fn": "cash"}), {})
        self.assertIn("cash", self.f.IMPLS)
        self.assertIn("trend_long_flat", self.f.IMPLS)

    # (b) seeding and the 60-cycle run
    def test_b_seeds_exactly_eight_entries(self):
        reg = self.seeded["registry"]
        self.assertEqual(set(reg), REG_NAMES)
        self.assertEqual(len(reg), 8)
        self.assertEqual(set(self.seeded["contestants"]), set(reg))
        names = list(reg)
        self.assertEqual(names[-2:], ["crypto_btc_benchmark", "crypto_cash_baseline"])
        self.assertEqual(self.f.BENCHMARK, "BTC-USD")
        self.assertEqual(sorted(self.f.ALL_TICKERS), sorted(FROZEN))
        self.assertTrue(self.f.TRADES_WEEKENDS)
        self.assertEqual(self.f.TAX_MODEL, "vda_india")
        self.assertEqual(self.f.VARIABLE_COST_PER_SIDE, 0.002)

    def test_b_sixty_weekend_inclusive_cycles_and_report_ran(self):
        self.assertEqual(set(self.ledger["contestants"]), REG_NAMES)
        con = self.pre_report["contestants"]
        for name, s in con.items():
            self.assertEqual(len(s["history"]), N_CYCLES, name)
            self.assertFalse(s["retired"], name)
        dates = [r[0] for r in con["crypto_cash_baseline"]["history"]]
        wk = {pd.Timestamp(d).weekday() for d in dates}
        self.assertTrue({5, 6} <= wk, "weekend days must be recorded")
        self.assertEqual(self.update_out.getvalue().count("Arena updated"), N_CYCLES)
        self.assertNotIn("[warn]", self.update_out.getvalue())
        self.assertNotIn("Traceback", self.report_out.getvalue())
        self.assertIn("VDA30", self.report_out.getvalue())
        self.assertIn("crypto_trend_sma_50", self.report_out.getvalue())

    def test_b_positions_change_only_on_rebalance_weekday(self):
        trend_changes = [c for c in self.changes if c[2].startswith("crypto_trend_")]
        self.assertTrue(trend_changes, "synthetic regimes should trigger some trades")
        for date, wd, name in trend_changes:
            self.assertEqual(wd, 4, f"{name} changed positions on {date} (weekday {wd})")
        con = self.ledger["contestants"]
        for name in REG_NAMES:
            if name.startswith("crypto_trend_"):
                pos = con[name]["positions"]
                self.assertLessEqual(sum(pos.values()), 1.0 + 1e-9)
                self.assertTrue(all(w > 0 for w in pos.values()))

    # (c) permanents
    def test_c_permanents_are_benchmark_verdicts_and_untouched(self):
        reg, con = self.ledger["registry"], self.ledger["contestants"]
        out = self.report_out.getvalue()
        for name in ("crypto_btc_benchmark", "crypto_cash_baseline"):
            self.assertTrue(reg[name].get("permanent"), name)
            b = con[name]
            self.assertEqual(b["rung"], 0)
            self.assertFalse(b["evolved_out"])
            self.assertIsNone(b["lineage"])
            line = [ln for ln in out.splitlines() if name in ln]
            self.assertEqual(len(line), 1, name)
            self.assertIn("BENCHMARK", line[0])
            self.assertNotIn("PROMOTE", line[0])
            self.assertNotIn("DEMOTE", line[0])
        self.assertNotIn("advisor-evolved", out)
        self.assertNotIn("bred (", out)
        self.assertEqual(set(reg), REG_NAMES)   # nothing born or evolved

    def test_c_cash_baseline_compounds_cash_rate_daily(self):
        b = self.ledger["contestants"]["crypto_cash_baseline"]
        rate = self.f.CASH_RATE_ANNUAL
        self.assertEqual(rate, 0.0525)
        for _, net, _e in b["history"]:
            self.assertAlmostEqual(net, rate / 365.0, places=6)
        self.assertAlmostEqual(b["equity"], (1 + rate / 365.0) ** N_CYCLES, places=4)
        self.assertEqual(b["positions"], {})
        self.assertEqual(b["trades"], 0)

    def test_c_first_permanent_is_the_btc_benchmark(self):
        bm = self.f.benchmark_returns(self.ledger["registry"], self.ledger["contestants"])
        hist = self.ledger["contestants"]["crypto_btc_benchmark"]["history"]
        self.assertEqual(bm, {r[0]: r[1] for r in hist})

    # (d) VDA tax
    def test_d_vda_no_loss_offset(self):
        f = self.f
        pos, label = f.post_tax_expectancy_vda(0.001, 200, 0)
        self.assertEqual(label, "VDA30")
        self.assertAlmostEqual(pos, 0.001 * 0.70, places=12)
        # a losing year gets NO credit: post-tax equals pre-tax, never better
        neg, _ = f.post_tax_expectancy_vda(-0.001, 200, 0)
        self.assertAlmostEqual(neg, -0.001, places=12)
        self.assertLessEqual(neg, -0.001)
        # TDS is a drag on top: more trades -> strictly lower post-tax
        busy, _ = f.post_tax_expectancy_vda(0.001, 200, 20)
        self.assertLess(busy, pos)
        self.assertAlmostEqual(pos - busy, 0.01 * 10 / 200, places=12)
        # even a losing contestant pays TDS drag, never receives a credit
        neg_busy, _ = f.post_tax_expectancy_vda(-0.001, 200, 20)
        self.assertLess(neg_busy, -0.001)

    def test_d_equity_post_tax_function_unchanged(self):
        d = tempfile.mkdtemp(prefix="crypto_eq_")
        try:
            eqf = load_copy(d, None)
            self.assertEqual(eqf.TAX_MODEL, "india_equity")
            self.assertEqual(eqf.CASH_RATE_ANNUAL, 0.0)
            self.assertEqual(eqf.seed_registry_for_profile(), eqf.seed_registry())
            self.assertEqual(eqf.post_tax_expectancy(0.001, 100, 10), (0.001 * 0.8, "STCG"))
        finally:
            shutil.rmtree(d, ignore_errors=True)

    # (e) profile integrity
    def test_e_profile_file_and_health_check(self):
        p = load_profile("crypto")
        self.assertIs(p["enabled"], False)
        self.assertEqual(p["class"], "B1")
        self.assertIs(p["trades_weekends"], True)
        self.assertEqual(p["BENCHMARK"], "BTC-USD")
        self.assertEqual(p["MACRO_PROXIES"], [])
        self.assertEqual(p["UNIVERSE"], {"crypto": FROZEN})
        self.assertEqual(p["tax_model"], "vda_india")
        self.assertEqual(p["cash_rate_annual"], 0.0525)
        self.assertEqual(p["VARIABLE_COST_PER_SIDE"], 0.002)
        self.assertEqual(p["DP_CHARGE_PER_SCRIP"], 0)
        self.assertEqual((p["STCG_RATE"], p["LTCG_RATE"], p["LTCG_EXEMPTION_PER_YEAR"]),
                         (0.30, 0.30, 0))
        self.assertIn("_holding_tax_note", p)
        self.assertIn("candidate_note", p)
        self.assertEqual(list(p["registry"])[-2:], ["crypto_btc_benchmark", "crypto_cash_baseline"])
        self.assertEqual(health_check.check_profile_integrity(), [])

    def test_e_rules_proposal_matches_current_rules_and_is_inert(self):
        p = load_profile("crypto")["rules_proposal"]
        for k, v in self.f.RULES.items():
            self.assertEqual(p[k], v, k)
        self.assertIn("INERT", p["_note"])
        self.assertIn("ENABLE PROFILE crypto WITH RULES AS PROPOSED", p["_note"])


if __name__ == "__main__":
    unittest.main()
