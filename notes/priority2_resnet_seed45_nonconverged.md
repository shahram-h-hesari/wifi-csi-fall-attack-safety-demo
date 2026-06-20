# ResNet18 Seed 45 — Non-Converged / Diverged Training Run

A standalone record for ResNet18 **seed 45** in the Priority 2 cross-architecture
study. Based entirely on the already-committed seed-45 results (commit
`6db1485`); no experiment was rerun.

## Summary
ResNet18 seed 45 was executed under the **same fixed protocol** as seeds 42–44,
but the model **failed to train** — the optimizer diverged and the clean model
collapsed to a trivial single-class predictor. Seed 45 is therefore recorded as a
**non-converged / diverged training run** and is **excluded** from the
adversarial-collapse evidence and from any clean-qualified ResNet18 aggregate.

## What was run
- Same model: `UT_HAR_ResNet18`, same UT-HAR/SenseFi pipeline, same primary
  500-window test split (45 fall / 455 non-fall), same preprocessing, same
  fall/non-fall mapping, same epsilon grid, same FGSM/PGD settings, same
  safety-proxy metrics, same scripts and model factory as seeds 42–44.
- The run **executed successfully** and produced all expected output files
  (28 `resnet18_seed45_*` files: clean + matched ε=0.03 + FGSM/PGD sweeps),
  committed in `6db1485`. There were no script, tensor-shape, gradient,
  checkpoint, or metric-script errors — only the trained model diverged.

## Why it is non-converged
- The model **did not learn a meaningful clean classifier**.
- **Clean fall recall was 0.000 before any attack.**
- The clean model **predicted only the "walk" class for all 500 test windows.**
- **Clean accuracy was 0.294**, exactly matching the walk-class fraction in the
  test split (147 / 500 = 0.294).
- The **optimizer diverged numerically**: validation loss rose to approximately
  $10^{15}$ by epoch 2, `best_epoch = 1`, and validation macro-F1 stayed at
  ~0.065 throughout. The early-stopped checkpoint is effectively the
  untrained/epoch-1 state.

## Why the attacked numbers are not adversarial-collapse evidence
The attacked fall recall of **0.000** under FGSM and PGD at ε=0.03 is **not**
meaningful evidence of adversarial collapse, because the **clean fall recall was
already 0.000**. There is no clean fall-detection capability to lose, so the
attack results carry no robustness signal for this seed. The collapse thresholds
(first ε where fall recall < 0.50 / < 0.10 / = 0) all read 0.0 for the same
reason and should be ignored for seed 45.

## How seed 45 should be used
- Seed 45 should be used **only as a training-stability / convergence
  observation**: ResNet18 on UT-HAR with the fixed protocol (Adam, lr 1e-3) is
  seed-sensitive and can diverge for some seeds.
- Seed 45 is **excluded** from:
  - the ResNet18 adversarial-collapse evidence, and
  - any clean-qualified ResNet18 aggregate summary.
- The ResNet18 PGD@ε=0.03 collapse evidence therefore remains **3/3 converged
  seeds (42, 43, 44)**, each with clean fall recall 0.956–0.978 collapsing to
  0.000 under PGD at ε=0.03.

## Protocol integrity
**No learning-rate, optimizer, gradient-clipping, or schedule change was applied**
to "rescue" seed 45. Changing the protocol for a single seed would break
comparability with seeds 42–44, so the divergence is reported as-is rather than
patched.

## Next step
Seed 46 should be run **later, under the same fixed protocol**, and will
determine whether the converged-seed count for ResNet18 is 4/5 (with seed 45 as
the lone divergence) or otherwise. No protocol change should be made without an
explicit decision to do so.

## Provenance
- Seed-45 results commit: `6db1485` ("Add Priority 2 ResNet seed 45 results
  (NON-CONVERGED / diverged run)").
- Raw files: `results/cross_architecture/resnet/resnet18_seed45_*`.
- Checkpoints are git-ignored (local only).
