# Variant E λ=1.0 — cross-seed decision analysis (seeds 42 + 43)

> **Analysis-only.** No training was run, seed 44 / λ-tuning were not run, and no Variant D or
> existing Variant E (seed 42 / seed 43) artifacts or thesis `.tex` files were modified. New
> derived files: this report + `selection_rescore_both_seeds.csv` under
> `results/safety_guided_defense/variantE_motion_hard_negative/cross_seed_decision_analysis/`.
> All numbers test n=500 / val n=496, ε=0.030 unless noted; window-level, digital-domain,
> white-box; not solved/certified/clinical/over-the-air.

**Diagnosis (one line):** the mixed seed-43 result is driven mainly by **(A) checkpoint-selection
sensitivity compounded by (D) a too-weak clean-performance guard** — *not* loss instability (B) or
irreducible seed variance (C). On seed 43 the recall-heavy safety score selected an early,
clean-weak, high-false-alarm epoch (18) when much better-balanced epochs existed (24/28) but were
neither selected nor saved. **Recommendation: fix the selection/guard and save candidate
checkpoints, then re-evaluate (Options B+C) — before any new seed or loss redesign.**

## 1. Cross-seed replication summary (E λ=1.0 safety vs Variant D safety; test, ε=0.030)

| Effect | Seed 42 | Seed 43 | Consistent? |
|---|---|---|---|
| PGD recall (E − D) | 0.356 − 0.444 = −0.088 | 0.378 − 0.289 = **+0.089** | direction differs |
| Total PGD FP (E − D) | 117 − 157 = −40 (**−25%**) | 151 − 160 = −9 (**−6%**) | direction yes, magnitude no |
| walk/run→fall (E − D) | 80 − 120 = −40 (**−33%**) | 108 − 119 = −11 (**−9%**) | direction yes, magnitude no |
| Clean accuracy (E − D) | +0.060 | **−0.090** | **no — reversed** |
| Clean macro-F1 (E − D) | +0.090 | **−0.076** | **no — reversed** |
| PGD binary-F1 (E − D) | 0.180 − 0.180 = 0 | 0.160 − 0.119 = +0.041 | E ≥ D both |
| PGD collapse ε | 0.030 = 0.030 | 0.030 = 0.030 | **yes** |
| Matched-recall frontier (E lower FP) | yes | yes (smaller margin) | **yes** |

## 2. What replicated robustly

- **PGD recall stayed well above the FGSM defense** on both seeds (E 0.356 vs 0.089; 0.378 vs 0.022).
- **The attacked recall/false-alarm frontier improved on both seeds** (E has lower FP at matched
  recall across the epsilon sweep — §6).
- **Collapse ε unchanged** (0.030) on both.
- **Residual motion false alarms stayed high-confidence** on both: median fall-probability walk/run
  ≈ 0.82/0.83 (seed 42), ≈ 0.71/0.75 (seed 43), vs true falls ≈ 0.26 both. **Thresholding still
  cannot separate them** — the inverted geometry persists (the penalty cuts FA *count*, not their
  confidence).

## 3. What did NOT replicate

- **False-alarm reduction magnitude:** −25%/−33% (seed 42) vs −6%/−9% (seed 43).
- **Clean accuracy / macro-F1 effect:** improved on seed 42, **degraded** on seed 43 (reversed).
- **Selected epoch behaviour:** seed 42 safety pick = epoch 56 (late, clean-strong); seed 43 = epoch
  18 (early, clean-weak). This is the proximate cause of the differences above.
- **Safety-score behaviour:** on seed 43 the score peaked at an early high-recall/high-FP epoch; on
  seed 42 it peaked at a late high-clean epoch.

## 4. Checkpoint-selection diagnosis

| Seed | Selection | Epoch | val acc | val macro-F1 | val PGD rec | val PGD FP | test acc | test PGD rec | test PGD FP | test walk/run FP |
|---|---|---|---|---|---|---|---|---|---|---|
| 42 | safety | 56 | 0.859 | 0.851 | 0.386 | 101 | 0.806 | 0.356 | 117 | 80 |
| 42 | macro-F1 | 66 | 0.875 | 0.871 | 0.000 | 13 | 0.836 | 0.000 | 20 | 15 |
| 43 | safety | 18 | **0.643** | **0.640** | 0.432 | **146** | 0.630 | 0.378 | 151 | 108 |
| 43 | macro-F1 | 34 | 0.800 | 0.795 | 0.045 | 31 | 0.792 | 0.022 | 38 | 21 |

