"""CE-4-02: kill switch (factory_state/KILL) stops every write path.

Runs on a temp copy of factory.py with a seeded synthetic panel and a
monkeypatched fetch_prices -- no network, real factory_state/ never touched.
The golden-master test is untouched; the "no KILL file" test here re-runs the
golden scenario and checks the ledger fingerprint against the committed
golden file, so a KILL check that perturbed normal behaviour would fail both.
"""
import contextlib
import io
import os
import random
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
from synthetic_panel import make_panel  # noqa: E402
from test_golden_master import (  # noqa: E402
    _load_factory_copy, fingerprint_lines, GOLDEN, SHOCKS,
    N_HISTORY, N_CYCLES, SEED, _read)

NOTICE = "KILL SWITCH ACTIVE -- "


class KillSwitchBase(unittest.TestCase):
    def setUp(self):
        import numpy as np
        self._cwd = os.getcwd()
        self.tmp = tempfile.mkdtemp(prefix="kill_switch_")
        os.chdir(self.tmp)
        self.state = os.path.join(self.tmp, "factory_state")
        os.makedirs(self.state)
        self.f = _load_factory_copy(self.tmp)
        # block agents/ exactly as the golden harness does
        self._saved_agents = {k: sys.modules.pop(k) for k in list(sys.modules)
                              if k == "agents" or k.startswith("agents.")}
        sys.modules["agents"] = None
        random.seed(SEED)
        np.random.seed(SEED)
        self.panel = make_panel(list(self.f.ALL_TICKERS), N_HISTORY, N_CYCLES,
                                SEED, SHOCKS, benchmark=self.f.BENCHMARK)
        self.cursor = N_HISTORY
        self.f.fetch_prices = lambda: self.panel.iloc[:self.cursor].copy()
        self.ledger_path = os.path.join(self.state, "ledger.json")

    def tearDown(self):
        os.chdir(self._cwd)
        sys.modules.pop("agents", None)
        sys.modules.update(self._saved_agents)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def call(self, fn):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            fn()
        return out.getvalue()

    def cycle(self, i):
        self.cursor = N_HISTORY + i + 1
        return self.call(self.f.update)

    def ledger_bytes(self):
        return _read(self.ledger_path, "rb") if os.path.exists(self.ledger_path) else None

    def kill(self, text="halt for test", where=None):
        path = os.path.join(where or self.state, "KILL")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)
        return path


class NoKillFile(KillSwitchBase):
    def test_golden_scenario_identical_without_kill_file(self):
        self.assertIsNone(self.f.kill_switch_active())
        outs = [self.cycle(i) for i in range(N_CYCLES)]
        outs.append(self.call(self.f.report))
        self.assertFalse(any("KILL SWITCH" in o for o in outs))
        import json
        ledger = json.loads(_read(self.ledger_path))
        self.assertEqual(_read(GOLDEN).splitlines(), fingerprint_lines(ledger))


class GlobalKill(KillSwitchBase):
    def test_five_updates_and_report_change_nothing(self):
        self.kill("pulled by Het")
        for i in range(5):
            out = self.cycle(i)
            self.assertIn(NOTICE + "pulled by Het; no state changed.", out)
        out = self.call(self.f.report)
        self.assertIn(NOTICE + "pulled by Het; no state changed.", out)
        self.assertIsNone(self.ledger_bytes())        # no ledger was even created
        self.assertFalse(os.path.exists(self.f.MARKET_LOG_PATH))
        self.assertEqual(sorted(os.listdir(self.state)), ["KILL"])

    def test_existing_ledger_bytes_identical(self):
        for i in range(3):
            self.cycle(i)
        before = self.ledger_bytes()
        market_before = _read(self.f.MARKET_LOG_PATH, "rb")
        self.kill()
        for i in range(3, 8):
            self.assertIn(NOTICE, self.cycle(i))
        self.assertIn(NOTICE, self.call(self.f.report))
        self.assertEqual(before, self.ledger_bytes())
        self.assertEqual(market_before, _read(self.f.MARKET_LOG_PATH, "rb"))

    def test_notice_truncates_to_200_chars_and_handles_empty(self):
        self.kill("x" * 500)
        self.assertEqual(self.f.kill_switch_active(), "x" * 200)
        self.kill("")
        self.assertEqual(self.f.kill_switch_active(), "(no reason given)")

    def test_removing_file_resumes(self):
        self.cycle(0)
        path = self.kill()
        self.cycle(1)
        stalled = self.ledger_bytes()
        os.remove(path)
        self.assertNotIn("KILL SWITCH", self.cycle(1))
        self.assertNotEqual(stalled, self.ledger_bytes())
        import json
        hist = json.loads(self.ledger_bytes())["contestants"]
        self.assertTrue(any(len(c["history"]) == 2 for c in hist.values()))


