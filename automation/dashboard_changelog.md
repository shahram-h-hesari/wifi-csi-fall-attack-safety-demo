# Dashboard changelog — APPEND-ONLY

Never edit or delete entries. Every state transition, plan change, and processed-receipt batch
appends here. At Stage 3+ the render script writes these entries; today they are written by hand.

---

## 2026-07-10 — REG-CANDIDATES: Evidence-grounded experiment-candidate registry created

- **actor:** user-approved implementation; recorded by Claude. **HEAD** `d09937f`.
- New `automation/registry/experiment_candidates.yaml` implements the accepted design contract
  (`automation/acceptance/experiment-candidates.yaml`, hash-bound, not modified): **8 candidate
  records** covering AFAC low-FAR calibration, Neyman-Pearson FAR control, low-FAR partial-AUC
  objective, temporal/event-level FAR reduction, ensemble/gating, walking-detection baseline,
  gait/mobility data acquisition, and future fall-risk data acquisition.
- **No manually asserted verdict anywhere** — GO/REVIEW/NO-GO remains exclusively a future,
  separately-implemented Brainstorm Checker's computed output; the validator rejects any
  verdict-named field or unexpected schema field (which is also how queue auto-promotion is
  blocked).
- **Prior negative evidence is structurally required, not optional**, for directly related
  candidates: the partial-AUC candidate cites D14's failed validation gate (all 3 primary
  conditions failed across 6 pre-registered runs); the ensemble/gating candidate cites D13's
  narrowly-failed shared-input transfer veto (short by 0.0022). The validator enforces this
  (rejects a candidate in either direction that omits the corresponding negative-evidence
  reference).
- **AFAC F20 is never presented as frozen evidence** — the validator cross-checks every AFAC
  reference against `reference_evidence.yaml`'s actual `test-post-hoc` level and scans note text
  for an unqualified "frozen" claim.
- **2 candidates are dataset-blocked** (`no_experiment_allowed`): gait/mobility data acquisition
  (targets `walking_pattern_recognition` + `gait_or_mobility_change_detection`, both `NO_DATA`)
  and future fall-risk data acquisition (`NO_DATA_ASPIRATIONAL`, empty `allowed_evidence_levels`).
  Dataset readiness is validator-enforced to agree with each target goal's own registry status.
- **No candidate authorizes a test read**: every candidate's `allowed_split` is either
  `validation_only` or `no_experiment_allowed`; the validator enforces split/frozen-protocol/
  test-read-risk coherence so a `validation_only` candidate cannot smuggle in a frozen-protocol
  reference, and a hypothetical `requires_new_frozen_protocol` candidate can never claim low risk.
- Validator `validate_experiment_candidates.py` (read-only, no network, no PDF/checkpoint
  requirement, deterministic): real registry **PASS, zero errors** (candidates=8,
  literature_support_entries=27, literature_gap_refs=4, prior_negative_evidence_candidates=2,
  dataset_blocked=2). Tests `test_experiment_candidates.py`: **33/33 ALL PASS**.
- **Task REG-CANDIDATES registered** in `automation/tasks.yaml` (gated, depends on REG-PAPERS,
  REG-GOALS, REG-DATASETS, REG-EXPERIMENT-ID, REF-EVID). **No later layer implemented**: the
  Brainstorm Checker, validation-pilot gate, experiment-queue integration, and dashboard rendering
  of candidates all remain separate, later, explicitly-approved tasks.

## 2026-07-10 — D4a-1: Local-source academic paper registry created

- **actor:** user-approved implementation; recorded by Claude. **HEAD** `131bcea`.
- New `automation/literature/paper_registry.yaml` (+ policy `automation/literature/README.md`):
  **47 canonical papers, 48 citation keys**, backfilled READ-ONLY from local cited sources only —
  the thesis repository's `references.bib`, the D1--D12 literature-framing appendix, and chapter
  citations. **No web access, API lookup, or download occurred**; every record is
  `verification_status: local_bib_only` with external metadata verification explicitly deferred
  to D4a-2.
- **D1--D12 and foundational literature deduplicated:** all 36 D1--D12 anchor citations (34 unique
  papers; `kannan2018adversarial` spans D4+D9, `narasimhan2013partialauc` spans D6+D8) plus
  robust-optimization/PGD (`madry2018towards`), FGSM/adversarial-training foundations, SenseFi,
  TRADES/GAIRAT/SAT, NP/partial-AUC/ROC operating-point anchors, ensemble/gating,
  temporal-false-alarm, walking-detection, and gait/fall-risk anchors. The bib-header-documented
  alias `narasimhan2013pauc` → `narasimhan2013partialauc` is consolidated onto ONE record;
  WiCAM vs WiCAM2.0 deliberately NOT merged. Internal labels (AFAC, BASAT, H15, D-codes) are
  never papers.