Seed 43's safety pick (epoch 18) is **too early, too recall-heavy, and too weak on clean
guardrails**: its validation clean accuracy (0.643) and macro-F1 (0.640) are far below seed 42's
pick (0.859 / 0.851), and it carries the most false alarms of any reasonable epoch (val FP 146). The
recall-heavy safety score (0.45·pgd_recall vs only −0.10·false-alarm-burden) rewarded epoch 18's
high val recall (0.432) and the guard (clean_acc ≥ 0.60) was too weak to exclude it. On seed 42 the
same score happened to peak at a clean-strong epoch, so no problem surfaced — the issue is latent in
the score, exposed by seed 43.

## 5. Alternative-selection simulation (validation logs; `selection_rescore_both_seeds.csv`)

| Rule | Seed 42 → epoch (saved?) | Seed 43 → epoch (saved?) | Seed 43 val acc / rec / FP |
|---|---|---|---|
| R0 current safety (guard .60/.50) | 56 (safety) | 18 (safety) | 0.643 / 0.432 / 146 |
| R1 stronger acc guard (≥.70) | 56 (safety) | **24 (NOT saved)** | 0.738 / 0.273 / 81 |
| R2 stronger macro-F1 guard (≥.65) | 56 (safety) | **24 (NOT saved)** | 0.738 / 0.273 / 81 |
| R3 FP-constrained (val FP≤110) | 56 (safety) | **24 (NOT saved)** | 0.738 / 0.273 / 81 |
| R4 cost FN×10+FP | 56 (safety) | 18 (safety) | 0.643 / 0.432 / 146 |
| R5 min acc .75 + max recall | 56 (safety) | **28 (NOT saved)** | 0.764 / 0.182 / 60 |
| R6 min macro-F1 .70 + max recall | 56 (safety) | **24 (NOT saved)** | 0.738 / 0.273 / 81 |

