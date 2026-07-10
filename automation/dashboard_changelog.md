# Dashboard changelog — APPEND-ONLY

Never edit or delete entries. Every state transition, plan change, and processed-receipt batch
appends here. At Stage 3+ the render script writes these entries; today they are written by hand.

---

## 2026-07-10 — Research OS layer D2d-1: Curated Reference Evidence registry (contract only)

- **actor:** user-approved design (D2d memo, Option B chosen over Option A ledger-backfill);
  recorded by Claude. **HEAD** `4bdf5db`.
- **Why:** real-data smoke tests (post-D2) found `H15_eps0015_frozen` returned no_matching_artifact
  (the frozen H15 artifacts exist in the manifest but have no ledger row) and
  `AFAC_eps0030_F20_posthoc` matched 71 rows instead of the one canonical F20 point. Backfilling
  `results/defense_attempt_inventory/defense_attempt_results_long.csv` by hand (Option A) was
  rejected: that ledger is a derived, protected-path file — a hand row would have no derivation
  trail and would trip the dashboard's protected-path integrity gate.
- **Created:** `automation/registry/reference_evidence.yaml` — two curated entries recording
  numbers already published in committed artifacts: H15_eps0015_frozen (frozen-test, eps 0.015,
  TP/FN/FP/TN 41/4/60/395, Rfall 0.911111, FAR 0.131868, protocol_id
  H15-TEST-EPS0015-AFAC-20260705, clean-disclosure companion) and AFAC_eps0030_F20_posthoc
  (test-post-hoc, eps 0.030, TP/FN/FP/TN 36/9/91/364, Rfall 0.8, FAR 0.2 — selected as the UNIQUE
  F20_reached=True row in the ledger's 158-row test/pgd/eps=0.03 pool, not a hand choice).
- **Edited:** `automation/acceptance/result-explorer.yaml` — curated-first named-reference
  resolution, mandatory manifest cross-check (mismatch -> `provenance_mismatch` refusal, numbers
  never rendered), fallback-unchanged rule, fixtures F12-F15. `automation/registry/README.md` gained
  a curated-source section. Registered `REF-EVID` in tasks.yaml.
- **Scope: CONTRACT ONLY.** `result_explorer.py` / `test_result_explorer.py` NOT touched this step —
  F12-F15 are not yet passing; the resolution code lands in D2d-2 (separate approval). No
  results/ file was created, edited, or backfilled. Receipt: `REF-EVID` (requires user approval).

## 2026-07-10 — Research OS layer D2: Result Explorer v1 (read-only lookup tool)

- **actor:** user-approved D2a spec (`f49a58b`) → D2b test-first fixtures → D2c implementation;
  recorded by Claude. **HEAD** `f49a58b`.
- **Created:** `scripts/automation/test_result_explorer.py` (D2b: 12 fixtures F1–F11 + no-test-leakage
  bonus, fully synthetic temp-dir data mirroring real ledger/manifest/registry schemas) then
  `scripts/automation/result_explorer.py` (D2c). Suite green: **12 passed**; zero test edits were
  needed after implementation.
- **Safety properties (spec-enforced + fixture-proven):** manifest is the evidence-level authority
  (ledger source_file → manifest path join; never filename inference, never upgrades);
  registry-resolved goals/datasets with unsupported-pair + disallowed-evidence refusals;
  validation-first defaults (filterless queries can never surface held-out-test rows); saved
  test/frozen/post-hoc summaries reachable only via named reference_evidence_queries or explicit
  filters; mandatory warning bands (incl. "not R90F10" on every fall row); honest empty states
  (data-needed / supported-not-evaluated / no-match / too-broad, cap 25); read-only by construction
  (no process spawning, no split-flag command strings, no file writes — stdout only; runtime
  snapshot proof in F1); no real results/ access during tests.
- **Registered:** `TOOL-REXP` in tasks.yaml. Receipt: `TOOL-REXP` (requires user approval).
- **NOT built (later, separate approvals):** dashboard rendering of goals/tracks/explorer summary (D3).

## 2026-07-10 — Research OS layer D1: Goal Registry + Dataset Capability Registry

- **actor:** user-approved design (Commit D plan, refined schema); recorded by Claude. **HEAD** `309e507`.
- **Created:** `automation/registry/goals.yaml` (5 goals: fall_detection ACTIVE_THESIS_PRIMARY;
  walking_detection DATA_AVAILABLE_NOT_EVALUATED; walking_pattern_recognition +
  gait_or_mobility_change_detection NO_DATA; future_fall_risk_prediction NO_DATA_ASPIRATIONAL),
  `automation/registry/datasets.yaml` (SenseFi/UT-HAR capabilities), `automation/registry/README.md`,
  acceptance specs `goal-registry.yaml` + `dataset-registry.yaml`; task defs REG-GOALS + REG-DATASETS.
- **Key rules encoded:** validation-first defaults (`default_query_fields.split: val` everywhere;
  known test/frozen evidence preserved only as named `reference_evidence_queries`); missing data is
  first-class information; `frozen-test` allowed only for fall_detection (only goal with a frozen
  protocol); supported/unsupported goal split per dataset = integrity gate for the future Result
  Explorer; no clinical claims (binding `clinical_claim_boundary.forbidden`).
- **Label-map provenance:** UT-HAR indices read (read-only) from `scripts/analyze_safety_guided_seed.py:39`,
  cross-checked against 3 sibling scripts — fall=1, walk=2; recorded in the registry, never guessed.
- **NOT built (later, separate approvals):** Result Explorer v1 (D2: result_explorer.py + fixtures +
  acceptance), dashboard rendering of goals/tracks (D3), any evaluation of walking_detection.
  Receipts: `REG-GOALS`, `REG-DATASETS` (require user approval).

## 2026-07-09 — Plan change: roadmap-2026-07-10-v2 supersedes roadmap-2026-07-09-v1

- **actor:** user-approved plan change (draft reviewed with revisions); recorded by Claude. **HEAD** `f628b3e`.
- **Why:** v1 assumed serial build-out; Stages 3–6 + test-split-guard landed on day 1, and the TSG
  auditable-warning fix (`dbf658a`/`5fb2e06`), val-pilot-gate design memo (`3d8e5b2`, ACCEPTED), and
  HTML visual-design spec rev 2 (`427dacc`, ACCEPTED) completed ahead of plan (reconciled `f628b3e`).
  v1 left §1 Now/Next and §3 rendering already-finished work as future — the last stale SoT surface.
- **v2 shape:** Markdown-dashboard soak days 1–4 (with untracked-backlog triage as secondary work);
  val-pilot-gate design→fixtures→scanner ladder on days 3/5/7, **each CONDITIONAL on separate future
  user approval (none authorized yet)**; ledger-sync --audit day 6 (also conditional). DASH-S8 HTML
  stays parked: **eligible for review after the soak condition** — a user decision, never automatic.
- **Immutability:** v1 plan block untouched (superseded, never deleted).
  Receipt: `ROADMAP-V2` (requires user approval).

## 2026-07-09 — test-split-guard warnings made auditable (stderr + exit 1)

- **actor:** session sot-reconciliation (Claude), user-approved commits; **commits** `dbf658a` (behavior) + `5fb2e06` (spec truth-up); **HEAD** `5fb2e06`.
- **Change:** warn-only mechanism replaced — risky commands now print ONE WARN-ONLY line to **stderr and exit 1**
  (non-blocking under Claude Code hook rules: stderr is shown to the user and the tool call continues; **only
  exit 2 blocks**). Safe commands exit 0 silently. Supersedes the original exit-0/stdout-JSON design.
- **Why:** two visibility mechanisms (stdout systemMessage, then stderr) executed correctly but were not rendered
  in the Claude Code Desktop main view; diagnosis via session-transcript JSONL proved the hook fires and each
  warning is durably recorded as a `hook_non_blocking_error` attachment — the **transcript is the audit trail**.
- **Spec truth-up (`5fb2e06`):** `acceptance/test-split-guard.yaml` gained a `warn_contract` block and corrected
  `phase_A test_passed` (obsolete exit-0 expectation removed); `frontier.yaml` test_split_guard note updated.
- **Unchanged:** warn-only (never blocks), no guard log, no tokens, no permission-decision output; fixture suite
  ALL PASS under the new contract. Receipt: `2026-07-10T064709Z_test-split-guard_AUT-TSG-impl` (supersedes the
  exit-0 receipt; requires re-approval).

## 2026-07-09 — HTML dashboard visual design spec revision 2

- **actor:** user-approved design/spec update; **commit** `427dacc`.
- **Edited:** `automation/acceptance/html-dashboard.yaml` — evidence-gated research cockpit identity (NOT a
  startup KPI dashboard; evidence type before performance numbers), `layout_v1` (header band with val/frozen
  read counters, alert strip, two-lane frontier with hard evidence wall, val-pilot placeholder, collapsed audit
  sections, provenance footer), color law (green ONLY for frozen-test + ACCEPTED), three badge families
  (evidence / automation_status / val_pilot_verdict), figure provenance rules (never render unbadged),
  no-code-execution interactivity rules, Desktop-preview + public-website rules, V1/later split.
- **Not built:** no `dashboard/index.html`, no `build_html_dashboard.py`, no dev server. Stage-8 parking-lot
  soak condition unchanged. Receipt: `2026-07-10T064711Z_dashboard_DASH-S8-design`.

## 2026-07-09 — val-pilot-gate design memo committed (v0.2, user-calibrated)

- **actor:** user-approved design memo; **commit** `3d8e5b2`.
- **Created:** `automation/designs/VAL_PILOT_GATE_DESIGN.md` — completed-validation-pilot definition, evidence
  rules, strict matching rule (checkpoint path + SHA-256, run_name, seed, epsilon, threshold source), and the
  user-calibrated verdict scheme **STRONG-GO / REVIEW-GO / NO-GO / NEEDS-REVIEW** with three accepted edge-case
  defaults (no-category -> NEEDS-REVIEW; operational dominance; operational low-FAR improvement, novelty stays
  human-judged). Gate never authorizes a test read; test-split-guard stays warn-only; no blocking mode.
- **Design only:** no implementation, no scanner, no receipts directory, no guard integration.
  `acceptance/val-pilot-gate.yaml` reconciliation deferred (memo §10 step 1, awaits explicit go-ahead).
  Receipt: `2026-07-10T064710Z_val-pilot-gate_AUT-VPG-design`.

## 2026-07-09 — test-split-guard built (WARN-ONLY phase)

- **actor:** skill/dashboard-build (Claude); **HEAD** `77280f0`.
- **Created:** `scripts/automation/test_split_guard.py` (PreToolUse matcher, pure stdlib, read-only,
  ALWAYS exits 0), `scripts/automation/test_split_guard_cases.py` (fixture/acceptance test).
- **Created:** `.claude/settings.json` with a PreToolUse hook (matcher `Bash|PowerShell`).
  `.claude/settings.local.json` was NOT touched.
- **Edited:** `automation/acceptance/test-split-guard.yaml` (two-phase: warn-only current, blocking
  future), `automation/frontier.yaml` (`test_split_guard.status` unguarded → **warn-only**).
- **Behavior:** WARNS on `--split test`, `--split legacy`, and export/gate scripts invoked without
  `--split`; ALLOWS `--split val`, reading existing test CSVs, dashboard/scan/git/pytest. Never
  blocks; writes no guard log (disabled this phase); creates no tokens.
- **Tests:** fixture suite ALL PASS (14 classification cases + never-block + --split val silent +
  empty-command + static no-write check). Manual stdin: `--split test` warns exit 0; `--split val`
  silent exit 0; export-without-split warns; non-Bash tool ignored.
- **Activation note:** hooks load at session start; the hook activates on the next Claude Code
  session (the matcher itself was verified directly via the exact stdin path a hook uses).
- **Correction:** the earlier design's guard-log path `results/test_read_guard_log.csv` violated the
  no-write-results rule; relocated the (future, Phase-B-only) log to `automation/test_split_guard_log.csv`.
- **Not built:** blocking mode, guard log, authorization tokens (all Phase B / future).

## 2026-07-09 — Stage 6 scan_artifacts.py + artifact_manifest.csv + Overleaf-ready section built

- **actor:** skill/dashboard-build (Claude); **HEAD** `b140b04`.
- **Created:** `scripts/automation/scan_artifacts.py` (read-only; dry-run default; `--write`,
  `--manifest-out`), `scripts/automation/test_scan_artifacts.py`, `automation/acceptance/scan-artifacts.yaml`,
  and (via `--write`) `automation/artifact_manifest.csv` + `automation/artifact_manifest.meta.json`.
- **Edited (minimal, additive):** `update_dashboard.py` renders §8 inventory + §9 Overleaf-ready from
  the manifest and adds a staleness banner line. **No change to Stage 4/5 verify/approve logic.**
  `tasks.yaml` (DASH-S6 acceptance ref), `frontier.yaml` (overleaf block marked superseded).
- **Manifest:** 2512 artifacts. Evidence levels — frozen-test 5, validation-only 140,
  test-descriptive 1296, test-post-hoc 120, diagnostic-internal 951. Overleaf-ready — yes 42,
  candidate 2, no 2468.
- **Conservative labeling:** frozen-test is protocol-allowlist only (size 5); post-hoc read from the
  ledger `result_status` column; validation wins over any 'test'-in-filename signal; default
  diagnostic-internal.
- **Tests:** acceptance ALL PASS — dry-run writes nothing; `--write` writes only manifest+meta; two
  writes byte-identical; fabricated `FROZEN_TEST` name is NOT frozen-test; val file named with 'test'
  stays validation-only; 15/15 spot-check labels; every frozen-test row in the allowlist. Dashboard
  idempotency PASS; Stage 4/5 regression PASS.
- **Bug fixed mid-build:** initial ledger join read `source_type` instead of `result_status`, so
  post-hoc rows were mislabeled test-descriptive; corrected (120 test-post-hoc now).
- **Not built (later):** Notion push (S7), HTML view (S8), Stop-event reminder hook.

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
