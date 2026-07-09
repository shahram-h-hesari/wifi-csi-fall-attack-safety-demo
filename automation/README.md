# Automation & dashboard system — how it works

One rule governs everything here: **Claude claims; scripts verify; you accept.**
The dashboard is a *rendered view* of machine-readable state, never the state itself.
Completion is *computed from evidence* — it is not something Claude writes.

## The three-state ladder

- **CLAIMED** — a receipt in `receipts/` asserts work is done. This is an assertion, shown as one.
- **VERIFIED** — `scripts/automation/update_dashboard.py --verify` re-checked the evidence and
  every check passed (files exist + hashes match, exit codes 0, acceptance evidence parses PASS,
  no test-split read without authorization, no forbidden command, git clean on protected paths,
  no `.pt/.pth/.ckpt/.log` staged). *Not built until Stage 4.*
- **ACCEPTED** — **you** approved (an approval receipt with `actor.kind: user`). Gated tasks
  (frozen-test adjacency, thesis claims, plan changes) can only reach "done" through here.

A task renders DONE only at VERIFIED (routine) or ACCEPTED (gated). Claude never moves a task past CLAIMED.

## Files

| Path | Role | Updated by | Your approval? |
|---|---|---|---|
| `../RESEARCH_DASHBOARD.md` | Human view (Stage 1 hand-maintained → Stage 3 generated) | hand now; script later | no (it's a view) |
| `roadmap.yaml` | Versioned 7-day plans; pivots via `supersedes` | you (Claude drafts) | **yes** |
| `tasks.yaml` | Task registry — **definitions only, no status** | you (Claude drafts) | **yes** for gated tasks |
| `experiment_queue.yaml` | Queue entries w/ pilot-config refs | you enqueue; queue skill updates run-state via receipts | **yes** to enqueue |
| `acceptance/*.yaml` | One acceptance spec per automation | you | **yes** |
| `receipts/*.json` | Append-only claim log | every skill/hook/script | no (claims); acceptance is separate |
| `status.json` | Computed rollup | `update_dashboard.py` (Stage 3+) | no |
| `artifact_manifest.csv` | Computed inventory | `scan_artifacts.py` (Stage 6) | no |
| `dashboard_changelog.md` | Append-only history | generated (hand now) | no |
| `do_not_build_yet.md` | Parking lot + revisit conditions | you | **yes** |

## Current stage

**Stage 3 (render phase active).** `scripts/automation/update_dashboard.py --render` now regenerates
`../RESEARCH_DASHBOARD.md` + `status.json` from the SoT. **Verification is NOT active yet** — all
statuses are CLAIMED/unverified until Stage 4. Build order: Stage 3 render → Stage 4 receipts+verify
→ Stage 5 `/dashboard-refresh` skill → Stage 6 `scan_artifacts.py` → Stage 7 optional Notion one-way
push → **Stage 8 optional static HTML view (`dashboard/index.html`)**.

**Stage 8 — static HTML dashboard view (future).** A single self-contained `dashboard/index.html`,
*generated* (never hand-edited, never SoT) from `status.json` + `artifact_manifest.csv` + the YAML
SoT, only after a fresh verify+render passes. Purely a nicer-to-read view: cards, progress bars,
roadmap timeline, badges distinguishing CLAIMED/VERIFIED/ACCEPTED and
validation-only/frozen-test/thesis-safe/research-goal. Waits until `status.json` (Stage 4) and the
artifact manifest (Stage 6) are stable. Spec: `acceptance/html-dashboard.yaml`.

## Hard safety rules (never)

auto-edit thesis/Overleaf files · auto-run held-out test · auto-create test authorization tokens ·
auto-stage/commit/push · auto-mark frozen-test tasks done without your approval · show validation
results as test evidence · hide failed experiments · overwrite history · delete artifacts · treat Notion as SoT.
