# CSI Sentinel — Agent & Skills View (local mirror)

> **This is a plain-text mirror of the CSI Sentinel claude.ai artifact**, kept here so any
> local tool (Codex, grep, a future renderer) can read it without web/artifact access.
> Source of truth for the *data* is `RESEARCH_DASHBOARD.md` (this repo) + the research-os
> program dashboard; this file is a curated summary, updated by hand alongside the artifact.
> Live styled version: https://claude.ai/code/artifact/0f907387-ae53-4736-a839-9e23913eba62

Last synced: 2026-07-20 — the three redundant standalone artifacts (Research OS Architecture
`dd0cc064…`, Research Intelligence Workflow `dc0b8dc0…`, Combined Architecture and Operational
Workstreams Map `9766d8e9…`) are **deleted** (user action, 2026-07-20), after a verified
content-parity check confirmed every real gap was migrated first: all six Architecture §02–§07
sections, all 25 RI Workflow task records (23 phase-counted + 2 `notRICount`-labeled
Validation-Pilot Gate tasks), and one residual §01 gap (Publications/future-research-agent as
Knowledge Base consumers + the bidirectional feedback-loop note) added as an addendum to the
Canonical Information Flow section. All three URLs are now dead; every reference to them across
the artifact family (CSI Sentinel, VLR, Thesis Chapter View) was found and repointed to the
Control Center's `#architecture-workstreams` / `#panel-ri` anchors before the deletion. The
Research OS Control Center is now the sole artifact for architecture/workstreams content — a
four-artifact family (Control Center, VLR, CSI Sentinel, Thesis Chapter View). The
Priority 1 (Validation-Pilot Gate) card is a full-width card above four equal secondary cards; a
collapsed "How Stage 3, Validation-Pilot Gate, and Stage 4 relate" section makes explicit that
Stage 3 / Phase 3C is NOT a formal Stage 4 dependency — only Validation-Pilot Gate acceptance is.
All five Current Position cards remain populated by the Control Center's single live priority
engine (one dataset, one calculation — no static duplicate). Full detail and the canonical
priority queue live in [Research OS Control Center — Current Work
Priorities](https://claude.ai/code/artifact/f155b23f-cb75-4710-ab64-5da8b52b1931#current-work-priorities)
— the canonical answer to "what should I work on now, and what can I work on in parallel?" and
"how does Stage 3 relate to Stage 4?" This file stays a concise summary, not a duplicate of the
full task registry.

## Mission

One agent, five duties: read the literature, keep the evidence registries current, propose
gated experiments, prepare attack/defense evaluations, and export thesis- and grant-ready
evidence. Skills are a shared library — the agent is the role that composes them.

**Hard rule:** the agent never reads held-out test data. Frozen reads are one-shot and
human-approved.

## Phase-1 targets (corrected framing)

- **PROMISE — F20 @ ε=0.015**: recall ≥0.80, FAR ≤0.20. **PASS, frozen-test** (recall 0.9111,
  FAR 0.1319). Shareable now.
- **PROMISE — F20 @ ε=0.030**: post-hoc knife-edge only (~0.00028-wide band); verify whether
  the written proposal pins this epsilon.
- **STRETCH — R90F10 @ ε=0.015 (unpromised)**: val-feasible on `ST1b6_lowFA`
  (0.9545/0.0951). **First provenance-VERIFIED hash-bound validation pilot** (regen byte-
  identical to audited originals). Gate verdict held at NEEDS-REVIEW pending clean-degradation
  definition.
- **R90F10 @ ε=0.030 (research goal)**: not met.
- **FGSM @ ε=0.015**: evidence exists and is now hash-bound for ST1b6 (corrects an earlier
  "no admissible evidence" note) — feasibility audit possible with zero new runs.

## Skills board

**Built & working:** `dashboard-refresh`, `test-split-guard` (hook), `git-stage-check`,
`candidate-review`, `graphify`, `verifiable-literature-review`.

`verifiable-literature-review` (research-os) — the real, built PDF-to-Markdown research skill:
source PDF → identity/provenance → reliable parsing → local evidence retrieval → priority-aware
selection → bounded evidence packet → candidate source-statement drafting → exact-quote verification →
independent page re-localization → visual escalation → human ratification + receipt. Finalized
and checkpointed (commit `98980ad`, 131 tests passing). Artifact:
[claude.ai/code/artifact/dcc9eb8d-e965-4012-b83f-36a95c7650e6](https://claude.ai/code/artifact/dcc9eb8d-e965-4012-b83f-36a95c7650e6).
This is distinct from `literature-intake` below, which is this repo's own not-yet-built local
wrapper/interface to the pipeline, not the pipeline itself.

**Designed, not built:** `protocol-freeze`, `experiment-queue`, `ledger-sync --audit`.

**val-pilot-gate (`AUT-VPG`) — design only, step 1/5 as of 2026-07-18 (corrected):**
1. Acceptance spec / design memo — ACCEPTED (receipt `2026-07-10T064710Z`, user-approval `2026-07-10T065209Z`)
2. Fixtures — NOT started. No `val_pilot_gate_lib.py` or `test_val_pilot_gate_cases.py` exists in the repo.
3. Real `results/`-walking scanner — NOT started. No `val_pilot_scan.py` exists in the repo.
4. Dashboard receipt rendering — not started
5. Guard integration — not started

This corrects a stale prior claim ("step 3/5, fixtures + scanner done") that did not match the
actual repo file state — verified 2026-07-18 by direct file search and `git log`; found no trace
of the fixtures/scanner files ever existing. `dashboard_changelog.md` independently confirms:
"Design only: no implementation, no scanner" and the fixtures→scanner ladder is "CONDITIONAL on
separate future user approval (none authorized yet)."

**`AUT-VPG` (val-pilot-gate) is a separate task from `VALIDATION-PILOT-GATE` (ROS-15).** They
share overlapping vocabulary but are different capabilities: AUT-VPG will eventually execute a
real validation-split scientific evaluation; VALIDATION-PILOT-GATE is a read-only reviewer of a
human-authored pilot *proposal* and never runs code or touches val/test data. **Only
VALIDATION-PILOT-GATE blocks program Stage 4** — AUT-VPG does not appear in
`DASH-UPGRADE-STAGE-4`'s `depends_on` at all.

**VALIDATION-PILOT-GATE real status (discovered 2026-07-18, previously not reflected anywhere):**
implementation exists and passes its own tests — `scripts/automation/validation_pilot_gate.py`
(407 lines, commit `a17cdd6` "ROS-15: implement Validation-Pilot Gate per accepted design
contract") and `test_validation_pilot_gate.py` (21/21 passing, re-verified 2026-07-18). No claim
receipt has been filed, so `automation/status.json` still shows `not_started` — this repo's
discipline is that nothing counts as claimed until a receipt exists, regardless of whether the
code is written. **This is the actual next actionable task**: file a claim receipt and get human
review — not "write the code," which is already done.

**Scope, confirmed 2026-07-18:** VALIDATION-PILOT-GATE is one of the 44 global Research OS task
records (`automation/tasks.yaml`), category **Experiment Workflow** — a curated display grouping
derived from its native `kind: tool` field and its role unblocking Stage 4, not a literal
`category:` field in the registry and not guessed from its name. It is **not** part of the
Research Intelligence Workflow (Phases 3A–3D), which is tracked separately and proceeds
independently in parallel. The full category breakdown (all 9 categories, summing to 44), the
selectable A/B/C/D progress-scope blocks, and the color legend (rose = "work on this now," never
"part of Research Intelligence") live in the Control Center's "Progress hierarchy and scope"
panel.

## Research-os program mapping

| Program stage | This repo's equivalent | Status |
|---|---|---|
| 3A — Candidate Review Foundation | candidate registry + checker + `candidate-review` skill | aligned, VERIFIED |
| 3B — Paper Intelligence | `candidate_claims.py` bounded-input selector + `verifiable-literature-review` skill (below) | Selector contract frozen 07-17; PaperQA2 buy-vs-build evaluation closed 07-17 (custom pipeline kept) |
| Stage 4 — Experiment Workflow | blocked on `VALIDATION-PILOT-GATE` (ROS-15), NOT `val-pilot-gate`/`AUT-VPG` | corrected 2026-07-18 — see val-pilot-gate section above |

## Paper-intelligence pipeline (Stage 3B, cross-repo with research-os)

- **B1 `docling convert`** — built, tested (research-os). PDF → Tier-1 raw MD.
- **B2 `paper-extract`** — built (Codex, research-os). All 6 pilot records claims+identity
  verified (36 claims, Crossref cross-check caught 1 real upstream DOI/venue bug). Pilot
  ACCEPTED, Stage 3B closed.
- **Bounded-input selector / candidate-claim drafting stage (`candidate_claims.py`)** — the
  current active sub-thread, aimed at hundreds-of-papers scale. Design → two-mode selector
  (standard/complex) → 2-paper tuning benchmark (12/12 recall) → 3-paper **blind** held-out
  benchmark (structurally diverse: unusual/experimental/survey) → selector v1 failed blind
  validation (2/6–6/6 recall depending on paper; 83–88% request-token overhead found) →
  targeted fix spec → **v2 built** (document-family-aware synthesis budget reservation,
  case-insensitive header matching, late-section protection for surveys) → **fragmentation
  floor and serialization-overhead fixes still open** → blind re-validation authorized,
  scoped: passing recall does not by itself clear the selector for economical-model drafting
  until overhead/fragmentation are also fixed.
- File: `research-os/scripts/automation/candidate_claims.py` (+ `test_candidate_claims.py`).
- No model drafting, real-paper processing, or authoritative-record changes have occurred at
  any point in this sub-thread — design/build/validation only.

## Pickup point (if you stop today)

**The real next actionable task (corrected 2026-07-18):** file a claim receipt for
`VALIDATION-PILOT-GATE`'s already-implemented, already-tested (21/21) ROS-15 implementation and
get it human-reviewed — see the Control Center's "Next actionable task" card for full detail.
This directly unblocks program Stage 4.

**Other open threads:**
1. **wifi-csi repo** — interpret the ST1b6_lowFA clean-degradation definitional question.
2. **research-os repo** — blind benchmark re-validation of `adaptive_sentence_window_knapsack.v2`
   is authorized but not yet run; roadmap-source disagreement (thesis roadmap vs. dashboard
   task) flagged by Codex, unresolved.

Model ladder: `haiku·low` mechanical → `sonnet·low–med` routine code → `opus·med–high`
multi-file/debug → `fable·high–max` research & claim boundaries. Anything touching claim
boundaries, frozen protocols, or threshold selection is always fable.
