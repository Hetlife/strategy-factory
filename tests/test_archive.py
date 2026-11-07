"""CE-6-01: data archive (archive.py + factory.main). No network.

Part 1 tests archive.py directly; part 2 runs factory.main() on a temp copy of
factory.py (same harness as the golden master) with a monkeypatched
fetch_prices and a seeded synthetic panel.
"""
import contextlib
import csv
import glob
import io
import json
import os
import random
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
import archive  # noqa: E402
from synthetic_panel import make_panel  # noqa: E402
from test_golden_master import _load_factory_copy  # noqa: E402


def _rows(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


class RecordPull(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="archive_pull_")
        idx = pd.to_datetime(["2026-09-28", "2026-09-29", "2026-09-30",
                              "2026-10-01", "2026-10-02", "2026-10-05", "2026-10-06"])
        self.raw = pd.DataFrame({"A.NS": np.arange(7) + 100.0,
                                 "B.NS": np.arange(7) + 200.0}, index=idx)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def pulls(self, month):
        return os.path.join(self.tmp, "archive", "pulls", month + ".csv")

    def test_first_call_writes_last_six_dates_split_by_month(self):
        n = archive.record_pull(self.tmp, self.raw, "T1", "r1")
        self.assertEqual(n, 12)                       # 6 dates x 2 tickers
        sep, octo = _rows(self.pulls("2026-09")), _rows(self.pulls("2026-10"))
        self.assertEqual({r["panel_date"] for r in sep},
                         {"2026-09-29", "2026-09-30"})   # 09-28 is outside last 6
        self.assertEqual({r["panel_date"] for r in octo},
                         {"2026-10-01", "2026-10-02", "2026-10-05", "2026-10-06"})
        self.assertEqual(len(sep) + len(octo), 12)
        self.assertEqual(list(sep[0]), archive.PULL_FIELDS)
        self.assertEqual(sep[0]["first_seen_utc"], "T1")
        self.assertEqual(sep[0]["pull_id"], "r1")

    def test_identical_second_call_writes_nothing(self):
        archive.record_pull(self.tmp, self.raw, "T1", "r1")
        before = open(self.pulls("2026-10")).read()
        self.assertEqual(archive.record_pull(self.tmp, self.raw, "T2", "r2"), 0)
        self.assertEqual(open(self.pulls("2026-10")).read(), before)

    def test_revised_value_writes_exactly_one_row(self):
        archive.record_pull(self.tmp, self.raw, "T1", "r1")
        raw2 = self.raw.copy()
        raw2.loc["2026-10-02", "B.NS"] = 999.5
        self.assertEqual(archive.record_pull(self.tmp, raw2, "T2", "r2"), 1)
        rows = _rows(self.pulls("2026-10"))
        self.assertEqual(len(rows), 9)
        last = rows[-1]
        self.assertEqual((last["panel_date"], last["ticker"], last["close"],
                          last["pull_id"]), ("2026-10-02", "B.NS", "999.5", "r2"))
        # and the revision is now the latest value: repeating writes nothing
        self.assertEqual(archive.record_pull(self.tmp, raw2, "T3", "r3"), 0)

    def test_nan_transitions_each_write_one_row(self):
        archive.record_pull(self.tmp, self.raw, "T1", "r1")
        raw2 = self.raw.copy()
        raw2.loc["2026-10-06", "A.NS"] = np.nan             # value -> NaN
        self.assertEqual(archive.record_pull(self.tmp, raw2, "T2", "r2"), 1)
        self.assertEqual(_rows(self.pulls("2026-10"))[-1]["close"], "")
        self.assertEqual(archive.record_pull(self.tmp, raw2, "T2b", "r2b"), 0)
        self.assertEqual(archive.record_pull(self.tmp, self.raw, "T3", "r3"), 1)  # NaN -> value
        self.assertEqual(_rows(self.pulls("2026-10"))[-1]["close"], "106.0")

    def test_missing_unwritable_dir_does_not_raise_through_safe(self):
        blocker = os.path.join(self.tmp, "afile")
        open(blocker, "w").close()
        bad = os.path.join(blocker, "state")               # parent is a file
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            res = archive.safe(archive.record_pull, bad, self.raw, "T", "r")
        self.assertIsNone(res)
        self.assertIn("[archive warning]", buf.getvalue())

    def test_empty_or_none_panel_writes_nothing(self):
        self.assertEqual(archive.record_pull(self.tmp, None, "T", "r"), 0)
        self.assertEqual(archive.record_pull(self.tmp, pd.DataFrame(), "T", "r"), 0)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "archive")))