- **Paper claims separated from Research OS interpretation:** `paper_contribution_summary`
  restates only what the local framing says a paper reports; `relevance_to_current_results` is
  prefixed "OUR INTERPRETATION:"; per-paper `claim_boundaries` forbid image-domain→CSI transfer
  claims, paper-benchmark-as-our-result claims, and any clinical/deployment claim. One genuine
  local metadata conflict recorded honestly (`miyato2018vat` title differs between the bib and
  the D9 framing table) — represented as `conflicting_local`, not silently resolved.
- **Literature gaps recorded honestly (5):** UT-HAR-origin publication not separately cited;
  probability-calibration literature missing for the low-FAR AFAC direction; temporal
  false-alarm anchors are wearable-domain only; no gait-pattern-labeled CSI dataset; no
  longitudinal WiFi-CSI fall-risk cohort. Gaps are first-class records — no paper was invented.
- Validator `validate_paper_registry.py` (read-only, no network, no PDF requirement,
  deterministic): real registry **PASS, zero errors**. Tests `test_paper_registry.py`:
  **28/28 ALL PASS** (P1--P25 + 3 defensive extras).
- **Experiment recommendations are NOT implemented** — no experiment-candidate registry, no
  Brainstorm Checker, no dashboard literature section (D3 rendering untouched). Receipt:
  `REG-PAPERS` claim (requires user approval).

## 2026-07-10 — D3: Markdown research-evidence rendering added

- **actor:** user-approved implementation; recorded by Claude. **HEAD** `73b3aca`.
- New `scripts/automation/dashboard_research_summary.py` renders a generated
  `## 2. Research Evidence & Canonical Identity` section into `RESEARCH_DASHBOARD.md` (BEGIN/END
  `AUTO:RESEARCH-EVIDENCE` markers): a research-evidence snapshot, one entry per curated reference-
  evidence key, an F20/R90F10 target-assessment table, goal/dataset readiness, and a safety/
  evidence legend. This is still the Markdown dashboard -- the HTML dashboard (DASH-S8) remains
  untouched and deferred.
- **Canonical display names are the primary label** for every rendered reference evaluation;
  historical codes (`H15`, `D8b`, `D8`) appear only as secondary structured legacy aliases, sourced
  verbatim from Result Explorer's own `experiment_identity` block -- never re-matched or
  independently inferred by the renderer.
- **Architectural authority rule enforced and tested:** the renderer calls
  `result_explorer.run_query()` in-process for every scientific metric and identity value; it reads
  `reference_evidence.yaml` only for `(key, goal)` routing pairs (never metrics/thresholds/
  aliases); F20/R90F10 comparator operators and thresholds are parsed from `goals.yaml`
  `success_targets[*].rule` text, never hardcoded. A static test (`D3-13`) proves the production
  module contains no hardcoded canonical ID, display name, or H15/AFAC metric literal.
- **H15 preserved as an unverified legacy alias** (`meaning: null, meaning_status: unverified`);
  **F20 and R90F10 status are always evidence-qualified** (e.g. "F20 boundary, test-post-hoc";
  "R90 recall component reached, FAR component not reached; frozen-test at ε=0.015") -- never a
  bare pass/fail badge, and H15 never receives an R90F10 pass.
- **Mobility/fall-risk data gaps shown honestly** -- `walking_detection` renders "dataset-supported
  but not yet evaluated"; `walking_pattern_recognition`, `gait_or_mobility_change_detection`, and
  `future_fall_risk_prediction` render "data needed" (`walking_pattern_recognition` and
  `gait_or_mobility_change_detection` additionally note "no supporting dataset locally"), all
  derived from each goal's own registry `status` field -- never hand-written per goal.
- **Safe degradation states implemented and tested:** identity `unavailable`/`mismatch` always
  keep the scientific evidence visible while suppressing only the canonical identity; a
  provenance-mismatch/refused reference withholds metrics entirely; a missing reference renders an
  honest empty state with no stale metrics retained (the section rebuilds fresh every render).
