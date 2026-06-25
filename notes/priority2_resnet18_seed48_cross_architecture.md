# Priority 2 — ResNet18 Seed 48 Cross-Architecture Evidence (Clean-Qualified)

A standalone record for **ResNet18 seed 48**, run as the **second replacement
attempt** (after seeds 45 and 47 both diverged) to test whether ResNet18 could
reach five clean-qualified seeds under the fixed protocol. **Seed 48 PASSED the
clean gate** and completed attack evaluation, giving ResNet18 a full five
clean-qualified seeds (42, 43, 44, 46, 48).

This was a **fixed-protocol replacement-seed attempt, not hyperparameter tuning or
rescue**: no learning rate, optimizer, epochs, patience, model code, data split,
attack settings, or thresholds were changed. Same scripts/conventions as seeds
42–47.

## What was run
- **Stage 1 (clean):** `scripts/train_converged_clean_baseline.py --model resnet18
  --seed 48 --epochs 200 --patience 20 --lr 1e-3 --batch-size 64
  --run-name resnet18_seed48 --results-dir results/cross_architecture/resnet
  --checkpoint-dir checkpoints/cross_architecture/resnet`
- **Stage 2 (matched ε=0.03):** `scripts/run_converged_attacks.py --model resnet18
  --seed 48 --epsilon 0.03 --attacks both --run-name resnet18_seed48
  --checkpoint checkpoints/cross_architecture/resnet/resnet18_seed48_best.pt
  --results-dir results/cross_architecture/resnet`
- **Stage 2 (18-point sweep):** same as above with `--epsilon-sweep`.

Environment: Python 3.10.11, torch 2.12.0+cpu (CPU), SenseFi commit `15fd8724`,
repo commit `45d8e66` (HEAD at run time), branch `feature/converged-clean-baseline`.
Checkpoints are git-ignored (local only); seeds 42–47 files were not modified.

## Clean results (no attack) — PASS strict clean gate
Test split: n = 500 windows (45 fall / 455 non-fall). Best checkpoint selected on
validation macro-F1; early-stopped at epoch 93 (best epoch 73).

| Metric | seed 48 | a converged seed (44, ref) | excluded seed (47, ref) |
|---|---|---|---|
| Accuracy | 0.978 | 0.984 | 0.294 |
| Macro-F1 | 0.964 | 0.975 | 0.065 |
| Fall recall | **1.000** | 0.978 | 0.000 |
| Fall precision | 0.957 | 0.957 | 0.000 |
| False-fall alarms (FP) | 2 | 2 | 0 |
| TP/FN/FP/TN | 45/0/2/453 | 44/1/2/453 | 0/45/0/455 |
| Best epoch | 73 | 70 | 6 |
| Val loss (best) | 0.043 | (healthy) | ≈ 8.6×10⁶ |

Per-class recall (seed 48): lie down 0.955, fall 1.000, walk 1.000, pickup 0.980,
run 1.000, sit down 0.925, stand up 0.871. Validation at the selected checkpoint:
macro-F1 0.983, accuracy 0.988, loss 0.043.

**Clean-gate decision: PASS (strict).** Every strict criterion is satisfied:
- Fall recall is meaningful — in fact **perfect (1.000, 45/45 falls caught)**.
- Macro-F1 is strong (0.964).
- Predictions are distributed across **all seven classes** (per-class recall
  0.87–1.00); the model is **not** a single-class / walk-only predictor.
- Training converged cleanly: early-stopped at epoch 93 (best 73), validation loss
  0.043, no numerical divergence — the opposite of the seed-45/47 failures.

Seed 48 is an excellent ResNet18 clean classifier and is **clean-qualified**.

## FGSM / PGD at ε = 0.03 (test split, n = 500)
| Attack | Fall recall | Accuracy | Macro-F1 | TP/FN/FP/TN | False alarms (FP) |
|---|---|---|---|---|---|
| FGSM ε=0.03 | 0.000 | 0.006 | 0.004 | 0/45/36/419 | 36 |
| PGD ε=0.03  | 0.000 | 0.000 | 0.000 | 0/45/50/405 | 50 |

Under matched attacks at ε=0.03, ResNet18 seed 48 **misses every one of the 45 fall
windows** under both FGSM and PGD (fall recall 0.000) — i.e. it **does reach exactly
0.000 at ε=0.03** under both attacks, despite perfect clean fall recall (1.000).
Multiclass accuracy falls from 0.978 clean to 0.006 (FGSM) / 0.000 (PGD).

