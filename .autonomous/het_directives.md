# Het's directives log (append-only) — what he's asked for, over time

Distinct from `operator_profile.md` (identity/communication-style/goals,
static-ish) and from `AUTONOMOUS_LOG.md` (what the AI did). This file is
specifically for tracking Het's own instructions/requests as they come in
across a session, so a later session (or Het himself) can see what's been
asked and whether it's been acted on — WITHOUT storing verbatim personal
conversation (see operator_profile.md's "What NOT to do" section, same
reasoning applies here: summarized intent, not a chat transcript).

Format: `DATE | directive (summarized) | status`

---

- 2026-08-24 | Build a "team of agents" in subfolders (judge, researcher, breeder, risk_manager, reporter), even after being warned it's not Phase 0/1 priority — confirmed "build it anyway" | **DONE**, commit `a06e392`, see `agents/README.md` and `state.json` decision `agents-team-override`.
- 2026-08-24 | Report only once a day; keep working autonomously in between even without a reply | **ACTIVE** — operating this way now. Daily check-in cadence to be set up via a scheduled Routine if the session ends before Het returns.
- 2026-08-24 | Keep a bug log so issues found are tracked | **DONE** — `.autonomous/bug_log.md` created (OPEN/FIXED format), CLAUDE.md points to it.
- 2026-08-24 | "We are making a private fund company... input money into it" | **CORRECTED, NOT BUILT** — this repo is a personal paper-trading research system, not a fund. Pooling outside money into a fund requires SEBI PMS/AIF registration, a completely separate legal undertaking. Flagged directly to Het; nothing fund-shaped has been or will be built without a dedicated, explicit conversation about that first.
- 2026-08-24 | Before ending any session, have enough work done + a "crash file" so work isn't lost mid-session | **STANDING PRACTICE** — already committing + pushing after every tested unit of work (not batching), and `.autonomous/next_session.md` is rewritten before ending a session as the literal handoff. This directives log + bug_log.md add to that safety net.
- 2026-08-24 | In daily reports, explicitly highlight anything that needs human/Het verification or action | **NOTED FOR REPORTING FORMAT** — see the "NEEDS HET" section this file's own updates should carry forward into `next_session.md` and any daily summary. Standing items that already need Het: PR #1 merge decision, dashboard.py auth confirmation (needs a real browser outside any sandbox), LADDER rung-1 sizing decision, the Routine zero-commit fix confirmation.
- 2026-08-24 | "Give you every permission, work on your own" | **ACKNOWLEDGED, GUARDRAILS UNCHANGED** — CLAUDE.md's hard rules (never merge/push main, never touch RULES/LADDER/COST_PER_SIDE, never real capital/broker code, never make the repo public) still require Het's fresh, explicit, in-session confirmation each time, regardless of a general permission grant. Stated this back to Het directly rather than silently expanding scope.
- 2026-08-24 | Store this session's ongoing instructions in a file to reference later, even while Het is away and sending updates | **DONE** — this file. Append new directives here as they arrive; update status as they're acted on.

- 2026-08-24 | "Report to me once a day, keep working if I don't reply" | **DONE** — daily Routine `trig_01Y9q1Dn98ghLMD4KX7xZfxp` created, fires 13:00 UTC daily into a fresh session, reads state.json/bug_log.md/het_directives.md and reports plain-language status + anything needing Het's decision. Push notification enabled.

## NEEDS HET (carry this section into the next daily report / next_session.md)

- PR #1 merge decision — hold, needs fresh confirmation, not inferred from any prior "yes."
- dashboard.py private-repo auth — needs Het to check the raw ledger URL in a plain incognito browser (sandbox network can't test this validly, see standing_env_facts).
- LADDER rung-1 capital sizing — flagged as a pending decision, not resolved, not to be resolved autonomously.
- **Autonomous dev-loop Routine (5-hourly) — NOW DISABLED, three confirmed zero-commit failures.** 2026-08-24 19:00 UTC: confirmed cse_01LFv3QXjUowxWUHD4XwLMym (anti-give-up prompt fix) ran 16 real minutes, real spend, ended cleanly, committed NOTHING. Tried a second, more specific fix (named the exact classifier-timeout error text, gave an explicit 5-retry protocol, gave it a deliberately trivial unambiguous test task) — fired it directly via fire_trigger, session cse_01RJf6KJXJSv3YveSfSHuLxj: ran 8 real minutes, ended cleanly, STILL zero commits, no ambiguity this time. Then the Routine's own normal schedule fired again unattended at 2026-08-25 00:49 UTC on the same updated prompt — also zero commits, confirmed via git log. That's three real, paid firings in a row with nothing landed. **Decision: disabled the Routine (trig_013GUxs9AwHaRvb1o4eGJRGx) rather than keep guessing at prompt wording.** It needs an actual root cause — visibility into what the session does internally, not another external retry — before being re-enabled. The separate DAILY REPORT Routine (trig_01Y9q1Dn98ghLMD4KX7xZfxp, push-notified) is unaffected, still enabled, fine to rely on for status.
- Any future request that implies pooling outside money / running a fund — needs its own dedicated conversation (SEBI registration territory), not something to build incrementally by default.