- Tests: `scripts/automation/test_dashboard_research_summary.py` new, 18/18 pass (D3-1..D3-15 +
  2 extra checks), plus a real-committed-registry smoke render. Regression: Result Explorer 40/40,
  identity suite 32/32, approval/verifier suites ALL PASS -- all unaffected. Receipt-impact
  analysis (read-only, before this claim) confirmed no existing task's hash-checked evidence
  references `scripts/automation/update_dashboard.py`'s content, and an empirical post-edit
  `--verify` confirmed zero drift across every previously-ACCEPTED task; no superseding claim was
  required for any existing task. **HTML remains deferred** (DASH-S8 not started).

## 2026-07-10 — D2e-2: Result Explorer enriched with canonical experiment identity

- **actor:** user-approved implementation; recorded by Claude. **HEAD** `894e786`.
- Curated reference-evidence results (`H15_eps0015_frozen`, `AFAC_eps0030_F20_posthoc`) now carry
  a supplemental `experiment_identity` block sourced from the D2e-1 registry -- **scientific
  evidence remains authoritative and unchanged**: metrics, evidence_level, attack, epsilon, split,
  threshold, and manifest provenance are never altered by enrichment; identity is attached only
  after the existing D2d-2 scientific resolution + manifest cross-check has already succeeded.
- **H15 displayed as a legacy alias with unverified expansion** -- `meaning: null,
  meaning_status: unverified` shown verbatim, never invented.
- **Identity mismatch never overrides metrics** -- a conflicting or ambiguous identity mapping
  (wrong epsilon, wrong evidence level, duplicate mapping, unresolved run) degrades to
  `experiment_identity.state: mismatch` with the trusted scientific row completely untouched and
  no canonical ID ever shown; a missing/absent identity source degrades to `state: unavailable`.
  Matching is exact-key only (`reference_evidence_key`) -- H15/D8/D8b/A1/H1 are never valid
  standalone lookup values, never fuzzy-matched.
- **D3 rendering remains deferred** -- this step only enriches Result Explorer's own output; no
  dashboard sections were added.
- Tests: 40/40 (24 pre-existing F1-F15+extras unmodified + 16 new I1-I15/I4b). Identity-suite
  regression 32/32 (the D2e-1 claim receipt's own summary said 31/31 due to an earlier counting
  error, never corrected since receipts are append-only; the actual verified count has been 32/32
  throughout). Receipt: superseding `TOOL-REXP` claim (requires user approval); `REG-EXPERIMENT-ID`
  unaffected (none of its hashed artifacts changed) -- remains ACCEPTED with no new receipt.

## 2026-07-10 — D2e-1: Experiment Identity & Naming Standard added

- **actor:** user-approved implementation; recorded by Claude. **HEAD** `2e75cdd`.
- Added a parallel identity layer (`automation/registry/experiment_identity.md` policy +
  `experiment_identity.yaml` registry + read-only `validate_experiment_identity.py`) separating
  **run identity** (training/checkpoint provenance) from **evaluation identity** (attack/epsilon/
  split/evidence conditions), with mandatory readable display names and structured legacy aliases.
- **Readable names added** for the two curated reference-evidence entries: H15 -> "AFAC frozen-test
  evaluation under PGD epsilon=0.015"; the AFAC F20 entry -> "AFAC post-hoc F20 operating point
  under PGD epsilon=0.030".
- **H15 preserved as a legacy alias** -- the letter "H" has no authoritative expansion anywhere in
  the repository (exhaustively searched); recorded honestly as `meaning: null, meaning_status:
  unverified`, never guessed.
- **Proven, not assumed:** H15 and the AFAC eps=0.030 post-hoc result share one underlying run --
  confirmed by independently re-hashing the checkpoint file on disk against the SHA256 documented
  in the H15 frozen-test protocol (exact match). D8b (not bare D8) verified field-for-field against
  its defining `Target()` entry in `scripts/analysis/plot_d1_d12_recall_far.py`. A1 recorded
  honestly as a genuine reused/ambiguous alias (two unrelated objects), never silently resolved.
- **No historical artifact renamed** -- zero edits to `results/`, existing receipts, or any other
  `automation/registry/*.yaml` file; `reference_evidence.yaml`'s keys are cited, not touched.
- **Result Explorer integration deferred** to a future, separately-approved step; D3 dashboard
  rendering of canonical names is likewise not started. This step only creates and validates the
  identity registry (31/31 tests pass; validates against the real committed registry with zero
  errors). Receipt: `REG-EXPERIMENT-ID` (requires user approval).

## 2026-07-10 — D2d-2: curated reference resolution + manifest cross-check in Result Explorer