**Key result:** on **seed 42** every rule keeps the already-good epoch 56 (the fix is harmless
there). On **seed 43**, four of seven rules (stronger guard / FP-constrained / macro-F1-floor) would
have selected **epoch 24** (val acc 0.738, recall 0.273 still ≫ the FGSM bar 0.022, FP 81 — far
below epoch 18's 146) or **epoch 28** (acc 0.764, recall 0.182, FP 60). **A stronger clean-performance
guard would have avoided the seed-43 clean-accuracy drop while keeping PGD recall above the
FGSM-defense baseline and cutting false alarms.**

**Caveat (important):** epochs 24/28 were **not saved** (only the safety-best and macro-F1-best
checkpoints are persisted), so these are **validation-only candidates** — their *test* operating
points cannot be confirmed without re-generating the weights. This is itself the finding that future
training should **save multiple candidate checkpoints** (or all epochs / top-k) so better selections
can be evaluated without a full re-run.

## 6. Frontier analysis (D vs E across epsilon sweeps)

- **E reduces PGD false alarms at (nearly) every epsilon on both seeds** — seed 42 ΔFP −24…−62;
  seed 43 ΔFP −2…−20 (one tie at ε=0.040).
- **E improves matched-recall false alarms on both seeds** (e.g. seed 43 at recall ≈0.73: E 125 FP
  vs D 140 FP; at recall ≈0.91: E 55 FP vs D 83 FP).
- **Seed 43's improvement is smaller but directionally consistent** with seed 42.
- **E shifts the frontier (lower FP at matched recall), it does not merely move along D's curve** —
  on both seeds. Collapse ε is unchanged (0.030).

So the *capability* the motion penalty adds (a better recall/false-alarm frontier) replicates; the
*operating point* the safety score picks off that frontier is what varies — reinforcing §4/§5.

## 7. Loss / objective diagnosis

The probability penalty cut false-alarm *count* on both seeds but left residual motion false alarms
**high-confidence** on both (§2) — so a **margin-based motion penalty** (forcing the true-class logit
above the fall logit for adversarial walk/run) remains the best-motivated *eventual* geometry fix.
**However, the cross-seed evidence says the immediate, dominant problem is selection, not the loss:**
the same loss produced a good operating point on seed 42 and a recoverable-by-selection one on seed
43. Fixing the loss before fixing selection would conflate the two. **Fix selection first; revisit
the margin penalty only if high-confidence residual false alarms remain the bottleneck after
selection is corrected.**

## 8. Decision options

| Option | Verdict | Why |
|---|---|---|
| A. Continue E λ=1.0 to seeds 44–46 | **Premature** | Would add variance on top of an un-fixed, seed-sensitive selection; the operating points would not be comparable across seeds. |
| **B. Improve checkpoint selection / guards first (no new loss)** | **Recommended (with C)** | §4/§5: a stronger clean-performance guard fixes the seed-43 weakness and is harmless on seed 42. |
| **C. Save / evaluate multiple candidate checkpoints per run** | **Recommended (with B)** | §5: the better seed-43 epochs (24/28) exist but weren't saved, so B cannot be *confirmed on test* without this. |
| D. Redesign loss (margin penalty) | Defer | §7: best-motivated eventual geometry fix, but selection — not the loss — explains the heterogeneity now. |
| E. Stop; write up D/E as trade-off studies | Not yet | The frontier improvement is real and consistent; the instability is a fixable selection artifact, not a dead end. |

## 9. Recommendation

**Do B + C together: re-run E λ=1.0 on seed 42 AND seed 43 with a stronger clean-performance guard
and with multiple candidate checkpoints saved, then test-evaluate the guard-balanced pick.** This is
the minimal-experiment / maximum-information step:

- It is **deterministic** (same recipe, seeds 42/43) — re-running reproduces the same epochs; we only
  change the *selection rule* (e.g. require val clean_acc ≥ 0.70 **and** clean_macro_f1 ≥ 0.65 for
  safety-score eligibility) and *persist* the top-k candidate checkpoints.
- It directly tests the §5 hypothesis: does the guard-balanced seed-43 pick (≈ epoch 24/28) confirm
  on test as higher clean accuracy + lower false alarms + recall above the FGSM bar?
- It **does not redesign the loss**, **does not run seed 44**, and **does not tune λ** — so it cannot
  overfit a new design to one seed, and it keeps the claim thesis-safe (a defense is only as good as a
  *stable, reproducible* selection rule).
- If the guard-balanced picks are consistent across both seeds → *then* proceed to seeds 44–46 (with
  the fixed selection). If high-confidence residual false alarms remain the bottleneck after that →
  *then* design the margin penalty (Option D).

Holding pattern for the thesis in the meantime: report Variant D and Variant E honestly as a
**trade-off study** (Variant E improves the attacked recall/false-alarm frontier vs Variant D on both
seeds, with a selection-sensitive operating point), not as a settled "better defense."

## 10. Exact next prompt

```
Analysis-plus-targeted-rerun: fix Variant E checkpoint selection, no loss redesign, seeds 42 and 43 only.

Constraints:
- Do NOT run seed 44-46. Do NOT tune lambda (lambda_motion = 1.0 only). Do NOT change the motion
  penalty or the Variant D training recipe. Do NOT modify frozen Variant D results or the existing
  seed-42/seed-43 Variant E result artifacts (write to a NEW sub-namespace, e.g.
  variantE_motion_hard_negative/selection_v2/seed42 and .../seed43).
- Add a STRONGER clean-performance guard to the safety-score selection (e.g. require val clean
  accuracy >= 0.70 AND val clean macro-F1 >= 0.65 for safety-score eligibility) and SAVE top-k
  candidate checkpoints per run (e.g. the best safety-eligible checkpoint under the stronger guard,
  plus the macro-F1 best). Implement this as a NEW training script or a documented flag; do not
  modify the committed train_variantE_motion_hard_negative.py used for the prior results.
- Re-run E lambda=1.0 on seed 42 and seed 43 (deterministic), evaluate the new guard-balanced
  checkpoint(s) (single-eps 0.030 + 18-eps FGSM/PGD sweeps + probability export), and compare on
  test vs: FGSM defense, Variant D safety, and the PRIOR Variant E safety pick, for each seed.
- Report whether the stronger-guard selection (a) raises clean accuracy/macro-F1 toward Variant D,
  (b) keeps PGD recall above the FGSM-defense baseline, (c) reduces false alarms incl. walk/run, and
  (d) makes the seed-42 and seed-43 operating points consistent. Honest trade-off framing; no
  solved/certified/clinical/over-the-air claims. Do not edit thesis .tex. Do not commit until I review.
```
