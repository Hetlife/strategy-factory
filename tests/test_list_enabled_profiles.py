"""CE-1-03: tools/list_enabled_profiles.py against a temp profiles dir."""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tools import list_enabled_profiles as lep  # noqa: E402


def run(args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = lep.main(args)
    return rc, out.getvalue().strip()


class ListEnabledProfilesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        for name, body in {
            "zeta": {"enabled": True, "trades_weekends": True},
            "equity_nse": {"enabled": True, "trades_weekends": False},
            "alpha": {"enabled": True},                       # no flag -> weekday
            "off_wk": {"enabled": False, "trades_weekends": True},
            "off_str": {"enabled": "true", "trades_weekends": False},  # not exactly true
        }.items():
            with open(os.path.join(self.tmp.name, name + ".json"), "w") as fh:
                json.dump(body, fh)
        with open(os.path.join(self.tmp.name, "__init__.py"), "w") as fh:
            fh.write("")

    def test_all_enabled_sorted(self):
        self.assertEqual(run(["--dir", self.tmp.name]),
                         (0, '["alpha","equity_nse","zeta"]'))

    def test_weekday_flag(self):
        self.assertEqual(run(["--weekday", "--dir", self.tmp.name]),
                         (0, '["alpha","equity_nse"]'))

    def test_weekend_flag(self):
        self.assertEqual(run(["--weekend", "--dir", self.tmp.name]), (0, '["zeta"]'))

    def test_disabled_never_listed(self):
        for flag in ([], ["--weekday"], ["--weekend"]):
            _, out = run(flag + ["--dir", self.tmp.name])
            self.assertNotIn("off_wk", out)
            self.assertNotIn("off_str", out)

    def test_empty_weekend_list(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "equity_nse.json"), "w") as fh:
                json.dump({"enabled": True, "trades_weekends": False}, fh)
            self.assertEqual(run(["--weekend", "--dir", d]), (0, "[]"))

    def test_bad_json_is_loud(self):
        with open(os.path.join(self.tmp.name, "broken.json"), "w") as fh:
            fh.write("{nope")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rc, _ = run(["--dir", self.tmp.name])
        self.assertEqual(rc, 1)

    def test_real_repo_equity_is_weekday_only(self):
        self.assertEqual(run(["--weekday"])[1], '["equity_nse"]')
        self.assertEqual(run(["--weekend"])[1], "[]")


if __name__ == "__main__":
    unittest.main()
