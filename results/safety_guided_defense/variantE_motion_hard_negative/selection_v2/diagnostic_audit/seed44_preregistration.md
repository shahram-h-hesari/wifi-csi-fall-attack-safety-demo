# Seed-44 pre-registration (Variant E selection-v2)

> **Experimental criteria, not clinical thresholds.** Window-level, digital-domain, white-box
> evaluation on processed CSI tensors. Fixed before running seed 44 to avoid post-hoc rationalization.

## Frozen protocol (no changes permitted for seed 44)
- **Recipe:** Variant E, `λ_motion = 1.0`, fall-weighted CE + motion hard-negative penalty. **No λ tuning, no loss change.**
- **Selection rule (frozen selection-v2):** safety-score selection restricted to checkpoints with
  `val clean accuracy ≥ 0.70` AND `val clean macro-F1 ≥ 0.65`; save candidates v2safety, v2maxrec,
  v2lowFA, v2macroF1. **No guard change.**
- **Model:** LeNet only. **Split:** same UT-HAR/SenseFi split. **Eval:** PGD steps=10, α=ε/6, ε=0.030
  headline + 18-ε sweep; report a PGD-20 robustness check.
- Save multiple candidate checkpoints; export per-class probabilities/logits.

## Reference baselines for seed 44 (from this seed's own runs)
- `FGSM_defense_s44` PGD@0.030 fall recall = the recall floor (seeds 42/43 were 0.089 / 0.022).
- `D_safety_s44` PGD@0.030 fall recall and false alarms = the high-recall/high-FA reference.

## Success criteria (selection-v2 v2safety on seed 44 — ALL must hold)
1. **No clean collapse:** test clean accuracy ≥ 0.70 AND clean macro-F1 ≥ 0.65 (guard holds out-of-sample).
2. **Clean fall recall:** ≥ 0.90.
3. **PGD recall floor:** test PGD@0.030 fall recall **strictly above** `FGSM_defense_s44` recall
   (point estimate), AND its 95% Wilson interval lower bound > 0 (i.e. not a single-window artifact).
4. **False-alarm reduction vs Variant D:** total PGD false alarms ≤ 0.70 × `D_safety_s44` false alarms.
5. **Walk/run false-alarm reduction vs Variant D:** walk+run→fall count ≤ 0.70 × `D_safety_s44` walk+run.
6. **Collapse ε reported** (first ε with fall recall < 0.50) and ≥ `FGSM_defense_s44` collapse ε.

## Failure criteria (any ONE rejects selection-v2 as a stable recipe)
- Clean accuracy < 0.70 or macro-F1 < 0.65 on test (guard fails out-of-sample).
- PGD@0.030 fall recall ≤ `FGSM_defense_s44` recall, OR recall collapses to 0.000 under the PGD-20 check.
- No false-alarm reduction vs Variant D (criterion 4 fails).

## Decision rules after seed 44
- **Supports selection-v2** (all success criteria across seeds 42–44, or ≥2/3 with the third not failing):
  proceed to seeds 45–46 with the frozen rule; report as a multi-seed trade-off result.
- **Rejects selection-v2** (any failure criterion on seed 44): do not add more seeds; the clean/false-alarm
  gains do not generalize.
- **Suggests margin-based loss is needed** (independent of the above): residual walk/run false alarms remain
  high-confidence (median fall-prob > true-fall fall-prob) AND PGD recall sits at/near the FGSM-defense floor.
  In that case the next experiment is a margin-based motion penalty (seed-42 pilot first), not more seeds.

## Cost-ratio preference rule (sensitivity, experimental only — NOT clinical)
Report `Cost = λ_FN·missed_falls + λ_FP·false_alarms` for FN:FP ∈ {1,2,5,10,20,50}:1 and state, per seed,
which checkpoint (Variant D / prior E / selection-v2 / FGSM defense) is cost-preferred. A defensible
"safety-leaning" deployment is expected to need a high FN:FP ratio for any Variant-E point to be preferred;
this is a sensitivity analysis, not a recommended operating point.
