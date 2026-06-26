# Variant F / next-defense design memo

> **Design/planning only.** No model trained, no experiment run, seed 44 / seeds 45–46 not run, no
> λ tuned, no training script or thesis `.tex` modified, no experiment artifact overwritten. Reasoning
> uses only committed seed-42/seed-43 evidence and the diagnostic audit / thesis-math documentation.
> All numbers are **window-level, digital-domain, white-box** on processed CSI tensors, test n=500
> (45 fall windows), ε=0.030 unless noted. No clinical, certified-robustness, or over-the-air claim.

Evidence anchor (test PGD@0.030, fall recall / total FP / walk+run→fall / clean acc / clean macro-F1):

| Model | seed 42 | seed 43 |
|---|---|---|
| Variant D safety | 0.444 / 157 / 120 / 0.746 / 0.700 | 0.289 / 160 / 119 / 0.720 / 0.676 |
| prior Variant E safety | 0.356 / 117 / 80 / 0.806 / 0.790 | 0.378 / 151 / 108 / **0.630** / **0.600** |
| selection-v2 v2safety | 0.356 / 117 / 80 / 0.806 / 0.790 | **0.111** / **79** / **50** / 0.720 / 0.669 |
| FGSM defense (floor) | 0.089 / 54 / 39 / 0.834 / 0.814 | 0.022 / 35 / 26 / 0.902 / 0.901 |

Geometry (test PGD, v2safety): residual walk/run false-alarm median fall-prob ≈ 0.82–0.85 vs true-fall
≈ 0.14–0.26; median `logit_fall − logit_true` for walk/run FAs large and **positive**; calibration ECE
≈ 0.44–0.54; under PGD-20 seed-43 v2safety recall collapses 0.111 → 0.000.

---

## 1. Executive recommendation

**Primary: F — a combined *minimal* Variant F = fall-weighted CE + motion-margin hard-negative +
true-fall-margin preservation** (Candidate F3 below), **piloted on seed 42 only.** The diagnosed open
problem is *geometric* (residual walk/run false alarms are confidently on the fall side) and the
diagnosed risk is *recall fragility* (selection-v2 lost specific fall windows and collapses under
PGD-20). A margin objective is the principled fix for the geometry; a true-fall margin term is the
principled guard against further recall loss. The probability penalty (prior Variant E) cannot do this
— it reduced false-alarm *count* but not their confidence.

**Fallback: A — motion-margin-only loss (Candidate F1)**, a like-for-like replacement of Variant E's
probability penalty by a margin penalty (same number of knobs), if the two-term F3 proves hard to
attribute on a single design seed.

**Sequencing (important):** Variant F is a *new* defense piloted on the **design seed 42**. **Seed 44
remains untouched as an independent validation seed** — it must not be used during Variant F design or
tuning. **After** the seed-42 Variant F pilot, we will decide whether seed 44 should validate the *frozen
selection-v2* rule **or** the *frozen Variant F* design; seed 44 should validate whichever frozen candidate
is best, and must never be used for debugging or tuning. Designing Variant F now is justified because it
targets the actual remaining limitation that selection-v2 explicitly did **not** fix (the high-confidence
residual motion false alarms), not the selection artifact that selection-v2 already addressed.

Not recommended as the primary step: **G (no new defense)** — the geometry problem is well-diagnosed and
addressable; **C/F4 (class-normalized probability penalty)** — still a probability penalty, so it would
not fix the confidence geometry; **D/F5 and E/F6** — useful *companions* but not the core fix.

## 2. Mechanistic diagnosis from existing evidence

- **Variant D improves recall but creates high false alarms.** Fall-weighted CE + multi-ε FGSM/PGD
  training pushes the decision boundary toward fall (highest recall 0.444/0.289) but also maps adversarial
  non-fall — especially high-motion walk/run — to fall (FP 157/160; walk+run 120/119). It is the
  high-recall/high-false-alarm corner of the frontier.
- **Prior Variant E reduces motion false alarms but is checkpoint-sensitive.** The probability penalty
  `mean P_fall(x_adv)` over adversarial walk/run lowers motion FA count (walk+run 120→80 on seed 42), but
  the recall-heavy SafetyScore selects different epochs per seed: seed 42 → clean-strong epoch 56; seed 43
  → clean-weak early epoch 18 (clean acc 0.630, fails the later guard). Same loss, very different operating
  point ⇒ **checkpoint-selection sensitivity**, not loss instability.
