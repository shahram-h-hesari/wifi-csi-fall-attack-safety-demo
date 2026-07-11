# Dashboard changelog — APPEND-ONLY

Never edit or delete entries. Every state transition, plan change, and processed-receipt batch
appends here. At Stage 3+ the render script writes these entries; today they are written by hand.

---

## 2026-07-11 — RESEARCH-OS-MIGRATION-design: verification-contract strengthening (post-audit correction)

- **actor:** user-identified correction, following a read-only audit of the pushed
  `migrate/research-os-layer` branch; recorded by Claude. **HEAD** `54559c3`.
- The audit found the migration IMPLEMENTATION (not this design) contained defects and one
  unauthorized scope change against the THEN-accepted contract. This amendment strengthens the
  contract so those gaps cannot recur, without touching `research-os` in any way.
- **Absolute-path classification (new section `absolute_path_classification_policy`):** replaces the
  old unconditional "zero matches" wording with two explicit categories — `active_machine_path_matches`
  (must be exactly 0, hard gate, no exceptions) and `historical_documentary_literal_matches` (every
  occurrence individually enumerated by file/line/excerpt/justification and human-reviewed, never
  silently folded into a generic "pass"). A bare "scoped pass" string is now explicitly disallowed as
  acceptance evidence — directly correcting the audited implementation's self-authorized reclassification
  of a failing check.
- **`.gitattributes` policy (new section, exact decision made):** `.gitattributes` MAY be added for
  the migrated code paths, but `automation/receipts/** -text` is now a REQUIRED exclusion line —
  historical receipts must never be subject to line-ending normalization. The audit found 29 of 68
  shared receipts silently changed from CRLF to LF; the contract now requires any future
  implementation to restore exact source bytes and prove it via raw sha256 (not JSON-equivalence).
- **Durable active reverification (`actively_reverified_durable_and_rerunnable`):** `TOOL-REXP`,
  `DASH-D3`, `REG-EXPERIMENT-ID`, `REG-CANDIDATES`, `NEXT-EXP-REVIEW`, `DASH-NEXT-EXP-REVIEW`, and
  (newly added) `EXTERNAL-REPO-RESOLUTION` must each be verified via a durable, re-runnable,
  task-specific check from `research-os` — never the generic historical-receipt-hash shortcut the
  audit found applied uniformly to every task, which made a future resolver regression invisible to
  `--verify`.
- **`AUT-TSG-impl` exact annotation:** the dashboard must render, reachably, the exact statement
  "Historical acceptance only — operational enforcement remains in wifi-csi-fall-attack-safety-demo
  and is not active from research-os." The audit found the annotation mechanism existed in code but
  was unreachable (dead) for this task.
- **Byte-level status idempotency:** both `RESEARCH_DASHBOARD.md` and `automation/status.json` must
  be raw-sha256-identical across two consecutive renders with no source-fingerprint change — stronger
  than `--check` reporting PASS alone, since the audit observed `status.json`'s raw bytes differing
  across renders despite `--check` passing.
- **New `correction_consequences` section:** explicitly states the existing target-repository
  implementation claims (`093919Z`/`094307Z`/approval `094324Z`, at target commits `de0f1aa`/`5820d2d`)
  remain historical but are INSUFFICIENT for this corrected contract; a future implementation must
  capture a new `SOURCE_SNAPSHOT_SHA`, rebuild or update `migrate/research-os-layer`, and create a
  new superseding implementation claim and approval.
- **Design-only, nothing performed:** no file was migrated, copied, or moved; no file in `research-os`
  was modified, committed, pushed, or regenerated; `migrate/research-os-layer` and `main` were
  independently re-confirmed unchanged (`5820d2d9...` / `b997ed6a...`) both before and after this
  correction. No experiment, queue action, protocol change, merge, or held-out-test read occurred.

## 2026-07-11 — RESEARCH-OS-MIGRATION-design: source-snapshot self-reference correction

- **actor:** user-identified correction; recorded by Claude. **HEAD** `3021f12`.
- **Defect found:** the accepted contract's history-range upper endpoint was hard-coded to
  `ed50db0d62b755cd7aae9f00228665ba0cdb5750`. This design contract (and its own claim/approval
  receipts) was itself subsequently committed at `3021f1279ce8cdd9d5dd728e683d8376fb0f83ea` —
  **after** that endpoint — so following the old range literally would have **omitted the contract
  itself, its claims, and its approval receipt** from the migration inventory, directly violating the
  "entire automation directory / all historical receipts" policy.
