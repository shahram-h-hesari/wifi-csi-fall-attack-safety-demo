# Completion receipts — APPEND-ONLY claim log

One JSON file per completion event. Filename: `<UTC-timestamp>_<automation>_<task_id>.json`
(e.g. `2026-07-11T0942Z_val-pilot-gate_AUT-VPG.json`). **Never edited, never deleted** —
corrections are new receipts with `supersedes: <receipt_id>`. Git history provides tamper-evidence.

A receipt records a **CLAIM**. It must **not** contain a self-assessed "verified" field —
verification is computed later by `update_dashboard.py --verify` (Stage 4), outside the writer.

## Schema (schema_version 1)

```json
{
  "schema_version": 1,
  "receipt_id": "2026-07-11T09:42:00Z_val-pilot-gate_AUT-VPG",
  "task_id": "AUT-VPG",
  "automation": "val-pilot-gate",
  "actor": { "kind": "skill|hook|subagent|user|script", "name": "val-pilot-gate", "session_hint": "" },
  "status_claimed": "done|partial|failed|blocked",
  "summary": "One-sentence human-readable outcome.",
  "files_created":  [ { "path": "results/J1/val_gate/GATE_REPORT.md", "sha256": "" } ],
  "files_modified": [ { "path": "automation/validation_selection_log.csv", "change": "append-1-row" } ],
  "commands_run":   [ { "cmd": "...export_probability_predictions.py --split val ...", "exit_code": 0 } ],
  "artifacts":      [ { "path": "", "kind": "csv|figure|table|report|protocol",
                        "split": "val|test|none", "evidence_level": "validation-only|frozen-test|n/a" } ],
  "acceptance_tests": [ { "id": "VPG-repro-afac", "result": "pass|fail|not_run", "evidence_path": "" } ],
  "split_usage": { "splits_touched": ["val"], "test_read": false, "authorization_token": null },
  "git": { "head": "b140b04", "expected_dirty": ["results/J1/**"] },
  "requires_user_approval": true,
  "blocked_on": null,
  "supersedes": null,
  "next_action": "Review GATE_REPORT.md; approve AUT-VPG or kill candidate J1."
}
```

## Convention (adopt now, verify later)

Every skill/hook ends by: writing one receipt here → (Stage 4+) running the verifier → reporting
in its final message the **receipt_id** and the **computed** (not claimed) verification result.
Approval receipts are written only by the user via `/dashboard-refresh --approve` and carry
`actor.kind: user`.
