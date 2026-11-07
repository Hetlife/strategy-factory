"""CE-4-02 follow-up (2026-10-11): portfolio/aggregate.py --write persists
factory_state/portfolio_view.json without going through update()/report(), so
it must refuse while a KILL file exists. Printing the table is a read and stays
allowed.

Found during the M1 post-merge review: every write path in the repo honoured
the kill switch EXCEPT this one, which made the review brief's claim ("no write
path in the repo runs under KILL") false.

These tests never create a KILL file in the real repo -- they point REPO_ROOT at
a temporary copy, so a regression cannot freeze the live daily run.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AggregatorKillSwitch(unittest.TestCase):
    """Run the aggregator against a throwaway copy of the repo tree."""

    def _sandbox(self):
        """A temp dir with just enough of the repo for the aggregator to run."""
        tmp = tempfile.mkdtemp()
        for name in ("portfolio", "profiles"):
            shutil.copytree(os.path.join(ROOT, name), os.path.join(tmp, name))
        for name in ("factory.py",):
            shutil.copy2(os.path.join(ROOT, name), os.path.join(tmp, name))
        state = os.path.join(tmp, "factory_state")
        os.makedirs(state, exist_ok=True)
        src_ledger = os.path.join(ROOT, "factory_state", "ledger.json")
        if os.path.exists(src_ledger):
            shutil.copy2(src_ledger, os.path.join(state, "ledger.json"))
        return tmp

    def _run(self, tmp, *args, cwd=None):
        env = dict(os.environ, PYTHONPATH=tmp)
        return subprocess.run(
            [sys.executable, "-m", "portfolio.aggregate", *args],
            cwd=cwd or tmp, env=env, capture_output=True, text=True, timeout=120)

    def test_write_refused_under_kill(self):
        tmp = self._sandbox()
        try:
            with open(os.path.join(tmp, "factory_state", "KILL"), "w") as fh:
                fh.write("test freeze")
            r = self._run(tmp, "--write")
            self.assertIn("KILL SWITCH ACTIVE -- test freeze", r.stdout)
            self.assertIn("refusing --write", r.stdout)
            self.assertFalse(
                os.path.exists(os.path.join(tmp, "factory_state", "portfolio_view.json")),
                "portfolio_view.json was written while a KILL file existed")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_write_allowed_without_kill(self):
        tmp = self._sandbox()
        try:
            r = self._run(tmp, "--write")
            out = os.path.join(tmp, "factory_state", "portfolio_view.json")
            self.assertTrue(os.path.exists(out),
                            f"no view written without a KILL file; stderr={r.stderr[-400:]}")
            with open(out) as fh:
                json.load(fh)      # must be valid JSON, not a truncated write
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_read_still_allowed_under_kill(self):
        tmp = self._sandbox()
        try:
            with open(os.path.join(tmp, "factory_state", "KILL"), "w") as fh:
                fh.write("test freeze")
            r = self._run(tmp)                      # no --write: a pure read
            self.assertIn("Portfolio aggregator", r.stdout)
            self.assertNotIn("refusing --write", r.stdout)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_kill_is_found_from_any_working_directory(self):
        """The guard must anchor at REPO_ROOT, not cwd.

        factory's KILL_GLOBAL_PATH is relative, so a naive
        factory.kill_switch_active() resolves against the current directory
        while this module still writes to REPO_ROOT -- run it from elsewhere
        and the guard would miss the kill file and write anyway.
        """
        tmp = self._sandbox()
        elsewhere = tempfile.mkdtemp()
        try:
            with open(os.path.join(tmp, "factory_state", "KILL"), "w") as fh:
                fh.write("test freeze")
            r = self._run(tmp, "--write", cwd=elsewhere)   # cwd has no KILL file
            self.assertIn("refusing --write", r.stdout,
                          "guard missed the KILL file when run from another directory")
            self.assertFalse(
                os.path.exists(os.path.join(tmp, "factory_state", "portfolio_view.json")))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            shutil.rmtree(elsewhere, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
