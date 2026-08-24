EXECUTION PLAN — STRATEGY FACTORY
=======================================================
Condensed operating reference. Derived from mission_document.txt
(v1.0), pivot_document.txt, and understanding.txt — all dated
2026-08-24, all ~55KB combined.

PURPOSE: let any session (human or AI) act correctly on this project
without re-reading or re-deriving the three source documents each
time. Read this file first. Open a source document only when you need
detail this file compresses away, or to resolve a conflict — if this
file and a source ever disagree, the source wins; flag the conflict
and fix this file, don't silently trust the summary.

Operator: Het (SevaaConnect Solutions Pvt Ltd, Surat). Capital: Rs
2,00,000. Real money deployed to date: Rs 0.

Tax/legal figures throughout inherit the source docs' own caveat:
approximately right as of the knowledge cutoff, MUST be verified with
a practising CA before any money moves. This file condenses the
operator's own analysis; it is not independent financial or legal
advice.


==========================================================
1. MISSION, ONE LINE
==========================================================
Build a closed loop where a validated trading edge on Rs 2,00,000
generates profit that funds progressively better infrastructure, each
stage gated on evidence, not enthusiasm. Success = live results
CONSISTENT with what paper trading predicted, sustained long enough to
be statistically meaningful. Profit is a consequence of that
consistency, not the goal itself.

Explicitly in scope for LATER phases, not now: changing asset class
(Section 9 covers the current evaluation), changing market, operating
from outside India, and monetising the system itself (Section 9,
growth-lever 4). The middle two aren't elaborated beyond this mention
anywhere in the source docs — noted here so they aren't dismissed by
default, not because a plan for them exists yet.


==========================================================
2. SETTLED FACTS — DO NOT RE-DERIVE, DO NOT RE-ARGUE
==========================================================
 1. Data-mined signal detection fails at retail data volumes.
    Hypotheses must come from a stated real-world mechanism, tested
    once — never discovered by scanning.
 2. Costs dominate above ~10-15 round trips/year (a correctly
    specified strategy lost ~5.5%/yr to friction at 30 round
    trips/year against a 0.38% modelled round-trip cost).
 3. Correlation-only strategies with no fundamental mechanism collapse
    out-of-sample. Event-lag drift is the only family that survived a
    simulated regime break in both training and holdout.
 4. Leverage multiplies volatility, not skill. 10x on an 18%/yr edge:
    MEDIAN outcome is losing 80%, 54.5% of accounts wiped out. Never
    assume leverage — it must be earned from measured live drawdown.
 5. HFT/latency arbitrage is closed to retail (co-location, crores of
    infrastructure). Do not pursue.
 6. Flat-percentage cost models are wrong below ~Rs 25,000/position.
    True round-trip cost = 0.222% of position + Rs 15.34 fixed (DP
    charge/scrip). factory.py's COST_PER_SIDE=0.0019 (0.38% RT)
    understates cost by up to ~3x at small position sizes. Live
    defect.
 7. Holding >12 months changes tax from 20% STCG to 12.5% LTCG AND
    unlocks a Rs 1.25L/yr exemption. On a Rs 2L account that exemption
    alone can zero out an entire year's tax — a bigger, more certain
    lever than most strategy improvements. Design should bias toward
    long-hold, low-turnover positions; cost (Fact 2) and tax both push
    the same direction.
 8. At small capital, CONTRIBUTION RATE > RETURN RATE. Rs 2L @ 18% net
    for 10yr = Rs 10.5L. Same + Rs 50,000/yr contribution = Rs 22.2L.
    Chasing 18%->25% is harder, riskier, and worth less than feeding
    the account.
 9. Compute is not the bottleneck. Current stack: Rs 0/month, ~90 of
    2,000 free GitHub Actions minutes used (22x headroom). This
    workload is a few minutes of pandas per day.
10. CURRENT EVIDENCE: 35 days live paper history, 20 contestants (1
    retired), equity range 0.876-1.011 (-12.4% to +1.1%). ZERO
    promotions. This is noise, not evidence — nothing proven yet.
