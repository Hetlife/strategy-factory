"""Golden-master regression harness for factory.py (CE-1-01).

Copies factory.py into a temp dir, runs 40 x update() then report() on a
seeded synthetic panel (fetch_prices monkeypatched -- never touches the
network), and fingerprints the resulting ledger. Any behavioural change to
the equity arena changes the fingerprint and fails this test.

The real factory_state/ is NEVER written: everything runs in the temp dir.
The run starts from a FRESH state (no ledger/market_log/advisor files), not a
copy of the live one: the live ledger is rewritten daily by CI, so a golden
hash derived from it would rot within a day. The live ledger is only READ,
for the "committed registry entries are unmutated" check.

Fingerprint file tests/golden/equity_nse.sha256:
  line 1  : "ledger_sha256 <sha256(json.dumps(ledger, sort_keys=True, default=str))>"
  then    : one "registry|contestant <name> <sha256>" line per entry, so a
            mismatch diff shows WHICH entries changed.
First run (file absent) writes it; later runs compare.

Test-only hook to prove the harness detects change:
  GOLDEN_MUTATE="PAPER_HOLDING_TAX_WEEKLY=0.0014" python3 -m unittest tests.test_golden_master
rewrites that top-level constant in the TEMP COPY of factory.py only.
"""
import contextlib
import difflib
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GOLDEN = os.path.join(HERE, "golden", "equity_nse.sha256")
sys.path.insert(0, HERE)
from synthetic_panel import make_panel  # noqa: E402

N_HISTORY, N_CYCLES, SEED = 300, 40, 20261004
# Forced events (new-row index -> ticker -> daily return): leaders jump so
# event_drift fires; Brent falls hard for several days so input_cost fires.
SHOCKS = {
    5: {"ULTRACEMCO.NS": 0.06, "LT.NS": -0.05, "TATASTEEL.NS": 0.045},
    12: {"BZ=F": -0.07}, 13: {"BZ=F": -0.06}, 14: {"BZ=F": -0.05},
    20: {"ULTRACEMCO.NS": -0.045, "TATASTEEL.NS": -0.05},
}


def _read(path, mode="r"):
    with open(path, mode) as fh:
        return fh.read()


def _sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str)
                          .encode()).hexdigest()


def fingerprint_lines(ledger):
    lines = ["ledger_sha256 " + _sha(ledger)]
    for k in sorted(ledger["registry"]):
        lines.append(f"registry {k} {_sha(ledger['registry'][k])}")
    for k in sorted(ledger["contestants"]):
        lines.append(f"contestant {k} {_sha(ledger['contestants'][k])}")
    return lines


def _load_factory_copy(tmp):
    src = _read(os.path.join(ROOT, "factory.py"))
    mut = os.environ.get("GOLDEN_MUTATE")
    if mut:
        name, val = mut.split("=", 1)
        src, n = re.subn(rf"(?m)^{re.escape(name)}\s*=\s*[^\n#]*",
                         f"{name} = {val}  ", src, count=1)
        if n != 1:
            raise RuntimeError(f"GOLDEN_MUTATE: constant {name} not found")
    path = os.path.join(tmp, "factory.py")
    with open(path, "w") as f:
        f.write(src)
    spec = importlib.util.spec_from_file_location("factory_goldencopy", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)          # cwd is tmp: relative paths land there
    state = os.path.join(tmp, "factory_state")
    mod.STATE_DIR = state
    mod.PARAM_BANK_PATH = os.path.join(state, "parameter_bank.json")
    mod.ADVISOR_STATE_PATH = os.path.join(state, "advisor_state.json")
    mod.MARKET_LOG_PATH = os.path.join(state, "market_log.json")
    return mod


