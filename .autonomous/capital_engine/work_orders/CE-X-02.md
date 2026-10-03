# CE-X-02 — Broker adapter (read-only reconciliation first) — GATED

**Status:** BLOCKED on Het's explicit authorization (`00_DESIGN.md` §8, item BROKER) AND on CE-4-03 (contract) AND on CE-4-01 showing at least one class at AMBER (G1+G2 met).
**Order of build when authorised:** (1) read-only: holdings/positions/cash via the chosen NSE broker API, reconciled nightly against the ledger, mismatches → KILL + NEEDS HET; (2) paper adapter parity tests; (3) order placement for ONE class, ONE contestant, at `LADDER[1]`, with per-order and per-day limits, only after a fresh `AUTHORIZE REAL CAPITAL …` line (CE-4-01 G4).
**Secrets:** via LucyOS scoped store only (`PJ_strategy-factory__…`); never in this repo.
**Venue choice:** from R2 §4 — prefer a broker with a free API and a sandbox; record the decision with date in `00_DESIGN.md` §7 before coding.
