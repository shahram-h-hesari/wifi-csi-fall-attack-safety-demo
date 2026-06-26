# Multi-seed confirmation plan (FROZEN) — safety-proxy-guided defense

Status: **prepared, not yet run.** Do not execute seeds 43–46 until explicitly approved.
Seed 42 is the **pilot / protocol-design run** (committed in `f9e5ac5`,
`results/safety_guided_defense/seed42/`, see `seed42/SEED42_REPORT.md`).

## Frozen protocol

- **Recipe (frozen as best-balanced): Variant D** — FGSM+PGD **multi-epsilon** adversarial
  training, **fall-weighted** loss (fall class weight = 3), **safety-guided** checkpoint
  selection with the **clean-collapse guard** (`clean_val_accuracy ≥ 0.60` AND
  `clean_val_macro_f1 ≥ 0.50`).
- **Standard-selection comparison kept:** the **val macro-F1** checkpoint from the same run,
  as the control for "standard vs safety-guided selection."
- **Confirmation seeds:** 43, 44, 45, 46.
- **Model:** LeNet only.
- **Dataset / split:** same UT-HAR / SenseFi split (train 3977 / val 496 / test 500); no changes.
- **No new hyperparameter search** during multi-seed confirmation. Reuse the exact seed-42
  settings: train epsilons {0.005, 0.015, 0.030}; training PGD 7 steps (α=ε/4); mixture
  50% clean / 25% FGSM / 25% PGD; epochs 70, patience 15, min-epochs 35; Adam lr 1e-3; batch 64.
- **Evaluation attack protocol (unchanged, matches thesis):** ε=0.030 headline; PGD steps=10,
  α=ε/6; FGSM single-step; 18-point ε-sweep; no value clamp (processed CSI tensors); test n=500
  primary, legacy val+test n=996 comparison-only.

## Metrics

- **Main metric:** PGD@0.030 fall recall.
- **Secondary metrics:** FGSM@0.030 fall recall, clean accuracy, clean fall recall,
  false-fall alarms (FGSM and PGD), collapse epsilon (first ε with fall recall < 0.50),
  confusion / fall↔non-fall transitions.
- **Reporting:** per-seed values plus mean ± spread across seeds 42–46, for both
  safety-guided and macro-F1 selection.

## Honest trade-off framing (required)

Improved attacked fall recall **may come with lower clean accuracy and higher false-fall
alarms**. Report the gain and the cost together in every table; do not present recall gains
in isolation.

## Claim boundaries (do not exceed)

Window-level, digital-domain, white-box robustness on processed CSI tensors only.
**Do not claim** solved/closed robustness, clinical or medical-device safety, certified
robustness, or over-the-air / physical-layer validation.

## Key seed-42 interpretation to carry forward

1. **Variant D is best-balanced, not necessarily max raw PGD recall.** D gives PGD@0.030
   recall ≈0.44 while keeping clean fall recall 1.000 and the highest safety-pick clean
   accuracy (≈0.746), with the widest robust ε-range.
2. **Variant C maximizes raw PGD recall (≈0.49) but is worse on clean accuracy (≈0.642)
   and has higher false-fall alarms** than D. C may be reported as the max-recall point,
   not the recommended operating point.
3. **Safety-guided selection is the main lever.** On the same trained weights, macro-F1
   selection can pick a checkpoint with **much weaker PGD fall recall** (seed-42 variant B:
   0.444 safety-guided vs 0.089 macro-F1, ≈ the existing FGSM defense).
4. **The clean-collapse guard is required.** The raw SafetyScore (0.10 false-alarm penalty)
   is gamed by a degenerate **always-fall** predictor (clean acc ≈0.09, nearly all non-fall
   windows flagged) for fall_weight=3 (seed-42 variants B/C/D); the guard excludes these.
5. **Unguarded degenerate results stay logged for transparency** — recorded as
   `raw_ungated_safety_best` in each training metadata JSON; do not delete or hide them.

## Planned commands (DO NOT RUN until approved)

```bash
for S in 43 44 45 46; do
  python scripts/train_safety_guided_defense.py --variant D --seed $S \
      --epochs 70 --patience 15 --min-epochs 35
  for f in checkpoints/safety_guided_defense/seed${S}/*_best.pt; do
    run=$(basename "$f" | grep -oE 'variant[A-D]')_$(basename "$f" | grep -oE 'by(SafetyScore|ValMacroF1)')
    python scripts/run_converged_attacks.py --checkpoint "$f" --model lenet \
        --epsilon 0.03 --attacks both --run-name "$run" \
        --results-dir results/safety_guided_defense/seed${S}/test_eval
    python scripts/run_converged_attacks.py --checkpoint "$f" --model lenet \
        --attacks both --epsilon-sweep --run-name "$run" \
        --results-dir results/safety_guided_defense/seed${S}/test_eval
  done
done
```

Note: the training script currently writes seed-specific paths via its `seed{N}` tag, so each
seed lands under `checkpoints/safety_guided_defense/seed{N}/` and
`results/safety_guided_defense/seed{N}/logs/`. A small per-seed output-dir confirmation should be
done at run time. Variant D is the frozen recipe; variants A–C are not part of multi-seed
confirmation.
