# Priority 2 — ResNet18 Multi-Seed Summary (Clean-Qualified)

Thesis-ready aggregate for the ResNet18 multi-seed extension of the Priority 2
cross-architecture study. Built **only** from already-committed ResNet18 seed
results (no experiment was rerun; no raw result file was modified). **Refreshed to
five clean-qualified seeds** after seed 48 (the second replacement attempt) passed
the clean gate; seeds 45 and 47 remain excluded as non-converged.

## Headline
- **5/5 clean-qualified ResNet18 seeds (42, 43, 44, 46, 48) collapse to exactly
  0.000 PGD fall recall at ε=0.03** — every one of the 45 fall windows missed in
  each seed (zero variance).
- **FGSM at ε=0.03 reaches exactly 0.000 fall recall in 3/5** clean-qualified seeds
  (43, 46, 48); seeds 42 and 44 retain a small residual (0.022, one true positive).
  All five reach exactly 0.000 fall recall under FGSM by ε ≤ 0.035.
- **Two seeds (45 and 47) were non-converged and are excluded** from the
  clean-qualified aggregate (documented in
  `notes/priority2_resnet_seed45_nonconverged.md` and
  `notes/priority2_resnet18_seed47_cross_architecture.md`).
- ResNet18 now has **full five clean-qualified seeds**, joining LeNet, GRU, BiLSTM,
  and Transformer, all of which have full five-seed evidence. It required **seven
  training runs (seeds 42–48) to obtain five clean-qualified seeds** because
  ResNet18 is seed-sensitive under the fixed protocol (2 divergences).

## Convergence status (all seven attempted seeds)
| Seed | Status | Clean accuracy | Clean fall recall | Best epoch |
|---|---|---|---|---|
| 42 | clean-qualified | 0.942 | 0.978 | 43 |
| 43 | clean-qualified | 0.964 | 0.956 | 21 |
| 44 | clean-qualified | 0.984 | 0.978 | 70 |
| 45 | **non-converged (excluded)** | 0.294 | **0.000** | 1 |
| 46 | clean-qualified | 0.982 | 0.978 | 44 |
| 47 | **non-converged (excluded)** | 0.294 | **0.000** | 6 |
| 48 | clean-qualified | 0.978 | 1.000 | 73 |

Seeds 45 and 47 each diverged under the fixed protocol (Adam lr 1e-3): validation
loss rose to ~10¹⁵ (seed 45) / ~8.6×10⁶ (seed 47), the model became a trivial
"walk"-only predictor, and clean fall recall was 0.000 *before* any attack — so
their attacked 0.000 fall recall is not adversarial-collapse evidence. They are
retained only as training-stability observations and are **not** in any
clean-qualified robustness statistic. No protocol/lr/optimizer change was made to
rescue them — these were fixed-protocol replacement attempts, not tuning.

## Clean-qualified aggregate (seeds 42, 43, 44, 46, 48; n = 5)
Test split: n = 500 windows (45 fall / 455 non-fall). Mean ± SD (95% CI, Student-t df=4).

| Condition | Metric | Mean ± SD | 95% CI |
|---|---|---|---|
| Clean | Fall recall | 0.978 ± 0.016 | [0.958, 0.997] |
| Clean | Missed-fall rate | 0.022 ± 0.016 | [0.003, 0.042] |
| Clean | False-fall alarms | 1.40 ± 0.89 | [0.29, 2.51] |
| Clean | Accuracy | 0.970 ± 0.017 | [0.948, 0.992] |
| Clean | Macro-F1 | 0.952 ± 0.030 | [0.914, 0.990] |
| Clean | MCC | 0.971 ± 0.014 | [0.954, 0.988] |
| FGSM ε=0.03 | Fall recall | 0.009 ± 0.012 | [0, 0.024] |
| FGSM ε=0.03 | False-fall alarms | 32.2 ± 20.3 | [7.0, 57.4] |
| FGSM ε=0.03 | MCC | −0.064 ± 0.047 | [−0.122, −0.006] |
| **PGD ε=0.03** | **Fall recall** | **0.000 ± 0.000** | **[0.000, 0.000]** |
| PGD ε=0.03 | False-fall alarms | 54.0 ± 32.0 | [14.2, 93.8] |
| PGD ε=0.03 | MCC | −0.107 ± 0.037 | [−0.153, −0.061] |

