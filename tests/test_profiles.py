"""CE-1-02: profile loader, forbidden keys, env selection, weekend calendar flag.

No network: yfinance is replaced by a fake module, and everything that loads
factory.py does so from a temp copy (with a copy of profiles/), so the real
factory_state/ is never written.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from profiles import load_profile, ProfileError  # noqa: E402
from tools import health_check  # noqa: E402

OVERRIDDEN = ("UNIVERSE", "MACRO_PROXIES", "BENCHMARK", "STATE_DIR",
              "VARIABLE_COST_PER_SIDE", "DP_CHARGE_PER_SCRIP", "STCG_RATE",
              "LTCG_RATE", "LTCG_EXEMPTION_PER_YEAR", "TRADES_WEEKENDS",
              "ALL_TICKERS", "PARAM_BANK_PATH", "ADVISOR_STATE_PATH",
              "MARKET_LOG_PATH")


def load_factory_copy(tmp, profile_env=None):
    """Import a fresh copy of factory.py living in `tmp` (with its profiles/)."""
    shutil.copy(os.path.join(ROOT, "factory.py"), tmp)
    shutil.copytree(os.path.join(ROOT, "profiles"), os.path.join(tmp, "profiles"),
                    ignore=shutil.ignore_patterns("__pycache__"), dirs_exist_ok=True)
    saved = os.environ.pop("FACTORY_PROFILE", None)
    if profile_env is not None:
        os.environ["FACTORY_PROFILE"] = profile_env
    try:
        spec = importlib.util.spec_from_file_location(
            "factory_profcopy", os.path.join(tmp, "factory.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        os.environ.pop("FACTORY_PROFILE", None)
        if saved is not None:
            os.environ["FACTORY_PROFILE"] = saved
    return mod


class ProfileLoader(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="profiles_test_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_a_unknown_profile_is_a_clean_error(self):
        with self.assertRaises(ProfileError):
            load_profile("does_not_exist")
        with self.assertRaises(ProfileError):
            load_profile("../factory")
        env = dict(os.environ, FACTORY_PROFILE="does_not_exist")
        r = subprocess.run([sys.executable, os.path.join(ROOT, "factory.py"), "update"],
                           env=env, capture_output=True, text=True, cwd=self.tmp)
        self.assertEqual(r.returncode, 1)
        self.assertIn("unknown profile 'does_not_exist'", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_b_forbidden_keys_rejected_by_loader_and_health_check(self):
        good = json.load(open(os.path.join(ROOT, "profiles", "equity_nse.json")))
        for key in ("rules", "ladder", "cost_per_side"):
            d = os.path.join(self.tmp, key)
            os.makedirs(d)
            bad = dict(good, **{key: {"x": 1}})
            json.dump(bad, open(os.path.join(d, "equity_nse.json"), "w"))
            with self.assertRaises(ProfileError, msg=key):
                load_profile("equity_nse", d)
            found = health_check.check_profile_integrity(d)
            self.assertTrue(any(lvl == "error" for lvl, _ in found), key)
        # a non-equity profile MAY carry such keys (inert proposals)
        d = os.path.join(self.tmp, "other")
        os.makedirs(d)
        json.dump(dict(good, rules={"x": 1}), open(os.path.join(d, "crypto_x.json"), "w"))
        self.assertIn("rules", load_profile("crypto_x", d))

    def test_health_check_passes_on_committed_profile(self):
        self.assertEqual(health_check.check_profile_integrity(), [])
        d = os.path.join(self.tmp, "drift")
        os.makedirs(d)
        good = json.load(open(os.path.join(ROOT, "profiles", "equity_nse.json")))
        good["DP_CHARGE_PER_SCRIP"] = 99.0
        json.dump(good, open(os.path.join(d, "equity_nse.json"), "w"))
        found = health_check.check_profile_integrity(d)
        self.assertTrue(any("DP_CHARGE_PER_SCRIP" in m for _, m in found))

    def test_c_unset_and_equity_nse_give_identical_constants(self):
        a, b = os.path.join(self.tmp, "a"), os.path.join(self.tmp, "b")
        os.makedirs(a)
        os.makedirs(b)
        fa = load_factory_copy(a)
        fb = load_factory_copy(b, "equity_nse")
        da = {n: getattr(fa, n) for n in OVERRIDDEN}
        db = {n: getattr(fb, n) for n in OVERRIDDEN}
        self.assertEqual(da, db)
        self.assertEqual(da["STATE_DIR"], "factory_state")
        self.assertEqual(da["PARAM_BANK_PATH"],
                         os.path.join("factory_state", "parameter_bank.json"))
        self.assertIs(da["TRADES_WEEKENDS"], False)
        for n in ("RULES", "LADDER", "COST_PER_SIDE"):
            self.assertEqual(getattr(fa, n), getattr(fb, n))

    def test_nondefault_profile_uses_its_own_state_dir(self):
        d = os.path.join(self.tmp, "n")
        os.makedirs(d)
        self._write_profile_into_copy(d, "crypto_t", True)
        f = load_factory_copy(d, "crypto_t")
        self.assertEqual(f.STATE_DIR, os.path.join("factory_state", "crypto_t"))
        self.assertEqual(f.MARKET_LOG_PATH,
                         os.path.join("factory_state", "crypto_t", "market_log.json"))

    @staticmethod
    def _write_profile_into_copy(tmp, name, weekends):
        """Pre-create tmp/profiles/<name>.json (load_factory_copy keeps it)."""
        prof = json.load(open(os.path.join(ROOT, "profiles", "equity_nse.json")))
        prof.update(trades_weekends=weekends, enabled=True, **{"class": "T"})
        os.makedirs(os.path.join(tmp, "profiles"), exist_ok=True)
        json.dump(prof, open(os.path.join(tmp, "profiles", name + ".json"), "w"))

    def _fetch_with_fake_yfinance(self, weekends):
        d = os.path.join(self.tmp, "w%d" % weekends)
        os.makedirs(d)
        self._write_profile_into_copy(d, "cal_t", weekends)
        f = load_factory_copy(d, "cal_t")
        self.assertEqual(f.TRADES_WEEKENDS, weekends)
        idx = pd.date_range("2026-10-01", "2026-10-07")   # Thu..Wed, incl. Sat+Sun
        close = pd.DataFrame({"AAA": range(1, 8), "BBB": range(11, 18)},
                             index=idx, dtype=float)
        raw = pd.concat({"Close": close}, axis=1)
        fake = types.ModuleType("yfinance")
        fake.download = lambda *a, **k: raw
        saved = sys.modules.get("yfinance")
        sys.modules["yfinance"] = fake
        try:
            return f.fetch_prices()
        finally:
            if saved is not None:
                sys.modules["yfinance"] = saved
            else:
                del sys.modules["yfinance"]

    def test_d_trades_weekends_flag_controls_weekend_rows(self):
        kept = self._fetch_with_fake_yfinance(True)
        self.assertEqual(len(kept), 7)
        self.assertTrue((kept.index.weekday >= 5).any())
        dropped = self._fetch_with_fake_yfinance(False)
        self.assertEqual(len(dropped), 5)
        self.assertTrue((dropped.index.weekday < 5).all())


if __name__ == "__main__":
    unittest.main()
