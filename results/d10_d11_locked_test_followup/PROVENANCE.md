# Provenance — D10/D11 Locked Held-Out Test Follow-Up

Generated: 2026-07-04. Analysis performed at repo commit `1bcf6b8f35493a73269171c6b0678ca52b0a7580`
on branch `feature/safety-proxy-guided-defense`. No thesis/Overleaf files were edited. Nothing committed.

## Checkpoints (inference only — no training performed in this follow-up)

All three checkpoints were trained at commit `7b9db40fec3b19790d05c5cf67e67c2efe5683a9`
(per each run's metadata JSON), CPU, torch 2.12.0+cpu, seed 42, with `test_set_used: false`
recorded at training time.

| ID | Checkpoint | Trained | Metadata |
|----|-----------|---------|----------|
| D10 | `checkpoints/safety_guided_defense/boundary_aware_selective_at/gairat/seed42/GR1/seed42_basat_gairat_GR1_v2macroF1_best.pt` | 2026-06-29 | `results/safety_guided_defense/boundary_aware_selective_at/gairat/seed42/GR1/metadata/seed42_basat_gairat_GR1_metadata.json` |
| D11a | `checkpoints/safety_guided_defense/boundary_aware_selective_at/seed42/beta6p0/seed42_basat_stage1_beta6p0_v2lowFA_best.pt` | 2026-06-29 | `results/safety_guided_defense/boundary_aware_selective_at/seed42/beta6p0/metadata/seed42_basat_stage1_beta6p0_metadata.json` |
| D11b | `checkpoints/safety_guided_defense/boundary_aware_selective_at/sat/seed42/SA1/seed42_basat_sat_SA1_v2lowFA_best.pt` | 2026-06-29 | `results/safety_guided_defense/boundary_aware_selective_at/sat/seed42/SA1/metadata/seed42_basat_sat_SA1_metadata.json` |

Checkpoint-variant choice (v2macroF1 for D10; v2lowFA for D11a/D11b) was made from validation
evidence only: these are the variants whose validation PGD FAR-sweep rows appear in Internal
Appendix IA / `results/defense_attempt_inventory/defense_attempt_results_long.csv`
(validation AUROC 0.871229 / 0.868966 / 0.872788 respectively).

## Data and splits

UT-HAR via SenseFi benchmark loader (`third_party/WiFi-CSI-Sensing-Benchmark`), standard project
splits: train 3,977 / val 496 (44 fall, 452 non-fall) / held-out test 500 (45 fall, 455 non-fall).
Split counts were assert-checked in the analysis script for every score file.

## Test score generation (new in this follow-up)

`scripts/export_probability_predictions.py --split test` (logging/export only), one run per
checkpoint, defaults: epsilon 0.030, PGD steps 10, alpha = eps/6, attack generation delegated to
`run_converged_attacks.generate_attacked_batch` — byte-identical protocol to the existing
validation exports (all GO/NO-GO docs record "Eval PGD-10 (alpha=eps/6)"). Outputs in `test_eval/`
(clean, FGSM, PGD per checkpoint; PGD files are the primary evidence).

## Threshold protocol

`scripts/analysis/d10_d11_locked_test_followup.py`:
for each method and each FAR cap in {0.20, 0.15, 0.10}, the threshold maximizing validation fall
recall subject to validation FAR <= cap was chosen from the EXISTING validation PGD score exports
(tie-break: lower FAR, then higher threshold), frozen, and applied once to the test PGD scores.
Selection and application run in a single pass with no test feedback into selection.

`scripts/analysis/d10_d11_posthoc_test_characterization.py` additionally sweeps the test scores
directly; those rows are labeled "test post-hoc FAR sweep (characterization only)" and exist solely
for an apples-to-apples comparison with the D8b post-hoc reference row.

## Evidence-type labels used in outputs

- `held-out test, frozen validation-selected threshold` — the headline evidence of this follow-up.
- `test post-hoc FAR sweep (characterization only)` — same evidence type as the D8b reference.
- D8b reference row values are copied from
  `results/operating_region_characterization/operating_region_summary.csv`
  (optionB_maxscore seed42, threshold 0.153246, TP/FN/FP/TN 36/9/91/364, AUROC 0.8439).
