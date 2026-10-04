"""CE-4-01: capital activation gates (synthetic temp trees; no network, read-only)."""
import datetime
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from portfolio import gates as G  # noqa: E402

LADDER = [0, 25_000, 50_000, 100_000, 200_000]
TODAY = datetime.date(2026, 10, 10)
AUTH_A = "- 2026-10-09 | Het: AUTHORIZE REAL CAPITAL A strat_a 25000 | **GRANTED**\n"
AUTH_B = "- 2026-10-09 | Het: AUTHORIZE REAL CAPITAL B strat_b 25000 | **GRANTED**\n"


def contestant(rung=0, days=0, retired=False):
    return dict(rung=rung, days_on_rung=days, retired=retired, equity=1.0, peak=1.0,
                history=[["2026-01-01", 0.0, 1.0]])


def write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)


def ledger(**con):
    return json.dumps(dict(registry={k: {} for k in con}, contestants=con))


def make_tree(root, directives=AUTH_A + AUTH_B):
    """Everything passes for A and B (and C, which must stay RED regardless)."""
    write(root, "profiles/equity_nse.json", json.dumps({"class": "A2"}))
    write(root, "profiles/crypto.json", json.dumps({"class": "B"}))
    write(root, "factory_state/ledger.json", ledger(strat_a=contestant(4, 130)))
    write(root, "factory_state/crypto/ledger.json", ledger(strat_b=contestant(1, 130)))
    write(root, "docs/capital_engine/validation/A_strat_a_2026-10-08.md", "validated 2026-10-08")
    write(root, "docs/capital_engine/validation/B_strat_b_2026-10-08.md", "validated 2026-10-08")
    write(root, "docs/capital_engine/EXECUTION_ADAPTER_CONTRACT.md", "contract")
    write(root, "factory.py", "def kill_switch_active(global_only=False):\n    return None\n")
    write(root, ".autonomous/het_directives.md",
          "# directives\n\n- 2026-08-24 | old | DONE\n" + directives
          + "\n## NEEDS HET (carry)\n\n- 2026-10-04 | AUTHORIZE REAL CAPITAL A strat_a 25000 (pending)\n")


def run(root):
    return G.evaluate(root, ladder=LADDER, min_days=126, today=TODAY)