11. Pure trading returns on Rs 2L do not reach "large sum" on any
    acceptable timescale (18% net ~= 23.6yr to Rs 1Cr; even 35% net —
    essentially unheard of at retail scale without leverage — still
    takes ~13yr). See Section 9 for the actual growth-lever priority.


==========================================================
3. PHASE 0 — IMMEDIATE QUEUE
   (do these before any capital and before any further feature work;
   gate to Phase 1 = all 4 done AND tested)
==========================================================
Each item may be drafted, implemented, and tested on a branch
autonomously. NONE may be merged to main without Het's FRESH, EXPLICIT,
IN-SESSION authorization — a prior session's approval does not carry
forward, and COST_PER_SIDE is protected exactly like RULES/LADDER even
though this particular change is a correctness fix, not a
risk-appetite change (it alters every historical verdict).

[ ] P0-1  SIZE-AWARE COST MODEL
      Replace flat COST_PER_SIDE with:
        round_trip_cost_pct(position_size_rupees)
          = 0.222 + (1534 / position_size_rupees)
      (0.222 = variable STT+exchange txn+stamp+GST component, as a %
      of position; 1534/position = the Rs 15.34 fixed DP charge
      expressed as a percentage. Verify how this splits across
      factory.py's existing per-side charging structure so the two
      pieces sum to this round-trip figure — don't just halve it
      naively, since the DP charge is a sell-day-only fixed charge,
      not a per-side one.)
      Acceptance: a 6-name rung-1 basket (Rs 10,000 / 6 ~= Rs
      1,667/name) must price at ~1.1-1.15% RT, not 0.38%.
      Then: re-run every existing verdict against the corrected model
      and report what changes (= Q1, Section 8).

[ ] P0-2  POST-TAX EXPECTANCY METRIC
      Add as a first-class ranking metric next to Sharpe:
        holding <= 12 months -> STCG 20%
        holding  > 12 months -> LTCG 12.5%, minus Rs 1.25L/yr exemption
      Exemption is annual and account-wide, not per-strategy — confirm
      the aggregation approach before this feeds any promotion logic.
      Surface per-contestant in report() output.

[ ] P0-3  NIFTY BUY-AND-HOLD BENCHMARK CONTESTANT
      Add a permanent, unkillable buy-and-hold Nifty contestant to the
      same ledger and daily cycle as every other contestant. It must
      never be eligible for demotion, retirement, or evolution — it
      exists only as the bar everything else has to clear.

[ ] P0-4  FALSIFICATION CRITERIA — COMMIT AS WRITTEN
      Content is Section 5 below, already written. Commit it to the
      repo verbatim and dated, before more live data accrues, so it
      can't later be loosened to fit whatever the data shows. This
      step is satisfied in substance by this file existing; copy
      Section 5 into its own tracked file too if that fits the repo
      layout better.

Once all 4 are done and tested: STOP. Do not start new feature work.
Move to Section 4.


==========================================================
4. PHASE 1 — STANDING MODE
   (default state once Phase 0 clears; ~12 months minimum, Rs 0 at
   risk; this is where most sessions will find the project)
==========================================================
DO, every scheduled run:
  - Let weekday update() and Sunday report() execute unmodified.
  - Log any bug found/fixed tersely, one line: what broke, what fixed
    (pattern already established — see Section 10).
  - Track each contestant's accumulated days-in-market toward the
    126-day RULES threshold (Section 5a).

DO NOT, during Phase 1:
  - Add strategy families, evolution mechanisms, or advisors. Three
    breeding mechanisms already sit on top of 35 days of noise; more
    machinery is more surface for a short sample to overfit against.
  - Touch RULES, LADDER, or COST_PER_SIDE without fresh explicit
    in-session authorization.
  - Merge or push to main without fresh explicit in-session
    authorization.
  - Treat any contestant's result as validated before it has >=126
    days on its current rung.
  - Present synthetic/simulated output as live, or claim a test ran
    against real market data when it did not.
  - Enable real-money execution. Funding a rung is always a deliberate
    human action, never automatic.