(CI lower bounds shown as 0 where the symmetric-t interval goes slightly negative
on a non-negative quantity.)

The defining result: clean fall recall is high and tight (0.978 ± 0.016), yet
**PGD at ε=0.03 drives fall recall to exactly 0.000 in every clean-qualified seed**
(zero variance). FGSM at ε=0.03 is near-total (mean 0.009; exactly 0.000 in 3/5
seeds, 0.022 in seeds 42 and 44). False-fall alarms are inflated but high-variance
across seeds (PGD 17–105).

## Collapse thresholds (smallest ε on the grid; clean-qualified seeds)
| Seed | FGSM recall=0 ε | PGD recall=0 ε |
|---|---|---|
| 42 | 0.035 | 0.0075 |
| 43 | 0.0075 | 0.0075 |
| 44 | 0.015 | 0.010 |
| 46 | 0.010 | 0.0075 |
| 48 | 0.030 | 0.0075 |
| **mean ± SD** | 0.0195 ± 0.0123 | 0.0080 ± 0.0011 |

PGD reaches zero fall recall by ε ≤ 0.010 in all five seeds (tight; mean ≈ 0.008);
FGSM reaches zero by ε ≤ 0.035 in all five (more variable). At the matched ε=0.03,
PGD is exactly 0.000 in 5/5 seeds while FGSM is exactly 0.000 in 3/5.

## Generated package files
- `results/cross_architecture/resnet/resnet18_clean_qualified_seedwise_metrics.csv` (5 seeds)
- `results/cross_architecture/resnet/resnet18_clean_qualified_summary.csv` (n=5)
- `results/cross_architecture/resnet/resnet18_clean_qualified_thresholds.csv` (5 seeds)
- `results/cross_architecture/resnet/resnet18_seed_convergence_status.csv` (7 attempted seeds)
- `results/cross_architecture/resnet/figures/resnet18_clean_qualified_fall_recall_vs_epsilon.png` (regenerated, 5 seeds)
- `results/cross_architecture/resnet/figures/resnet18_pgd_false_alarms_at_003_clean_qualified.png` (regenerated, 5 seeds)
- `results/cross_architecture/resnet/figures/resnet18_collapse_threshold_distribution.png` (regenerated, 5 seeds)
- Per-seed raw results: `results/cross_architecture/resnet/resnet18_seed{42,43,44,46,48}_*` (clean-qualified)
  and `resnet18_seed{45,47}_*` (excluded, non-converged).

## Limitations & wording
- This is a **ResNet18 full five-seed clean-qualified result** over seeds
  42, 43, 44, 46, 48, plus **two non-converged, excluded seeds (45, 47)**. Obtaining
  five clean-qualified seeds required seven training runs.
- Correct statements: "5/5 clean-qualified ResNet18 seeds collapse to exactly 0.000
  PGD fall recall at ε=0.03 (seeds 45 and 47 excluded as non-converged)"; "FGSM at
  ε=0.03 reaches exactly 0.000 in 3/5 clean-qualified seeds, and all five by
  ε ≤ 0.035." Do **not** state "7/7 seeds collapsed" or imply seeds 45/47 are
  robustness evidence.
- Do **not** claim clinical unsafe behavior, over-the-air validation, or certified
  robustness. All quantities are window-level safety-proxy metrics on
  digital-domain, processed-tensor perturbations.
- **LaTeX note (out of scope here):** the committed
  `tables/chapter_resnet18_multiseed_*.tex` artifacts still describe the prior
  four-seed aggregate and will need a separate update to the five-seed numbers;
  thesis LaTeX was intentionally not modified in this run.