- **Correction:** replaced the fixed endpoint with an execution-time `SOURCE_SNAPSHOT_SHA` policy
  (`repositories.source_snapshot_policy`). At migration-implementation preflight, the full 40-char
  HEAD of `wifi-csi-fall-attack-safety-demo`'s `feature/safety-proxy-guided-defense` is captured
  fresh, verified to have `3021f1279ce8cdd9d5dd728e683d8376fb0f83ea` (`minimum_required_ancestor`) as
  an ancestor, verified to exactly match `origin/feature/safety-proxy-guided-defense`, and verified
  clean (no tracked modifications/staged files) — then the source repository is **frozen** for the
  remainder of the migration; any change before target-side validation completes aborts the run.
  `f64d5626d3b159f85988668f0a86281035678e93` (the repo's own root commit) remains the fixed,
  permanent lower bound (`research_os_history_floor`) since it can never become stale.
  `3021f1279ce8cdd9d5dd728e683d8376fb0f83ea` is recorded **only** as a minimum-ancestor floor, **not**
  as a new hard-coded snapshot — deliberately avoiding reproducing the same self-referential staleness
  with this very correction's own future commit. A re-run capturing a different snapshot than a prior
  attempt must fail visibly unless a new migration claim explicitly supersedes the earlier one.
- All history-extraction commands (`git subtree split`, `git format-patch`) now reference
  `SOURCE_SNAPSHOT_SHA` symbolically instead of the stale literal endpoint; the target base
  (`b997ed6aba4e3395c3b02eef951b3536450b8961`) is unchanged.
- `automation/tasks.yaml` and this changelog were **not** re-edited beyond this append — the task
  registration's title does not reference the stale endpoint, so no change was needed there.
- **Design-only, nothing performed:** no migration branch, history extraction, patch generation,
  copy, deletion, merge, experiment, queue action, protocol change, or held-out-test read occurred.
  `research-os` confirmed untouched (still `b997ed6a`, clean). A new superseding design claim was
  created; the prior superseded claim, active claim, and approval receipt from the `3021f12` commit
  all remain byte-unchanged and historical.

## 2026-07-11 — RESEARCH-OS-MIGRATION-design: Research OS migration Phase 2 design contract (corrected)

- **actor:** user-approved design step, corrected after review; recorded by Claude. **HEAD** `ed50db0`.
- New design-only contract `automation/acceptance/research-os-migration.yaml` for a controlled,
  **history-preserving relocation** of the Research OS layer (dashboard, registries, acceptance
  contracts, receipts, reviews, automation) from `wifi-csi-fall-attack-safety-demo` into
  `research-os`, using the now-ACCEPTED external-repository resolver
  (`EXTERNAL-REPO-RESOLUTION`, 52/52) so experiment evidence is never copied.
- **Migration inventory:** `RESEARCH_DASHBOARD.md`, `automation/` (entire directory), and
  `scripts/automation/` (entire directory) **except** `test_split_guard.py` /
  `test_split_guard_cases.py`, which remain in the experiment repository — an explicit, documented
  exception, since the `.claude` PreToolUse hook that invokes them protects the experiment
  repository's own git/shell operations and would silently stop firing there if moved. Also covers
  the relevant `.gitignore` line and `.claude/skills/dashboard-refresh/SKILL.md`.
- **Exclusion inventory:** `results/`, `figures/`, checkpoints/model weights, `scripts/analysis/`,
  `scripts/archive/`, dataset/training code, experiment execution scripts, thesis-specific files
  (`EXPERIMENT_EVIDENCE_INDEX.md`, `LOCAL_PROJECT_MAP.md`, `README.md`, etc.), and
  `.claude/skills/git-stage-check/SKILL.md` — all remain sole-sourced in the experiment repository.
- **Correction 1 — dependency policy:** a new, minimal `automation/requirements.txt`
  (`PyYAML==6.0.3`, `pytest==9.1.0` — the complete non-stdlib import set of every
  `scripts/automation/*.py`, verified by grep) is authored fresh for the target, scoped inside
  `automation/` rather than the repo root; the source repo's full `requirements.txt`
  (numpy/pandas/matplotlib/scipy/scikit-learn/jupyter/streamlit/torch) is explicitly NOT copied.
  A clean-venv import + full `pytest` pass from `research-os` is now a required validation step.
- **Correction 2 — target collision inventory:** a read-only inventory of the actual `research-os`
  repository at `b997ed6a` found it is **not empty** — it is an existing, operating Markdown-ledger +
  Claude-Code-agent "Weekly PhD Research OS Agent" (`dashboard.md`, `CLAUDE.md`, `state/*.md`,
  `lanes/*.md`, `guardrails/*.md`, `.claude/agents/research-os.md`, `.claude/commands/*.md`) that
  already reads `wifi-csi-fall-attack-safety-demo` via a documented sibling-folder convention (a
  pre-existing, different mechanism this migration does not touch). One real, blocking collision was
  found: the target's `.gitignore` blocks `*.csv`, which would silently swallow
  `automation/artifact_manifest.csv` — resolved via an explicit, labeled **append** (never overwrite)
  adding a negation plus the migrated local-override ignore line. `RESEARCH_DASHBOARD.md` vs. the
  target's own `dashboard.md`, and `.claude/skills/` vs. the target's own `.claude/agents/` /
  `.claude/commands/`, are flagged as naming-ambiguity notes (no technical collision) — both pairs
  coexist unmodified. No target file is silently overwritten; any unresolved collision hard-stops.
- **Correction 3 — one exact history-preservation procedure:** `git subtree split` for `automation/`
  and `scripts/automation/`, run in a **temporary, disposable clone** (never the working checkout),
  over a verified, exact 27-commit range (`f64d5626`..`ed50db0d`) confirmed to contain **zero**
  commits mixing migrated and excluded paths; `git format-patch`/`git am` for
  `RESEARCH_DASHBOARD.md` and `SKILL.md`; the single `.gitignore` line is explicitly **not**
  format-patched (whole-file patch tooling is the wrong mechanism for a one-line addition to a
  structurally different target file) but added as a manually-authored, provenance-recorded content
  addition instead. Includes duplicate-import detection and documented rerun-safety (delete-and-retry
  a partial branch, never silently append a second import).
- **Correction 4 — migration provenance record:** a new, separate
  `automation/migration_provenance.yaml` (never an edit to any historical receipt) maps historical
  receipt/task identity → source repository/commit context, with a fixed interpretation policy
  (every legacy 7-character `git.head` value is **always** read as the source repository, never
  reinterpreted as `research-os`) and explicit `"unresolvable"` reporting for any hash that cannot be
  resolved — never silently accepted. Verification now distinguishes three claim categories:
  historical source-repository, reverified cross-repository, and new target-repository (full SHAs).
- **Correction 5 — per-task target-state classification:** every migrated task now has an explicit
  target state — historical ACCEPTED (REG-GOALS, REG-DATASETS, REF-EVID, REG-PAPERS, etc.),
  actively-reverified ACCEPTED (TOOL-REXP, DASH-D3, REG-EXPERIMENT-ID, REG-CANDIDATES/
  NEXT-EXP-REVIEW/DASH-NEXT-EXP-REVIEW), or the special case `AUT-TSG-impl` — **excluded from active
  target-state computation** in `research-os` since its enforcement files don't migrate; the
  dashboard must render this exclusion explicitly and never present it as actively reverified.
- **Correction 6 — unambiguous 10-step sequence:** migration validation (create branch → import →
  configure a **local-only, uncommitted** external-repo override → validate → create+approve the
  migration claim → **push, non-force**) is now steps 1–7 and is **strictly separate** from the
  main-branch merge/authority transition (step 8) and source decommission (step 10), each its own
  later, separately-approved task. Rollback (deleting the unmerged branch) applies only to steps 1–7;
  `VALIDATION-PILOT-GATE` resumes **only after step 8** actually completes, never merely after an
  unmerged, validated branch passes tests.
- **Design-only, nothing performed:** no migration branch created, no file copied/moved/deleted in
  either repository, no remote changed, no history merged, no `git subtree`/`filter-repo`/
  `format-patch`/`cherry-pick`/`bundle` command run, no real local override created. `wifi-csi-fall-
  attack-safety-demo` remains authoritative; `VALIDATION-PILOT-GATE` implementation remains paused;
  `research-os` confirmed untouched (still at `b997ed6a`, clean working tree).
- Task `RESEARCH-OS-MIGRATION-design` registered in `automation/tasks.yaml` as its own gated design
  task (`depends_on: [EXTERNAL-REPO-RESOLUTION, EXTERNAL-REPO-RESOLUTION-design]`).

## 2026-07-11 — EXTERNAL-REPO-RESOLUTION: external repository resolver implementation

- **actor:** implementation step by Codex on branch `feature/safety-proxy-guided-defense`.
- Added the Phase 1 resolver layer defined by
  `automation/acceptance/external-repo-resolution.yaml`: governance-repository resolution remains
  distinct from explicit external repository resolution; external repositories resolve only through
  the tracked portable registry plus the gitignored local override; no sibling-folder inference,
  network access, repository mutation, evidence copying, or Research OS migration is introduced.
- Added `scripts/automation/repo_resolver.py` with full 40-character commit-SHA capture, exact
  local `origin` remote-string verification, required-path checks, dirty-worktree policy handling,
  path traversal and absolute-path rejection, allowed-evidence-root enforcement, symlink-escape
  rejection via realpath, deterministic typed errors, deterministic public metadata, zero-config
  same-repository fallback, and bounded legacy bare-path compatibility.
- Added the tracked zero-config registry `automation/registry/external_repositories.yaml` and the
  committed safe template `automation/local/external_repository_paths.example.yaml`; the real
  machine-local override `automation/local/external_repository_paths.yaml` is explicitly ignored by
  `.gitignore` and was not created.
- Added `scripts/automation/validate_external_repositories.py` and
  `scripts/automation/test_repo_resolver.py` using synthetic temporary local Git repositories only.
  Existing scanner, Result Explorer, and dashboard code now use the shared governance root and accept
  repository-aware metadata without changing legacy outputs in same-repository mode.
- Registered implementation task `EXTERNAL-REPO-RESOLUTION` as gated and dependent on the accepted
  design plus the relevant dashboard/result/identity/artifact-scanning tasks.

## 2026-07-11 — EXTERNAL-REPO-RESOLUTION-design: Research OS migration Phase 1 design contract

- **actor:** user-approved design step; recorded by Claude. **HEAD** `890a1e6`.
- New design-only contract `automation/acceptance/external-repo-resolution.yaml` for a future
  **repository-resolution layer** (Research OS migration Phase 1) that removes the current hard
  assumption — `REPO = Path(__file__).resolve().parents[2]` in `scan_artifacts.py` /
  `update_dashboard.py` — that Research OS automation and experiment evidence must share one Git
  repository.
- Defines a **two-layer configuration model**: a tracked, portable
  `automation/registry/external_repositories.yaml` registry (repository_id, expected remote URL,
  allowed evidence roots, dirty-worktree policy, claim boundaries — never an absolute local path) +
  a gitignored, machine-local `automation/local/external_repository_paths.yaml` override (repository_id
  → absolute checkout path only, never committed, never in a receipt).
- Defines the future resolver's responsibilities: resolve governance-repo root and each external
  evidence-repo root through **distinct** code paths; resolve every evidence reference as
  `(repository_id, repository_relative_path)`, never a bare string; **never** infer an external
  repository from sibling-folder layout; verify existence, Git-worktree validity, exact remote-URL
  match, required-path presence, a full 40-character commit SHA, and the configured dirty-worktree
  policy before any read; reject path traversal, absolute evidence paths, and symlink escape
  (via realpath resolution) outside `allowed_evidence_roots`; remain strictly read-only and
  network-free against every external repository (no fetch/clone/checkout/pull/reset/merge/push);
  fail visibly (never silently fall back or guess) on every listed error condition.
- **Commit/provenance policy:** distinguishes the Research OS governance-repository commit from each
  external experiment-repository commit — both recorded as full 40-character SHAs in any *future*
  cross-repository claim. Historical receipts (every existing receipt's ambiguous 7-character
  `git.head`) are explicitly **not** reinterpreted, rewritten, or backfilled — they remain read as
  single-repository-era historical records.
- **Path migration policy:** legacy bare-string paths (`results/...`, `checkpoints/...`, etc.) are
  not rewritten by this design; a bounded legacy-compatibility mode is defined (valid only while
  exactly one experiment `repository_id` is configured) with an explicit removal condition once every
  reference is migrated to explicit `(repository_id, repository_relative_path)` pairs — a separate,
  later, explicitly-approved task.
- Lists future-only changes needed in `scan_artifacts.py`, `result_explorer.py`,
  `update_dashboard.py`, every path/evidence validator, artifact-manifest handling, experiment
  identity, reference evidence, `frontier.yaml`, candidate-review inputs, receipt creation, dashboard
  status generation, and every test currently assuming one repository root — **none implemented by
  this contract**.
- **Design-only, nothing implemented:** no resolver module, no
  `automation/registry/external_repositories.yaml`, no `automation/local/external_repository_paths.yaml`
  (or its example template), no synthetic-repository test suite. No Research OS file was moved,
  copied, or deleted; no migration branch or `research-os` file was created; no queue entry, pilot
  proposal, protocol-freeze record, or experiment occurred. `VALIDATION-PILOT-GATE` implementation
  remains paused, unaffected by this step.
- Task `EXTERNAL-REPO-RESOLUTION-design` registered in `automation/tasks.yaml` as its own gated
  design task (`depends_on: [DASH-D3, TOOL-REXP, REG-EXPERIMENT-ID]`), following the
  `VALIDATION-PILOT-GATE-design` precedent of explicit task registration.

## 2026-07-11 — VALIDATION-PILOT-GATE-design: Validation-pilot gate design contract (Step 15)

- **actor:** user-approved design step; recorded by Claude. **HEAD** `34648b4`.
- New design-only contract `automation/acceptance/validation-pilot-gate.yaml` for a future
  **Validation-Pilot Gate** that reads a human-authored pilot proposal for ONE selected experiment
  candidate and answers only: "is this candidate specified clearly and safely enough to be
  proposed for a validation-only pilot?" It explicitly never answers scientific-success guarantee,
  run authorization, queue entry, held-out-test access, frozen-protocol use, or final scientific
  approval.
- **Distinct from the existing, still-unimplemented AUT-VPG task** (`val-pilot-gate.yaml`): AUT-VPG
  will eventually EXECUTE a validation-split evaluation and compute a numeric AUROC/recall gate;
  this new gate only reviews a WRITTEN PROPOSAL and never runs code or touches val/test data —
  strictly upstream of any such execution.
- Defines a full pilot-proposal schema (**25 fields** incl. `research_question`, `hypothesis`,
  `claimed_material_difference`, `explicit_prohibition_on_held_out_test_access`,
  `pilot_size_and_bounded_scope`, `seed_plan`, `success_criteria`, `failure_and_stop_criteria`,
  `provenance_requirements`, `claim_boundaries`), nine **separately reported** gate dimensions
  (never one opaque score), three outcomes (`READY-FOR-HUMAN-APPROVAL` / `NEEDS-REVISION` /
  `BLOCKED`, precedence BLOCKED > NEEDS-REVISION > READY), 14 hard-`BLOCKED` rules, 11
  `NEEDS-REVISION` conditions, and explicit `READY` conditions. Every `READY-FOR-HUMAN-APPROVAL`
  outcome must state, verbatim, **"Suitable for human pilot-approval review only."** and that this
  does not authorize execution.
- **Held-out-test policy (section 3b) is unconditional:** any request/implication/comparison/
  tuning/read of held-out-test data is `BLOCKED` with no exception; an existing accepted frozen
  protocol never lifts this, never contributes to `READY`, and a `protocol_id` may be recorded
  only as contextual dependency information pointing to a separate, later, human-run
  protocol/test-review stage — this gate never authorizes, prepares, or short-circuits held-out-
  test use under any outcome.
- **Task `VALIDATION-PILOT-GATE-design` is registered in `automation/tasks.yaml`** (kind: design,
  gated, `depends_on: [NEXT-EXP-REVIEW, REG-CANDIDATES]`) as its own separate design task —
  distinct from the future `VALIDATION-PILOT-GATE` implementation task, which will be registered
  separately when the gate itself is built.
- **No gate implementation, pilot proposal (for AFAC or any other candidate), experiment-queue
  entry, execution script, or protocol-freeze record was created.**

## 2026-07-11 — DASH-NEXT-EXP-REVIEW: Candidate review added to research dashboard (Step 14)

- **actor:** user-approved implementation; recorded by Claude. **HEAD** `a6ef7d5`.
- New `scripts/automation/dashboard_candidate_review.py` renders a generated
  `## 2b. Next-Experiment Candidate Review — Human Decision Required` section into
  `RESEARCH_DASHBOARD.md`, purely by **displaying** the already-accepted
  `automation/reviews/next_experiment_review.yaml` verbatim — review_id, source_fingerprint,
  GO/REVIEW/NO-GO counts (**0 / 6 / 2**), the accepted rank order for all 8 candidates, each
  candidate's verdict/reasons/blockers/required-human-actions/material-difference status, and the
  highest-ranked candidate (`candidate_afac_low_far_calibration_v1`, REVIEW).
- **Never recalculates, reinterprets, reranks, or overrides** any verdict the Brainstorm Checker
  (NEXT-EXP-REVIEW) already produced — the renderer contains no verdict-derivation logic at all
  (statically test-enforced: no `dataset_readiness ==`, `allowed_split ==`, `derive_verdict`, etc.
  in the renderer source).
- **A prominent warning** states no verdict authorizes running an experiment, entering the
  experiment queue, using a frozen protocol, or accessing held-out test data — GO is explicitly
  "suitable for human planning review only." Candidates 1–6 (REVIEW) require human planning
  review; candidates 7–8 (NO-GO) are blocked (dataset-blocked / `no_experiment_allowed`). AFAC
  (`candidate_afac_low_far_calibration_v1`) is **not** approved to run.
- **Honest degradation:** if `automation/reviews/next_experiment_review.yaml` is missing,
  malformed, or structurally inconsistent (duplicate/missing `candidate_id`, non-contiguous ranks,
  summary counts disagreeing with its own entries), the section renders a visible **INTEGRITY
  WARNING** instead of silently omitting the section or fabricating data.
- Tests `test_dashboard_candidate_review.py`: **17/17 ALL PASS** (section renders, exact rank
  order, exact counts, all 8 candidates exactly once, verdicts match, NO-GO blockers shown, D13/D14
  material-difference statuses shown, required human actions shown, no-execution warning present,
  missing/invalid review → integrity warning, deterministic/idempotent, existing sections
  unaffected, candidate registry + experiment queue unchanged by rendering, no verdict
  recomputation, no source mutation). Regression: dashboard-research-summary 18/18, result-explorer
  40/40, next-experiment-brainstorm-checker 39/39 + validator PASS, experiment-candidates 33/33 +
  validator PASS, paper-registry 28/28 + validator PASS, experiment-identity 32/32 + validator
  PASS, approve/verify suites ALL PASS — all unaffected.
- Task **DASH-NEXT-EXP-REVIEW** registered in `automation/tasks.yaml` (gated; depends on
  NEXT-EXP-REVIEW, DASH-D3).

## 2026-07-10 — NEXT-EXP-REVIEW: Read-only Next Experiment Brainstorm Checker implemented

- **actor:** user-approved implementation; recorded by Claude. **HEAD** `af19644`.
- New `scripts/automation/next_experiment_brainstorm_checker.py` (read-only) reads the accepted
  registries, **re-resolves every candidate reference** (paper/gap/dataset/goal/evidence/
  evaluation/protocol/repo-relative path — unresolved forces NO-GO, never silently omitted), and
  derives a deterministic GO/REVIEW/NO-GO verdict per candidate from the accepted policy
  (`acceptance/next-experiment-review.yaml`). It reports four **separate** dimensions
  (scientific_promise / practical_readiness / data_readiness / split_safety — never one opaque
  score), ranks deterministically (verdict > data_readiness > allowed_split > evidence_strength >
  candidate_id), and is idempotent via a `source_fingerprint`.
- **Generated** `automation/reviews/next_experiment_review.yaml` over the 8 accepted candidates:
  **0 GO, 6 REVIEW, 2 NO-GO, 0 unresolved references.** The 6 fall/walking candidates are REVIEW
  (indirect-only literature, literature gaps, `available_not_evaluated`, or prior D13/D14 negative
  evidence with only a *stated* material difference); the 2 data-acquisition candidates are NO-GO
  (`dataset_blocked` / `no_experiment_allowed`, `future_fall_risk_prediction` empty
  `allowed_evidence_levels`). No candidate reaches GO under the current evidence.
- **Material-difference is derived, not stored:** prior negative evidence + no stated difference →
  `missing` → NO-GO; + a stated difference → `stated_unverified` → capped at REVIEW; the checker
  **never certifies** a claimed difference is sufficient (human scientific review required). D13
  and D14 are referenced by pointer, never re-typing their result tables.
- **GO means "Suitable for human planning review only"** — never permission to run, enter the
  queue, read held-out test data, or use a frozen protocol. The checker's only write target is the
  review file; it never modifies a registry or `automation/experiment_queue.yaml`, imports no
  subprocess/network module, and constructs no runnable command (statically test-enforced).
- Validator `validate_next_experiment_review.py` (rebuilds from source + independent structural
  scans): **PASS**. Tests `test_next_experiment_brainstorm_checker.py`: **39/39 ALL PASS**.
  Idempotency proven (byte-identical second generation). Task **NEXT-EXP-REVIEW** registered in
  `automation/tasks.yaml` (gated; depends on REG-CANDIDATES/REG-PAPERS/REG-GOALS/REG-DATASETS/
  REF-EVID/REG-EXPERIMENT-ID). No dedicated dashboard section was added.

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