- **Selection-v2 stabilizes clean/false alarms but loses recall.** The stronger clean guard (≥0.70/≥0.65)
  defers selection to a clean-stable epoch (seed 43 → epoch 24): clean acc recovers 0.630→0.720, total FP
  151→79 (−48%), walk/run 108→50 (−54%, 58 of 75 removed FAs are walk/run, only 3 introduced). But the
  clean-stable epoch detects fewer attacked falls: recall 0.378→0.111, losing **13 specific fall windows**
  that the earlier model caught. So the gain is bought with attacked recall.
- **Residual walk/run false alarms remain high-confidence.** Median fall-prob ≈ 0.82–0.85 and large
  positive `logit_fall − logit_true`. The probability penalty reduced their *number* but not their
  *placement*: the surviving ones are confidently on the fall side ⇒ a **geometry** problem.
- **seed-43 v2safety collapse under PGD-20 matters.** Recall 0.111 → 0.000 under a stronger attack ⇒ the
  seed-43 operating point's attacked recall is at the few-window noise floor (5/45, Wilson CI [0.05,0.24]).
  Any Variant F that only trims false alarms further (without protecting fall logits) risks pushing recall
  to zero.
- **Thresholding is not enough.** Because residual motion FAs have *higher* fall-probability than true
  falls (and missed falls are moderately confident, not low-confident), no single fall-probability
  threshold separates them; calibration is poor (ECE ≈ 0.5). The fix must change the **logit geometry**,
  not the read-out threshold.

## 3. Candidate Variant F objectives

Notation as in `thesis_math_snippets.tex`. `z_k(x)` = logit of class k; `c_f` = fall; `B^adv_motion` =
adversarial walk/run sub-batch; margins `γ_m, γ_f > 0`.

### Candidate F1 — motion-margin hard-negative loss
`L_motion_margin = mean_{i∈B^adv_motion} max(0, γ_m + z_fall(x_i^adv) − z_true(x_i^adv))`
Goal: push the *true* walk/run logit above the fall logit by margin γ_m for adversarial motion windows —
directly attacks the high-confidence FA geometry (replaces Variant E's saturating probability penalty,
which has weak gradient once P_fall is mid-range).

### Candidate F2 — true-fall margin preservation
`L_fall_margin = mean_{i: y_i=c_f} max(0, γ_f + max_{c≠c_f} z_c(x_i^adv) − z_fall(x_i^adv))`
Goal: keep the fall logit above all non-fall logits by margin γ_f on adversarial true-fall windows —
a guard against recall collapse (the §2 failure of selection-v2).

### Candidate F3 — combined motion-negative + fall-positive margin (PRIMARY)
`L_F = L_FWCE + λ_m · L_motion_margin + λ_f · L_fall_margin`
Goal: reduce confident walk/run false alarms *and* protect true-fall recall simultaneously — targets both
the diagnosed problem and the diagnosed risk.

### Candidate F4 — class-normalized motion probability penalty
`L_motion_norm = 0.5 · mean_{walk^adv} P_fall + 0.5 · mean_{run^adv} P_fall`
Goal: prevent the more populous motion class from dominating the penalty. Limitation: still a *probability*
penalty ⇒ does not fix the confidence geometry (the core §2 problem). Low priority as a primary.

### Candidate F5 — curriculum schedule
Phase 1: clean + fall-weighted CE. Phase 2: add FGSM/PGD adversarial training. Phase 3: add motion+fall
margins. Goal: avoid the early clean-immature high-recall/high-FA spike (seed-43 epoch 18) that drives
selection sensitivity. Orthogonal to F1–F3; a *stability* aid, not the geometry fix.

### Candidate F6 — hard-positive fall mining
Up-weight true-fall windows repeatedly missed under PGD (e.g., the 13 windows selection-v2 lost). Goal:
recover recall on the specific lost subset. Companion to F2/F3; risks raising false alarms if applied alone.

## 4. Compare candidates

