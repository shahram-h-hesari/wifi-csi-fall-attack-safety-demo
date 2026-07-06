# H15-E0 — Hard-Window Inventory + Cross-Model Union-Oracle Audit (Phase 0)

Date: 2026-07-05. Evidence type: **validation-only, saved-scores-only diagnostic.** No training,
no checkpoint loaded, no attack generated, no test-split file opened, read, or referenced. All
union/oracle numbers below are **DIAGNOSTIC ONLY and non-deployable** — they use per-model
thresholds with hindsight window assignment and answer only whether the fall windows H15 needs
are separable by *any* existing model, not whether any deployable rule achieves it.

Script: `scripts/analysis/h15_e0_hard_window_inventory.py`
Outputs: `results/defense_attempt_inventory/h15_e0_hard_window_inventory/` (7 CSVs, 5 plots,
`h15_e0_key_numbers.json`).

Operating rule used to define "hard" (validation-only, pre-registered in the H15 roadmap Gate 0):
per-model threshold τ_m = max val recall s.t. val FAR ≤ **0.12** (FP ≤ 54/452), tie-break lower
FAR then higher τ — the same frozen rule used by every committed selection in this ledger.
Hard fall for model m = fall window scoring < τ_m; hard non-fall = non-fall window scoring ≥ τ_m.
Caps 0.10 and 0.15 are reported as sensitivity, not as the gate.

---

## 1. Executive conclusion

**H15 is NOT mechanistically plausible from the existing validation artifacts, and the
pre-registered Gate 0 FAILS on both of its conditions.**

- **8 of the 44 validation fall windows are missed by every one of the 24 saved score axes**
  (9 training families, 2 representations, including the BiLSTM pilot) at the FAR-0.12 budget.
  Gate 0 allowed at most 4.
- Consequently the **union oracle over all 24 axes reaches only TP 36/44 (recall 0.818)** at
  FAR ≤ 0.12 — below the required 40/44 (0.909). Even a hindsight oracle that picks, per fall
  window, the best model ever trained in this project cannot reach the H15 validation gate.
- Because any fusion/ensemble of existing models is mathematically upper-bounded by this union,
  **fusion is excluded by arithmetic**, independent of the already-failed D13 transfer veto.
- The one alternate representation on file (BiLSTM finetune) rescues **zero** of the
  universally-missed falls — it has ≈0 recall at this budget (val PGD-AUROC 0.726).

Per the roadmap's stop rule 1 (Phase-0 data-limit stop): **the H15 chase stops here, before any
training compute is spent.** The 8 never-rescued windows behave as information-poor under PGD
ε=0.030 at the window level: their maximum fall-probability across all 24 models is 0.14–0.31,
while every healthy model's FAR-0.12 threshold sits at 0.10–0.42.

---

## 2. Artifact inventory

### Used (24 validation PGD ε=0.030 probability exports; all verified 496 windows, 44 fall /
452 non-fall, identical `sample_id` and true-class sequence — alignment asserted in-script)

