# NEXT SESSION

## READ FIRST
1. CLAUDE.md (auto-loaded — binding rules, architecture, phase pointer)
2. .autonomous/state.json (structured queue, decisions, test status)
3. This file
4. .autonomous/het_directives.md — Het's own recent asks + a standing
   "NEEDS HET" section; carry that section into any report back to him.
   **Also carries an active COST CONSTRAINT — read it before firing any
   new paid session/Routine.**
5. .autonomous/bug_log.md — known OPEN/FIXED defects, check before
   assuming something is broken
6. AUTONOMOUS_LOG.md (tail -30, don't read the whole thing)
7. .autonomous/operator_profile.md — before writing anything Het will
   read: plain language, why not just what, hands-off on code
8. EXECUTION_PLAN.md — only if you need the phase/gate detail this file
   compresses away

## ACTIVE CONSTRAINT — READ THIS FIRST, LITERALLY
**2026-08-25: Het asked to stop incurring extra cost and to be asked before
any further cost.** Still standing as of this rewrite. Practical rule:
**do NOT fire the autonomous dev-loop Routine, call
`create_session`/`create_trigger`/`fire_trigger`, or otherwise spin up a
new paid session without asking him first.** Normal work inside an
existing, already-running interactive session (edits, commits, git
operations, reading files, GitHub MCP calls) is fine.

## CURRENT STATE
**PR #1 IS MERGED** (merge commit `aa55914`, 2026-08-25). `main` now has
everything: P0-1..P0-3, agents/ team, advisor-informed evolution layer,
and the LADDER raise. This branch
(`claude/scheduled-maintenance-template-d7yufr`) is still where all
further work happens per this repo's git-development-branch requirement
— it still exists and tracks ahead of `main` for any new commits.

**Phase 1 = STANDING MODE** (EXECUTION_PLAN.md Section 4): run the daily
`update()` / weekly `report()` cycle (now via `factory.yml` against
`main` for real, since the merge), don't add new structural machinery,
let real evidence accumulate for ~12 months. The evidence clock starts
meaningfully from 2026-08-24 (when P0-1's cost fix landed), not earlier.

**LADDER is now `[0, 25_000, 50_000, 100_000, 200_000]`** (raised from
`[0, 10_000, 25_000, 50_000, 100_000]`, commit `6caf01c`) — Het gave
fresh explicit sign-off on the exact figures via AskUserQuestion, not
just the direction. Cuts rung-1's fixed-cost drag from ~1.14% to ~0.6%
round-trip on a 6-name basket.

**The 5-hourly autonomous dev-loop Routine (`trig_013GUxs9AwHaRvb1o4eGJRGx`)
is STILL BROKEN and STILL DISABLED — now 5 confirmed zero-commit
failures**, including a clone-first fix that had looked like the real
root cause. See "WHAT WAS LEARNED" below — do not assume this is close
to fixed just because a plausible-sounding theory was proposed once.

**The daily report Routine (`trig_01Y9q1Dn98ghLMD4KX7xZfxp`, 13:00 UTC,
push-notified) is unaffected and still running.**

A live status report for Het (redeployable, same URL) exists at:
https://claude.ai/code/artifact/c8ef2e56-3280-4141-b6fd-bc14c91333c1 —
keep it updated rather than making him read raw repo files. (Not
re-verified as current in this session — check before relying on it.)

## WHAT WAS DONE (2026-08-25, this session — a separate diagnostic
session from the primary interactive one, resumed hours after its
initial firing)
- Confirmed (again, cleanly) that a `create_session`-based session can
  commit/push where `create_trigger`-fired ones fail — the original
  point of this session's existence.
- Given fresh, in-session authorization by Het via `AskUserQuestion` on
  the two items that were genuinely blocked on him:
  - PR #1 → **merge**. Merged (`aa55914`).
  - LADDER → **`[0,25k,50k,100k,200k]`**. Implemented, tested (30
    synthetic `update()` cycles + `report()`, isolated copy, no crash),
    committed (`6caf01c`), pushed *before* the merge so it landed inside
    PR #1 rather than needing a second PR.
  - Along the way, fixed a real small bug: `report()`'s footer printed a
    hardcoded "Rs 10k / 25k / 50k / 1L" string that would have gone
    stale the moment LADDER changed. Now derives from `LADDER` directly.
- **Caught and corrected a stale claim in the tracking docs.** The docs
  (as of commit `03ec534`) described the Routine's clone-first fix as
  "proposed, untested, on hold pending Het's go-ahead." But
  `list_triggers` showed the Routine had actually already fired at
  **11:03 UTC** (by the primary interactive session, evidently without
  waiting for that go-ahead — not clear if Het separately authorized it
  in that session; worth asking him directly if it matters). Verified
  independently via `git fetch origin --prune` + `git log --all --grep`
  across every branch: **zero matching commits landed anywhere.** The
  fix failed too. Updated `state.json`/`bug_log.md`/`het_directives.md`
  to reflect this rather than let the optimistic "likely fixed" status
  stand uncorrected.

## WHAT WAS LEARNED
- **The repo-binding theory (create_trigger sessions lack git-repo
  binding) is real but was NOT the full explanation.** Even a Routine
  firing with an explicit, literal-first-step `git clone` +
  `git checkout` instruction still produced zero commits. Two
  structurally different fixes (retry-tuning, then explicit-clone) have
  now both failed the same way, which means the failure mode is
  something else — possibly something in how a Routine-fired session's
  container/permissions differ beyond just the repo binding, possibly
  something else entirely. Not yet known.
- **The real blocker to root-causing this further is tooling, not
  effort**: no tool available in this project exposes what a
  Routine-fired session's transcript/tool-calls actually did
  step-by-step. `get_session` gives only metadata (status, cost,
  duration). Guessing at prompt wording without that visibility has now
  failed 5 times.
- Multiple sessions have been working on this project somewhat in
  parallel today (a primary interactive session plus this diagnostic
  child session) — worth being aware that `state.json`/docs can be
  stale relative to what another concurrently-running session already
  did. Always `git fetch` + compare before trusting a locally-read
  snapshot when picking up mid-session.

## WHAT REMAINS
state.json `queue`:
- P0 tier: ALL DONE, gate cleared. P0-5 (loop bug): still open, see above.
- P1-pr1-decision: **done**, merged.
- P1-ladder-rung1-raise: **done**.
- P1-dashboard-auth: blocked_on_human — needs Het, real browser.
- P1-advisor-training-real-run: unblocked now that PR #1 merged — no
  action needed unless Het wants it triggered manually before its
  monthly cron.
- Fund research: early scoping done in a prior session (see the status
  Artifact), SEBI RIA route not yet researched in depth. Findings live
  outside this repo, not in `.autonomous/`.
- P2/P3 items: unchanged, low-priority/gated per Phase 1's "don't add
  machinery" guidance — see state.json for exact status per item.

## EXACT NEXT TASK
1. Confirm `state.json`'s `current_phase` is still `"phase_1"` and
   re-read `het_directives.md`'s cost-constraint note — this file is a
   snapshot, those are the live sources.
2. **Do not fire the autonomous dev-loop Routine, or any new paid
   session/Routine, without asking Het first.** Still the single most
   important behavioral constraint. Given 5 failures including the
   clone-first fix, a 6th attempt with another prompt tweak is unlikely
   to help — if picking this up, either find a genuinely new diagnostic
   angle or raise with Het whether to keep spending on it at all (see
   NEEDS HET in het_directives.md).
3. Otherwise: standing-mode discipline applies — don't start new
   features, watch for a real PROMOTE (first ever, flag prominently),
   verify `factory.yml`'s daily/weekly Actions runs are actually landing
   commits against `main` now that PR #1 is merged (don't assume it
   works — check `list_commits` on `main`), keep the status Artifact
   current rather than making Het read raw files.
