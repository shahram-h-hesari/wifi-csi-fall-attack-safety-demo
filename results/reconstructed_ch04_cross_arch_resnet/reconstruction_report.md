# Chapter 4 Reconstructed Cross-Architecture/ResNet18 Artifacts

Status: Reconstructed reproducibility generator from verified source data; original generator not found.

No training or attacks are run by this script. Thesis files are read only for
hash/dimension comparison; they are not modified.

## Source Files

- fig47_summary: results/cross_architecture/cross_architecture_seed42_pilot_summary.csv
- fig47_thresholds: results/cross_architecture/cross_architecture_seed42_pilot_thresholds.csv
- fig47_existing: results/cross_architecture/figures/cross_architecture_seed42_fall_recall_vs_epsilon.png
- fig47_thesis: C:\Users\Hesar\Documents\GitHub\thesis-overleaf-linked\images\ch04_cross_arch_fall_recall_vs_epsilon.png
- fig48_summary: results/cross_architecture/resnet/resnet18_clean_qualified_summary.csv
- fig48_seedwise: results/cross_architecture/resnet/resnet18_clean_qualified_seedwise_metrics.csv
- fig48_thresholds: results/cross_architecture/resnet/resnet18_clean_qualified_thresholds.csv
- fig48_convergence: results/cross_architecture/resnet/resnet18_seed_convergence_status.csv
- fig48_existing: results/cross_architecture/resnet/figures/resnet18_clean_qualified_fall_recall_vs_epsilon.png
- fig48_thesis: C:\Users\Hesar\Documents\GitHub\thesis-overleaf-linked\images\ch04_resnet18_multiseed_fall_recall_vs_epsilon.png
- table47_csv: results/cross_architecture/cross_architecture_multiseed_summary.csv
- table47_tex: tables/chapter_cross_architecture_multiseed_table.tex
- table47_note: notes/priority2_cross_architecture_multiseed_summary.md
- table48_summary: results/cross_architecture/resnet/resnet18_clean_qualified_summary.csv
- table48_seedwise: results/cross_architecture/resnet/resnet18_clean_qualified_seedwise_metrics.csv
- table48_thresholds: results/cross_architecture/resnet/resnet18_clean_qualified_thresholds.csv
- table48_tex: tables/chapter_resnet18_multiseed_table.tex

## Generated Files

- results/reconstructed_ch04_cross_arch_resnet/ch04_figure_4_7_cross_architecture_fall_recall_vs_epsilon_reconstructed.png
- results/reconstructed_ch04_cross_arch_resnet/ch04_figure_4_7_cross_architecture_fall_recall_vs_epsilon_thesis_clean.png
- results/reconstructed_ch04_cross_arch_resnet/ch04_figure_4_8_resnet18_multiseed_fall_recall_vs_epsilon_reconstructed.png
- results/reconstructed_ch04_cross_arch_resnet/ch04_figure_4_8_resnet18_multiseed_fall_recall_vs_epsilon_thesis_clean.png
- results/reconstructed_ch04_cross_arch_resnet/hash_comparison_report.txt
- results/reconstructed_ch04_cross_arch_resnet/reconstruction_report.md
- results/reconstructed_ch04_cross_arch_resnet/table_4_7_cross_architecture_multiseed_reconstructed.csv
- results/reconstructed_ch04_cross_arch_resnet/table_4_7_cross_architecture_multiseed_reconstructed.md
- results/reconstructed_ch04_cross_arch_resnet/table_4_7_cross_architecture_multiseed_reconstructed.tex
- results/reconstructed_ch04_cross_arch_resnet/table_4_8_resnet18_multiseed_reconstructed.csv
- results/reconstructed_ch04_cross_arch_resnet/table_4_8_resnet18_multiseed_reconstructed.md
- results/reconstructed_ch04_cross_arch_resnet/table_4_8_resnet18_multiseed_reconstructed.tex

## Figure Hash and Dimension Summary

