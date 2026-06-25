# Priority 2 — ResNet18 Seed 47 Clean-Gate Result (NON-CONVERGED / FAILED)

A standalone record for **ResNet18 seed 47**, run as a **replacement attempt** for
the previously-excluded diverged seed 45, to test whether ResNet18 could reach a
full five clean-qualified seeds. **Seed 47 also failed the clean gate** under the
same fixed protocol — it diverged to a trivial walk-only predictor. Attack
evaluation was **intentionally skipped** (clean fall recall is already 0.000, so
there is no clean capability to lose and no robustness signal to measure).

## What was run
- **Stage 1 (clean only):** `scripts/train_converged_clean_baseline.py
  --model resnet18 --seed 47 --epochs 200 --patience 20 --lr 1e-3 --batch-size 64
  --run-name resnet18_seed47 --results-dir results/cross_architecture/resnet
  --checkpoint-dir checkpoints/cross_architecture/resnet`
- **Stage 2 (attacks): NOT RUN** — skipped because the clean gate failed.

Same model (`UT_HAR_ResNet18`), same UT-HAR/SenseFi pipeline, same 500-window test
split (45 fall / 455 non-fall), same preprocessing, same fall/non-fall mapping,
same hyperparameters and scripts as seeds 42–46. **No protocol, learning-rate,
optimizer, or schedule change was made** — changing the protocol for a single seed
would break comparability with the converged seeds, so the divergence is reported
as-is rather than patched.

Environment: Python 3.10.11, torch 2.12.0+cpu (CPU), SenseFi commit `15fd8724`,
repo commit `b099954` (HEAD at run time), branch `feature/converged-clean-baseline`.
Checkpoints are git-ignored (local only); seeds 42–46 files were not modified.

## Clean results (no attack) — FAIL clean gate
Test split: n = 500 windows (45 fall / 455 non-fall).

| Metric | seed 47 (FAILED) | seed 45 (excluded, ref) | a converged seed (44, ref) |
|---|---|---|---|
| Accuracy | 0.294 | 0.294 | 0.984 |
| Macro-F1 | 0.065 | (degenerate) | 0.975 |
| Fall recall | **0.000** | **0.000** | 0.978 |
| Fall precision | 0.000 | 0.000 | 0.957 |
| False-fall alarms (FP) | 0 | — | 2 |
| TP/FN/FP/TN | 0/45/0/455 | 0/45/.../... | 44/1/2/453 |
| Best epoch | 6 | 1 | 70 |
| Val loss (best) | ≈ 8.6×10⁶ | ≈ 10¹⁵ | (healthy) |

Per-class recall (seed 47): **walk = 1.000; lie down / fall / pickup / run /
sit down / stand up = 0.000** — the model predicts only the "walk" class for all
500 test windows.

**Clean-gate decision: FAIL.** Every failure indicator is present:
- **Clean fall recall is 0.000 before any attack** (0/45 falls caught).
- **Macro-F1 is degenerate (0.065)** — far from a meaningful multiclass value.
- **Predictions collapse into a single class** (walk-only; accuracy 0.294 exactly
  matches the walk-class fraction 147/500 = 0.294).
- **Validation behavior is unhealthy / diverged**: best validation loss ≈ 8.6×10⁶,
  best epoch 6, then early-stopped — effectively a near-untrained/diverged state.

This is the **same divergence failure mode as the excluded ResNet18 seed 45**
(`notes/priority2_resnet_seed45_nonconverged.md`). ResNet18 under the fixed
protocol (Adam, lr 1e-3) is seed-sensitive and diverges for some seeds.

## Why attack evaluation was intentionally skipped
The attacked fall recall would be a meaningless 0.000 regardless of attack, because
the **clean fall recall is already 0.000** — there is no clean fall-detection
capability to degrade. Running FGSM/PGD here would produce no adversarial-collapse
signal (exactly as documented for seed 45), so Stage 2 was not run, per the
clean-gate protocol.

## Impact on ResNet18 cross-architecture evidence
- **ResNet18 remains at 4 clean-qualified seeds (42, 43, 44, 46).** The replacement
  attempt did not yield a fifth clean-qualified seed.
- **Both seed 45 and seed 47 are excluded** as non-converged / diverged.
- Seed 47 is **NOT** added to the ResNet18 clean-qualified robustness aggregate
  (`resnet18_clean_qualified_seedwise_metrics.csv`, `..._summary.csv`,
  `..._thresholds.csv` are unchanged); those remain over seeds 42, 43, 44, 46.
- The ResNet18 PGD@ε=0.03 collapse evidence therefore stands at **4/4
  clean-qualified seeds**, unchanged by this run.

## Generated package files
Stage-1 clean result files only (no attack files were produced),
`results/cross_architecture/resnet/resnet18_seed47_*`:
- `..._summary_metrics.csv`, `..._fall_binary_metrics.csv`,
  `..._per_class_metrics.csv`, `..._test_predictions.csv`,
  `..._training_curve.csv`, `..._metadata.json`, and the `..._legacy_eval_*`
  comparison files.
- Tracker (updated): `results/cross_architecture/resnet/resnet18_seed_convergence_status.csv`
  (seed 47 recorded as `non_converged`, excluded; seed 45 remains excluded).
- Checkpoints (git-ignored, local only):
  `checkpoints/cross_architecture/resnet/resnet18_seed47_{best,last}.pt`.

No attack metadata, attack safety-metric, prediction, or epsilon-sweep files exist
for seed 47 (Stage 2 was not run).

## Limitations & wording
- ResNet18 has **4 clean-qualified seeds (42, 43, 44, 46)**; **two replacement/
  extension attempts (seeds 45 and 47) both diverged** under the fixed protocol and
  are excluded. ResNet18 is therefore reported as a **clean-qualified multi-seed
  result (4 seeds)**, not a full five-seed result — unlike LeNet, GRU, BiLSTM, and
  Transformer, which each have full five-seed evidence.
- This is a **training-stability / convergence observation** for ResNet18, not an
  adversarial-robustness result. Do not interpret seed 47's attacked behavior
  (none was measured) as robustness evidence.
- All converged-seed quantities elsewhere are window-level safety-proxy metrics on
  digital-domain, processed-tensor perturbations — not clinical, over-the-air, or
  certified-robustness claims.
- See [[project_overview]], `notes/priority2_resnet_seed45_nonconverged.md`, and
  `notes/priority2_resnet18_multiseed_summary.md` for the converged-seed aggregate
  and the prior divergence record.
