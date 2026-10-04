"""CE-4-02 follow-up: tools/backfill_benchmark_history.py --apply must refuse
while a KILL file exists, before reading prices or touching the ledger."""
import os, subprocess, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class BackfillKillSwitch(unittest.TestCase):
    def run_tool(self, tmp, *args):
        env = dict(os.environ, PYTHONPATH=ROOT)
        return subprocess.run(
            [sys.executable, os.path.join(ROOT, "tools", "backfill_benchmark_history.py"), *args],
            cwd=tmp, env=env, capture_output=True, text=True, timeout=60)

    def test_apply_refused_under_global_kill(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "factory_state"))
            with open(os.path.join(tmp, "factory_state", "KILL"), "w") as fh:
                fh.write("test freeze")
            r = self.run_tool(tmp, "--apply")
            self.assertEqual(r.returncode, 1)
            self.assertIn("KILL SWITCH ACTIVE -- test freeze", r.stdout)
            self.assertIn("refusing --apply", r.stdout)
            # nothing was written: no ledger, no backup
            self.assertEqual(sorted(os.listdir(os.path.join(tmp, "factory_state"))), ["KILL"])


if __name__ == "__main__":
    unittest.main()