| Image | SHA256 | Dimensions | Path |
| --- | --- | --- | --- |
| Figure 4.7 reconstructed | 54433561ed8ae11faeb46324399e5481e874b263a27655b1055d71a733d2c149 | 1650x675 | results/reconstructed_ch04_cross_arch_resnet/ch04_figure_4_7_cross_architecture_fall_recall_vs_epsilon_reconstructed.png |
| Figure 4.7 existing experiment | 561656923916965618cd0bc3fce1d98ecb997bc3a2c17b78a65fa4b892aff87e | 1650x675 | results/cross_architecture/figures/cross_architecture_seed42_fall_recall_vs_epsilon.png |
| Figure 4.7 active thesis | 54433561ed8ae11faeb46324399e5481e874b263a27655b1055d71a733d2c149 | 1650x675 | C:\Users\Hesar\Documents\GitHub\thesis-overleaf-linked\images\ch04_cross_arch_fall_recall_vs_epsilon.png |
| Figure 4.8 reconstructed | a4fafd29b8a4bcfa81b4b831d6cf4ce930102ea313cf699f90324a6bf4a4e0f2 | 1600x900 | results/reconstructed_ch04_cross_arch_resnet/ch04_figure_4_8_resnet18_multiseed_fall_recall_vs_epsilon_reconstructed.png |
| Figure 4.8 existing experiment | abbdfb78c3f0434c87219285f72073aad3cedb05682c5090d44466c66a9641bc | 1600x900 | results/cross_architecture/resnet/figures/resnet18_clean_qualified_fall_recall_vs_epsilon.png |
| Figure 4.8 active thesis | a4fafd29b8a4bcfa81b4b831d6cf4ce930102ea313cf699f90324a6bf4a4e0f2 | 1600x900 | C:\Users\Hesar\Documents\GitHub\thesis-overleaf-linked\images\ch04_resnet18_multiseed_fall_recall_vs_epsilon.png |

## Pairwise Figure Matches

- fig47_reconstructed_matches_experiment: DIFFER
- fig47_reconstructed_matches_thesis: MATCH
- fig47_experiment_matches_thesis: DIFFER
- fig48_reconstructed_matches_experiment: DIFFER
- fig48_reconstructed_matches_thesis: MATCH
- fig48_experiment_matches_thesis: DIFFER

## Table 4.7 Headline Values

| Model | Clean fall recall | FGSM eps=0.03 | PGD eps=0.03 | Exact 0.000 at eps=0.03 (FGSM / PGD) |
| --- | --- | --- | --- | --- |
| LeNet | 0.978 +/- 0.016 | 0.049 +/- 0.046 | 0.000 +/- 0.000 | 2/5 / 5/5 |
| GRU | 0.920 +/- 0.012 | 0.009 +/- 0.012 | 0.000 +/- 0.000 | 3/5 / 5/5 |
| BiLSTM | 0.884 +/- 0.043 | 0.022 +/- 0.050 | 0.004 +/- 0.010 | 4/5 / 4/5 |
| Transformer | 0.947 +/- 0.049 | 0.004 +/- 0.010 | 0.000 +/- 0.000 | 4/5 / 5/5 |
| ResNet18 | 0.978 +/- 0.016 | 0.009 +/- 0.012 | 0.000 +/- 0.000 | 3/5 / 5/5 |

PGD reaches exactly 0.000 fall recall at epsilon 0.03 in 24/25 clean-qualified seed-runs and all 25 by epsilon <= 0.035.

## Table 4.8 Headline Values

| Condition | Metric | Mean +/- SD | 95% CI |
| --- | --- | --- | --- |
| Clean | Fall recall | 0.978 +/- 0.016 | [0.958, 0.997] |
| Clean | False-fall alarms | 1.40 +/- 0.89 | [0.3, 2.5] |
| FGSM epsilon=0.03 | Fall recall | 0.009 +/- 0.012 | [0, 0.024] |
| FGSM epsilon=0.03 | False-fall alarms | 32.2 +/- 20.3 | [7.0, 57.4] |
| PGD epsilon=0.03 | Fall recall | 0.000 +/- 0.000 | [0.000, 0.000] |
| PGD epsilon=0.03 | False-fall alarms | 54.0 +/- 32.0 | [14.2, 93.8] |


## Provenance Note

This script can be included in provenance as: "Reconstructed reproducibility generator from verified source data; original generator not found."
