"""CE-2-04: paper holding tax is a per-profile setting (default unchanged).

No network, real factory_state/ never written: every factory.py runs from a
temp copy with its own profiles/ dir, cwd inside the temp dir, fetch_prices
monkeypatched to a seeded synthetic panel.
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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from synthetic_panel import make_panel  # noqa: E402
from tools import health_check  # noqa: E402

N_HISTORY, N_CYCLES, SEED = 300, 5, 20261004
KEY = "paper_holding_tax_weekly"


def _equity_profile():
    with open(os.path.join(ROOT, "profiles", "equity_nse.json")) as fh:
        return json.load(fh)


def _load_copy(tmp, profile_name, profile):
    """Fresh factory.py copy in tmp, with profiles/<profile_name>.json = profile."""
    shutil.copy(os.path.join(ROOT, "factory.py"), tmp)
    pdir = os.path.join(tmp, "profiles")
    shutil.copytree(os.path.join(ROOT, "profiles"), pdir,
                    ignore=shutil.ignore_patterns("__pycache__"), dirs_exist_ok=True)
    with open(os.path.join(pdir, profile_name + ".json"), "w") as fh:
        json.dump(profile, fh)
    saved = os.environ.pop("FACTORY_PROFILE", None)
    os.environ["FACTORY_PROFILE"] = profile_name
    try:
        spec = importlib.util.spec_from_file_location(
            "factory_taxcopy", os.path.join(tmp, "factory.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        os.environ.pop("FACTORY_PROFILE", None)
        if saved is not None:
            os.environ["FACTORY_PROFILE"] = saved
    return mod


def _run_report(profile_name, profile):
    """Run N_CYCLES update() then report() in a temp dir. Returns
    (factory_module, pre_report_ledger, post_report_ledger)."""
    cwd = os.getcwd()
    tmp = tempfile.mkdtemp(prefix="holding_tax_")
    saved_agents = {k: sys.modules.pop(k) for k in list(sys.modules)
                    if k == "agents" or k.startswith("agents.")}
    sys.modules["agents"] = None          # report() takes its non-fatal path
    try:
        os.chdir(tmp)
        f = _load_copy(tmp, profile_name, profile)
        state = os.path.join(tmp, "factory_state")
        os.makedirs(state)
        f.STATE_DIR = state
        f.PARAM_BANK_PATH = os.path.join(state, "parameter_bank.json")
        f.ADVISOR_STATE_PATH = os.path.join(state, "advisor_state.json")
        f.MARKET_LOG_PATH = os.path.join(state, "market_log.json")
        panel = make_panel(list(f.ALL_TICKERS), N_HISTORY, N_CYCLES, SEED,
                           None, benchmark=f.BENCHMARK)
        cursor = [N_HISTORY]
        f.fetch_prices = lambda: panel.iloc[:cursor[0]].copy()
        ledger_path = os.path.join(state, "ledger.json")
        with contextlib.redirect_stdout(io.StringIO()):
            for i in range(N_CYCLES):
                cursor[0] = N_HISTORY + i + 1
                f.update()
        with open(ledger_path) as fh:
            pre = json.load(fh)
        with contextlib.redirect_stdout(io.StringIO()):
            f.report()
        with open(ledger_path) as fh:
            post = json.load(fh)
        return f, pre, post
    finally:
        os.chdir(cwd)
        sys.modules.pop("agents", None)
        sys.modules.update(saved_agents)
        shutil.rmtree(tmp, ignore_errors=True)


def _profile(**kw):
    p = _equity_profile()
    p.pop(KEY, None)
    p.update(kw)
    p.update(enabled=True, **{"class": "T"})
    return p


class HoldingTaxProfile(unittest.TestCase):
    def _check(self, factor, f, pre, post):
        reg = post["registry"]
        paper = bench = 0
        for name, s in pre["contestants"].items():
            p = post["contestants"].get(name)
            if p is None or s["retired"] or s["rung"] != 0:
                continue
            if reg.get(name, {}).get("permanent"):
                bench += 1
                self.assertEqual(p["equity"], s["equity"], name)
            else:
                paper += 1
                self.assertAlmostEqual(p["equity"], s["equity"] * factor,
                                       places=12, msg=name)
        self.assertGreater(paper, 5)
        self.assertGreater(bench, 0)

    def test_zero_tax_leaves_equity_unchanged(self):
        f, pre, post = _run_report("tax_zero", _profile(**{KEY: 0.0}))
        self.assertEqual(f.PAPER_HOLDING_TAX_WEEKLY, 0.0)
        self._check(1.0, f, pre, post)

    def test_explicit_0013_multiplies_by_09987(self):
        f, pre, post = _run_report("tax_default", _profile(**{KEY: 0.0013}))
        self.assertEqual(f.PAPER_HOLDING_TAX_WEEKLY, 0.0013)
        self._check(0.9987, f, pre, post)

    def test_nondefault_profile_omitting_key_gets_0013(self):
        f, pre, post = _run_report("tax_omitted", _profile())
        self.assertNotIn(KEY, _profile())
        self.assertEqual(f.PAPER_HOLDING_TAX_WEEKLY, 0.0013)
        self._check(0.9987, f, pre, post)

    def test_committed_equity_profile_carries_0013(self):
        self.assertEqual(_equity_profile()[KEY], 0.0013)

    def test_health_check_errors_on_missing_or_drifted_key(self):
        tmp = tempfile.mkdtemp(prefix="holding_tax_hc_")
        try:
            self.assertEqual(health_check.check_profile_integrity(), [])
            for label, value in (("missing", None), ("drift", 0.0), ("drift2", 0.002)):
                d = os.path.join(tmp, label)
                os.makedirs(d)
                prof = _equity_profile()
                if value is None:
                    del prof[KEY]
                else:
                    prof[KEY] = value
                with open(os.path.join(d, "equity_nse.json"), "w") as fh:
                    json.dump(prof, fh)
                found = health_check.check_profile_integrity(d)
                self.assertTrue(any(lvl == "error" and KEY in m for lvl, m in found),
                                (label, found))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
