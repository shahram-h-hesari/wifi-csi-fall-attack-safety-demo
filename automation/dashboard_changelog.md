# Dashboard changelog — APPEND-ONLY

Never edit or delete entries. Every state transition, plan change, and processed-receipt batch
appends here. At Stage 3+ the render script writes these entries; today they are written by hand.

---

## 2026-07-09 — Stage 5 /dashboard-refresh skill + approval path built

- **actor:** skill/dashboard-build (Claude); **HEAD** `b140b04`.
- **Created:** `.claude/skills/dashboard-refresh/SKILL.md` (thin wrapper — all logic stays in the
  script), `scripts/automation/test_approve.py` (approval round-trip test).
- **Added to `update_dashboard.py`:** `--approve <TASK_ID>` writes a `actor.kind: user` approval
  receipt (the only path to ACCEPTED); refuses unless the task is VERIFIED-AWAITING-APPROVAL. Also
  added `[delta]` task-state-change reporting on every refresh.
- **Safety fix:** `compute_display` now gates on evidence FIRST — a stray/user approval can never
  override a failed evidence check (unverified stays CLAIMED-UNVERIFIED even if an approval exists).
- **Tests:** approval round-trip ALL PASS — verified+no-approval→AWAITING, verified+approval→ACCEPTED,
  **unverified+approval→CLAIMED-UNVERIFIED** (approval does not override), dry-run approval carries
  actor.kind=user. Stage 4 three-fixture test still passes; idempotency PASS.
- **Not fabricated:** no real approval was written. `AUT-GSC-impl` remains VERIFIED-AWAITING-APPROVAL
  pending YOUR explicit `--approve`.
- **Not built (later):** `scan_artifacts.py` (S6), Notion push (S7), HTML view (S8), Stop-event reminder hook.

## 2026-07-09 — Stage 4 receipts + verify phase built

- **actor:** skill/dashboard-build (Claude); **HEAD** `b140b04`.
- **Verification is now ACTIVE.** `update_dashboard.py` computes the three-state ladder from receipt
  evidence: files exist (+ SHA256 if present), command exit codes, forbidden-command scan
  (`--split test/legacy`, `git commit/push/add`, thesis/overleaf paths, checkpoint deletion),
  split-usage gate (no test read without a valid token), and declared acceptance-test results. Plus a
  repo-global **integrity gate**: no `.pt/.pth/.ckpt/.log` staged and no protected tracked path
  (thesis_artifacts/, FROZEN_*, ledger CSV) dirty.
- **States:** CLAIMED-UNVERIFIED (loud) / VERIFIED / VERIFIED-AWAITING-APPROVAL / ACCEPTED. Gating now
  honors both `tasks.yaml gated:` and a receipt's `requires_user_approval`.
- **Created:** `scripts/automation/test_verify.py` (three-fixture acceptance test).
- **Tests:** three-fixture test ALL PASS — good→VERIFIED, missing-file→CLAIMED-UNVERIFIED (names the
  failed check), gated/no-approval→VERIFIED-AWAITING-APPROVAL, plus forbidden `--split test`→
  CLAIMED-UNVERIFIED. Real receipts: DASH-S1/S2/S3 VERIFIED (existence-only — no SHA256 in those
  receipts), AUT-GSC-impl VERIFIED-AWAITING-APPROVAL. Integrity gate CLEAN. Idempotency PASS.
- **Note:** existing receipts carried empty `sha256`, so their verification is existence-only;
  skill-written receipts (Stage 5+) should include hashes for hash-verified strength.
- **Not built (later):** `/dashboard-refresh` skill + `--approve` path (S5), `scan_artifacts.py` (S6),
  Notion push (S7), HTML view (S8), any hook.

## 2026-07-09 — Stage 3 render phase built

- **actor:** skill/dashboard-build (Claude); **HEAD** `b140b04`.
- **Created (working tree only — NOT staged/committed):** `scripts/automation/update_dashboard.py`
  (render + `--check` idempotency + `--verify` stub), `automation/frontier.yaml` (interim research-state
  SoT), receipts for DASH-S1/S2/S3 + a git-stage-check legacy record.
- **RESEARCH_DASHBOARD.md is now GENERATED** from SoT (was hand-maintained). Also emits `automation/status.json`.
- **Verification NOT active** — all statuses render CLAIMED/unverified; VERIFIED/ACCEPTED impossible until Stage 4.
- **Tests:** YAML/JSON all parse; `--render` succeeds; `--check` idempotency PASS (double render byte-identical).
- **Refinement to design:** the renderer does NOT auto-append this changelog (that would break idempotency
  and spam it); changelog stays append-on-event, written at meaningful transitions.
- **Not built (later):** verify phase (S4), `/dashboard-refresh` skill (S5), `scan_artifacts.py` (S6),
  Notion push (S7), HTML view (S8), any hook.

## 2026-07-09 — Plan change: added Stage 8 (static HTML dashboard view)

- **actor:** user-approved plan change; recorded by Claude. **Plan in effect unchanged** (`roadmap-2026-07-09-v1`).
- Added Stage 8 as a **future stage** (beyond the 7-day horizon) to `roadmap.yaml` (`future_stages`),
  `tasks.yaml` (`DASH-S8`, depends on DASH-S4 + DASH-S6), `README.md` build order, `do_not_build_yet.md`,
  and new acceptance spec `acceptance/html-dashboard.yaml`.
- **Nature:** `dashboard/index.html`, generated (never SoT, never hand-edited), built only after a fresh
  verify+render, distinguishing CLAIMED/VERIFIED/ACCEPTED and val-only/frozen-test/thesis-safe/research-goal.
- Also added `DASH-S6` (scan_artifacts stage) to `tasks.yaml` as an explicit dependency of S8.

## 2026-07-09 — Stage 1+2 scaffolded

- **actor:** skill/dashboard-build (Claude), hand-maintained; **HEAD** `b140b04`.
- **Created (working tree only — NOT staged/committed):**
  - `RESEARCH_DASHBOARD.md` (Stage 1, hand-maintained view)
  - `automation/README.md`, `roadmap.yaml`, `tasks.yaml`, `experiment_queue.yaml`,
    `do_not_build_yet.md`, `dashboard_changelog.md`
  - `automation/acceptance/{test-split-guard,val-pilot-gate,ledger-sync-audit,protocol-freeze,experiment-queue,git-stage-check,dashboard-refresh}.yaml`
  - `automation/receipts/README.md` (receipt schema convention)
- **Plan in effect:** `roadmap-2026-07-09-v1` (initial; supersedes nothing).
- **State:** all 5 new automations at design-approved / not-implemented. `git-stage-check`
  accepted-legacy (in use). Dashboard S1+2 in progress.
- **Deliberately NOT built (later stages):** `update_dashboard.py` (S3), receipts verifier (S4),
  `/dashboard-refresh` skill (S5), `scan_artifacts.py` (S6), Notion push (S7), any hook.
- **Frozen-test ledger unchanged:** H15-TEST-EPS0015-AFAC-20260705 = PASS remains the only test read.
