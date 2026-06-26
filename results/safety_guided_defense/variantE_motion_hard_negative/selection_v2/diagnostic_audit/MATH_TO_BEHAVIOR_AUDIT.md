# Math-to-behavior diagnostic audit — Variant E + selection-v2 (seeds 42 & 43)

> **Analysis-only.** No model was trained; seed 44 and seeds 45–46 were not run; no λ tuning, no
> loss redesign, no selection-v2 guard change; no Variant D / prior Variant E / selection-v2 / thesis
> `.tex` artifacts were modified. The only model loading was **evaluation-only** (stronger-PGD sanity
> check, §13). All new files are under `.../selection_v2/diagnostic_audit/`. All numbers are
> **window-level, digital-domain, white-box** on processed CSI tensors, test split n=500 (45 fall
> windows), ε=0.030 unless noted. No clinical, certified-robustness, or over-the-air claim is made.

Derived CSVs and figures referenced below live in this directory and `figures/`.

---

## 1. Executive diagnosis

- **Variant D** (safety-guided adversarial training) prioritizes attacked fall recall and reaches the
  highest PGD@0.030 recall (0.444 / 0.289 on seeds 42 / 43) but at the **highest false-alarm burden**
  (157 / 160) and reduced clean accuracy (0.746 / 0.720). It is a high-recall/high-false-alarm
  **trade-off operating point**.
- **Prior Variant E** (motion hard-negative, λ=1.0) lowers the motion-class false alarms and improves
  the matched-recall frontier, but its operating point is **checkpoint-selection-sensitive**: on seed
  42 the safety score landed on a clean-strong epoch (56), on seed 43 on a clean-weak, early,
  high-false-alarm epoch (18, val clean acc 0.643).
- **Selection-v2 fixed the selection artifact**, not the loss: with the *same* objective and a stronger
  clean guard (val acc ≥ 0.70 ∧ macro-F1 ≥ 0.65) it moved seed 43 to epoch 24 — clean accuracy
  recovered 0.630 → 0.720, total false alarms 151 → 79 (−48%), walk/run 108 → 50 (−54%) — and left
  seed 42 unchanged (epoch 56, harmless). It is a more **conservative** point: seed-43 PGD recall fell
  to 0.111.
- **Selection-v2 did not fix the geometry.** Residual walk/run false alarms remain *more confident*
  than true falls (median fall-prob ≈ 0.71–0.85 vs true-fall ≈ 0.14–0.26), calibration stays poor
  (ECE ≈ 0.44–0.54), and under PGD-20 the seed-43 v2safety recall collapses to 0.000. The recall
  estimates rest on ≤ 17 of 45 fall windows with wide, overlapping confidence intervals.
- **Recommendation (see §19):** the cheapest high-information next step is **independent validation on
  seed 44 with the frozen selection-v2 rule, against the pre-registered criteria (§17)** — but the
  selection signal should be re-grounded on *false alarms + clean guard* (reliable), not validation
  PGD recall (noisy). A margin-based loss is the eventual geometry fix, deferred behind seed-44.

---

## 2. Formal math summary

### 2.1 Variant E training objective
`L_total = L_FWCE + λ_motion · L_motion`, with `λ_motion = 1.0` (frozen).
- `L_FWCE = CrossEntropy(logits, y; class_weights)`, class weight 3 on fall (class 1), 1 elsewhere,
  evaluated on the batch-split mixture (50% clean / 25% FGSM / 25% PGD).
- `L_motion = mean( P_fall(x_adv) : y(x_adv) ∈ {walk, run} )`, the mean softmax fall-probability over
  the **adversarial** sub-batch windows whose true class is walk or run (0 if none in the batch).