class GatesBase(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = self._td.name
        make_tree(self.root)

    def tearDown(self):
        self._td.cleanup()

    def verdict(self, letter="A"):
        return run(self.root)[letter]


class TestEachGateFlips(GatesBase):
    def test_baseline_all_green(self):
        for letter in "AB":
            r = self.verdict(letter)
            self.assertEqual(r["verdict"], "GREEN", r)
            self.assertTrue(all(s == "GREEN" for s, _ in r["gates"].values()), r["gates"])

    def test_g1_flips(self):
        write(self.root, "factory_state/ledger.json", ledger(strat_a=contestant(4, 125)))
        r = self.verdict()
        self.assertEqual(r["gates"]["G1"][0], "RED")
        self.assertIn("125d", r["gates"]["G1"][1])
        self.assertEqual(r["verdict"], "RED")
        for g in ("G2", "G3", "G4", "G5"):
            self.assertEqual(r["gates"][g][0], "GREEN")
        write(self.root, "factory_state/ledger.json", ledger(strat_a=contestant(0, 300)))
        self.assertIn("zero promotions", self.verdict()["gates"]["G1"][1])

    def test_g1_ignores_retired_and_permanent(self):
        led = dict(registry={"bench": {"permanent": True}, "dead": {}},
                   contestants={"bench": contestant(2, 500), "dead": contestant(2, 500, True)})
        write(self.root, "factory_state/ledger.json", json.dumps(led))
        self.assertEqual(self.verdict()["gates"]["G1"][0], "RED")

    def test_g2_flips(self):
        os.remove(os.path.join(self.root, "docs/capital_engine/validation/A_strat_a_2026-10-08.md"))
        r = self.verdict()
        self.assertEqual(r["gates"]["G2"][0], "RED")
        self.assertEqual(r["verdict"], "RED")
        self.assertEqual(self.verdict("B")["gates"]["G2"][0], "GREEN")  # per class
        write(self.root, "docs/capital_engine/validation/A_x.md", "no date here")
        self.assertIn("names a date", self.verdict()["gates"]["G2"][1])
        write(self.root, "docs/capital_engine/validation/A_x.md", "checked on 2026-10-01")
        self.assertEqual(self.verdict()["gates"]["G2"][0], "GREEN")

    def test_g3_flips_on_ceiling(self):
        # B is 25k of 225k = 11% (green); with no A capital B would be 100% > 30%
        self.assertEqual(self.verdict("B")["gates"]["G3"][0], "GREEN")
        write(self.root, "factory_state/ledger.json", ledger(strat_a=contestant(0, 0)))
        r = self.verdict("B")
        self.assertEqual(r["gates"]["G3"][0], "RED")
        self.assertIn("ceiling 30%", r["gates"]["G3"][1])
        self.assertEqual(r["verdict"], "RED")

    def test_g3_flips_on_aggregator_problem(self):
        write(self.root, "factory_state/ledger.json", "{ not json")
        self.assertEqual(self.verdict()["gates"]["G3"][0], "RED")

    def test_g3_flips_on_kill_rule(self):
        orig = G.agg.aggregate

        def tripped(root, ladder):
            view = orig(root, ladder)
            view["drawdown_rules"]["kill_tripped"] = True
            return view
        G.agg.aggregate = tripped
        try:
            r = self.verdict()
        finally:
            G.agg.aggregate = orig
        self.assertEqual(r["gates"]["G3"][0], "RED")
        self.assertIn("kill rule tripped", r["gates"]["G3"][1])

    def test_g4_flips_amber_never_red(self):
        write(self.root, ".autonomous/het_directives.md", "# d\n\n- 2026-08-24 | nothing\n")
        r = self.verdict()
        self.assertEqual(r["gates"]["G4"][0], "AMBER")
        self.assertEqual(r["verdict"], "AMBER")
        self.assertIn("all met except G4", r["reason"])

    def test_g4_is_per_class(self):
        write(self.root, ".autonomous/het_directives.md", "# d\n\n" + AUTH_A)
        self.assertEqual(self.verdict("A")["gates"]["G4"][0], "GREEN")
        self.assertEqual(self.verdict("B")["gates"]["G4"][0], "AMBER")

    def test_g5_flips(self):
        os.remove(os.path.join(self.root, "docs/capital_engine/EXECUTION_ADAPTER_CONTRACT.md"))
        r = self.verdict()
        self.assertEqual(r["gates"]["G5"][0], "RED")
        self.assertIn("EXECUTION_ADAPTER_CONTRACT", r["gates"]["G5"][1])
        write(self.root, "docs/capital_engine/EXECUTION_ADAPTER_CONTRACT.md", "c")
        write(self.root, "factory.py", "x = 1\n")
        r = self.verdict()
        self.assertEqual(r["gates"]["G5"][0], "RED")
        self.assertIn("kill_switch_active", r["gates"]["G5"][1])


class TestG4Regex(GatesBase):
    def g4(self, text):
        write(self.root, ".autonomous/het_directives.md", "# d\n\n" + text)
        return self.verdict()["gates"]["G4"][0]

    def test_real_dated_line_accepted(self):
        self.assertEqual(self.g4(AUTH_A), "GREEN")
        hit = G.find_authorization(self.root, "A", TODAY)
        self.assertEqual(hit, ("2026-10-09", "strat_a", 25000))

    def test_strikethrough_ignored(self):
        self.assertEqual(self.g4("- 2026-10-09 | ~~AUTHORIZE REAL CAPITAL A strat_a 25000~~ withdrawn\n"),
                         "AMBER")

    def test_needs_het_section_ignored(self):
        self.assertEqual(self.g4("## NEEDS HET\n\n" + AUTH_A), "AMBER")
        # a later heading ends the NEEDS HET section
        self.assertEqual(self.g4("## NEEDS HET\n\n## Log\n\n" + AUTH_A), "GREEN")

    def test_quoted_example_ignored(self):
        self.assertEqual(self.g4("- 2026-10-09 | format is `AUTHORIZE REAL CAPITAL A strat_a 25000`\n"), "AMBER")
        self.assertEqual(self.g4("- 2026-10-09 | for example AUTHORIZE REAL CAPITAL A strat_a 25000\n"), "AMBER")

    def test_undated_placeholder_future_and_wrong_class_ignored(self):
        self.assertEqual(self.g4("AUTHORIZE REAL CAPITAL A strat_a 25000\n"), "AMBER")
        self.assertEqual(self.g4("- AUTHORIZE REAL CAPITAL A strat_a 25000\n"), "AMBER")
        self.assertEqual(self.g4("- 2026-10-09 | AUTHORIZE REAL CAPITAL <class> <contestant> <amount>\n"), "AMBER")
        self.assertEqual(self.g4("- 2027-01-01 | AUTHORIZE REAL CAPITAL A strat_a 25000\n"), "AMBER")
        self.assertEqual(self.g4("- 2026-10-09 | AUTHORIZE REAL CAPITAL B strat_a 25000\n"), "AMBER")
        self.assertEqual(self.g4("- 2026-10-09 | AUTHORIZE REAL CAPITAL A strat_a lots\n"), "AMBER")


class TestClassC(GatesBase):
    def test_c_always_red_even_if_everything_passes(self):
        write(self.root, "profiles/deriv.json", json.dumps({"class": "C"}))
        write(self.root, "factory_state/deriv/ledger.json", ledger(c1=contestant(1, 200)))
        write(self.root, "docs/capital_engine/validation/C_c1_2026-10-08.md", "2026-10-08")
        write(self.root, ".autonomous/het_directives.md",
              "# d\n\n" + AUTH_A + "- 2026-10-09 | AUTHORIZE REAL CAPITAL C c1 25000\n")
        r = self.verdict("C")
        self.assertTrue(all(s == "GREEN" for s, _ in r["gates"].values()), r["gates"])
        self.assertEqual(r["verdict"], "RED")
        self.assertIn("no derivatives logic exists and none is authorized", r["reason"])
        self.assertIn("design section 8 A4", r["reason"])


class TestReport(GatesBase):
    def test_summary_and_format(self):
        res = run(self.root)
        lines = G.summary_lines(res)
        self.assertEqual(set(lines), {"A", "B", "C"})
        self.assertTrue(lines["A"].startswith("GREEN"))
        self.assertTrue(lines["C"].startswith("RED"))
        text = G.format_report(res)
        for g in ("G1", "G2", "G3", "G4", "G5", "Class C: RED"):
            self.assertIn(g, text)

    def test_empty_tree_does_not_raise(self):
        with tempfile.TemporaryDirectory() as td:
            os.makedirs(os.path.join(td, "profiles"))
            res = G.evaluate(td, ladder=LADDER, min_days=126, today=TODAY)
        self.assertTrue(all(r["verdict"] == "RED" for r in res.values()))


if __name__ == "__main__":
    unittest.main()
