# Experiment Identity & Naming Standard (D2e-1)

**Status:** design + initial backfill for two evaluations. Read-only registry; not yet consumed by
Result Explorer (that integration is a separate, future step). Nothing historical is renamed.

## Why this exists

Historical labels like `H15`, `D8`, `G1`, `A1`, `H1` are useful internal shorthand, but none of
them, alone, tell a reader the research goal, dataset, method, attack, epsilon, evidence level, or
protocol behind a result. This standard adds a **parallel identity layer** — canonical IDs and
readable display names — without touching a single historical file, directory, receipt, or key.

## The four-part identity model

### 1. Run identity (`run_id`)

A run identifies **training/model/checkpoint provenance**, independent of any particular attack
evaluation. One trained checkpoint = one run, however many times it is later evaluated under
different attacks, epsilons, or splits. A run record's provenance is anchored on the checkpoint's
own SHA-256 whenever that can be verified (see `identity_status` below) — not on a filename guess.

### 2. Evaluation identity (`evaluation_id`)

An evaluation identifies the **conditions under which a run (or, for legacy backfills, an artifact
whose run cannot be confidently established) was evaluated**: attack, epsilon, split, evidence
level, and threshold/protocol. The same run can have many evaluations (e.g. the same checkpoint
evaluated at ε=0.015 under a frozen protocol, and again at ε=0.030 via a post-hoc threshold sweep
— exactly the H15 / AFAC-F20 pair below, which this backfill proved share one run).

### 3. Human-readable display name

A short sentence a researcher can read without opening any file, e.g. *"AFAC frozen-test
evaluation under PGD ε=0.015."* Every evaluation record MUST have one (rule 5, §Identity safety
rules). Display names never encode raw letter-number codes as the only content.

### 4. Legacy aliases

Historical labels (`H15`, `D8b`, `A1`, …) are preserved as **structured** alias records — never
bare strings — each carrying `alias_type`, `meaning`, `meaning_status`, `source_paths`, and a note.
Aliases are searchable and citable but never override canonical identity, and an unverified alias's
`meaning` field stays `null` rather than being guessed (see **Important uncertainty rule** below).

### 5. Reference-evidence keys

`automation/registry/reference_evidence.yaml`'s existing keys (`H15_eps0015_frozen`,
`AFAC_eps0030_F20_posthoc`) are the pre-existing, user-approved, stable lookup keys Result Explorer
already resolves (D2d-2). **They are immutable and out of scope for renaming.** This standard adds
canonical evaluation identity *alongside* them (`reference_evidence_key` field on the evaluation
record), never replacing or aliasing over them.

## Important uncertainty rule (binding)

Do not guess what `H`, `H15`, `D8`, `G1`, `A1`, or any other historical code means. Only an
authoritative, quoted, cited repository artifact may set `meaning_status: verified`. Everything
else — including highly plausible reads (e.g. "H15" *might* stand for "Hypothesis 15") — stays:

```yaml
meaning: null
meaning_status: unverified
note: "Historical internal label; expansion not asserted."
```

Proximity, chronology, or a plausible-sounding pattern is never sufficient evidence.

## Canonical ID format

**snake_case, lowercase, repository-safe, no spaces, no uppercase historical codes as the sole
content.** Two patterns:

```
run_<goal>_<dataset>_<method>_<verified-disambiguator>_v<version>
eval_<goal>_<dataset>_<method>_<attack>_eps<epsilon-token>_<evidence-token>_v<version>
```

**Epsilon tokens** — deterministic, unambiguous mapping from the decimal value:

```
0.015 -> eps0p015
0.030 -> eps0p030
```

Rule: replace the decimal point with `p`; strip no trailing digits (`0.030` keeps its trailing
zero — `eps0p03` would collide with a differently-rounded value and is disallowed). The validator
checks this algorithmically (§ validator rule "epsilon ID token consistency") — no ad hoc tokens.

**Evidence tokens** used in evaluation IDs: `frozen_test`, `test_posthoc`, `validation_only`,
`test_descriptive`, `diagnostic_internal` — one-to-one with `reference_evidence.yaml` /
`goals.yaml` evidence-level vocabulary (underscored instead of hyphenated, to stay snake_case).

**Examples** (the two backfilled below):

```
eval_fall_detection_sensefi_ut_har_afac_pgd_eps0p015_frozen_test_v1
eval_fall_detection_sensefi_ut_har_afac_pgd_eps0p030_test_posthoc_v1
```

## Method-family and method-variant labels

`method_family` is the defense/algorithm family (e.g. `AFAC`); `method_variant` is the specific
selector/setting within that family (e.g. `optionB_AFAC`, matching the ledger's existing
`method_internal_name`/`approach_group` vocabulary verbatim — this standard never invents a new
method vocabulary, it cites the existing one).

## Evidence-level naming

Evidence levels are copied verbatim from `automation/registry/goals.yaml` /
`automation/artifact_manifest.csv` (`frozen-test`, `validation-only`, `test-descriptive`,
`test-post-hoc`, `diagnostic-internal`). The identity registry never introduces a competing
evidence-level vocabulary.

## Versioning

- `_v1`, `_v2`, … suffix on both run and evaluation IDs.
- **A changed protocol** (different threshold rule, different pre-registration, different success
  criterion) → **new evaluation ID/version**, even if run and conditions are otherwise identical.
- **A changed training run** (retrained checkpoint, different weights) → **new run ID**, never a
  version bump reusing the old run ID — a run ID names one specific checkpoint's provenance.
- Re-evaluating the *same* run under the *same* conditions with the *same* protocol does not
  warrant a new ID; the existing ID's provenance is updated only via a superseding registry entry
  (registry files follow the same append/supersede discipline as `automation/receipts/`).

## How evaluations of one run receive separate evaluation IDs

Each `(attack, epsilon, split, evidence_level, protocol)` tuple on a given run is its own
evaluation record with its own `evaluation_id`, linked back via `run_id`. The H15/AFAC-F20 backfill
is the worked example: one run, two evaluation IDs, one differing only in ε and evidence level.

## How legacy backfills may remain partially unresolved

A **new** experiment (anything created after this standard lands) must have a resolvable `run_id` —
no `null` run links going forward (rule 15). A **legacy backfill** describing pre-existing evidence
may honestly record:

```yaml
run_id: null
run_link_status: unresolved_legacy
identity_status: partial_legacy
```

only when the underlying run genuinely cannot be established from committed artifacts. This is not
a loophole for new work — it exists solely so that old evidence can be given a readable identity
without fabricating provenance that was never recorded at the time.

## Why historical artifacts are not renamed

Renaming `results/.../frozen_h15_test_confusion.csv`, the protocol ID
`H15-TEST-EPS0015-AFAC-20260705`, the reference-evidence keys, or any receipt would break
provenance chains that other committed artifacts (manifest entries, ledger rows, prior receipts,
frozen-protocol registries) already cite by exact path/ID. The whole point of a parallel identity
layer is to add readability **without** that risk. Historical strings are frozen exactly as any
other already-committed evidence is frozen.

## Relationship to Result Explorer (D2d-2) and future integration

This registry is **read-only reference material** as of D2e-1. `scripts/automation/
result_explorer.py` is not modified in this step and does not consult
`experiment_identity.yaml`. A future integration step (not this one) may add canonical
display names alongside Result Explorer's existing `evidence_level`/`source_file`/`provenance`
output — deferred deliberately so the identity registry can stabilize independently first.