| Family (9) | Representation | Score axes used (24) | Source |
|---|---|---|---|
| AFAC_optionB (D8b ref) | LeNet | `optionB_maxscore` (rep), `B_optBminFA` | `afac_score_frozen_threshold_followup/val_eval/`, `dual_specialist_safety_gate/A1/seed42/probabilities/` |
| GR1_gairat (D10) | LeNet | `v2macroF1` (rep), `v2lowFA`, `v2safety` | `boundary_aware_selective_at/gairat/seed42/GR1/val_eval/` |
| SA1_sat (D11b) | LeNet | `v2lowFA` (rep), `v2macroF1`, `v2safety` | `boundary_aware_selective_at/sat/seed42/SA1/val_eval/` |
| ST1_beta3p0 | LeNet | `v2lowFA` (rep), `v2macroF1`, `v2safety` | `boundary_aware_selective_at/seed42/beta3p0/val_eval/` |
| ST1b6_beta6p0 (D11a) | LeNet | `v2lowFA` (rep), `v2macroF1`, `v2safety` | `boundary_aware_selective_at/seed42/beta6p0/val_eval/` |
| D14_pauc_rank | LeNet | config-B `seed44` (rep), `seed43` | `d14_partial_auc_low_far_ranking/config_B/seed4x/val_eval/` |
| variantD | LeNet | `seed42` (rep), `seed43` | `decision_analysis/validation_probabilities/` (reduced schema; `predicted_label` mapped to class names, mapping verified against each file's own true columns) |
| G1_hardneg | LeNet | `G_G1_v2safety` seed44 (rep), `B_G1lowFA`, `R_G1maxrec` seed42 | `variantG_targeted_hardneg/seed44/test_eval/` (provenance quirk: file is a genuine 496-row **val** export despite the folder name — verified), `dual_specialist_safety_gate/A1/seed42/probabilities/` |
| BiLSTM_finetune (representation pilot) | **BiLSTM** | `v2macroF1` (rep), `v2maxrec`, `v2safety` | `variantG_bilstm_representation_test/seed42/g1_finetune_cleaninit/val_eval/` |

Also consulted (context only, no scores re-used): D13 stage-0 overlap/oracle artifacts
(`d13_score_fusion/stage0_validation_complementarity_audit/`) and the D14 gate reports.

### Missing / not usable

- **D14 config A (all seeds) and config B seed42 validation exports** — never written
  (`CLEAN_GUARD_FAILED_NO_VALIDATION_EXPORT` per the D14 gate report).
- **variantE / variantF validation PGD exports** — only test-side exports exist for those pilots;
  excluded (this audit opens no test files).
- `provenance/appendices/internal_defense_experiment_ledger/` — directory does not exist in the
  working tree (noted previously in the D10/D11 diagnosis; nothing here depends on it).

---

## 3. Hard fall-window analysis: universal core + rotating fringe

Per-model FAR-0.12 operating points (`per_model_operating_points.csv`): best single model is
AFAC_maxscore at TP 26/44 (recall 0.591, τ=0.2006); healthy LeNet representatives span TP 18–26;
the two variantD seeds and the BiLSTM axes are non-competitive at this budget (recall 0.00–0.07;
val PGD-AUROC 0.65–0.73).

Structure of the missed falls (`cross_model_hard_window_overlap.csv`):

- **Universal core: 8/44 falls (18%) are missed by all 24 score axes** — sample_ids
  69, 70, 88, 89, 94, 97, 99, 103. Their PGD fall-probability never exceeds 0.14–0.31 in any
  model (mean across models 0.03–0.13). Argmax destinations (AFAC view): lie down ×3, walk ×2,
  run ×2, pickup ×1 — several are "post-fall-stillness"-type confusions, not just motion-class
  confusions.
- **11/44 are missed by all 8 LeNet family representatives**; the BiLSTM rescues none of them
  (its recall at this budget is ~0), so 11 falls have no counterexample among healthy axes
  either — the all-24 count of 8 is the strict lower bound.
- **Fringe: rescue fractions are high** (`per_model_fall_rescue_fraction.csv`): 56–82% of each
  representative's misses are rescued by some other model — Gate 0(b) passes. The miss sets are
  strongly overlapping though: pairwise Jaccard among the 7 healthy LeNet representatives is
  mean **0.70** (range 0.54–0.84).

Reading: the fall low-tail is a **shared core plus a rotating fringe**. The fringe explains the
oracle's +10 TP over the best single model; the core is what kills H15 — the recall bar cannot be
met without rescuing at least 4 of 8 windows that no model in nine families and two
representations has ever ranked above a FAR-0.12 threshold.

Plot: `hard_fall_overlap_heatmap.png` (window×family miss matrix + family Jaccard).

---

## 4. Hard non-fall (false-alarm) analysis: run/walk-dominated shared tail

Union of hard negatives across all 24 axes at FAR-0.12: **116 distinct non-fall windows**
(`hard_nonfall_windows_by_model.csv`). Only **1** window is hard for all 24 axes, but the sets
are still substantially shared among healthy models: pairwise Jaccard among the 7 healthy LeNet
representatives is mean **0.60** (range 0.50–0.80). So the false-alarm tail is a shared core with
a model-specific fringe — same shape as the fall side, slightly more model-specific at window
level.

Class sources (`class_source_hard_negative_summary.csv`, plot
`hard_negative_class_source_bar.png`):

| True class | Union hard negatives | Share | Per-class rate |
|---|---|---|---|
| run | 44 | 37.9% | 0.364 |
| walk | 28 | 24.1% | 0.192 |
| lie down | 19 | 16.4% | 0.288 |
| stand up | 12 | 10.3% | 0.400 |
| pickup | 10 | 8.6% | 0.204 |
| sit down | 3 | 2.6% | 0.075 |

**Yes — run/walk dominate (62% of the union),** consistent with the held-out-test diagnosis
(referenced as motivation only). Stand-up has the highest per-class rate (0.40) but small
absolute count; lie-down contributes a non-trivial 16% (the stillness-confusion channel again).

---

## 5. Cross-model complementarity

- **Falls:** real but marginal complementarity. Union oracle over the 9 family representatives:
  TP 33 vs best single 26 (+7); over all 24 axes: TP 36 (+10). All of the gain comes from the
  rotating fringe; none touches the 8-window core.
- **Non-falls:** the false-alarm tails of different families overlap heavily (Jaccard ~0.60);
  different models do **not** produce disjoint false positives. Pessimistic union-of-FP counts:
  116 at cap 0.12 (FAR 0.26 if realized jointly).
- **The alternate representation adds nothing here:** the BiLSTM axes rescue 0 universal misses
  and contribute ~0 recall at the budget; its hard-negative set barely intersects the LeNet union
  only because its operating threshold saturates (FP≈1 at recall≈0).
- D13's shared-input transfer veto (pre-registered FAIL) already established that even the
  observed fringe complementarity does not survive a shared adversarial input.

Conclusion: complementarity is insufficient in magnitude (bounded at 0.818 oracle recall), wrong
in location (fringe, not core), and known not to be adversarially robust.

---

## 6. Validation-only union/oracle analysis (DIAGNOSTIC, NON-DEPLOYABLE)

`validation_union_oracle_summary.csv`; every row carries the warning column. Headline rows:

| Model set | FAR cap | Best single TP | Union-oracle TP | Falls missed by ALL | Gate TP≥40 @0.12? |
|---|---|---|---|---|---|
| all 24 score axes | 0.10 | 24 | 33 | 11 | — |
| **all 24 score axes** | **0.12** | **26 (0.591)** | **36 (0.818)** | **8** | **NO** |
| all 24 score axes | 0.15 | 33 | 41 | 3 | (cap ≠ gate) |
| one per family (9) | 0.12 | 26 | 33 | 11 | NO |
| LeNet families only (8) | 0.12 | 26 | 33 | 11 | NO |
| D13 trio (AFAC/D10/D11b) | 0.12 | 26 | 32 | 12 | NO |

Notes:
- The union at cap 0.15 reaches 41, but the gate is **pre-registered at 0.12** (buffered
  precisely because validation→test FAR drift of +0.03 was observed once already); moving the
  gate to 0.15 after seeing this table would be exactly the post-hoc rule-shifting this ledger
  forbids. The pessimistic union-of-FP count at 0.15 is 137 (FAR 0.30) in any case.
- The oracle assigns each fall window to the most favorable model with hindsight and lets every
  model keep its own 54-FP budget simultaneously — it is a strict upper bound on any single
  model, any calibration, and any fusion of these axes. **It fails the gate.**

Plot: `union_oracle_vs_best_single.png` (the oracle curve crosses the 0.909 line only near
FAR ≈ 0.15, and only in the non-deployable oracle sense); `val_recall_vs_far_by_model.png`.

---

## 7. Decision

**Stop H15 because the hard windows appear universal and the target is not plausible.**

Gate 0 verdict against its pre-registered conditions:
- (a) union-oracle recall ≥ 40/44 at FAR ≤ 0.12: **FAIL** (36/44; falls missed by every model:
  8 > 4).
- (b) ≥ 25% of each representative's misses rescued elsewhere: PASS (0.56–0.82) — but the gate
  required (a) AND (b).

Interpretation: 8 validation falls (18% of the positive set) are information-poor under PGD
ε=0.030 at the window level for every objective and both representations ever trained here. H15's
recall bar (40/44 validation, TP ≥ 39/45 test) cannot be met without rescuing ≥ 4 of them, and no
evidence anywhere in the ledger suggests any model can. Phase 1 representation screening is NOT
authorized: even a screening winner would be chasing a bar that the all-model oracle misses.
Hard-negative training and fusion are excluded for the same arithmetic reason (both are bounded
by score axes whose union already fails). This is the cheap, clean negative the roadmap was
designed to produce before compute was spent.

What survives for the thesis: the F20-level operating-region evidence and this Phase-0
demonstration that the residual gap is a data/threat-model limit (a per-window information
ceiling under white-box PGD at ε=0.030), not an under-trained model — a stronger and more
defensible claim than another failed training attempt.

---

## 8. First next command

Record the Gate-0 stop decision in the ledger folder (no compute, no test read; advisor/PI
sign-off action):

```
echo "2026-07-05 H15 Gate 0: FAIL. Union oracle 36/44 < 40/44 at FAR<=0.12; 8 of 44 validation falls missed by all 24 saved score axes (limit was 4). H15 closed per pre-registered Phase-0 data-limit stop rule. No Phase 1 training authorized." > results/defense_attempt_inventory/h15_e0_hard_window_inventory/GATE0_STOP_DECISION.txt
```

---

*Reproduction:* `python scripts/analysis/h15_e0_hard_window_inventory.py` — deterministic;
reads only the 24 saved validation CSVs; writes only under
`results/defense_attempt_inventory/h15_e0_hard_window_inventory/`.
