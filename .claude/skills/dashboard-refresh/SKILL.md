---
name: dashboard-refresh
description: Refresh the WiFi-CSI research control dashboard — run the evidence verifier + renderer, summarize what changed, and (only on explicit request) record a user approval. Thin wrapper over scripts/automation/update_dashboard.py; all logic lives in the script.
---

Use this skill to refresh `RESEARCH_DASHBOARD.md` from the source-of-truth, or to record an
explicit user approval. **All verification/rendering logic lives in the Python script — this skill
only invokes it and summarizes the result.** Never hand-edit `RESEARCH_DASHBOARD.md` or
`automation/status.json`; they are generated.

Governing rule: **Claude claims → the script verifies → the user accepts.** You may run the verifier
and renderer freely; you may **never** create a user approval on your own.

## Default: refresh (verify + render)

Run:

    .venv/Scripts/python.exe scripts/automation/update_dashboard.py

Then report to the user, from the command output:
1. The integrity gate (CLEAN / WARN) and any staged-model/log or protected-path warnings.
2. The `[delta]` task state changes since the last refresh.
3. Anything now in **VERIFIED-AWAITING-APPROVAL** (needs their decision) or **CLAIMED-UNVERIFIED**
   (a failed evidence check — name the failing check).

Read-only variants (never write): `--verify` (print the verification ledger), `--check`
(idempotency self-test).

## Approval — HUMAN-ONLY, never autonomous

Only when the user's message **explicitly** asks to approve a specific task (e.g. they type
`/dashboard-refresh --approve AUT-GSC` or say "approve AUT-GSC"), run:

    .venv/Scripts/python.exe scripts/automation/update_dashboard.py --approve <TASK_ID>

Rules:
- **Do NOT** run `--approve` proactively, as a convenience, or to "finish" a task. Approval is the
  user's act; you invoke it only because they explicitly told you to, this turn, for this task.
- The script refuses unless the task is currently **VERIFIED-AWAITING-APPROVAL** (evidence passed).
  It will not accept a CLAIMED-UNVERIFIED task — do not try to work around that.
- After approval, re-report the delta (the task should flip to **ACCEPTED**).
- Frozen-test / thesis-claim tasks (`gated: true`) reach done-ness ONLY through this path.

## Receipt convention (for every other automation skill)

Every skill/hook that completes work must end by writing ONE append-only receipt to
`automation/receipts/<UTC>_<automation>_<task_id>.json` (schema: `automation/receipts/README.md`),
then run the default refresh above and report the **computed** (not claimed) result. Include SHA256
for each `files_created` so verification is hash-verified, not existence-only.

## Never

Hand-edit generated files · fabricate or auto-create a user approval · create test authorization
tokens · run held-out test reads · stage / commit / push · edit thesis/Overleaf files.
