"""CE-2-03: portfolio aggregator tests (synthetic ledgers; no network)."""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from portfolio import aggregate as agg  # noqa: E402

LADDER = [0, 25_000, 50_000, 100_000, 200_000]


def contestant(equities, rung=0, retired=False):
    hist = [[f"2026-01-{i + 1:02d}", 0.0, e] for i, e in enumerate(equities)]
    return dict(rung=rung, retired=retired, equity=equities[-1], peak=max(equities),
                history=hist)


def make_root(tmp, specs):
    """specs: {profile: (profile_json, ledger_or_None or raw str)}"""
    os.makedirs(os.path.join(tmp, "profiles"))
    os.makedirs(os.path.join(tmp, "factory_state"))
    for name, (prof, ledger) in specs.items():
        with open(os.path.join(tmp, "profiles", name + ".json"), "w") as fh:
            json.dump(prof, fh)
        if ledger is None:
            continue
        path = (os.path.join(tmp, "factory_state", "ledger.json") if name == "equity_nse"
                else os.path.join(tmp, "factory_state", name, "ledger.json"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(ledger if isinstance(ledger, str) else json.dumps(ledger))


def two_ledgers():
    a = dict(registry={"x": {}, "y": {}, "dead": {}, "nifty_benchmark": {"permanent": True}},
             contestants={"x": contestant([1.0, 1.02, 1.05, 1.03]),
                          "y": contestant([1.0, 0.99, 0.98, 0.97]),
                          "dead": contestant([1.0, 0.9], retired=True),
                          "nifty_benchmark": contestant([1.0, 1.5, 2.0, 3.0])})
    b = dict(registry={"c1": {}, "c2": {}},
             contestants={"c1": contestant([1.0, 1.10, 0.99, 1.0]),
                          "c2": contestant([1.0, 0.9, 0.8, 0.7])})
    return a, b


class TestAggregate(unittest.TestCase):
    def test_two_synthetic_profiles(self):
        a, b = two_ledgers()
        with tempfile.TemporaryDirectory() as tmp:
            make_root(tmp, {"equity_nse": ({"class": "A2", "enabled": True}, a),
                            "crypto_spot": ({"class": "B1", "trades_weekends": True,
                                             "enabled": True}, b),
                            "options": ({"class": "C1", "enabled": False}, None)})
            v = agg.aggregate(tmp, ladder=LADDER)
        rows = {p["profile"]: p for p in v["profiles"]}
        self.assertEqual(rows["equity_nse"]["paper_count"], 2)      # benchmark excluded
        self.assertEqual(rows["equity_nse"]["retired_count"], 1)
        self.assertEqual(rows["equity_nse"]["best_paper_name"], "x")
        self.assertAlmostEqual(rows["equity_nse"]["best_paper_equity"], 1.03)
        self.assertEqual(rows["crypto_spot"]["paper_count"], 2)
        self.assertEqual(rows["crypto_spot"]["real_exposure"], 0)
        self.assertEqual(rows["options"]["status"], "no ledger yet")
        self.assertEqual(v["total_real_exposure"], 0)
        self.assertEqual(v["classes"]["A"]["ceiling_text"], "no real capital (ceiling 50% max)")
        self.assertEqual(v["classes"]["B"]["ceiling_text"], "no real capital (ceiling 30% max)")
        self.assertEqual(v["classes"]["C"]["ceiling_text"], "no real capital (ceiling 20% max)")
        self.assertEqual(v["paper_view"]["classes_blended"], ["A", "B"])
        self.assertIn("PAPER VIEW", agg.format_table(v))
        # blend of x [1,1.02,1.05,1.03] and c1 [1,1.10,0.99,1.0]: means
        # 1.0, 1.06, 1.02, 1.015 -> peak 1.06, trough 1.015
        self.assertAlmostEqual(v["paper_view"]["max_drawdown"], 1.015 / 1.06 - 1, places=9)

    def test_ceiling_math_with_real_capital(self):
        a, b = two_ledgers()
        a["contestants"]["x"]["rung"] = 2   # Rs 50,000 in class A
        b["contestants"]["c1"]["rung"] = 1  # Rs 25,000 in class B
        with tempfile.TemporaryDirectory() as tmp:
            make_root(tmp, {"equity_nse": ({"class": "A2"}, a),
                            "crypto_spot": ({"class": "B1"}, b)})
            v = agg.aggregate(tmp, ladder=LADDER)
        self.assertEqual(v["total_real_exposure"], 75_000)
        self.assertAlmostEqual(v["classes"]["A"]["share_of_real"], 50 / 75)
        self.assertIn("[OVER CEILING]", v["classes"]["A"]["ceiling_text"])   # 66.7% > 50%
        self.assertIn("[OVER CEILING]", v["classes"]["B"]["ceiling_text"])   # 33.3% > 30%
        self.assertNotIn("OVER", v["classes"]["C"]["ceiling_text"])

    def test_drawdown_known_minus_10pct(self):
        self.assertAlmostEqual(agg.max_drawdown([1.0, 1.2, 1.08, 1.3, 1.25]), -0.10)
        self.assertEqual(agg.max_drawdown([1.0, 1.1, 1.2]), 0.0)
        c1 = {"d1": 1.0, "d2": 1.2, "d3": 1.08, "d4": 1.3}
        blended = agg.blend_curves([c1, dict(c1, d5=9.0)])   # d5 not common -> dropped
        self.assertEqual([d for d, _ in blended], ["d1", "d2", "d3", "d4"])
        self.assertAlmostEqual(agg.max_drawdown(v for _, v in blended), -0.10)

    def test_real_repo_equity_only(self):
        v = agg.aggregate()
        self.assertEqual(v["total_real_exposure"], 0)
        self.assertEqual(v["problems"], [])
        eq = [p for p in v["profiles"] if p["profile"] == "equity_nse"][0]
        self.assertEqual(eq["status"], "ok")
        self.assertEqual(eq["class"], "A2")
        self.assertFalse(v["drawdown_rules"]["kill_tripped"])
        agg.format_table(v)

    def test_malformed_ledger_reported_not_raised(self):
        a, _ = two_ledgers()
        with tempfile.TemporaryDirectory() as tmp:
            make_root(tmp, {"equity_nse": ({"class": "A2"}, a),
                            "crypto_spot": ({"class": "B1"}, "{not json"),
                            "options": ({"class": "C1"}, json.dumps({"registry": {}}))})
            v = agg.aggregate(tmp, ladder=LADDER)
        rows = {p["profile"]: p for p in v["profiles"]}
        self.assertEqual(rows["equity_nse"]["status"], "ok")
        self.assertEqual(rows["crypto_spot"]["status"], "ERROR")
        self.assertEqual(rows["options"]["status"], "ERROR")
        self.assertEqual(len(v["problems"]), 2)
        self.assertIn("PROBLEMS", agg.format_table(v))


if __name__ == "__main__":
    unittest.main()