- `x_adv` are FGSM/PGD perturbations generated with an **unweighted** CE (the adversary does not see the
  defender's weights); the attack generation is unchanged — only the defender loss adds `L_motion`.

Expected effect: raising `λ_motion` lowers adversarial walk/run → fall probability, reducing motion
false alarms; if too large it also suppresses fall-favoring decision regions and lowers fall recall.
This matches the observed λ sweep (test, seed 42 safety pick): λ=0.5 → recall 0.089/FP 145 (too weak);
λ=1.0 → 0.356/117 (best); λ=2.0 → 0.178/122 (over-penalized).

### 2.2 False-alarm condition
A false fall alarm on a non-fall window occurs iff `argmax_k logit_k(x_adv) = fall`. For a walk/run
window define `margin_motion = logit_fall − logit_true_class`: `> 0` ⇒ predicted fall; `< 0` ⇒ true
motion class kept above fall; large positive ⇒ high-confidence false alarm. The audit's measured
`logit_fall − logit_true` medians for residual walk/run false alarms are large and positive
(§10), i.e. confidently wrong.

### 2.3 Selection-v2 rule
Per epoch compute `SafetyScore = 0.35·R_clean + 0.45·R_pgd + 0.10·R_fgsm − 0.10·NFAB`, where the R's are
validation fall recalls (clean / PGD@0.030 / FGSM@0.030) and `NFAB = 0.5·(FP_fgsm/n_nonfall) +
0.5·(FP_pgd/n_nonfall) ∈ [0,1]` is the normalized false-alarm burden (n_nonfall = non-fall validation
windows). Selection-v2 changes **eligibility only**: a checkpoint is eligible for the safety pick iff
`clean_acc_val ≥ 0.70` AND `macroF1_val ≥ 0.65` (was 0.60 / 0.50). Candidates saved each run:
- `v2safety` = eligible argmax SafetyScore;
- `v2maxrec` = eligible argmax (val PGD recall, tie → min val PGD FP);
- `v2lowFA` = eligible, val PGD recall ≥ 0.10, argmin (val PGD FP, tie → max recall);
- `v2macroF1` = argmax val macro-F1 (no guard).
Effect: the guard removes clean-weak epochs (seed-43 epoch 18) and selects a more conservative epoch
(seed-43 epoch 24), improving clean performance and cutting false alarms, at the cost of attacked recall.

---

## 3. Loss-scale and gradient diagnostics  (`loss_scale_diagnostics.csv`, `fig_loss_scale_vs_epoch.png`)

**Gradient norms were not computed** (would require a backward-pass instrumentation hook in the
training loop, i.e. a code change to the training script — out of scope for an analysis-only audit).
Best available proxies are the logged loss-term scales and the downstream probability/logit geometry.

From the logs: the raw motion penalty `L_motion` (mean adversarial walk/run fall-probability) starts
≈ 0.13 and declines to ≈ 0.05 by late epochs on both seeds, i.e. **λ_motion·L_motion ≈ 0.05–0.13**
against a fall-weighted CE of order ≈ 0.8–1.8. So **λ=1.0 is numerically a small-to-moderate additive
term (penalty/CE ratio ≈ 0.03–0.15), not dominant.** The penalty declines toward a plateau and the
safety-selected epochs (seed 42 ep 56, seed 43 ep 24) occur *after* it has largely stabilized.
Interpretation: the motion penalty plausibly explains the **false-alarm reduction** (it directly lowers
adversarial walk/run fall-probability), and *can* contribute to the **recall reduction** indirectly
(suppressing fall-favoring regions), but at this scale the dominant driver of the recall/false-alarm
operating point is **which epoch is selected**, not the penalty magnitude (see §4, §8).

## 4. Per-epoch trajectories  (`epoch_trajectory_summary.csv`, `fig_epoch_trajectory_seed{42,43}.png`)

- **Seed 42:** validation clean accuracy rises and stabilizes ≈ 0.80–0.88 by the 40s–60s; the safety
  score peaks at **epoch 56** (val acc 0.859, PGD recall 0.386, FP 101). Both prior-E-safety and
  v2safety select epoch 56 because it already clears the stronger guard — so they are identical.
- **Seed 43:** the safety score's global max is **epoch 18** (val acc 0.643, PGD recall 0.432, FP 146)
  — an **early, high-recall, high-false-alarm, clean-weak** spike *before clean accuracy stabilizes*.
  Prior-E-safety selected it. The stronger guard makes epoch 18 ineligible (0.643 < 0.70), so
  selection-v2 selects the best eligible epoch, **epoch 24** (val acc 0.738, PGD recall 0.273, FP 81) —
  after clean accuracy has stabilized. This is the mechanism of the whole seed-43 story: the recall-heavy
  score rewards an early clean-immature spike, and the guard defers selection to a clean-stable region.

## 5. Recall vs false-alarm Pareto  (`pareto_points.csv`, `fig_pareto_seed{42,43}.png`)

Dominance defined among guard-passing points (recall ≥, FP ≤, strict somewhere). Classification per point:

| seed | point | recall | FP | clean acc | guard | class |
|---|---|---|---|---|---|---|
| 42 | D_safety | 0.444 | 157 | 0.746 | pass | high-recall/high-FA |
| 42 | priorE_safety = v2safety | 0.356 | 117 | 0.806 | pass | balanced |
| 42 | v2lowFA | 0.133 | 61 | 0.818 | pass | conservative low-FA |
| 42 | FGSM_defense | 0.089 | 54 | 0.834 | pass | conservative low-FA |
| 42 | priorE_macroF1 | 0.000 | 20 | 0.836 | pass | invalid (recall collapse) |
| 43 | priorE_safety | 0.378 | 151 | **0.630** | **fail** | fails clean guard |
| 43 | D_safety | 0.289 | 160 | 0.720 | pass | high-recall/high-FA (dominated) |
| 43 | v2safety | 0.111 | 79 | 0.720 | pass | conservative low-FA |
| 43 | v2lowFA | 0.067 | 63 | 0.766 | pass | conservative low-FA |
| 43 | FGSM_defense | 0.022 | 35 | 0.902 | pass | conservative low-FA |

**Answers.** Selection-v2 is **not** a strict frontier improvement over prior-E at a fixed recall on
seed 43; it is a **conservative lower-recall / lower-false-alarm, clean-stable** operating point. The
honest framing is a menu of trade-off points: D_safety (max recall, max FA), prior-E-safety
(frontier-improved but seed-42-only clean-stable), selection-v2 v2safety/v2lowFA (clean-stable,
false-alarm-controlled, conservative recall). Points that should **not** be called "better": any
macro-F1 pick (recall ≈ 0, invalid), and prior-E-safety seed 43 (fails the clean guard).

## 6. Decision-cost curves  (`cost_curve_preference.csv`, `fig_cost_preference_by_ratio.png`)

`Cost = λ_FN·missed_falls + λ_FP·false_alarms`, missed_falls = round((1−recall)·45). Preferred (lowest-cost)
checkpoint by FN:FP ratio:
- **Low ratios (1:1, 2:1):** FGSM defense (fewest false alarms) is preferred on both seeds.
- **Mid ratios (5:1–10:1):** the preference shifts toward lower-FA Variant-E points (v2lowFA / FGSM
  defense) — selection-v2's false-alarm control pays off here.
- **High ratios (20:1, 50:1):** D_safety / prior-E-safety (max recall) become preferred because missed
  falls dominate the cost.
The preferred checkpoint **changes with the FN:FP weighting** — there is no single winner. This is the
core justification for framing the work as a **trade-off study**, not a solved defense. (Experimental
sensitivity only; these are not clinical cost ratios.)

## 7. Statistical uncertainty  (`uncertainty_intervals.csv`, `paired_comparisons.csv`)

With only 45 fall windows, recall point estimates rest on few true positives and have wide 95% Wilson
intervals that **overlap heavily**:
- seed 43: v2safety 0.111 (tp 5/45) CI [0.048, 0.235]; D_safety 0.289 (13/45) CI [0.177, 0.434];
  prior-E-safety 0.378 (17/45) CI [0.251, 0.524].
- seed 42: v2safety 0.356 (16/45) CI [0.232, 0.502]; D_safety 0.444 (20/45) CI [0.309, 0.588].

**So differences like 0.111 vs 0.178 vs 0.289 are few-window effects (5 vs 8 vs 13 windows) and are not
statistically distinguishable at 95%.** Specificity intervals are tighter (455 non-fall windows). The
val→test recall gap (§8) is statistically unsurprising at this fall count. **Safe claims:** clean
accuracy/macro-F1 differences, false-alarm *count* differences (large, non-overlapping), and the
*direction* of the trade-off. **Suggestive only:** any specific PGD-recall ranking among Variant-D/E
points. Paired McNemar over fall windows (`paired_comparisons.csv`) shows the discordant counts are
small (single-digit), consistent with non-significant recall differences.

## 8. Validation-to-test reliability  (`val_test_reliability.csv`, `fig_val_vs_test_{recall,false_alarms}.png`)

| seed | ckpt | val→test recall | val→test FP |
|---|---|---|---|
| 42 | v2safety (56) | 0.386 → 0.356 (gap 0.03) | 101 → 117 |
| 43 | v2safety (24) | 0.273 → **0.111** (gap **0.16**) | 81 → 79 |
| 43 | v2lowFA (31) | 0.182 → 0.067 (gap 0.12) | 49 → 63 |

**Validation PGD recall is a noisy/optimistic selection signal** (seed-43 val 0.273 → test 0.111),
whereas **validation false alarms transfer reliably** (81 → 79; 49 → 63). Conclusion: future selection
should lean on **false-alarm constraints + the clean guard** (reliable), not on maximizing validation
PGD recall (noisy with 44 val fall windows). Per-epoch validation *window-level* predictions were not
saved, so bootstrap selection-stability across epochs is **not feasible without re-running** validation
inference per epoch (epoch checkpoints are not all persisted) — this is itself an argument to **save
multiple candidate checkpoints**, which selection-v2 now does.

## 9. Class imbalance & class-normalized false alarms  (`class_counts.csv`, `class_normalized_false_alarms.csv`)

Test counts: fall 45, lie down 66, walk **147**, pickup 50, run **121**, sit down 40, stand up 31
(walk+run = 268 of 455 non-fall ≈ 59%). But walk/run dominance is **not only** a count effect — their
**per-class** false-alarm rates are the highest: D_safety seed 42 run 65/121 = **0.54**, walk 37/147 =
**0.37**. Selection-v2 reduced walk/run in **both raw count and normalized rate** on seed 43 (run 0.50 →
0.30, walk 0.33 → **0.10**; vs Variant D run 0.55, walk 0.35). No other non-fall class becomes a major
new false-alarm source.

## 10. Logit-margin & probability geometry  (`logit_margin_diagnostics.csv`, `fig_fall_probability_distributions.png`, `fig_logit_margin_distributions.png`, `fig_confidence_by_error_type.png`)

For v2safety (test PGD): residual walk/run false alarms have median fall-probability ≈ **0.82/0.83**
(seed 42), **0.85/0.83** (seed 43), with large positive median `logit_fall − logit_true`, while true
falls sit at median fall-prob ≈ **0.26** (seed 42) / **0.14** (seed 43). **Residual false alarms remain
high-confidence and the inversion persists** — selection-v2 reduced the *number* of false alarms but
**did not fix the geometry**. True falls are still *lower*-confidence than residual walk/run false
alarms, so **a single fall-probability threshold cannot separate them** (confirming the earlier
decision analysis). A **margin-based loss** that explicitly pushes `logit_true − logit_fall > m` for
adversarial walk/run is the better-motivated geometry fix.

## 11. Instance-level fall windows  (`fall_window_overlap.csv`)

- 18/45 (seed 42) and 22/45 (seed 43) fall windows are **missed by every model** — a hard core the
  attack defeats regardless of defense.
- Seed 43: v2safety **loses 13 specific fall windows** that prior-E-safety detected and recovers only 1
  — the recall drop (17 → 5 detected) is **concentrated in a small, identifiable subset**, not a broad
  desensitization. These are ambiguous windows the earlier (clean-immature) epoch-18 model happened to
  flag; the clean-stable epoch-24 model does not.

## 12. Instance-level false alarms  (`false_alarm_overlap.csv`)

- Seed 43: v2safety **removed 75 false alarms vs prior-E**, of which **58 (77%) are walk/run** — it is
  removing the **intended motion-class** false alarms — and **introduced only 3** new ones (sample_ids
  117, 154, 332). 70 false alarms are **shared hard cases** across Variant D / prior-E / v2safety.
- Seed 42: v2safety = prior-E (identical), 53 false alarms removed vs Variant D; 104 shared hard cases.
So selection-v2 removes the targeted motion false alarms with almost no collateral, but a residual core
of confident false alarms is common across all models.

## 13. Stronger-attack sanity check  (`stronger_attack_eval/stronger_pgd_sanity_check.csv`)

Evaluation-only, fixed-start PGD-10/20/40 and PGD-20 random-start at ε=0.030:
- **Recall decreases monotonically with steps for every checkpoint** (e.g. D_safety s42 0.444 → 0.333 →
  0.311; prior-E/v2safety s42 0.356 → 0.244 → 0.222), and random-start does **not** raise robustness.
  ⇒ **No evidence of gradient masking; PGD-10 numbers are mild and not artificially robust.**
- **seed-43 v2safety recall collapses 0.111 → 0.000 under PGD-20/40** — its already-marginal attacked
  recall is at the noise floor and not durable. D_safety retains more recall under stronger PGD.
This reinforces §7: the seed-43 selection-v2 attacked recall should be described as **negligible/fragile**,
not as a robustness gain.

## 14. Representation geometry — NOT performed

Penultimate-layer embedding extraction was **not performed** in this audit. It requires a forward hook
into `UT_HAR_LeNet` (model-internal instrumentation) plus per-sample embedding export and PCA — feasible
but beyond the analysis-only, no-refactor scope here, and the **output-layer** logit-margin and
calibration analyses (§10, §15) already establish the key geometry conclusion (residual walk/run false
alarms are confidently placed on the fall side; true falls are not). **Proposed future diagnostic:** add
a forward hook on LeNet's pre-logit layer, export embeddings for clean + PGD test windows, compute
distance-to-fall-centroid and nearest-centroid class per group, and PCA-plot fall vs walk/run clusters;
this would directly test whether a *representation*-level margin loss is warranted over an output-logit one.

## 15. Calibration  (`calibration_metrics.csv`)

Under PGD@0.030 all checkpoints are **badly calibrated** (ECE ≈ 0.44–0.54, high Brier/NLL). Mean
max-confidence by error type: detected falls ≈ 0.35–0.55 (**low**), missed falls ≈ 0.52–0.59
(**moderate — confidently wrong, not low-confidence**), walk/run false alarms ≈ 0.67–0.79 (**high**),
other false alarms ≈ 0.65–0.85. Selection-v2 does **not** improve calibration (ECE comparable to
prior-E) — it reduces the *number* of false alarms, not their overconfidence. Because missed falls are
not low-confidence and false alarms are *more* confident than detected falls, **post-hoc thresholding
cannot recover the safety trade-off** — consistent with §10.

## 16. Predictive interpretation for seed 44 (directional, not a prediction)

If selection-v2 generalizes: expect seed-44 v2safety **clean accuracy near the guard (≈ 0.70–0.82)**;
**false alarms well below Variant D** (≈ 50–90 vs ~150–160), walk/run-dominated reduction; **PGD@0.030
recall low and uncertain (≈ 0.05–0.25)**, possibly at/near the FGSM-defense floor, with a wide CI and
likely further reduction under PGD-20. The likely trade-off is again *clean-stable + false-alarm-controlled
+ conservative recall*. **Success** = guard holds out-of-sample + false-alarm reduction vs Variant D +
recall above the FGSM-defense floor (CI lower bound > 0). **Failure** = guard fails out-of-sample, or
recall ≤ FGSM-defense / collapses to 0 under PGD-20. A failure on recall (recall at floor + high-confidence
residual false alarms) is what would **trigger the margin-loss redesign**.

## 17. Seed-44 pre-registration

See `seed44_preregistration.md` (frozen rule; guards; clean-fall-recall ≥ 0.90; PGD-recall floor =
strictly above FGSM-defense with Wilson lower bound > 0; ≤ 0.70× Variant D total and walk/run false
alarms; collapse-ε reporting; cost-ratio sensitivity; explicit support/reject/margin-loss decision
rules). These are **experimental criteria, not clinical thresholds.**

## 18. Thesis-safe interpretation

Variant D prioritizes attacked fall recall but produces high false alarms; prior Variant E improves the
motion false-alarm frontier but is checkpoint-selection-sensitive; selection-v2 stabilizes clean behavior
and false-alarm control while being more conservative in (and uncertain about) attacked recall. Residual
high-confidence motion false alarms remain an open **representation/geometry** problem that thresholding
cannot solve. The results support a **safety-proxy trade-off framework** across operating points — not a
solved defense. All evaluation is window-level, digital-domain, white-box; no clinical, certified, or
over-the-air claim is made.

## 19. Recommendation

**A — Freeze selection-v2 and run seed 44 as independent validation, against the pre-registered criteria
(§17)** — with one explicitly-scoped clarification: at selection time, treat **false-alarm + clean-guard**
as the primary, reliable signals and validation PGD recall as secondary (this is *interpretation of the
existing frozen rule*, not a guard change). Justification (advisor lens): (i) explainability is now
established — §3–§5/§8 mechanistically explain the high-recall↔low-FA movement via score+guard+epoch
selection, and §7/§13 quantify that the recall numbers are few-window and PGD-fragile; (ii) minimum new
experiments — one seed; (iii) avoids overfitting seeds 42/43 — the guard was tuned on them, so seed 44 is
the *only* honest generalization test, and pre-registration prevents post-hoc spin; (iv) uncertainty is
quantified and success/failure are fixed in advance. **Defer the margin-based loss (Option C)** behind
seed-44: it is the right eventual fix for the residual high-confidence false alarms, but it should be
evaluated against a *confirmed, frozen* selection baseline, and only if seed-44 shows recall at the floor
with persistent high-confidence residual false alarms. Do **not** adjust the guard before seed 44 (B —
would re-overfit 42/43), and do **not** stop (D) — the trade-off result is publishable but seed 44 makes
it defensible.

## 20. Exact next prompt

```
Run independent validation of the FROZEN Variant E selection-v2 rule on seed 44 only, against the
pre-registered criteria in
results/safety_guided_defense/variantE_motion_hard_negative/selection_v2/diagnostic_audit/seed44_preregistration.md.

Constraints:
- Seed 44 ONLY. Do NOT run seeds 45-46. lambda_motion = 1.0 only. No lambda tuning, no loss change,
  no selection-v2 guard change. Use scripts/train_variantE_selection_v2.py unchanged.
- LeNet only, same UT-HAR/SenseFi split. New namespace
  variantE_motion_hard_negative/selection_v2/seed44 (results + checkpoints). Do NOT modify any
  Variant D / prior Variant E / selection-v2 seed42-43 artifacts. Do NOT edit thesis .tex.
- Evaluate v2safety and v2lowFA on test: clean, FGSM@0.030, PGD@0.030, 18-eps FGSM/PGD sweeps,
  per-class probability/logit export, AND a PGD-20 fixed-start robustness check at eps=0.030.
- Also evaluate FGSM_defense_seed44 and Variant-D-safety_seed44 as the per-seed reference baselines
  (train Variant D seed44 only if its checkpoint does not already exist; if it must be trained, that
  is the one allowed training and it uses the existing frozen Variant D recipe).
- Score the result against EACH pre-registered success/failure criterion (clean guard out-of-sample,
  clean fall recall >=0.90, PGD recall vs FGSM-defense floor with 95% Wilson lower bound > 0,
  <=0.70x Variant D total and walk/run false alarms, collapse epsilon, PGD-20 non-collapse). State
  explicitly: does seed 44 SUPPORT selection-v2, REJECT it, or indicate the margin-loss redesign is
  needed. Quantify uncertainty (Wilson intervals; n_fall=45). Honest trade-off framing; no
  solved/certified/clinical/over-the-air claims. Do not commit until I review.
```

---

## Additional mathematical and diagnostic parameters

This section summarizes how the audit addressed each required analysis, with explicit notes where an
item was not feasible and what would be needed.

- **Loss-scale & gradient diagnostics (§3):** Addressed via logged loss-term scales and trajectories
  (`loss_scale_diagnostics.csv`, `fig_loss_scale_vs_epoch.png`). **Gradient norms NOT computed** —
  would require adding backward-pass norm instrumentation to the training loop (a code change to a
  training script), out of scope for analysis-only; proxies (loss scale, probability/logit geometry,
  epoch-level movement) were used instead.
- **Exact selection-score math (§2.3):** Provided in full (SafetyScore weights, NFAB normalization,
  guard thresholds, four candidate definitions, tie-breaks) and matched to the implemented script.
- **Statistical uncertainty (§7):** 95% Wilson intervals for recall and specificity, true-positive
  counts, and McNemar paired discordance over fall windows (`uncertainty_intervals.csv`,
  `paired_comparisons.csv`). Full paired bootstrap CIs were not added because the Wilson intervals
  already establish non-significance at n_fall=45; a window-resampling bootstrap could be added from the
  aligned prediction CSVs if tighter joint CIs are wanted.
- **Decision-cost curves (§6):** FN:FP ∈ {1,2,5,10,20,50}:1 (`cost_curve_preference.csv`,
  `fig_cost_preference_by_ratio.png`); experimental sensitivity only.
- **Pareto dominance (§5):** Formal dominance among guard-passing points with per-point classification
  (`pareto_points.csv`, `fig_pareto_seed{42,43}.png`).
- **Validation-to-test reliability (§8):** `val_test_reliability.csv` + figures; per-epoch bootstrap
  selection-stability NOT feasible (per-epoch validation window predictions / all-epoch checkpoints were
  not saved) — would need re-running validation inference per epoch, which selection-v2's multi-candidate
  saving now partially mitigates.
- **Class-normalized false alarms (§9):** Raw and per-class-window-normalized rates
  (`class_counts.csv`, `class_normalized_false_alarms.csv`).
- **Stronger-attack sanity check (§13):** Evaluation-only PGD-10/20/40 + PGD-20 random-start
  (`stronger_pgd_sanity_check.csv`); no gradient masking; seed-43 v2safety recall collapses under PGD-20.
- **Representation geometry (§14):** NOT performed (forward-hook embedding extraction + PCA beyond the
  no-refactor scope); output-layer geometry (§10) already supports the conclusion; concrete future
  approach proposed.
- **Calibration metrics (§15):** ECE, Brier, NLL, and per-error-type confidences (`calibration_metrics.csv`).
- **Seed-44 pre-registration (§17):** `seed44_preregistration.md` with fixed success/failure criteria.
