# Registry — Research OS layer (goals + dataset capabilities)

SOURCE-OF-TRUTH, user-approved, hand-maintained. Two files:

- **`goals.yaml`** — every WiFi-sensing goal this research program tracks, with task-aware metric
  keys, success targets, allowed evidence levels, data needs, grant relevance, and clinical-claim
  boundaries. **Missing data is first-class information**: a goal with `status: NO_DATA` is a
  recorded data need, not a failure.
- **`datasets.yaml`** — what each dataset actually supports. The `supported_goals` /
  `unsupported_goals` split is an integrity gate: no tool may synthesize a metric for a pair the
  registry marks unsupported.

## Conventions

1. **Validation-first defaults.** Every `default_query_fields` / `recommended_first_query` uses
   `split: val`. Known test/frozen evidence is preserved only as explicit, named
   `reference_evidence_queries` (read-only lookups of already-committed artifacts — never new reads).
2. **No unearned evidence.** A goal's `allowed_evidence_levels` may include `frozen-test` only if a
   frozen protocol exists for it (today: only `fall_detection`, via
   `H15-TEST-EPS0015-AFAC-20260705`). Goals without verified result rows must not claim results.
3. **Metric keys bind to real columns.** `fall_detection.primary_metric_keys` are exact columns of
   `results/defense_attempt_inventory/defense_attempt_results_long.csv`. Non-fall goals declare
   their metric names ahead of data; a lookup tool must report them as "defined, not evaluated".
4. **No clinical claims.** `clinical_claim_boundary.forbidden` is binding on every rendered view.

## Label-map provenance (UT-HAR)

`datasets.yaml` label indices were read (read-only, 2026-07-10) from the repo's own analysis code,
identical in all four locations checked:

- `scripts/analyze_safety_guided_seed.py:39`  (canonical source recorded in the registry)
- `scripts/analyze_variantE.py:35`
- `scripts/analyze_variantF.py:32`
- `scripts/analysis/h15_e0_hard_window_inventory.py:127`

`{0: lie down, 1: fall, 2: walk, 3: pickup, 4: run, 5: sit down, 6: stand up}` — fall = 1, walk = 2.

## Curated reference evidence (`reference_evidence.yaml`, D2d-1)

`automation/registry/reference_evidence.yaml` is a **hand-curated, user-approved source-of-truth**
that makes a small number of important, already-known results queryable by name (today: the H15
frozen-test PASS and the canonical AFAC post-hoc F20 operating point).

- **It must never override manifest evidence levels.** Every entry points at committed artifacts;
  a resolver must cross-check those paths against `automation/artifact_manifest.csv` and refuse
  (never render) if the manifest disagrees with the entry's declared `evidence_level`.
- **It points to committed artifacts and receipts** — it records numbers already published
  elsewhere (frozen-test confusion CSVs, post-hoc analysis reports); it does not generate, derive,
  or infer any metric itself.
- **It exists specifically to avoid backfilling `results/defense_attempt_inventory/
  defense_attempt_results_long.csv` by hand** — editing that ledger was evaluated (D2d design memo,
  "Option A") and rejected: the ledger is a derived, protected-path file, and a hand-inserted row
  would have no derivation trail and would trip the dashboard's protected-path integrity gate.

## Consumers

- **Result Explorer v1** (`scripts/automation/result_explorer.py`, D2 — future): read-only lookup of
  existing ledger/manifest rows, joined through these registries. Never runs experiments.
- **Dashboard rendering** (D3 — future, separate approval): active-goal chip, dual thesis/mobility
  track, missing-data section. No renderer changes shipped with D1.

Acceptance specs: `automation/acceptance/goal-registry.yaml`, `automation/acceptance/dataset-registry.yaml`.
