"""An empty price download must fail cleanly (exit 1, plain message) and
write nothing -- not crash with an IndexError."""
import io, os, sys, tempfile, unittest
from contextlib import redirect_stdout

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_golden_master import _load_factory_copy  # noqa: E402


class EmptyDownload(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self.tmp = tempfile.mkdtemp(prefix="empty_dl_")
        os.chdir(self.tmp)
        self.f = _load_factory_copy(self.tmp)

    def tearDown(self):
        os.chdir(self._cwd)

    def _run(self, frame):
        self.f.fetch_prices = lambda: frame
        buf = io.StringIO()
        with redirect_stdout(buf), self.assertRaises(SystemExit) as cm:
            self.f.update()
        return cm.exception.code, buf.getvalue()

    def test_empty_frame_exits_1_with_message_and_writes_nothing(self):
        code, out = self._run(pd.DataFrame())
        self.assertEqual(code, 1)
        self.assertIn("price download returned no usable rows", out)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "factory_state", "ledger.json")))

    def test_single_row_frame_is_also_unusable(self):
        one = pd.DataFrame({"^NSEI": [100.0]}, index=pd.to_datetime(["2026-10-05"]))
        code, out = self._run(one)
        self.assertEqual(code, 1)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "factory_state", "market_log.json")))


if __name__ == "__main__":
    unittest.main()
