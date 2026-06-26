# Safety-proxy-guided adversarial-training defense — seed 42 report

**Branch:** `feature/safety-proxy-guided-defense`
**Dataset / model:** UT-HAR (SenseFi), LeNet, existing train/val/test split (3977 / 496 / 500).
**Scope / claim boundary:** Window-level, digital-domain, white-box robustness on
processed CSI tensors. **Not** clinical validation, **not** over-the-air / physical-layer
attacks, **not** certified robustness, **not** deployment safety. Seed 42 only.

This phase tests whether a **safety-proxy-guided** defense can improve the
safety-critical trade-off (attacked fall recall, esp. under PGD) relative to the
existing FGSM adversarial-training defense, while controlling false-fall alarms and
avoiding unacceptable clean collapse.

---

## 1. Files changed / added

Added (no existing artifacts overwritten):
- `scripts/train_safety_guided_defense.py` — safety-guided PGD / FGSM+PGD adversarial
  training with dual checkpoint selection (SafetyScore + val macro-F1).
- `scripts/build_safety_guided_comparison.py` — comparison table + 3 diagnostic figures.
- `results/safety_guided_defense/seed42/**` — logs, test_eval, figures, comparison CSV, this report.
- `checkpoints/safety_guided_defense/seed42/**` — 12 checkpoints (4 variants × {bySafetyScore, byValMacroF1, last}).

No thesis `.tex` files modified. No baseline / attack / FGSM-defense artifacts modified.

## 2. Method summary

**SafetyScore (validation only):**
`0.35·clean_fall_recall + 0.45·pgd_fall_recall + 0.10·fgsm_fall_recall − 0.10·nfab`,
with FGSM/PGD evaluated at ε=0.030 (PGD steps=10, α=ε/6). `nfab` (normalized
false-alarm burden) = mean over the two attacks of (false-fall alarms / n_nonfall_val) ∈ [0,1].

**Clean-collapse guard (added after an empirical failure — see §7):** a checkpoint is only
eligible for SafetyScore selection if `clean_val_accuracy ≥ 0.60` AND `clean_val_macro_f1 ≥ 0.50`.

**Standard selection kept for comparison:** best `val_clean_macro_f1` checkpoint, same run.

**Training:** batch-split mixing (A/B: 50% clean + 50% PGD; C/D: 50/25/25 clean/FGSM/PGD);
fall-weighted cross-entropy for the training loss; **unweighted** CE for adversary generation.
Training PGD uses 7 steps (α=ε/4) for CPU tractability; **evaluation PGD uses the thesis
protocol (10 steps, α=ε/6)**. Variants: A=PGD fw1, B=PGD fw3, C=FGSM+PGD fw3,
D=FGSM+PGD multi-ε{0.005,0.015,0.030} fw3.

## 3. Reproduce

```bash
# Train all four variants (seed 42), each ~35 min CPU:
for V in A B C D; do
  python scripts/train_safety_guided_defense.py --variant $V --seed 42 \
      --epochs 70 --patience 15 --min-epochs 35
done

# Test-eval each selected checkpoint (single-eps + 18-eps FGSM/PGD sweep):
for f in checkpoints/safety_guided_defense/seed42/*_best.pt; do
  run=$(basename "$f" | grep -oE 'variant[A-D]')_$(basename "$f" | grep -oE 'by(SafetyScore|ValMacroF1)')
  python scripts/run_converged_attacks.py --checkpoint "$f" --model lenet \
      --epsilon 0.03 --attacks both --run-name "$run" \
      --results-dir results/safety_guided_defense/seed42/test_eval
  python scripts/run_converged_attacks.py --checkpoint "$f" --model lenet \
      --attacks both --epsilon-sweep --run-name "$run" \
      --results-dir results/safety_guided_defense/seed42/test_eval
done

# Comparison table + figures (highlight the best-balanced variant D):
python scripts/build_safety_guided_comparison.py --best-variant variantD_bySafetyScore
```

## 4. Runtime notes (CPU-only)

Training ~2100–2245 s per variant (46–64 epochs) ≈ **2.3 h** total.
Test-eval ≈ **80 min** (8 checkpoints × single-eps + two 18-point sweeps over test n=500 and
legacy n=996). Deterministic per seed (variant D was interrupted once by machine sleep and
re-ran identically).

## 5–9. Results (held-out TEST, n=500, ε=0.030)

| Model / selection | Clean acc | Clean fall recall | FGSM fall recall | FGSM FP | **PGD fall recall** | PGD FP | FGSM collapse ε | PGD collapse ε |
|---|---|---|---|---|---|---|---|---|
| Clean LeNet baseline | 0.970 | 0.956 | 0.000 | 47 | 0.000 | 48 | 0.005 | 0.005 |
| **Existing FGSM defense** | 0.834 | 0.911 | 0.311 | 27 | **0.089** | 54 | 0.025 | 0.018 |
| A · safety (PGD fw1) | 0.678 | 0.822 | 0.222 | 52 | 0.133 | 76 | 0.020 | 0.018 |
| A · macro-F1 | 0.706 | 0.711 | 0.111 | 11 | 0.044 | 25 | 0.007 | 0.007 |
| B · safety (PGD fw3) | 0.580 | 0.978 | 0.489 | 162 | 0.444 | 182 | 0.030 | 0.025 |
| B · macro-F1 | 0.668 | 0.911 | 0.244 | 74 | 0.089 | 105 | 0.025 | 0.018 |
| C · safety (FGSM+PGD fw3) | 0.642 | 0.978 | 0.556 | 146 | **0.489** | 190 | 0.040 | 0.030 |
| C · macro-F1 | 0.750 | 0.933 | 0.422 | 64 | 0.200 | 86 | 0.030 | 0.025 |
| **D · safety (multi-ε fw3)** | **0.746** | **1.000** | **0.778** | 123 | **0.444** | 157 | 0.045 | 0.030 |
| D · macro-F1 | 0.848 | 0.956 | 0.467 | 70 | 0.133 | 79 | 0.030 | 0.025 |