## Collapse thresholds (smallest ε on the 18-point grid, test split)
| Attack | recall < 0.50 | recall < 0.10 | recall = 0 |
|---|---|---|---|
| FGSM (seed 48) | 0.0075 | 0.0125 | 0.030 |
| PGD  (seed 48) | 0.005 | 0.0075 | 0.0075 |

(Clean fall recall = 1.000.) Both thresholds are concrete (not null): FGSM reaches
exactly 0.000 by ε=0.030 and PGD by ε=0.0075, and both are 0.000 at the matched
ε=0.03 point — verified against the matched single-ε run.

## Updated ResNet18 clean-qualified aggregate (seeds 42, 43, 44, 46, 48; n = 5)
Seeds 45 and 47 remain **excluded** (non-converged) and are NOT in any statistic.

| Condition | Metric | Mean ± SD |
|---|---|---|
| Clean | Fall recall | 0.978 ± 0.016 |
| Clean | Accuracy | 0.970 ± 0.017 |
| Clean | Macro-F1 | 0.952 ± 0.030 |
| Clean | MCC | 0.971 ± 0.014 |
| FGSM ε=0.03 | Fall recall | 0.009 ± 0.012 |
| FGSM ε=0.03 | MCC | −0.064 ± 0.047 |
| **PGD ε=0.03** | **Fall recall** | **0.000 ± 0.000** |
| PGD ε=0.03 | MCC | −0.107 ± 0.037 |

**Exact collapse counts at ε=0.03:** PGD fall recall = 0.000 in **5/5** seeds; FGSM
fall recall = 0.000 in **3/5** seeds (43, 46, 48), with seeds 42 and 44 retaining
0.022. All five reach exactly 0.000 PGD fall recall by ε ≤ 0.010 and FGSM by
ε ≤ 0.035. Full per-seed values in
`results/cross_architecture/resnet/resnet18_clean_qualified_seedwise_metrics.csv`.

## Generated / updated package files
- Raw per-seed results (28 files): `results/cross_architecture/resnet/resnet18_seed48_*`
  (clean + matched ε=0.03 + FGSM/PGD sweeps, test & legacy splits, metadata).
- Updated aggregate (now 5 seeds): `resnet18_clean_qualified_seedwise_metrics.csv`,
  `resnet18_clean_qualified_summary.csv`, `resnet18_clean_qualified_thresholds.csv`.
- Regenerated aggregate figures (5 seeds):
  `figures/resnet18_clean_qualified_fall_recall_vs_epsilon.png`,
  `figures/resnet18_collapse_threshold_distribution.png`,
  `figures/resnet18_pgd_false_alarms_at_003_clean_qualified.png`.
- Updated tracker: `resnet18_seed_convergence_status.csv` (seed 48 = clean_qualified;
  seeds 45, 47 = non_converged).
- Updated aggregate note: `notes/priority2_resnet18_multiseed_summary.md`.
- Checkpoints (git-ignored, local only): `resnet18_seed48_{best,last}.pt`.

## Metric / provenance notes
- The `stage1_clean_references` block inside the attack metadata reports the
  committed **LeNet** Stage-1 reference values (comparison-only, same as all prior
  seeds). The ResNet18 clean references used in every metric row (clean_accuracy
  0.978, clean_fall_recall 1.000) are computed live from the loaded ResNet18
  checkpoint and are correct.
- MCC / Cohen's κ in the aggregate are the binary fall-vs-non-fall values computed
  from the committed TP/FN/FP/TN counts; recomputing them reproduced the prior
  committed seed-42/43/44/46 values exactly.

## Limitations & wording
- ResNet18 now has a **full five clean-qualified seeds (42, 43, 44, 46, 48)**, but
  reaching them required **seven runs** (seeds 45 and 47 diverged and are excluded).
  ResNet18 is the most seed-sensitive architecture in the study under the fixed
  protocol.
- Do **not** claim clinical fall-risk prediction, real-world clinical unsafe
  behavior, over-the-air validation, or certified robustness. All quantities are
  window-level safety-proxy metrics on digital-domain, processed-tensor
  perturbations.
- See [[project_overview]], `notes/priority2_resnet18_multiseed_summary.md`,
  `notes/priority2_resnet_seed45_nonconverged.md`, and
  `notes/priority2_resnet18_seed47_cross_architecture.md` for the full per-seed and
  aggregate detail.