class RunAndReport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="archive_run_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_record_run_appends_valid_sorted_lines_in_order(self):
        archive.record_run(self.tmp, {"ts_utc": "2026-11-07T10:00:00Z", "z": 1, "a": 2})
        archive.record_run(self.tmp, {"ts_utc": "2026-11-08T10:00:00Z", "outcome": "skipped"})
        path = os.path.join(self.tmp, "archive", "runs", "2026-11.jsonl")
        lines = open(path).read().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], '{"a": 2, "ts_utc": "2026-11-07T10:00:00Z", "z": 1}')
        self.assertEqual(json.loads(lines[1])["outcome"], "skipped")

    def test_save_report_overwrites_same_day(self):
        archive.save_report(self.tmp, "first", "2026-11-08")
        archive.save_report(self.tmp, "second", "2026-11-08")
        archive.save_report(self.tmp, "other", "2026-11-15")
        d = os.path.join(self.tmp, "archive", "reports")
        self.assertEqual(open(os.path.join(d, "2026-11-08.txt")).read(), "second")
        self.assertEqual(sorted(os.listdir(d)), ["2026-11-08.txt", "2026-11-15.txt"])


N_HISTORY, N_NEW, SEED = 300, 6, 20261004


class FactoryMain(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self.tmp = tempfile.mkdtemp(prefix="archive_main_")
        os.chdir(self.tmp)
        os.makedirs("factory_state")
        self.f = _load_factory_copy(self.tmp)
        self.panel = make_panel(list(self.f.ALL_TICKERS), N_HISTORY, N_NEW, SEED,
                                benchmark=self.f.BENCHMARK)
        self._saved_agents = {k: sys.modules.pop(k) for k in list(sys.modules)
                              if k == "agents" or k.startswith("agents.")}
        sys.modules["agents"] = None          # report() advisory layer stays out
        self.archive_dir = os.path.join(self.tmp, "factory_state", "archive")

    def tearDown(self):
        os.chdir(self._cwd)
        sys.modules.pop("agents", None)
        sys.modules.update(self._saved_agents)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def feed(self, raw, filled=None):
        """fetch_prices stand-in that sets LAST_RAW like the real one does."""
        def fake():
            self.f.LAST_RAW = raw.copy()
            return (raw if filled is None else filled).copy()
        self.f.fetch_prices = fake

    def run_main(self, cmd):
        buf = io.StringIO()
        code = None
        with contextlib.redirect_stdout(buf):
            try:
                self.f.main(cmd)
            except SystemExit as e:
                code = e.code
        return code, buf.getvalue()

    def runs(self):
        out = []
        for p in sorted(glob.glob(os.path.join(self.archive_dir, "runs", "*.jsonl"))):
            out += [json.loads(line) for line in open(p).read().splitlines()]
        return out

    def test_recorded_then_skipped_and_pulls_written(self):
        p = self.panel.iloc[:N_HISTORY + 1]
        self.feed(p)
        code, out = self.run_main("update")
        self.assertIsNone(code)
        self.assertIn("Arena updated " + str(p.index[-1].date()), out)   # tee still prints
        r = self.runs()
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]["outcome"], "recorded")
        self.assertEqual(r[0]["recorded_date"], str(p.index[-1].date()))
        self.assertEqual(r[0]["cmd"], "update")
        self.assertEqual(r[0]["profile"], self.f.FACTORY_PROFILE)
        self.assertEqual(r[0]["n_tickers"], len(p.columns))
        self.assertEqual(r[0]["n_nan_last_row"], 0)
        self.assertEqual(len(r[0]["ledger_sha256"]), 64)
        self.assertIn("python", r[0]["versions"])
        pulls = glob.glob(os.path.join(self.archive_dir, "pulls", "*.csv"))
        self.assertTrue(pulls)
        self.assertEqual(sum(len(_rows(x)) for x in pulls), 6 * len(p.columns))
        # same panel again: skipped, run logged, no new pull rows
        code, out = self.run_main("update")
        self.assertIn("Arena update SKIPPED", out)
        r = self.runs()
        self.assertEqual([x["outcome"] for x in r], ["recorded", "skipped"])
        self.assertEqual(sum(len(_rows(x)) for x in pulls), 6 * len(p.columns))

    def test_phantom_last_row_records_phantom_date(self):
        p = self.panel.iloc[:N_HISTORY + 2].copy()
        nse = [t for t in p.columns if t not in self.f.MACRO_PROXIES]
        raw = p.copy()
        raw.iloc[-1, [raw.columns.get_loc(t) for t in nse]] = float("nan")
        self.feed(raw, filled=raw.ffill())
        code, out = self.run_main("update")
        self.assertIsNone(code)
        r = self.runs()[0]
        self.assertEqual(r["phantom_skipped_date"], str(p.index[-1].date()))
        self.assertEqual(r["outcome"], "recorded")
        self.assertEqual(r["recorded_date"], str(p.index[-2].date()))
        self.assertEqual(r["n_nan_last_row"], len(nse))

    def test_empty_download_logs_failed_and_still_exits_1(self):
        self.feed(pd.DataFrame())
        code, out = self.run_main("update")
        self.assertEqual(code, 1)
        self.assertIn("price download returned no usable rows", out)
        r = self.runs()
        self.assertEqual([x["outcome"] for x in r], ["failed"])
        self.assertFalse(glob.glob(os.path.join(self.archive_dir, "pulls", "*")))

    def test_kill_switch_writes_nothing_under_archive(self):
        with open(os.path.join("factory_state", "KILL"), "w") as fh:
            fh.write("test stop")
        called = []
        self.f.fetch_prices = lambda: called.append(1)
        code, out = self.run_main("update")
        self.assertIn("KILL SWITCH ACTIVE", out)
        self.assertEqual(called, [])
        self.assertFalse(os.path.exists(self.archive_dir))
        code, out = self.run_main("report")
        self.assertFalse(os.path.exists(self.archive_dir))

    def test_report_text_is_saved(self):
        for n in (1, 2, 3):
            self.feed(self.panel.iloc[:N_HISTORY + n])
            self.run_main("update")
        code, out = self.run_main("report")
        self.assertIsNone(code)
        files = glob.glob(os.path.join(self.archive_dir, "reports", "*.txt"))
        self.assertEqual(len(files), 1)
        self.assertEqual(open(files[0]).read(), out)
        self.assertEqual(self.runs()[-1]["outcome"], "reported")
        self.assertEqual(self.runs()[-1]["cmd"], "report")

    def test_archive_failure_never_changes_exit_code_or_output(self):
        self.feed(pd.DataFrame())
        mod = sys.modules["archive"]
        orig = mod.record_run
        mod.record_run = lambda *a, **k: 1 / 0
        try:
            code, out = self.run_main("update")
        finally:
            mod.record_run = orig
        self.assertEqual(code, 1)
        self.assertIn("[archive warning]", out)

    def test_exception_is_logged_and_reraised(self):
        def boom():
            raise ValueError("x")
        self.f.update = boom
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(ValueError):
                self.f.main("update")
        self.assertEqual(self.runs()[0]["outcome"], "error:ValueError")

    def test_ledger_identical_with_and_without_wrapper(self):
        def run(use_main):
            tmp = tempfile.mkdtemp(prefix="archive_cmp_")
            os.chdir(tmp)
            os.makedirs("factory_state")
            f = _load_factory_copy(tmp)
            random.seed(SEED)
            np.random.seed(SEED)
            for n in (1, 2, 3):
                p = self.panel.iloc[:N_HISTORY + n]
                f.fetch_prices = lambda p=p: p.copy()
                with contextlib.redirect_stdout(io.StringIO()):
                    (f.main if use_main else (lambda c: f.update()))("update")
            data = open(os.path.join(tmp, "factory_state", "ledger.json"), "rb").read()
            os.chdir(self.tmp)
            shutil.rmtree(tmp, ignore_errors=True)
            return data
        self.assertEqual(run(True), run(False))


if __name__ == "__main__":
    unittest.main()