class PerProfileKill(KillSwitchBase):
    def as_profile(self, name):
        self.f.FACTORY_PROFILE = name
        self.f.STATE_DIR = os.path.join(self.state, name)

    def test_profile_kill_stops_only_that_profile(self):
        self.as_profile("crypto_x")
        self.kill("crypto halt", where=os.path.join(self.state, "crypto_x"))
        self.assertIn(NOTICE + "crypto halt;", self.cycle(0))
        self.assertIn(NOTICE + "crypto halt;", self.call(self.f.report))
        self.assertFalse(os.path.exists(os.path.join(self.state, "crypto_x", "ledger.json")))
        # a different profile is unaffected by crypto_x's file
        self.as_profile("other_y")
        self.assertIsNone(self.f.kill_switch_active())
        self.assertNotIn("KILL SWITCH", self.cycle(0))
        self.assertTrue(os.path.exists(os.path.join(self.state, "other_y", "ledger.json")))

    def test_profile_file_does_not_stop_default_profile(self):
        self.kill("crypto halt", where=os.path.join(self.state, "crypto_x"))
        self.assertIsNone(self.f.kill_switch_active())    # default profile
        self.assertNotIn("KILL SWITCH", self.cycle(0))

    def test_global_kill_stops_non_default_profile(self):
        self.as_profile("crypto_x")
        self.kill("global halt")
        self.assertIn(NOTICE + "global halt;", self.cycle(0))
        self.assertFalse(os.path.exists(os.path.join(self.state, "crypto_x", "ledger.json")))

    def test_advisors_check_is_global_only(self):
        self.as_profile("crypto_x")
        self.kill("crypto halt", where=os.path.join(self.state, "crypto_x"))
        self.assertIsNone(self.f.kill_switch_active(global_only=True))
        self.kill("global halt")
        self.assertEqual(self.f.kill_switch_active(global_only=True), "global halt")


class AdvisorsAndHealthCheck(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self.tmp = tempfile.mkdtemp(prefix="kill_switch_hc_")
        self.state = os.path.join(self.tmp, "factory_state")
        os.makedirs(self.state)

    def tearDown(self):
        os.chdir(self._cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_health_check_warns_while_present(self):
        from tools.health_check import check_kill_switch
        self.assertEqual(check_kill_switch(self.state), [])
        with open(os.path.join(self.state, "KILL"), "w") as fh:
            fh.write("market halted")
        os.makedirs(os.path.join(self.state, "crypto_x"))
        with open(os.path.join(self.state, "crypto_x", "KILL"), "w") as fh:
            fh.write("crypto only")
        res = check_kill_switch(self.state)
        self.assertEqual([lvl for lvl, _ in res], ["warning", "warning"])
        self.assertIn("factory_state/KILL", res[0][1])
        self.assertIn("market halted", res[0][1])
        self.assertIn("crypto_x/KILL", res[1][1])
        os.remove(os.path.join(self.state, "KILL"))
        os.remove(os.path.join(self.state, "crypto_x", "KILL"))
        self.assertEqual(check_kill_switch(self.state), [])

    def test_advisors_train_exits_with_notice_and_writes_nothing(self):
        # run in a temp cwd so the global relative path factory_state/KILL is ours;
        # train() must return BEFORE fetch_history() (which would hit the network)
        os.chdir(self.tmp)
        with open(os.path.join("factory_state", "KILL"), "w") as fh:
            fh.write("advisor halt")
        import advisors
        self.addCleanup(setattr, advisors, "fetch_history", advisors.fetch_history)
        advisors.fetch_history = lambda: self.fail("fetch_history called under KILL")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            advisors.train()
        self.assertIn(NOTICE + "advisor halt; no state changed.", out.getvalue())
        self.assertEqual(os.listdir("factory_state"), ["KILL"])


if __name__ == "__main__":
    unittest.main()
