# Variant E selection-v2 pilot — seeds 42 & 43

> **Framing (important):** this is a **selection-v2 pilot, not independent validation.** The
> stronger guard was motivated using seeds 42 and 43, so **no generalization is claimed** from this
> rerun. The Variant E training objective is byte-identical to the prior runs (λ=1.0); only
> checkpoint selection/saving changed. New namespace only; frozen Variant D and the prior
> Variant E seed-42/seed-43 artifacts were not modified; no thesis `.tex` edits; no seeds 44–46;
> no λ tuning; no loss redesign. Test n=500, ε=0.030 unless noted; window-level, digital-domain,
> white-box; not solved/certified/clinical/over-the-air.

**Headline:** Selection-v2 **confirms the cross-seed diagnosis** — the mixed seed-43 result was a
**selection artifact, not a loss problem.** With the *same* loss and a stronger clean guard
(val acc ≥ 0.70 ∧ macro-F1 ≥ 0.65), seed-43 selection moved from the clean-weak epoch 18 to the
better-balanced epoch 24: **clean accuracy recovered 0.630 → 0.720** and **false alarms halved
(151 → 79, walk/run 108 → 50)** — while on seed 42 the pick was **unchanged** (epoch 56 = the prior
Variant E safety checkpoint, identical weights). The trade-off: seed-43 PGD recall fell to 0.111
(still above the FGSM defense's 0.022, but much lower than the prior 0.378), and residual motion
false alarms remain high-confidence.

## What changed and how it was kept faithful

Selection only. The optimizer/data RNG are seeded identically, so per-epoch weights are
deterministic and independent of selection; early stopping replicates the prior run's length
(seed 42 → 70 epochs, seed 43 → 35) so v2 selects from the same visited epochs. Verification:
seed-42 v2safety reproduces the prior Variant E safety test metrics exactly (recall 0.356, FP 117,
clean acc 0.806). New script `scripts/train_variantE_selection_v2.py`; the committed
`train_variantE_motion_hard_negative.py` was not modified. Selected candidate epochs
(`analysis/selection_candidates.csv`): seed 42 v2safety=56, v2lowFA=64; seed 43 v2safety=24,
v2lowFA=31 — matching the cross-seed analysis predictions.

## Results (test, ε=0.030)

| Seed | Model | Clean acc | Clean macro-F1 | Clean fall recall | PGD recall | PGD FP | walk+run→fall | PGD collapse ε |
|---|---|---|---|---|---|---|---|---|
| 42 | FGSM defense | 0.834 | 0.814 | 0.911 | 0.089 | 54 | 39 | 0.018 |
| 42 | Variant D safety | 0.746 | 0.700 | 1.000 | 0.444 | 157 | 120 | 0.030 |
| 42 | prior E safety (ep56) | 0.806 | 0.790 | 0.978 | 0.356 | 117 | 80 | 0.030 |
| 42 | **v2safety (ep56)** | 0.806 | 0.790 | 0.978 | 0.356 | 117 | 80 | 0.030 |
| 42 | **v2lowFA (ep64)** | 0.818 | — | 0.956 | 0.133 | 61 | 36 | 0.025 |
| 43 | FGSM defense | 0.902 | 0.901 | 0.956 | 0.022 | 35 | 26 | 0.018 |
| 43 | Variant D safety | 0.720 | 0.676 | 1.000 | 0.289 | 160 | 119 | 0.030 |
| 43 | prior E safety (ep18) | **0.630** | **0.600** | 0.978 | 0.378 | 151 | 108 | 0.030 |
| 43 | **v2safety (ep24)** | **0.720** | **0.669** | 0.933 | 0.111 | 79 | 50 | 0.025 |
| 43 | **v2lowFA (ep31)** | 0.766 | — | 0.933 | 0.067 | 63 | 43 | 0.020 |

## The 7 questions

**1. Does selection-v2 avoid seed-43's clean-performance drop? Yes.** v2safety clean accuracy
0.720 vs prior 0.630 (+0.090) and macro-F1 0.669 vs 0.600 (+0.069) — recovered to Variant D's
clean-accuracy level (0.720) and back above the 0.70 guard.

**2. Does it reduce total + walk/run PGD false alarms? Yes, strongly on seed 43.** v2safety
total FP 151 → 79 (**−48%**), walk/run 108 → 50 (**−54%**); vs Variant D it halves both (FP 160→79,
walk/run 119→50). On seed 42 v2safety is unchanged (already the prior reduced pick vs D); the
v2lowFA candidate gives a further reduction (FP 117 → 61).

**3. Does PGD recall stay above the FGSM defense? Yes, on both seeds** — 0.356 > 0.089 (seed 42);
0.111 > 0.022 (seed 43) — but the seed-43 margin is now small (the recall cost of the fix).

**4. Is selection-v2 harmless or beneficial on seed 42? Harmless.** v2safety = the prior Variant E
safety checkpoint (epoch 56), identical weights and test metrics. The stronger guard did not
disturb seed 42 (its pick already cleared it). A lower-false-alarm alternative (v2lowFA) is also
available.

**5. Does it make seed-42 and seed-43 operating points more consistent? On the clean side, yes;
on the recall side, only partly.** Clean accuracy is now consistent (0.806 / 0.720, both above the
guard — the collapse is gone) and false alarms are controlled on both. But PGD recall is still
seed-variable (0.356 vs 0.111), and there is a notable **validation→test recall gap on seed 43**
(epoch 24: val recall 0.273 → test 0.111), i.e. validation PGD recall (n_fall=44) is a noisy
selection signal. So the guard fixed the *clean* inconsistency but not the *recall* variance.

**6. Do residual motion false alarms remain high-confidence? Yes.** v2safety walk/run median
fall-probability 0.82/0.83 (seed 42) and 0.85/0.83 (seed 43), vs true falls 0.26/0.14. The inverted
geometry persists — thresholding still cannot separate them. Selection-v2 cut FA *count*, not the
confidence geometry.

**7. Should selection-v2 be the recipe for seeds 44–46, or is a margin loss still needed?**
**Adopt selection-v2 as the (now frozen) selection rule** — it removes the clean-collapse failure
mode and is harmless on seed 42, and it confirms the diagnosis that selection (not the loss) drove
the seed-43 weakness. **But it is not, by itself, a uniformly stronger defense:** on seed 43 it
bought clean accuracy and false-alarm control by giving up most of the PGD recall (0.378 → 0.111),
and residual false alarms stay high-confidence. So a **margin-based motion penalty remains the
eventual geometry fix**, but it is *secondary* to first confirming the frozen selection rule
generalizes on independent seeds.

## Interpretation

Selection-v2 cleanly separates the two questions that were confounded before: it shows the seed-43
clean collapse was **selection sensitivity + a weak guard** (fixed here), and that the **loss is not
the cause** (same loss, much better clean behaviour under the stronger guard). What it does *not* do
is make the attacked operating point uniformly strong — it relocates seed 43 to a more conservative
(lower-recall, lower-false-alarm, clean-recovered) point. The honest thesis framing is a **trade-off
study**: Variant D (max recall, max false alarms) → prior Variant E (frontier-improved, but
selection-sensitive clean) → selection-v2 (clean-stable, false-alarm-controlled, more conservative
recall). The residual high-confidence motion false alarms are the remaining open problem.

## Recommendation (minimal experiments, maximum information, no overfitting, thesis-safe)

1. **Freeze selection-v2** (stronger guard) as the selection rule going forward — it is the
   diagnosed fix and is harmless on seed 42.
2. **Independent confirmation: run seeds 44–46 with the frozen selection-v2 rule** (no further
   tuning), reporting the full operating point per seed (clean acc/macro-F1, PGD recall, total +
   walk/run false alarms, collapse ε). This is now a *legitimate generalization test* because the
   rule is fixed; it is the single most informative next experiment.
3. **Defer the margin-based loss** (Option D) until after (2): it is the right eventual geometry
   fix for the high-confidence residual false alarms, but it should be evaluated against a
   *confirmed, frozen* selection baseline, not introduced while selection is still being settled.
4. **Report the val→test recall gap and the recall trade honestly** as limitations; do not claim
   selection-v2 is a settled "better defense" beyond fixing the clean-collapse selection artifact.

## Limitations

- **Pilot, not independent validation** (guard tuned on seeds 42/43) — no generalization claim.
- Selection-v2 trades PGD recall for clean accuracy + false-alarm control (seed 43 recall 0.111).
- Validation PGD recall is a noisy selection signal (n_fall val = 44); seed-43 epoch-24 val recall
  0.273 → test 0.111.
- Residual motion false alarms remain high-confidence (geometry unsolved).
- Window-level, digital-domain, white-box only; no clinical/over-the-air/certified claims.

## Exact next prompt

```
Independent confirmation of the FROZEN Variant E selection-v2 rule on seeds 44, 45, 46.

Constraints:
- Seeds 44, 45, 46 only. lambda_motion = 1.0 only. Do NOT tune lambda, do NOT change the motion
  penalty, the Variant E training recipe, or the selection-v2 guard (val clean acc >= 0.70 AND
  val clean macro-F1 >= 0.65). Use scripts/train_variantE_selection_v2.py unchanged.
- LeNet only, same UT-HAR/SenseFi split, same eval protocol (PGD steps=10, alpha=eps/6). New
  namespace under variantE_motion_hard_negative/selection_v2/seed{44,45,46}.
- For each seed, evaluate the v2safety and v2lowFA candidate checkpoints on test (single-eps 0.030
  + 18-eps FGSM/PGD sweeps + probability export). Build a cross-seed (42-46) summary of the
  selection-v2 operating point: clean accuracy/macro-F1, PGD recall, total + walk/run false alarms,
  collapse epsilon, and whether clean performance stays above the guard on every seed.
- Report whether selection-v2 generalizes: (a) no clean collapse on any seed, (b) PGD recall stays
  above the FGSM-defense baseline, (c) false alarms controlled vs Variant D, (d) how variable the
  recall/false-alarm operating point is across seeds. Honest trade-off framing; no
  solved/certified/clinical/over-the-air claims. Do not edit thesis .tex. Do not commit until I review.
```
