---
name: handoff-packet
description: Produce the AI SYNC PACKET that LucyOS ingests when work on strategy-factory is handed to another model, session, or to OpenClaw/WhatsApp. Use at the end of any session that changed files, when asked to "hand off", "sync to Lucy", "write the packet", or before a model switch. Mirrors LucyOS `directives/05_SYNC_AND_HANDOFF_PROMPT.txt` so the format never drifts.
---

# handoff-packet — convert this session's durable work into one ingestible packet

Write to `.autonomous/capital_engine/EVIDENCE/PACKET-<YYYYMMDD>-<short>.md` in
strategy-factory. If the LucyOS checkout is present (`/home/user/lucyos-`),
also copy it to `PROJECTS/strategy-factory/evidence/` there on a `task/…`
branch (never merge). Do not assume any other AI can see this conversation.

```
# AI SYNC PACKET
PACKET_ID: PACKET-<date>-<short>
SOURCE: strategy-factory session (<model>)
TIMESTAMP: <UTC>
PROJECT: strategy-factory
TOPIC:

## OWNER INTENT          (the end state Het is after, one paragraph)
## VERIFIED FACTS        (only what was actually observed: commands, outputs, SHAs)
## INFERENCES / ASSUMPTIONS
## DECISIONS             (with the rationale and who made them: Het vs session)
## TASKS CREATED         (CE IDs / TITLE / PRIORITY / DEPENDS / SUCCESS CRITERIA)
## TASKS COMPLETED       (CE IDs + evidence file)
## RESEARCH FINDINGS     (source + date)
## FILES / CODE / ARTIFACTS
## TESTS / VALIDATION    (what really ran)
## RISKS
## BLOCKERS
## APPROVALS REQUIRED    (copy the exact §8 sentence from docs/capital_engine/00_DESIGN.md)
## CURRENT STATE
## NEXT HIGHEST-VALUE ACTIONS
## EXACT RESUME POINT    (the next concrete command)
## RAW CONTEXT REFERENCE (commit SHAs, PR URLs)
END AI SYNC PACKET
```
Rules: no secrets, no chat dumps, mark unknowns, flag conflicts with prior
facts instead of overwriting, keep it under ~150 lines.
