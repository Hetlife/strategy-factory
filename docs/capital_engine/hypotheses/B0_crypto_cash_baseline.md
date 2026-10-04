# B0 — Class B baseline: cash (written 2026-10-04, before any crypto data was touched)

**Hypothesis:** holding INR cash earns the overnight rate (~5.25% repo, R2 §7)
with zero drawdown, zero tax drag from trading, and zero TDS. Any class-B
contestant that cannot beat this *post-tax* has no reason to exist.

**Rules:** `sig_cash` returns weight 0.0 for every ticker, always. Permanent
registry entry `crypto_cash_baseline` (`permanent: True`, excluded from
PROMOTE/DEMOTE/evolution/breeding exactly like `nifty_benchmark`). Its equity
curve accrues the profile's `cash_rate` (set to the RBI repo rate at profile
creation, updated only by a dated commit, never by data).

**Role:** second benchmark for class B. A contestant promotes only if it beats
BOTH `crypto_btc_benchmark` (see B1 §4) AND this, on the date-paired
excess-return gate, post-tax.

**Falsification:** none — a baseline is not a claim.