- **actor:** user-approved implementation; recorded by Claude. **HEAD** `eb0c6f6`.
- **Added to `scripts/automation/result_explorer.py`:** a named `reference_evidence_query` now
  resolves FIRST against an optional `sources['reference_evidence_yaml']` curated registry
  (`automation/registry/reference_evidence.yaml` in production, byte-unchanged by this step). An
  exact-key hit returns exactly one row after cross-checking its provenance paths (explicit
  allowlist: `confusion_csv`, `result_report`, `source_file`) against the manifest -- every path
  must exist there and the manifest `evidence_level` must agree with the curated entry's declared
  level (and `required_manifest_evidence_level`, when present). Duplicate keys refuse
  (`duplicate_curated_key`); any missing path or evidence-level disagreement refuses
  (`provenance_mismatch`) with zero metrics returned -- never a fabricated or manifest-only row.
  No curated source configured, or key not curated -> falls through UNCHANGED to the pre-existing
  (D2c) goals.yaml-driven ledger-filter path.
- **Real-data smoke queries (read-only):** `H15_eps0015_frozen` and `AFAC_eps0030_F20_posthoc`
  each returned exactly one curated result with `manifest_cross_check: pass` against the real
  committed manifest and results -- no fabrication, no `--split`, no experiment/eval script run.
- **Tests:** `scripts/automation/test_result_explorer.py` gained F12-F15 + 6 extra focused cases;
  24/24 pass, all 12 pre-existing F1-F11 unmodified and still green (proves the fallback path is
  untouched). `test_approve.py` + `test_verify.py` re-run unaffected.
- **Acceptance spec:** `automation/acceptance/result-explorer.yaml` status marker updated
  (`IMPLEMENTED_D2_PENDING_D2D2` -> `IMPLEMENTED_D2D2_PENDING_D3`); the contract itself (curated-
  first rule, cross-check rule, `provenance_mismatch`, F12-F15) was already accurate from D2d-1.
- **Receipt impact:** `TOOL-REXP` regressed to CLAIMED-UNVERIFIED (its two hashed files changed) --
  superseding claim + re-approval via the corrected CLI. `REF-EVID` unaffected (its only hashed
  artifact, `reference_evidence.yaml`, is byte-unchanged) -- no new receipt needed.
- **Not done this step:** D3 (dashboard rendering), experiment/H15 naming standard. No
  `results/`, ledger, manifest, `goals.yaml`, or `reference_evidence.yaml` file was modified.

## 2026-07-10 — Safety fix: approvals bound to the exact claim receipt (AUT-APPROVAL-BIND)

- **actor:** user-approved safety task; recorded by Claude. **HEAD** `3251764`.
- **Root cause:** `has_user_approval(task_id, receipts)` checked ANY user-kind receipt for a
  task_id, ignoring which claim it approved -- a newer claim silently inherited ACCEPTED from an
  older approval that had never seen it. Found live during REG-GOALS reconciliation; a read-only
  historical inventory then showed it also affected `AUT-TSG-impl` (its only approval predates the
  auditable-warning-contract claim that superseded the original claim it approved).
- **Fix (`scripts/automation/update_dashboard.py`):** new `active_claim_for_task()` (claims only,
  never an approval receipt, also fixing a latent bug where a same-day-later approval could be
  mistaken for the newest claim) + `claim_approved_by()` (exact `approved_claim_receipt_id` [+
  `approved_claim_sha256`] match, or a deterministic legacy rule for pre-fix approvals: applies
  only to the claim active at the approval's own timestamp, never to a later one).
  `write_approval()` now always stamps the binding; `do_approve()` resolves and binds to the
  current active claim; the `[Awaiting your approval]` count now dedupes by active claim per task.
- **Tests (`scripts/automation/test_approve.py`):** rewritten — original R1-R4 fixed (fixtures
  gained `receipt_id`) + new suite A-H (exact/old/new/wrong-task/hash-mismatch/legacy-format/CLI
  mechanism) + a synthetic reproduction of the real incident. All pass; `test_verify.py` unaffected.
- **Historical migration (read-only inventory, no receipts fabricated or edited):** applying the
  rule to real repo receipts regresses exactly one task, `AUT-TSG-impl`, from ACCEPTED to
  VERIFIED-AWAITING-APPROVAL -- correctly so; user may re-approve via `--approve AUT-TSG-impl`.
  `REG-GOALS` and all other single-claim/single-approval gated tasks are unaffected.
- **Not done this step:** D2d-2, experiment/H15 naming standard, any real re-approval of
  `AUT-TSG-impl`. Receipt: `AUT-APPROVAL-BIND` (requires user approval via the corrected CLI).

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