PENDING OPERATOR DECISION (flagged, not resolved — wait for Het):
  - LADDER rung 1 (Rs 10,000) is economically incoherent for a 6-name
    basket strategy (~1.14% RT friction vs. 0.38% modelled). Two
    options on the table: raise rung 1, or restrict rung-1 strategies
    to 1-2 names. Both are LADDER changes -> Het's explicit call only.


==========================================================
5. FALSIFICATION / KILL CONDITIONS
   (written now, before more data arrives, so they can't be
   rationalised away later — this is Phase 0 Step 4's content)
==========================================================
Stop, or fundamentally restructure, if:
 a. After 12 months of live paper trading, no strategy clears the
    RULES bar: 126 days on rung, >=10 trades, >=0.05%/day expectancy,
    Sharpe >=0.4, drawdown better than -12%.
 b. After 12 months, the best contestant fails to beat Nifty
    buy-and-hold net of the corrected size-aware cost model and
    applicable tax. -> Correct action: buy the index, redirect the
    effort. This is a SUCCESSFUL outcome for an evidence machine, not
    a failure.
 c. Promoted strategies systematically underperform their paper
    results once real costs apply. -> The whole promotion methodology
    is invalid, not just one strategy.
 d. Advisor trust_weight decays to its floor (0.05) -> advisor-evolved
    children consistently fail to beat the parents they replaced.
 e. Real drawdown exceeds the modelled maximum by a wide margin -> the
    risk model is wrong in the dangerous direction.
 f. Het, or any session, starts wanting to change RULES, LADDER, or
    COST_PER_SIDE specifically to make results look better. -> That
    impulse is itself the most reliable signal the edge isn't real.


==========================================================
6. GATES
==========================================================
PHASE GATES:
  0->1  4 Phase-0 deliverables (Section 3) done and tested.
  1->2  >=1 strategy clears the RULES bar AND beats Nifty net of
        corrected cost+tax. (A clean "no" here, per 5b, is a valid,
        successful outcome — not a failure to go fix.)
  2->3  6 months of live results CONSISTENT with the paper results
        that preceded them. Consistency is the gate, not profit —
        profit for reasons the paper model didn't predict is luck.
  3->4  G3 infra gate (Rs 25L) reached with track record intact.

CAPITAL DEPLOYMENT RULE (Phase 2+): at most 1-3 strategies get real
money, never the full contestant pool. Every real position >= Rs
25,000 (below that, the fixed DP charge reproduces Fact 6's problem).

INFRASTRUCTURE SPEND GATES (ceiling ~10% of expected annual net profit
at 18% net. CURRENT STATE: G0, spend Rs 0 — do not cross early):

  Gate Capital   Ann.profit  Ceiling/mo  Unlocks
  G0   Rs 2 L    Rs 36,000   Rs 300      Free tier only. SPEND NOTHING.
  G1   Rs 5 L    Rs 90,000   Rs 750      Small VPS, only if a real
                                         need is proven first.
  G2   Rs 10 L   Rs 1.80 L   Rs 1,500    Paid data feed OR VPS, not
                                         both.
  G3   Rs 25 L   Rs 4.50 L   Rs 3,750    Real cloud infra becomes
                                         rational.
  G4   Rs 50 L   Rs 9.00 L   Rs 7,500    Redundancy, managed data,
                                         research compute.
  G5   Rs 1 Cr   Rs 18.0 L   Rs 15,000   Dedicated hardware/colo, only
                                         if latency is PROVEN binding
                                         (per Fact 5, it isn't).


==========================================================
7. HARD GUARDRAILS (permanent, not phase-dependent)
==========================================================
THE THREE LAWS:
  1. Hypotheses are written before testing — never mined from data.
  2. Live strategies are never mutated — only replaced via bred
     children starting at rung 0.
  3. Capital is earned through the ladder, never granted.

NEVER, without Het's fresh explicit in-session instruction:
  - Change RULES, LADDER, or COST_PER_SIDE.
  - Add options, futures, margin, or leverage logic.
  - Add or modify broker/execution/API-key code.
  - Enable real-money execution.
  - Merge, push, or force-push to main.

BRIGHT LINES (never, full stop — no gain on Rs 2L is worth these):
  - Non-disclosure of foreign assets (ITR Schedule FA) if ever holding
    US/foreign equities.
  - Offshore forex/binary-options platforms as an India resident.
  - Structuring remittances to circumvent LRS limits.
  - Under-reporting crypto gains (1% TDS already gives the tax
    department the transaction record — nothing to hide behind).
  - Trading on material non-public information.
  - Spoofing, layering, wash trading, circular trading.
  - Using another person's PAN, demat, or bank account.
  - Presenting a paper track record as a live one, to anyone, ever.


==========================================================
8. RESEARCH BACKLOG — Q1-Q10, RANKED (answer with arithmetic)
==========================================================
 Q1  Correct size-aware cost function + effect on every existing
     verdict once applied retroactively.               [= P0-1]
 Q2  Post-tax expectancy per strategy family; which families change
     rank once tax is included.                          [= P0-2]
 Q3  Minimum viable position size per strategy family; implication for
     LADDER rung 1.
 Q4  Does ANY contestant currently beat Nifty net of corrected
     cost+tax? (Honest expected answer today: insufficient data.)
 Q5  At what N (sample size / calendar date) does the tournament's
     ranking become statistically distinguishable from noise?
 Q6  Does the 3-mechanism evolution system (spawn/advisor/crossover)
     increase overfitting risk vs. a simpler design at this sample
     size? Should any mechanism be disabled during Phase 1?
 Q7  Realistic capacity ceiling per strategy family before market
     impact matters. (Expected: far above anything this project
     reaches — confirm, then stop worrying about it.)
 Q8  Full 10-year closed-loop model: contributions, returns, tax,
     infra spend per gate, terminal value, sensitivity per input.
     (Prediction to verify/refute: contribution rate dominates —
     Fact 8.)
 Q9  Current, verified SEBI requirements for RIA / RA / PMS / AIF Cat
     III (Section 9, Route C — track-record monetisation).
 Q10 Single highest-value change right now — and whether it's a code
     change at all. (Live candidate answer: no, it's to wait.)


==========================================================
9. STRATEGIC DECISIONS ALREADY MADE — DO NOT RELITIGATE
==========================================================
ASSET CLASS: stay on Indian equity delivery through Phase 1-3.
  F&O          -> rejected. ~93% of individual F&O traders lose money
                  (SEBI study, FY22-24); one Nifty lot needs ~Rs
                  1.5-2L margin — the entire capital base in one
                  undiversified, unbuffered bet.
  Crypto       -> rejected. 30% flat tax, NO loss set-off, 1% TDS on
                  every transfer — structurally hostile to any
                  strategy with meaningful turnover.
  US equities  -> solves the fixed-cost problem permanently
  (via LRS)       (fractional shares) but abandons the one domain edge
                  claimed (Indian cement/infra/steel). Candidate ONLY
                  as a Phase-4 scaling venue, only if a real edge is
                  proven first. Schedule FA disclosure mandatory if
                  ever used.
  Nifty ETF    -> not a fallback, it's the bar. If nothing beats it
                  after 12 months of honest paper trading net of real
                  cost+tax, buying the index IS the correct answer.
  Entity structuring (LLP/Pvt Ltd), GIFT City IFSC -> not relevant
  below G4. Revisit only then.

GROWTH-LEVER PRIORITY (highest expectancy first — per Fact 8, 11):
  1. Contribution rate — dominates at this capital size. (Route A)
  2. Time / survival — most retail algo projects die from a blown
     account or abandonment, not insufficient cleverness. The Three
     Laws are the project's best protection for this; keep them.
     (Route B)
  3. The trading edge itself — necessary, but not sufficient alone on
     Rs 2L on any acceptable timescale.
  4. Monetise the TRACK RECORD, not the returns, via a SEBI-registered
     RIA / RA / PMS / AIF Cat III once genuinely proven (Phase 4+
     only). Prerequisite is identical across all four: an auditable,
     honest, multi-year track record — which Phase 1-3 exist to
     produce. (Route C)

RECURRING / CALENDAR-TRIGGERED (every financial year — easy to drop
because it isn't a code task, but costs real money if missed):
  - Harvest the Rs 1.25L/yr LTCG exemption. Unused, it does not carry
    forward.
  - Tax-loss harvest before 31 March.
  - File the ITR on time. Late filing forfeits the 8-year loss
    carry-forward.


==========================================================
10. BUILD-STATE QUICK REFERENCE (full detail: understanding.txt)
==========================================================
ENGINE  factory.py — update() runs daily (realises P&L from
  yesterday's positions against today's returns; no-lookahead ordering
  is verified correct, preserve in any refactor). report() runs
  Sunday (Sharpe, drawdown, PROMOTE/DEMOTE verdicts, ladder, breeding).
  Strategy families (sig_*): event_drift, momentum, input_cost,
  monsoon (dormant — needs an IMD rainfall CSV never sourced).

ADVISOR LAYER  advisors.py, monthly, writes parameter_bank.json. DOES
  NOT EXIST YET — advisor layer has never run against real data.

EVOLUTION (3 mechanisms, paper-tier only, real-money rungs excluded):
  spawn_neighbor  — rung>=2 contestants breed neighbour-parameter
                    children at rung 0. Original mechanism.
  advisor_evolve  — paper contestants ranked outside top 10 get
                    retired and replaced, parameters blended toward
                    the advisor bank by trust_weight (self-tunes
                    +/-0.05 per round based on whether children beat
                    the parents they replaced).
  crossover       — top-10 profitable paper contestants in the same
                    family+sector may mate. Additive (parents keep
                    their slot). Capped: MAX_CONTESTANTS=40,
                    BREEDING_MAX_NEW_PER_ROUND=3.

DASHBOARD  dashboard.py, Streamlit, read-only, sourced from GitHub raw
  URLs. Never a write path. Private-repo auth path is UNVERIFIED (only
  tested from inside the sandbox, which injects a token).

STATE  factory_state/{ledger.json, parameter_bank.json,
  advisor_state.json}. ledger.json is never hand-edited.
  PAPER_STARTING_CAPITAL=Rs 100,000/contestant — display only, does
  not affect real trading math or thresholds.

AUTOMATION  .github/workflows/{factory.yml, advisor_training.yml}.
  Rs 0/month. Both commit state to main.

SESSION INFRA  CLAUDE.md (binding rules, auto-loaded),
  .autonomous/state.json (machine state/queue),
  AUTONOMOUS_LOG.md (terse append-only log),
  AUTONOMOUS_TODO.md (narrative rationale). A scheduled Routine starts
  a fresh session every 5 hours from these files — this execution plan
  is meant to sit alongside them, not replace them.

OPEN ITEM  PR #1 unmerged, branch
  claude/scheduled-maintenance-template-d7yufr. Asked twice; standing
  answer is hold off. Same fresh-authorization rule as Section 7
  applies before it can merge.

KNOWN-FIXED BUGS (do not reintroduce): Sunday report cron pointed at a
  nonexistent schedule string; Sharpe variance floor produced absurd
  values (~106,512) on thin samples, could false-PROMOTE on no real
  evidence (now NaN below 20 days_in_market); cost_efficiency_advisor
  miscounted trades; backtest() silently swallowed strategy-function
  exceptions; paper-tier lineage lost on non-terminal demote;
  promotion-bred children had no lineage recorded; crossover child
  names chained unboundedly.


==========================================================
11. IF YOU ONLY DO ONE THING
==========================================================
Check whether Phase 0's 4 items (Section 3) are done. If not, that is
the entire task, in order, above any feature idea that seems good in
isolation. If they are done, the task is Section 4: run the schedule,
touch nothing structural, and let TIME accumulate real evidence. The
next genuinely valuable event here is the calendar, not a commit.