| Candidate | FP effect | PGD recall effect | Clean acc effect | Impl. complexity | Overfit risk | Thesis value | Risk of hurting fall recall | Priority |
|---|---|---|---|---|---|---|---|---|
| F1 motion margin | ↓↓ (geometry) | ↓ (no protection) | ≈ | low (λ_m, γ_m) | medium | high | **high** | high (fallback primary) |
| F2 fall margin | ≈ (not targeted) | ↑ (protects) | ≈ | low (λ_f, γ_f) | low | medium | low | medium (companion) |
| **F3 combined** | ↓ | protected (≈/↑) | ≈ | medium (4 knobs) | medium-high | **high** | low-medium | **highest (primary)** |
| F4 class-norm prob | ↓ (slight) | ≈ | ≈ | low | low | low-medium | low | low |
| F5 curriculum | ≈ | ≈ (more stable selection) | ↑ stability | medium | low | medium | low | medium (stability add-on) |
| F6 hard-positive mining | ↑ (risk) | ↑ (targeted) | ≈/↓ | medium | medium | medium | n/a (raises recall) | medium (companion) |

## 5. Minimal next experiment

**Pilot F3 on seed 42 only**, as a small, attributable design:
- **Loss:** `L_F = L_FWCE + λ_m·L_motion_margin + λ_f·L_fall_margin`, on the existing Variant E batch-split
  mixture (50% clean / 25% FGSM / 25% PGD), multi-ε {0.005,0.015,0.030}, fall weight 3.
- **Fix the margins** at small documented values `γ_m = γ_f = 0.5` (do not tune margins on the design seed).
- **Tiny λ grid (3 runs):** `(λ_m, λ_f) ∈ {(1.0, 0.5), (1.0, 1.0), (0.5, 1.0)}` — bracket motion-leaning vs
  recall-leaning. This is a deliberately small grid to limit design-seed overfitting; if even this feels
  too large, run only `(1.0, 1.0)` first.
- **Selection:** reuse the **frozen selection-v2 guard** (clean acc ≥ 0.70 ∧ macro-F1 ≥ 0.65) and save the
  same candidate set (v2safety / v2lowFA / v2macroF1). No guard change.
- **Seed:** **seed 42 only** for the pilot. **Seed 44 remains untouched** as an independent validation
  seed — not used during Variant F design or tuning. Whether it later validates the frozen selection-v2 rule
  or the frozen Variant F design is decided only **after** reviewing this pilot, and it validates the single
  best frozen candidate. Seeds 43/45/46 are not used by the Variant F pilot.
- **Decisive metrics:** PGD@0.030 fall recall and its Wilson CI; total + walk/run false alarms; the
  **logit-margin geometry** (median `logit_fall − logit_true` for residual walk/run FAs — the direct test
  of whether the margin loss moved the geometry); clean acc / macro-F1; PGD-20 non-collapse.

Rationale for F3 over F1-only: §2 shows recall is already fragile; a motion-margin-only loss (F1) on a
single seed risks pushing recall to the floor with no protection. The fall-margin term is cheap insurance
and directly tests the recall-preservation hypothesis. If F3's two terms cannot be attributed, fall back
to F1-only as the cleaner ablation.

## 6. Success / failure criteria (pre-registered, before running anything)

Variant F seed-42 pilot, evaluated on test (n=500; n_f=45). **Experimental criteria, not clinical.**
Reference points: selection-v2 v2safety seed 42 (recall 0.356 / FP 117 / walk+run 80) and Variant D
seed 42 (0.444 / 157 / 120).

**Success (a useful Variant F point — ALL must hold):**
1. Clean guard holds on test: clean acc ≥ 0.70 **and** clean macro-F1 ≥ 0.65.
2. Clean fall recall ≥ 0.90.
3. PGD@0.030 fall recall ≥ 0.356 (≥ selection-v2 v2safety) with Wilson lower bound > 0 (not a single-window artifact).
4. Total PGD false alarms ≤ 117 (≤ selection-v2 v2safety) **and** ≤ 0.70 × Variant D (≤ 110).
5. walk+run → fall ≤ 80 (≤ selection-v2 v2safety).
6. **Geometry moved:** median `logit_fall − logit_true` for residual walk/run FAs strictly lower than prior
   Variant E (evidence the margin loss changed the geometry, not just the count).
7. PGD-20 fixed-start recall does not collapse to 0.

**Strong success (Pareto win):** a point that **dominates** selection-v2 v2safety — recall ≥ 0.356 AND
FP ≤ 117 with the clean guard — i.e. strictly better on the recall/false-alarm frontier.

