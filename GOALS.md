# GOALS — where this is going and when we'll know things

Single-purpose "north star" file. Read this to answer "what are we
actually trying to achieve, and when will we know if it's working" —
for the rules/facts/mechanics behind these goals, see `EXECUTION_PLAN.md`
(don't duplicate that content here, cross-reference it). For how Het
wants this communicated, see `.autonomous/operator_profile.md`.

**Any session, autonomous or interactive: read this after `state.json`,
before doing substantive work, to stay oriented on the actual point of
all this — not just the current task.**

---

## The one-sentence goal

Find out, honestly and rigorously, whether Het's domain knowledge
(construction/cement/infra/steel) produces a real, tradeable edge in
Indian equities — and if it does, grow a small amount of capital into a
large one over years, patiently, without ever lying to ourselves about
the evidence.

## What "done" looks like — Het's own words (2026-08-24)

Not primarily profit. Success is **Het becoming someone who can build
and reason about a system like this** — understanding *why* it works or
doesn't, not just trusting a black box. He's explicitly comfortable with
a 12-month wait and with "no edge found, buy an index instead" as a
legitimate, successful outcome. See `operator_profile.md` for the full
Q&A this came from — don't re-derive it, don't assume it's changed
without him saying so directly.

---

## Timeline — when we'll know things (not when we'll have money)

This is the honest version of a "projection." Dates are estimates for
milestones, not promises, and depend heavily on how consistently
sessions actually make progress — see the note on the autonomous loop's
reliability below, which is a live open problem as of this writing.

| Milestone | Estimated timing | What it actually tells us |
|---|---|---|
| Phase 0 complete (P0-1..P0-4 shipped + tested) | Days to ~2 weeks from 2026-08-24, IF sessions run productively | The measuring stick is honest. Nothing about whether an edge exists yet. |
| Phase 1 minimum evidence window | 12 months from Phase 0 completion (~mid-to-late 2027) | Whether ANY strategy clears the RULES bar AND beats a Nifty ETF net of real costs and tax. Could be yes, could be no — both are valid results. |
| Phase 2 gate (first real capital, if Phase 1 says yes) | No fixed date — contingent entirely on Phase 1's outcome | Whether live results match what paper trading predicted, over 6 more months. |
| Phase 3/4 (scaling, alternate venues, track-record monetization) | Years out, contingent on Phase 2 | Only relevant if everything before it actually worked. |

**The single most likely outcome, stated plainly:** most systematic
retail trading attempts do not find a durable edge. This project's own
research already found that SEBI's own study showed ~93% of individual
F&O traders lost money over FY22-24 (a different asset class, cited here
only as calibration for how hard this generally is, not as a direct
prediction for equity delivery). The honest base rate says: expect "no
edge found" to be a live possibility all the way through, not a remote
one. Planning around a validated edge as the default outcome would be
exactly the overconfidence Law 1 exists to prevent.

## Scenario math — IF an edge is eventually validated (not a forecast)

These numbers come from `pivot_document.txt`'s arithmetic. They answer
"if we get to a real number, what would it look like" — they are NOT a
prediction that any of these CAGRs will happen. As of today we have no
evidence supporting ANY particular return, including whether it's
positive.

Rs 2,00,000 starting capital, no further contributions:

| Net CAGR (if achieved) | Value at 5 yrs | Value at 10 yrs | Years to ₹1 crore |
|---|---|---|---|
| 12% (~Nifty long-run) | ₹3.52L | ₹6.21L | 34.5 |
| 18% (good, plausible if a real edge exists) | ₹4.57L | ₹10.47L | 23.6 |
| 25% (excellent-professional territory) | ₹6.10L | ₹18.63L | 17.5 |
| 35% (essentially unheard of at retail scale without leverage) | ₹8.97L | ₹40.24L | 13.0 |

With Rs 50,000/year added on top of an 18% CAGR: ₹22.2L at 10 years —
more than double the no-contribution case. This is why
`EXECUTION_PLAN.md` ranks contribution rate above chasing a higher CAGR:
it's the one lever that doesn't depend on an edge being real at all.

## Current status snapshot (update this section, don't let it go stale)

- **Phase:** 0 (instrumentation). See `state.json.current_phase`.
- **P0-1 (size-aware cost model):** done, commit `38dee23`.
- **P0-2/P0-3/P0-4:** open.
- **Live evidence so far:** ~35 days paper trading, zero promotions, no
  edge demonstrated. This number moves only once Phase 1 actually
  starts — Phase 0 work doesn't add evidence, it corrects the ruler.
- **Known open risk:** the scheduled autonomous Routine has fired
  multiple times without committing anything (see `next_session.md` for
  the live diagnosis). Until this is confirmed fixed, don't assume
  unattended overnight progress is happening — verify against
  `AUTONOMOUS_LOG.md`/`git log`, don't just trust that time passed.

---

## Why this file exists, specifically

Every session — including ones running unattended after a context reset,
with zero memory of any conversation — should be able to read this and
know: what we're actually trying to prove, roughly when we'll know it,
what the numbers would mean if things go well, and that "things go well"
is not the assumed default. `EXECUTION_PLAN.md` has the rules and gates;
this file has the *point* of following them.
