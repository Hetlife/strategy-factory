# HR log (append-only) -- agent hires and proposals

Distinct from `het_directives.md` (Het's own instructions) and
`AUTONOMOUS_LOG.md` (terse action-by-action record). This file tracks
specifically: every proposal or actual hire made via `agents/hr/hr.py`.

**Scope, confirmed with Het 2026-08-26**: hires are new *team-role
tooling* agents (the same shape as Judge/Researcher/Breeder/Risk
Manager/Reporter/Healer) -- never trading strategies, never anything
that touches `factory.py`'s registry or a `sig_*` function. That stays
entirely on the existing mechanism-first hypothesis process (Law 1),
completely separate from this file.

**Cap**: the first 10 hires can be made on a session's own judgment
(free, code-only, matching existing safe patterns) without asking Het
first. Hire #11 onward needs his explicit go-ahead. `agents/hr/hr.py`'s
`scaffold_agent()` enforces this automatically by counting `HIRED` lines
below.

Format:
- `PROPOSED | DATE | role_name | reason` -- logged, nothing created yet.
- `HIRED | DATE | role_name | reason -- what was scaffolded`

---