**Failure (reject Variant F as designed — any one):**
- Clean guard fails on test, or clean fall recall < 0.90.
- PGD recall < 0.356 (no improvement over selection-v2) OR collapses to 0 under PGD-20.
- No false-alarm reduction vs selection-v2 (FP > 117) despite the margin penalty.
- Geometry unchanged (criterion 6 fails) — the margin loss did not do what it was designed to do.

**Trade-off judgment:** report Variant F against Variant D / prior E / selection-v2 on the
recall-vs-false-alarm Pareto frontier and the FN:FP cost curves (1–50:1); a "win" is a new
**Pareto-efficient or cost-preferred** point with the geometry actually improved, not merely a different
operating point. Report Wilson CIs throughout (n_f = 45).

## 7. Risks and overclaim controls

- **Seeds 42/43 are design seeds, not final validation.** Variant F is *designed and piloted* on seed 42;
  any apparent gain is design-stage evidence only.
- **Seed 44 remains untouched as an independent validation seed.** Do not pilot, design, or tune Variant F
  (or anything else) on seed 44. After the seed-42 Variant F pilot, decide whether seed 44 validates the
  frozen selection-v2 rule **or** the frozen Variant F design — it validates the single best frozen
  candidate, and is never used for debugging or tuning.
- **No clinical claim, no certified-robustness claim, no over-the-air claim.** Window-level, digital-domain,
  white-box only; margins are on processed-tensor logits.
- **No "solved" claim before validation.** Even a successful seed-42 pilot is a single design seed with
  n_f = 45 and wide recall CIs; describe as "a promising trade-off operating point," not a solved defense.
- **Overfitting control:** fixed margins, ≤ 3 λ settings, one design seed, pre-registered criteria, and the
  geometry check (criterion 6) to ensure the mechanism — not luck on 45 fall windows — explains any gain.

## 8. Exact next prompt

```
Implement and run a Variant F seed-42-only pilot: fall-weighted CE + motion-margin hard-negative +
true-fall-margin preservation (Candidate F3 in VARIANT_F_DESIGN_MEMO.md).

Constraints:
- Seed 42 ONLY. Do NOT run seeds 43-46. Keep seed 44 UNTOUCHED as an independent validation seed: do not
  use it for Variant F design, debugging, or tuning. The validation seed assignment -- and whether seed 44
  validates the frozen selection-v2 rule or the frozen Variant F design -- will be decided only AFTER
  reviewing this seed-42 pilot and freezing the single best candidate. LeNet only,
  same UT-HAR/SenseFi split. New variant in a NEW namespace
  (variantF_motion_margin/seed42 results + checkpoints). Do NOT modify the frozen Variant D / Variant E /
  selection-v2 training scripts or results; create a NEW training script that reuses the Variant E
  batch-split adversarial-training machinery and adds the two margin terms. Do NOT edit thesis .tex.
- Objective: L_F = L_FWCE + lambda_m * mean_{adv walk/run} max(0, gamma_m + z_fall - z_true)
                     + lambda_f * mean_{adv true-fall} max(0, gamma_f + max_{c!=fall} z_c - z_fall).
  Fix gamma_m = gamma_f = 0.5. Test (lambda_m, lambda_f) in {(1.0,0.5),(1.0,1.0),(0.5,1.0)} only (3 runs).
  Reuse the FROZEN selection-v2 guard (val clean acc >= 0.70 AND macro-F1 >= 0.65); save the same candidate
  checkpoints; export per-class probabilities/logits.
- Evaluate v2safety/v2lowFA candidates on test: clean, FGSM@0.030, PGD@0.030, 18-eps FGSM/PGD sweeps,
  per-class probability/logit export, AND a PGD-20 fixed-start robustness check.
- Score against the §6 pre-registered success/failure criteria, INCLUDING the geometry check
  (median logit_fall - logit_true for residual walk/run FAs vs prior Variant E). Compare on the
  recall/false-alarm Pareto frontier and FN:FP cost curves vs Variant D, prior E, and selection-v2.
  Report Wilson CIs (n_f=45). State explicitly whether Variant F SUCCEEDS, is a PARETO WIN, or FAILS.
  Honest trade-off framing; no solved/certified/clinical/over-the-air claims. Do not commit until I review.
```