4. If Het has replied since this was written: check his message against
   `het_directives.md`'s NEEDS HET section first.

## FILES TO OPEN
- `.autonomous/state.json`, `.autonomous/het_directives.md`,
  `.autonomous/bug_log.md` — the three living trackers.
- `factory.py` only if there's an actual bug to fix, not for feature work.

## FILES NOT TO OPEN UNLESS NEEDED
- understanding.txt / pivot_document.txt / mission_document.txt — already
  compressed into EXECUTION_PLAN.md.
- AUTONOMOUS_TODO.md — narrative decision rationale only.
- dashboard.py — no open work item touches it right now.

## TEST COMMANDS
No committed test suite exists — all testing is ad hoc, against
synthetic monkeypatched price data (Yahoo Finance unreachable here).
This session's LADDER test pattern (copy `factory_state/` + `factory.py`
into an isolated scratch dir, monkeypatch `fetch_prices()` with a
synthetic random-walk DataFrame, run N `update()` cycles + `report()`,
assert no crash) is a reusable template — see the session transcript or
recreate similarly.

## EXPECTED RESULT
Phase 1 standing mode: nothing should meaningfully change session to
session except accumulated ledger history and the loop-bug
investigation. A session that finds itself wanting to "improve" the
tournament (beyond what's already authorized) is probably violating
Phase 1's own discipline — check EXECUTION_PLAN.md Section 4 first.

## STOP IF
- You find yourself wanting to change RULES, LADDER, or COST_PER_SIDE's
  underlying risk appetite beyond what's already confirmed — kill-
  condition signal per EXECUTION_PLAN.md Section 5(f).
- You're about to fire a new paid session/Routine without having asked
  Het first — stop, per the active cost constraint.
- You're about to start a new feature beyond what's already
  approved/shipped — Phase 1 says don't.
- You're below ~20-30% of usable session context — stop, spend the
  remainder verifying and rewriting state.json/log/this file.

## OPERATOR AUTHORIZATION REQUIRED
- Confirming dashboard.py's private-repo auth (needs Het, real browser).
- Firing the autonomous-loop Routine again to test a new fix (cost
  constraint) — and per NEEDS HET, worth asking whether to keep trying
  at all given 5 straight failures.
- Continuing fund research beyond the initial scoping (already
  authorized in principle, but check for anything more specific Het
  wants next).
- Anything implying pooling outside money / a "fund" structure — needs
  its own dedicated conversation, SEBI registration territory.

## DO NOT RE-DERIVE
- EXECUTION_PLAN.md Section 2 (Settled Facts) and Section 9 (Strategic
  Decisions).
- The Three Laws and their authorized overrides (advisor layer,
  crossover breeding, agents/ team) — see state.json `decisions`.
- P0-1/P0-2/P0-3's formulas, the LADDER raise, or the PR #1 merge
  decision — all done, verified, documented with commit references.
- The autonomous-loop root-cause investigation up through the
  clone-first fix's failure — don't re-run that comparison, it's
  settled as "still broken, needs a new angle."

## IMPORTANT NEW KNOWLEDGE
- **PR #1 is merged.** `main` is current. This is the biggest state
  change since Phase 0 cleared — every "PR #1 unmerged" caveat in older
  docs is now resolved.
- **LADDER is raised and live.** Every "pending LADDER decision" caveat
  in older docs is now resolved.
- **The dev-loop Routine's "likely root cause found" was wrong, or at
  least incomplete** — the proposed fix was actually tested and failed.
  Don't trust an unverified "probably fixed" claim in any doc without
  checking `git log`/`list_commits` yourself first.
- Cost constraint is still active — see top of this file.