**Best by raw PGD recall:** C·safety (0.489). **Best by overall trade-off:** **D·safety** —
PGD recall 0.444 (5× the FGSM defense) with clean fall recall **1.000**, clean accuracy 0.746
(only −0.088 vs the FGSM defense), FGSM recall 0.778, and the widest robust ε-range
(collapse ε ≈ 0.030–0.045 vs the FGSM defense's 0.018–0.025).

**Did PGD recall improve over the FGSM defense?** **Yes, substantially** — every safety-guided
checkpoint with fall-weighting (B/C/D·safety) reaches PGD recall 0.44–0.49 vs **0.089**
(≈5×). FGSM recall also improves (up to 0.778 vs 0.311).

**Did false-fall alarms get worse?** **Yes — this is the cost.** The best variants raise
PGD false-alarms from 54 → 157–190 (≈3–3.5×) and FGSM false-alarms from 27 → 123–162.
D is the least costly of the strong variants (157 PGD FP). Reported as a genuine trade-off,
not hidden.

**Did clean performance collapse?** No catastrophic collapse, but a real clean cost: clean
accuracy drops from 0.834 (FGSM defense) / 0.970 (clean baseline) to 0.58–0.75 depending on
variant. **Clean fall recall is preserved or improved** (0.978–1.000 for B/C/D·safety).
D·safety keeps clean accuracy highest (0.746) among safety picks.

**Selection method is itself a lever (key comparison):** variant B's *same trained weights*
give PGD recall **0.444 under safety-guided selection** but only **0.089 under standard
macro-F1 selection** (≈ the FGSM defense). The robustness gain is delivered specifically by
the safety-proxy **checkpoint selection**, which is the hypothesis under test. Multi-ε
training (D) additionally improves the clean/robust balance over single-ε (C).

## 7. Methodological finding — the raw SafetyScore is gamed by a degenerate predictor

Without the clean-collapse guard, the raw SafetyScore selected a **degenerate "always-fall"
predictor** for every fall-weighted variant (recorded as `raw_ungated_safety_best` in each
metadata file):

| Variant | Raw pick | Clean acc | Clean fall recall | PGD false-alarms | Raw SafetyScore |
|---|---|---|---|---|---|
| B | epoch 6 | 0.089 | 1.000 | 451 / 452 | 0.800 |
| C | epoch 2 | 0.089 | 1.000 | 452 / 452 | 0.800 |
| D | epoch 6 | 0.109 | 1.000 | 409 / 452 | ~0.80 |
| A (fw1) | epoch 31 | 0.716 | 0.864 | 60 | 0.405 (already non-degenerate) |

A model that flags *every* window as a fall earns `0.35·1 + 0.45·1 + 0.10·1 − 0.10·(~1.0) ≈ 0.80`,
beating any genuinely robust epoch, because the 0.10 false-alarm penalty is too weak. The guard
(`clean_acc ≥ 0.60`, `clean_macro_f1 ≥ 0.50`) excludes these and is the reason the §5 results
are meaningful. The un-guarded picks are retained in metadata for transparency.

## 10–11. Artifact paths

- Comparison table: `results/safety_guided_defense/seed42/seed42_defense_comparison.csv`
- Figures: `results/safety_guided_defense/seed42/figures/fig1_fall_recall_vs_epsilon.png`,
  `fig2_false_fall_alarms_vs_epsilon.png`, `fig3_clean_fgsm_pgd_bar_summary.png`
- Per-epoch training logs + metadata: `results/safety_guided_defense/seed42/logs/`
- Per-checkpoint test-eval (single-eps + sweeps): `results/safety_guided_defense/seed42/test_eval/`
- Checkpoints: `checkpoints/safety_guided_defense/seed42/` (8 `*_best.pt` + 4 `*_last.pt`)

## 12. Recommendation on seeds 43–46

**Recommend proceeding to seeds 43–46 — pending your review** — focusing on **variants C and D
with safety-guided selection** (the two that clear the success criterion most decisively).
Variant A (fw1) is a weak improvement and could be dropped; the macro-F1-selected checkpoints
should be carried as the "standard selection" control. Suggested per-seed protocol: train C and D,
evaluate both selection methods, and report the PGD-recall gain together with the false-alarm and
clean-accuracy cost so the trade-off is visible across seeds before any multi-seed claim. Do not
generalize to other architectures or to `.tex` until the seed-42 result is confirmed to replicate.
