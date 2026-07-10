# VAL-PILOT-GATE — Design Memo

**Version:** v0.2 (calibrated)
**Date:** 2026-07-09
**Status:** DESIGN ONLY. No code, no hook changes, no blocking mode, no tokens, no logs, no experiments, no validation runs, no test reads.
**Scope anchor:** complements the warn-only test-split-guard committed in `dbf658a` (stderr + exit 1, non-blocking).
**Change from v0.1:** §5 replaced with the user-calibrated STRONG-GO / REVIEW-GO / NO-GO scheme; three edge-case defaults accepted and folded in (§5.4); receipt schema and fixture list updated to match.

---

## 1. Purpose

**Why it exists.** Every defense candidate in this project (E→H, Option A/B, G1, BASAT line, D1–D13) has followed the same implicit ritual: train → validation-split evaluation → decide → only then consider a locked-test protocol. The ritual is currently enforced by discipline and memos, not by machinery. The val-pilot gate standardizes that ritual into a checkable definition: *a candidate has a "completed validation pilot" if and only if a specific, machine-verifiable evidence set exists* — so the question "is this test read authorized by a val pilot?" has a deterministic answer instead of a judgment call made mid-session.

**How it protects against validation/test mixing.** The two failure modes it targets are the ones this project has already brushed against: (a) a test-split evaluation launched for a candidate whose validation evidence was incomplete, stale, or belonged to a *different* checkpoint (the D10/D11 transfer failure was diagnosed post-hoc precisely because val→test linkage wasn't formalized), and (b) post-hoc test artifacts silently standing in as "evidence" for later decisions (the F20 post-hoc infeasibility finding). The gate makes val-evidence a precondition object with identity fields, so test reads can only ever be *matched against* validation history, never confused with it.

**How it supports F20 → R90F10.** The current fallback operating target (recall@FAR≤0.20) was shown to be a knife edge (D8b: 0.00028-wide), and the 2026-07-05 recommendation was to stop chasing F20 pre-defense. The path toward the real safety target (R90F10: recall ≥ 0.90 at FAR ≤ 0.10) requires many more candidate evaluations, all validation-only, before any of them earns a locked-test shot. The gate is the standardized funnel for that: cheap, repeatable, val-only candidate scoring with a conservative verdict, so frozen-test protocol attempts stay rare and pre-justified.

---

## 2. Definition of a completed validation pilot

A validation pilot for candidate *C* is **complete** iff all of the following exist and are internally consistent:

**Required files** (all under the candidate's results directory, e.g. `results/safety_guided_defense/<line>/<variant>/<seedN>/`):

1. **Probability export CSV, validation split** — matching the established naming convention: `<run_name>_pgd_probabilities_val_epsilon_<eps>.csv` (and the clean/FGSM counterpart if the candidate line evaluates them). The `val` token in the *filename* is necessary but not sufficient — see §3.
2. **Export metadata JSON** — the `*_metadata.json` written by `export_probability_predictions.py` (or the line's training script) alongside the CSV.
3. **Checkpoint file present at the recorded path** — the `.pt` referenced by the metadata must exist (checkpoints are never committed, but they must exist locally for the pilot to be verifiable and for a future test read to evaluate *the same weights*).
4. **Analysis/summary artifact** — the candidate's selection-candidates CSV or summary JSON containing the derived metrics (the pattern already used by `analyze_*` scripts and `defense_attempt_results_long.csv`).

**Required split:** validation only. Any artifact whose metadata records `split != "val"` is out of scope for pilot evidence regardless of its filename (§3, §8-I).

**Required metadata fields** (in the metadata JSON; names per existing exports):

- `checkpoint` (path as invoked) — plus, in the future scanner, a computed **SHA-256 of the checkpoint file** at scan time (see §4)
- `run_name`
- `seed`
- `split` — must literally be `val`
- `epsilon` (and `pgd_steps`, attack type)
- `model` / architecture tag
- timestamp of export
- source script + git commit of the code state if available (already recorded by some exporters; required going forward for new pilots, tolerated-absent for legacy ones with a NEEDS-REVIEW flag)

**Required metrics** (from the analysis artifact, PGD condition at the pilot's ε):

- fall **recall** and **FAR** at the candidate's declared operating threshold
- **AUROC**
- **recall@FAR≤0.20** (the F20 fallback axis; column `Rfall_at_FAR_020` in the existing long-format inventory)
- **recall@FAR≤0.10** if the threshold sweep covers it (`Rfall_at_FAR_010`) — required for any candidate claiming progress toward R90F10, optional for legacy pilots
- clean-condition recall/FAR (context metric; feeds the clean-degradation criterion in §5)

If any required element is missing, the pilot is **incomplete**. Incompleteness caused by missing metadata, checkpoint mismatch, or wrong split is a **NO-GO** (integrity failure, §5); incompleteness caused by metric-coverage gaps in otherwise-consistent legacy artifacts is **NEEDS-REVIEW**. Incompleteness is never silently upgraded.

---

## 3. Validation evidence rules

**Counts as validation-only evidence:**

- Artifacts whose *metadata* says `split: val`, whose filename `val` token agrees, and whose metrics were derived from that same CSV (analysis artifact references the CSV it consumed).
- Evidence produced *before* the candidate's first test read, under the same checkpoint hash.

**Does not count:**

- Anything derived from `--split test` or `--split legacy`, regardless of directory or filename.
- Filename-only claims: a CSV named `..._val_...` whose metadata says `test` (or has no metadata) — metadata is authoritative; disagreement → quarantine as NEEDS-REVIEW (§8-I).
- Post-hoc test artifacts reinterpreted as pilots (§8-J) — the D10/D11 lesson codified: test-derived numbers can never authorize anything.
- Aggregate/inventory rows (e.g., `defense_attempt_results_long.csv`) *alone* — the inventory is a convenience view; the pilot must trace to primary per-candidate artifacts.
- Smoke/self-check outputs (the existing `--smoke`/`--self-check` conventions already label these as "no scientific claim" — they are explicitly non-evidence).

**Preventing old/mismatched validation outputs from authorizing a future test read:**

- **Identity binding:** a pilot is bound to (checkpoint-hash, run_name, seed, epsilon). A test command matching on fewer fields does not match (§4).
- **Staleness rule:** the checkpoint file's content hash at test-read time must equal the hash recorded when the pilot was verified. Retraining that overwrites a `.pt` in place invalidates all pilots bound to the old hash automatically — no reliance on mtimes or human memory.
- **One-directional flow:** pilots are consumed by *matching*, never by *editing*. Nothing ever updates a pilot record to point at a new checkpoint.

---

## 4. Matching rule

A future test-split command (e.g., `export_probability_predictions.py --checkpoint X --run-name R --split test --epsilon E`) **matches** a completed validation pilot iff **all** of:

| Field | Rule |
|---|---|
| checkpoint | exact path match **and** SHA-256 content match against the pilot's recorded hash |
| run_name | exact string match |
| seed | exact match (from metadata; never inferred from filename alone) |
| epsilon | exact numeric match (0.03 ≠ 0.015 — the H15 dose-response work makes ε a first-class identity field) |
| threshold source | the operating threshold used for the test read must be the one frozen from the pilot's validation sweep, recorded in the pilot's analysis artifact — never re-derived on test |

**Why exact checkpoint matching (path + hash) beats loose filename matching.** This repo's own history is the argument:

- Checkpoint filenames encode selection criteria (`_maxrec_`, `_v2safety_`, `_bySafetyScore_`) and multiple "best" checkpoints coexist per seed/variant. Loose matching ("same variant, same seed") would let a `maxrec` pilot authorize a `minFA` test read — different weights, different frontier point.
- Checkpoints get overwritten by re-runs. A path-only match would happily pair a fresh retrain with last week's pilot metrics — exactly the stale-evidence hazard in §3. The content hash closes this.
- The D10/D11 transfer diagnosis showed val→test behavior is *not* stable across nearby model states; the only safe unit of authorization is the literal weight file, byte-identical.

Any partial match (right checkpoint, wrong ε; right run-name, different hash; etc.) is a **non-match** and reported as such with the specific mismatching field — never a fuzzy "close enough."

---

## 5. STRONG-GO / REVIEW-GO / NO-GO gate (user-calibrated, 2026-07-09)

Validation-only guidance for *whether a candidate merits consideration for a frozen-test protocol*. **Not thesis evidence; never quoted as a result. No verdict ever schedules or authorizes a test read.**

**Precedence rule:** integrity is evaluated first — any NO-GO integrity condition overrides all metric conditions, no matter how good the numbers are. Order of evaluation: NO-GO (integrity) → STRONG-GO → REVIEW-GO → NEEDS-REVIEW (default).

**Band convention:** REVIEW-GO bands are half-open (`[0.50, 0.70)`, `[0.88, 0.90)`) so a candidate at exactly 0.70 / 0.90 is evaluated under STRONG-GO criteria, never double-classified.

### 5.1 NO-GO (any one suffices; integrity conditions are terminal)

- **Integrity:** any test-derived evidence contamination anywhere in the pilot's lineage
- **Integrity:** missing metadata, checkpoint mismatch (path or hash), or wrong split
- **Performance:** AUROC clearly below 0.88 **and** low-FAR recall not improved over the existing frontier
- **Performance:** dominated by an existing candidate (operational definition in §5.4)

### 5.2 STRONG-GO (all required)

- Complete pilot (§2) passing all §3 evidence rules
- val PGD `Rfall@FAR≤0.10` ≥ **0.70**
- val PGD AUROC ≥ **0.90**
- clean recall degradation ≤ **5 pp**
- **Still requires explicit human approval before any frozen-test protocol** — STRONG-GO produces a proposal, never an authorization

### 5.3 REVIEW-GO (all required)

- Complete pilot (§2) passing all §3 evidence rules
- `Rfall@FAR≤0.10` in **[0.50, 0.70)** **OR** AUROC in **[0.88, 0.90)**
- Candidate is novel **or** improves low-FAR behavior (operational definitions in §5.4)
- **Requires at least one additional validation seed** before frozen-test consideration — single-seed REVIEW-GO can only ever escalate to "replicate," never to a test proposal

### 5.4 Accepted edge-case defaults (user-accepted 2026-07-09)

1. **Default bucket:** anything matching no category becomes **NEEDS-REVIEW** (human). The gate never guesses upward. Examples that land here: `Rfall@FAR≤0.10` ≥ 0.70 with AUROC ≥ 0.90 but clean degradation > 5 pp; `Rfall@FAR≤0.10` < 0.50 with AUROC ≥ 0.90; metric-coverage gaps in otherwise-consistent legacy pilots.
2. **Dominated (operational):** another **VERIFIED** pilot at the same ε and split has ≥ `Rfall@FAR≤0.10`, ≥ AUROC, and ≤ clean degradation, with **at least one strict improvement**. Comparison set = the frontier of prior VERIFIED pilots (G1 seed44 — PGD recall 0.600 / FAR 14.3% — is the current anchor).
3. **Improves low-FAR (operational):** `Rfall@FAR≤0.10` — or `Rfall@FAR≤0.05` where available — **strictly exceeds** the best existing candidate's value at the same ε. **Novelty remains a human judgment recorded in the receipt**, not computed.

**Calibration anchors** (context for the numbers, not part of the rule): current defense frontier best = G1 seed44 (PGD recall 0.600 / FAR 14.3%); BASAT-line PGD-AUROC ceiling ≈ 0.876 (representation-spanning per the capstone). The 0.88 NO-GO line sits just above the ceiling band; the 0.90 STRONG-GO line requires clearing it decisively.

---

## 6. Relationship to test-split-guard

- `test_split_guard.py` **remains warn-only exactly as committed** (`dbf658a`): stderr + exit 1 on R1–R4, exit 0 silent otherwise. This memo changes nothing about it.
- The val-pilot gate **never authorizes a test read automatically**. Authorization remains a human act; the gate only changes the *information content* of the warning.
- Future warning ladder (design intent only, no implementation now):
  - risky command **with** a matching completed pilot → `WARN-ONLY … matching val pilot found: <run_name>/<seed>/ε — proceed only if this is the approved frozen-protocol read`
  - risky command **without** a match → `WARN-ONLY … NO matching val pilot found (mismatch: <field>) — test read is outside the validation-first protocol`
- Both rungs stay exit 1 / non-blocking. **No blocking mode now**; exit 2 remains a documented future option requiring separate, explicit user approval.
- The guard stays read-only and pure-stdlib; if it ever consults pilot records, it reads them, never writes them (consistent with the fixture suite's static no-write check).

---

## 7. Dashboard integration

**Receipt (written later, by the scanner — not by the guard, and not now).** One JSON per verified pilot, e.g. `automation/val_pilot_receipts/<run_name>_<seed>_eps<eps>.json`:

```json
{
  "receipt_version": 2,
  "run_name": "…", "seed": 42, "epsilon": 0.03,
  "checkpoint_path": "…", "checkpoint_sha256": "…",
  "split": "val",
  "artifacts": {"probabilities_csv": "…", "metadata_json": "…", "analysis": "…"},
  "metrics": {"recall": 0.0, "far": 0.0, "auroc": 0.0,
              "rfall_at_far_020": 0.0, "rfall_at_far_010": null,
              "rfall_at_far_005": null,
              "clean_recall_degradation_pp": null},
  "gate_verdict": "STRONG-GO | REVIEW-GO | NO-GO | NEEDS-REVIEW",
  "novelty_judgment": null,
  "verified_utc": "…", "scanner_version": "…",
  "acceptance": null
}
```

(`novelty_judgment` is the human-recorded field required by §5.4-3; the scanner never fills it.)

**CLAIMED / VERIFIED / ACCEPTED** — reusing the dashboard's existing verification vocabulary:

- **CLAIMED** — a pilot asserted (by a session note, inventory row, or receipt stub) but not yet re-derived from primary artifacts.
- **VERIFIED** — the read-only scanner has confirmed §2 completeness + §3 consistency + hash binding from the artifacts themselves.
- **ACCEPTED** — the user has explicitly recorded approval of the verdict (same explicit-approval pattern the dashboard-refresh skill already uses; `acceptance` field populated). Only ACCEPTED + STRONG-GO pilots would ever be cited in a future test-protocol proposal.

**Dashboard views:** a val-pilot table (candidate × seed × ε → status, verdict, metric summary); a **validation-read count** per candidate (how many val evaluations each candidate has consumed — visibility against val-split overfitting, the quieter cousin of test leakage); and a candidate-status strip (how many pilots VERIFIED, how many ACCEPTED, none ever implying a test read is scheduled).

---

## 8. Fixture cases for future implementation

| # | Case | Expected outcome |
|---|---|---|
| A | Pilot present, all fields match | match found; verdict computed; (future ladder: "matching val pilot found") |
| B | Pilot absent entirely | no match; "no matching val pilot" |
| C | Checkpoint path matches, **hash differs** (retrained in place) | non-match, reason `checkpoint_hash` |
| D | **Run-name mismatch** (same checkpoint, different run label) | non-match, reason `run_name` |
| E | **Seed mismatch** (e.g., pilot seed42, command seed44 artifact) | non-match, reason `seed` |
| F | **Epsilon mismatch** (pilot 0.03, command 0.015) | non-match, reason `epsilon` |
| G | **Stale artifact**: pilot verified, checkpoint since overwritten | pilot auto-invalid, reason `stale_checkpoint` |
| H | CSV exists, **metadata JSON missing** | integrity failure → NO-GO, never a match |
| I | Filename says `test`, metadata says `val` (and vice-versa) | metadata authoritative; disagreement → quarantine/NEEDS-REVIEW, never evidence |
| J | **Post-hoc test artifact** offered as pilot (metadata `split: test`) | hard non-evidence; can never authorize anything; explicit test asserting this |
| K | Metrics match no verdict category (e.g., high recall/AUROC, clean degradation > 5 pp) | **NEEDS-REVIEW** (default bucket, §5.4-1) |
| L | Candidate weakly worse-or-equal on all three §5.4-2 axes vs a VERIFIED pilot, one strict | **NO-GO** (dominated); strict-improvement-on-one-axis counterexample must NOT be dominated |

Plus the standing meta-fixtures inherited from the guard suite: scanner is read-only (no writes outside its own receipt dir, and in fixture mode no writes at all), and no permission-decision tokens anywhere in guard source.

---

## 9. What must never happen

1. **No automatic test read** — no component of this design ever runs, schedules, or green-lights a `--split test` command.
2. **No frozen-protocol modification** — locked-test rules, frozen thresholds, and existing test artifacts are untouchable inputs.
3. **No token creation** — no authorization tokens, no bypass files; matching is computed fresh from artifacts every time.
4. **No results/ modification** — this design phase writes nothing under `results/`; the future scanner writes only its own receipts directory (`automation/val_pilot_receipts/`), never inside existing result trees.
5. **No thesis/Overleaf edits** — gate verdicts are workflow guidance, not thesis content.
6. **No blocking mode** — warn-only remains the contract until the user separately and explicitly orders otherwise.

---

## 10. Recommended implementation order (later, each step gated on user approval)

1. **Acceptance spec first** — freeze §2–§5 of this memo as the versioned, testable contract (this v0.2 already carries the calibrated thresholds).
2. **Fixture tests second** — implement §8 as a `val_pilot_gate_cases.py` suite against synthetic artifacts in a temp dir, before any real scanner exists (same test-first pattern that caught the `permissionDecision`-comment bug in the guard suite).
3. **Read-only scanner third** — `scripts/automation/val_pilot_scan.py`: walk results, verify pilots, print a report; zero writes in its first iteration.
4. **Dashboard receipt fourth** — enable receipt writing + CLAIMED/VERIFIED/ACCEPTED rendering via the existing `update_dashboard.py` path.
5. **Optional guard integration last** — the two-rung warning ladder in `test_split_guard.py`, still warn-only, only after the scanner has proven stable and only with explicit user sign-off.

---

*End of memo. v0.2 supersedes the in-chat v0.1 draft of 2026-07-09.*