class GoldenMaster(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import random
        import numpy as np
        cls._cwd = os.getcwd()
        cls._tmp = tempfile.mkdtemp(prefix="golden_master_")
        os.chdir(cls._tmp)
        os.makedirs("factory_state")
        cls.f = f = _load_factory_copy(cls._tmp)
        # agents/ is read-only advisory (never writes the ledger); block it so
        # report() takes its non-fatal ImportError path and nothing outside the
        # temp dir can be reached.
        cls._saved_agents = {k: sys.modules.pop(k) for k in list(sys.modules)
                             if k == "agents" or k.startswith("agents.")}
        sys.modules["agents"] = None
        random.seed(SEED)
        np.random.seed(SEED)
        tickers = list(f.ALL_TICKERS)
        assert f.BENCHMARK in tickers and all(m in tickers for m in f.MACRO_PROXIES)
        cls.panel = make_panel(tickers, N_HISTORY, N_CYCLES, SEED, SHOCKS,
                               benchmark=f.BENCHMARK)
        cls.cursor = N_HISTORY
        f.fetch_prices = lambda: cls.panel.iloc[:cls.cursor].copy()
        cls.out = io.StringIO()
        with contextlib.redirect_stdout(cls.out):
            for i in range(N_CYCLES):
                cls.cursor = N_HISTORY + i + 1
                f.update()
        cls.ledger_path = os.path.join(cls._tmp, "factory_state", "ledger.json")
        cls.pre_replay = _read(cls.ledger_path, "rb")
        # idempotence guard: same panel row again must be SKIPPED, ledger untouched
        rep = io.StringIO()
        with contextlib.redirect_stdout(rep):
            f.update()
        cls.replay_msg = rep.getvalue()
        cls.post_replay = _read(cls.ledger_path, "rb")
        # snapshot before report() for the paper-holding-tax check
        cls.pre_report = json.loads(cls.pre_replay)
        rep = io.StringIO()
        with contextlib.redirect_stdout(rep):
            f.report()
        cls.report_out = rep.getvalue()
        cls.ledger = json.loads(_read(cls.ledger_path))

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls._cwd)
        sys.modules.pop("agents", None)
        sys.modules.update(cls._saved_agents)
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def test_fingerprint_matches_golden(self):
        lines = fingerprint_lines(self.ledger)
        if not os.path.exists(GOLDEN) and os.environ.get("CI"):
            self.fail(f"golden file {GOLDEN} is missing in CI -- it must be committed, "
                      "never regenerated silently on a runner")
        if not os.path.exists(GOLDEN):
            os.makedirs(os.path.dirname(GOLDEN), exist_ok=True)
            with open(GOLDEN, "w") as fh:
                fh.write("\n".join(lines) + "\n")
            print(f"\n[golden] wrote new fingerprint: {lines[0]}")
            return
        want = _read(GOLDEN).splitlines()
        if want != lines:
            diff = list(difflib.unified_diff(want, lines, "golden", "current",
                                             lineterm="", n=0))
            self.fail("equity-arena fingerprint changed\n"
                      + "\n".join(diff[:200]))

    def test_run_exercised_the_engine(self):
        con = self.ledger["contestants"]
        self.assertGreater(len(con), 20)
        self.assertTrue(any(c["trades"] > 0 for c in con.values()))
        self.assertTrue(any(len(c["history"]) == N_CYCLES for c in con.values()))

    def test_committed_registry_entries_byte_identical(self):
        live = json.loads(_read(os.path.join(ROOT, "factory_state", "ledger.json")))
        common = set(live["registry"]) & set(self.ledger["registry"])
        self.assertGreater(len(common), 0)
        for k in sorted(common):
            self.assertEqual(
                json.dumps(live["registry"][k], sort_keys=True),
                json.dumps(self.ledger["registry"][k], sort_keys=True),
                f"registry entry {k} differs from committed ledger")

    def test_idempotence_guard(self):
        self.assertIn("Arena update SKIPPED", self.replay_msg)
        self.assertEqual(self.pre_replay, self.post_replay)

    def test_paper_holding_tax(self):
        f, pre, post = self.f, self.pre_report["contestants"], self.ledger["contestants"]
        reg = self.ledger["registry"]
        checked = 0
        for name, s in pre.items():
            if name not in post or s["retired"] or s["rung"] != 0:
                continue
            p = post[name]
            if reg.get(name, {}).get("permanent"):
                self.assertEqual(s["equity"], p["equity"], name)
            elif p["paper_failures"] == s["paper_failures"]:
                self.assertAlmostEqual(
                    p["equity"], s["equity"] * (1 - f.PAPER_HOLDING_TAX_WEEKLY),
                    places=12, msg=name)
                checked += 1
        self.assertGreater(checked, 0)


if __name__ == "__main__":
    unittest.main()
