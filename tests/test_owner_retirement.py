"""RETIRED_BY_OWNER: an owner-decided retirement is applied through
load_state(), once, with history preserved and the registry key intact."""
import io, os, sys, tempfile, unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_golden_master import _load_factory_copy  # noqa: E402


class OwnerRetirementTest(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self.tmp = tempfile.mkdtemp(prefix="owner_retire_")
        os.chdir(self.tmp)
        self.f = _load_factory_copy(self.tmp)

    def tearDown(self):
        os.chdir(self._cwd)

    def test_monsoon_cement_retired_once_and_history_kept(self):
        f = self.f
        with redirect_stdout(io.StringIO()) as out:
            state = f.load_state()          # fresh ledger: seed + apply
        self.assertIn("RETIRED by owner decision: monsoon_cement", out.getvalue())
        s = state["contestants"]["monsoon_cement"]
        self.assertTrue(s["retired"])
        self.assertTrue(s["retired_reason"].startswith("owner decision:"))
        self.assertIn("monsoon_cement", state["registry"])   # never deleted
        f.save_state(state)
        with redirect_stdout(io.StringIO()) as out2:
            again = f.load_state()          # idempotent: no second print
        self.assertNotIn("RETIRED by owner decision", out2.getvalue())
        self.assertTrue(again["contestants"]["monsoon_cement"]["retired"])
        cause = next(g["cause"] for g in f.graveyard(again) if g["name"] == "monsoon_cement")
        self.assertIn("owner decision", cause)
        # the permanent benchmark can never be retired this way
        self.assertFalse(again["contestants"]["nifty_benchmark"]["retired"])


if __name__ == "__main__":
    unittest.main()
