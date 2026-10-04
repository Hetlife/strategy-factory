"""CE-2-02: class A profile shield_nse + sig_fixed_weight.

No network (fetch_prices is monkeypatched with the seeded synthetic panel) and
everything runs from a temp copy of factory.py + profiles/ in a temp cwd, so
the real factory_state/ is never written.
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
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
from synthetic_panel import make_panel  # noqa: E402
from profiles import load_profile  # noqa: E402
from tools import health_check  # noqa: E402

TARGET = {"LIQUIDCASE.NS": 0.40, "LTGILTBEES.NS": 0.20,
          "GOLDBEES.NS": 0.20, "NIFTYBEES.NS": 0.20}
N_HISTORY, N_CYCLES, SEED = 300, 40, 20261004


def load_copy(tmp, profile):
    shutil.copy(os.path.join(ROOT, "factory.py"), tmp)
    shutil.copytree(os.path.join(ROOT, "profiles"), os.path.join(tmp, "profiles"),
                    ignore=shutil.ignore_patterns("__pycache__"), dirs_exist_ok=True)
    saved = os.environ.pop("FACTORY_PROFILE", None)
    if profile:
        os.environ["FACTORY_PROFILE"] = profile
    try:
        spec = importlib.util.spec_from_file_location(
            "factory_shieldcopy_" + (profile or "default"),
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


class ShieldProfile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._cwd = os.getcwd()
        cls._tmp = tempfile.mkdtemp(prefix="shield_test_")
        os.chdir(cls._tmp)
        cls._saved_agents = {k: sys.modules.pop(k) for k in list(sys.modules)
                             if k == "agents" or k.startswith("agents.")}
        sys.modules["agents"] = None     # keep report() inside the temp dir
        cls.f = f = load_copy(cls._tmp, "shield_nse")
        cls.panel = make_panel(list(f.ALL_TICKERS), N_HISTORY, N_CYCLES, SEED,
                               None, benchmark=f.BENCHMARK)
        cls.cursor = N_HISTORY
        f.fetch_prices = lambda: cls.panel.iloc[:cls.cursor].copy()
        cls.seeded = f.load_state()          # fresh seed, before any update
        cls.update_out = io.StringIO()
        with contextlib.redirect_stdout(cls.update_out):
            for i in range(N_CYCLES):
                cls.cursor = N_HISTORY + i + 1
                f.update()
        cls.report_out = io.StringIO()
        with contextlib.redirect_stdout(cls.report_out):
            f.report()
        cls.ledger = json.load(open(os.path.join(cls._tmp, "factory_state",
                                                 "ledger.json")))

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls._cwd)
        sys.modules.pop("agents", None)
        sys.modules.update(cls._saved_agents)
        shutil.rmtree(cls._tmp, ignore_errors=True)

    # (a) signal
    def test_a_fixed_weight_returns_target_weights(self):
        f = self.f
        px = self.panel.iloc[:N_HISTORY]
        w = f.IMPLS["fixed_weight"](px, f.seed_registry_for_profile()["shield_core"])
        self.assertEqual(set(w), set(TARGET))
        self.assertAlmostEqual(sum(w.values()), 1.0, places=12)
        for t, x in w.items():
            self.assertAlmostEqual(x, TARGET[t], places=12)
            self.assertGreaterEqual(x, 0.0)
            self.assertLessEqual(x, 1.0)

    def test_a_fixed_weight_after_a_big_drift_still_gross_one(self):
        f = self.f
        px = self.panel.iloc[:N_HISTORY].copy()
        px["NIFTYBEES.NS"] = px["NIFTYBEES.NS"] * np.linspace(1, 3, len(px))
        w = f.sig_fixed_weight(px, {"weights": TARGET, "band": 0.05})
        self.assertAlmostEqual(sum(w.values()), 1.0, places=12)
        self.assertTrue(all(0.0 <= x <= 1.0 for x in w.values()))

    def test_a_fixed_weight_missing_ticker_renormalises_or_empty(self):
        f = self.f
        px = self.panel.iloc[:N_HISTORY].drop(columns=["GOLDBEES.NS"])
        w = f.sig_fixed_weight(px, {"weights": TARGET, "band": 0.05})
        self.assertNotIn("GOLDBEES.NS", w)
        self.assertAlmostEqual(sum(w.values()), 1.0, places=12)
        self.assertEqual(f.sig_fixed_weight(px[[]], {"weights": TARGET}), {})

    # (b) seeding and the 40-cycle run
    def test_b_seeds_exactly_the_two_profile_entries(self):
        self.assertEqual(set(self.seeded["registry"]),
                         {"shield_core", "shield_cash_benchmark"})
        self.assertEqual(set(self.seeded["contestants"]), set(self.seeded["registry"]))
        self.assertEqual(self.seeded["registry"]["shield_core"]["weights"], TARGET)
        self.assertEqual(self.f.STATE_DIR, os.path.join(self._tmp, "factory_state"))
        self.assertEqual(self.f.BENCHMARK, "LIQUIDCASE.NS")
        self.assertEqual(sorted(self.f.ALL_TICKERS), sorted(TARGET))

    def test_b_forty_cycles_and_report_ran(self):
        con = self.ledger["contestants"]
        self.assertEqual(set(con), {"shield_core", "shield_cash_benchmark"})
        for name, s in con.items():
            self.assertEqual(len(s["history"]), N_CYCLES, name)
            self.assertEqual(s["trades"], 1, name)   # day-1 entry only: stateless target
            self.assertFalse(s["retired"], name)
        self.assertEqual(self.update_out.getvalue().count("Arena updated"), N_CYCLES)
        self.assertEqual(set(self.ledger["registry"]), set(self.seeded["registry"]))
        self.assertIn("shield_core", self.report_out.getvalue())

    # (c) benchmark is never promoted / demoted / evolved / bred
    def test_c_benchmark_is_permanent_and_untouched(self):
        reg, con = self.ledger["registry"], self.ledger["contestants"]
        self.assertTrue(reg["shield_cash_benchmark"].get("permanent"))
        b = con["shield_cash_benchmark"]
        self.assertEqual(b["rung"], 0)
        self.assertFalse(b["evolved_out"])
        self.assertIsNone(b["lineage"])
        out = self.report_out.getvalue()
        line = [ln for ln in out.splitlines() if "shield_cash_benchmark" in ln]
        self.assertEqual(len(line), 1)
        self.assertIn("BENCHMARK", line[0])
        self.assertNotIn("PROMOTE", line[0])
        self.assertNotIn("DEMOTE", line[0])
        # no weekly paper-holding tax on the permanent entry, i.e. its equity is
        # exactly the compounded daily nets
        eq = 1.0
        for _, net, _e in b["history"]:
            eq *= 1 + net
        self.assertAlmostEqual(b["equity"], eq, places=3)
        self.assertNotIn("advisor-evolved", out)
        self.assertNotIn("bred (", out)

    # (d) profile integrity
    def test_d_profile_file_and_health_check(self):
        p = load_profile("shield_nse")
        self.assertIs(p["enabled"], False)
        self.assertEqual(p["class"], "A1")
        self.assertIs(p["trades_weekends"], False)
        self.assertEqual(p["BENCHMARK"], "LIQUIDCASE.NS")
        self.assertEqual(p["MACRO_PROXIES"], [])
        self.assertEqual(p["UNIVERSE"], {"shield": list(TARGET)})
        self.assertIn("rules_proposal", p)       # allowed on a non-equity profile
        self.assertIn("candidate_tickers_note", p)
        eq = load_profile("equity_nse")
        for k in ("VARIABLE_COST_PER_SIDE", "DP_CHARGE_PER_SCRIP", "STCG_RATE",
                  "LTCG_RATE", "LTCG_EXEMPTION_PER_YEAR"):
            self.assertEqual(p[k], eq[k], k)
        self.assertEqual(health_check.check_profile_integrity(), [])

    def test_d_rules_proposal_matches_current_rules_and_is_inert(self):
        p = load_profile("shield_nse")["rules_proposal"]
        for k, v in self.f.RULES.items():
            self.assertEqual(p[k], v, k)
        self.assertIn("INERT", p["_note"])

    def test_equity_seed_path_unchanged(self):
        d = tempfile.mkdtemp(prefix="shield_eq_")
        try:
            eqf = load_copy(d, None)
            self.assertEqual(eqf.seed_registry_for_profile(), eqf.seed_registry())
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
