# Variant F — seed-44 pre-registration and validation protocol

> **Pre-registration only.** Written **before** running seed 44, to fix the criteria and prevent
> post-hoc rationalization. No experiment was run, no model trained, no λ/margin/guard/loss changed,
> no thesis `.tex` edited, no existing artifact modified to produce this document. Seed 44 is
> **independent validation** of the frozen Variant F candidate, **not** tuning. All criteria are
> **experimental, not clinical**. Evaluation is window-level, digital-domain, white-box on processed
> CSI tensors; test n=500 (45 fall windows), ε=0.030 unless noted.

Frozen candidate under test: **Variant F, λ_m = 1.0, λ_f = 1.0, γ_m = γ_f = 0.5** — the seed-42 pilot
winner (test PGD recall 0.667, FP 115, clean acc 0.734, walk/run logit-margin 0.986, PGD-20 0.644).

## 1. Frozen method (nothing below may change for seed 44)

- **Seed 44 only.** Do not run seeds 43, 45, 46.
- **λ_m = 1.0, λ_f = 1.0** (no λ tuning). **γ_m = γ_f = 0.5** (no margin tuning).
- **Objective (unchanged):**
  `L_F = L_FWCE + λ_m·mean_{adv walk/run} max(0, γ_m + z_fall − z_true) + λ_f·mean_{adv fall} max(0, γ_f + max_{c≠fall} z_c − z_fall)`.
- **Training recipe (unchanged):** LeNet; same UT-HAR/SenseFi split logic (train 3977 / val 496 /
  test 500); batch-split mixture 50% clean / 25% FGSM / 25% PGD; multi-ε {0.005,0.015,0.030}; fall
  weight 3; train PGD 7 steps (α=ε/4); Adam lr 1e-3; batch 64; epochs 70 / patience 15 / min-epochs 35.
- **Selection guard (frozen selection-v2):** safety-score eligibility requires `val clean acc ≥ 0.70`
  AND `val clean macro-F1 ≥ 0.65`. **No guard change.** Save candidates `v2safety / v2maxrec / v2lowFA /
  v2macroF1`; the **primary candidate is v2safety**.
- **Evaluation protocol (unchanged):** PGD steps=10, α=ε/6; headline ε=0.030 + 18-ε FGSM/PGD sweeps;
  per-class probability/logit export; a PGD-20 fixed-start robustness check at ε=0.030.
- **One allowed implementation change:** the committed `scripts/train_variantF_motion_margin.py`
  currently hard-codes a seed-42-only guard (a pilot safety rail). For the seed-44 validation run, relax
  **only** the seed-eligibility check to permit seed 44 (or add a thin sibling script). This is an
  eligibility/plumbing change, **not** a method change — the loss, λ, margins, guard, and recipe are
  untouched. The (1.0,1.0) setting is already on the script's λ allow-list.

## 2. Reference baselines (what exists vs. what is missing)

Checked in the repo at pre-registration time:

| Baseline (seed 44) | Status | Value (if present) | Role |
|---|---|---|---|
| Clean LeNet baseline (`converged_seed44`) | **EXISTS** | — | context |
| **FGSM defense (`defended_fgsm_at_seed44`)** | **EXISTS (evaluated)** | PGD@0.030 recall **0.044**, FP 42, clean acc 0.928 | **recall floor** (criterion 4) |
| Variant D safety seed 44 | **MISSING** (Variant D ran only seeds 42, 43) | — | needed as same-seed false-alarm reference (criteria 6, 7) |
| prior Variant E safety seed 44 | **MISSING** | — | optional |
| selection-v2 seed 44 | **MISSING** | — | optional |

**Decisions:**
- The **FGSM-defense floor (0.044)** is the same-seed recall floor for criterion 4 — available now, no
  training needed.
- **Variant D seed 44 is required** as the same-seed false-alarm reference for criteria 6–7. It must be
  produced by training **once** with the **frozen Variant D recipe** (this is a baseline, not tuning; it
  is the *only* additional model trained during the seed-44 run). If, for time reasons, it is not
  trained, criteria 6–7 fall back to the **seed-42 Variant D reference (FP 157, walk/run 120)** and must
  be reported explicitly as a **cross-seed** comparison (weaker evidence).
- prior Variant E / selection-v2 seed 44 are **optional**; for the geometry criterion (8) and the Pareto
  context, the **seed-42 references** (prior-E walk/run logit-margin 2.716; selection-v2 v2safety recall
  0.356 / FP 117) are cited as cross-seed references — **do not** train E/selection-v2 on seed 44.
- **Do not train any other baselines.**

## 3. Success criteria (fixed before running)

For **Variant F (1.0,1.0) v2safety on seed 44, test, ε=0.030.** ALL must hold.

1. Clean accuracy ≥ 0.70.
2. Clean macro-F1 ≥ 0.65.
3. Clean fall recall ≥ 0.90.
4. **PGD@0.030 fall recall floor (tiered).**
   - *Minimal technical pass:* strictly above the same-seed FGSM-defense floor (> 0.044).
   - *SUPPORT:* PGD@0.030 fall recall ≥ **0.20**.
   - *STRONG SUPPORT:* PGD@0.030 fall recall ≥ **0.30**.
   *Why tiered:* with only 45 fall windows, "> 0.044" can mean as few as ~3 recovered windows — within
   few-window noise — so it must **not** by itself count as strong validation; the 0.20 / 0.30
   thresholds require a substantively recovered recall.
5. PGD@0.030 fall recall **95% Wilson lower bound > 0** (not a single-window artifact; n_f = 45).
6. PGD total false alarms **below or comparable to** the same-seed Variant D baseline (≤ Variant D
   seed-44 FP; "comparable" = within +10%). If Variant D seed 44 is unavailable, use the seed-42
   reference FP 157 and label cross-seed.
7. walk/run → fall false alarms **below or comparable to** the same-seed Variant D baseline (≤ its
   walk/run count, or within +10%). Same cross-seed fallback as criterion 6.
8. Residual walk/run `logit_fall − logit_true` median **lower than** the prior Variant E / selection-v2
   reference (seed-44 if produced, else the seed-42 reference 2.716) — i.e. the margin geometry is at
   least as improved as in the pilot.
9. **PGD-20 durability (tiered).**
   - *Failure check (must hold):* PGD-20 fixed-start fall recall **does not collapse to 0**.
   - *SUPPORT:* PGD-20 recall **> the FGSM-defense floor (0.044)** AND **≥ 50% of the PGD-10 recall**.
   - *STRONG SUPPORT:* PGD-20 recall **≥ 75% of the PGD-10 recall**.
   *Why:* a nonzero PGD-20 recall can still sit at the few-window noise floor; the retention ratio
   ensures the recall is genuinely **durable** under the stronger attack, not merely technically nonzero.
10. **No evidence of gradient masking:** fall recall is **non-increasing** from PGD-10 → PGD-20 (a
    monotonic or flat decrease; a recall *increase* under stronger PGD would be a masking red flag).

## 4. Strong-success criteria (independent validation "confirmed")

- Variant F v2safety is **Pareto-efficient** against all available same-seed baselines (not dominated by
  FGSM defense or Variant D on the recall/false-alarm frontier under the clean guard).
- Variant F **improves PGD recall while not increasing false alarms** relative to the strongest available
  prior same-seed defense (Pareto win: recall ↑ AND FP ≤).
- Clean guard **holds out-of-sample** (criteria 1–2).
- Logit-margin geometry **improves or is preserved** (criterion 8 holds with margin clearly < the
  reference, as on seed 42: 0.986 ≪ 2.716).
- **PGD-20 durability holds** (recall ≈ PGD-10 recall, no collapse), as on seed 42 (0.644 vs 0.667).

## 5. Failure criteria (reject or weaken Variant F)

Any one of the following **rejects** the cross-seed claim:
- Clean guard fails out-of-sample (clean acc < 0.70 or macro-F1 < 0.65).
- Clean fall recall < 0.90.
- PGD@0.030 fall recall collapses to 0 (or ≤ FGSM-defense floor 0.044), or its Wilson lower bound = 0.
- **PGD-20 recall collapses to 0** (durability fails).
- PGD total false alarms **exceed the same-seed Variant D baseline** (> Variant D seed-44 FP).
- **Geometry does not improve** (residual walk/run margin ≥ the reference) — the mechanism did not transfer.
- The result **only improves recall by adding a large false-alarm burden** (recall up but FP materially
  above the Variant D baseline) — a different, worse trade-off point, not the pilot mechanism.
- Result appears **unstable / inconsistent with the seed-42 mechanism** (e.g. recall high on test but the
  margin geometry unchanged, or evidence of masking from criterion 10).

## 6. Decision categories

After the seed-44 run, Variant F is assigned **exactly one** category (most-favorable category whose
conditions ALL hold). Recall thresholds and PGD-20 retention follow the tiered criteria 4 and 9.

- **STRONG SUPPORT** — all of: clean guard holds (clean acc ≥ 0.70 ∧ macro-F1 ≥ 0.65); clean fall recall
  ≥ 0.90; PGD@0.030 recall ≥ **0.30**; PGD-20 recall ≥ **75%** of PGD-10 recall; total false alarms
  ≤ same-seed Variant D; walk/run → fall false alarms ≤ same-seed Variant D; residual walk/run logit
  margin improves (lower than the reference); no gradient-masking red flag (criterion 10 holds).

- **SUPPORT** — all of: clean guard holds; clean fall recall ≥ 0.90; PGD@0.030 recall ≥ **0.20** and
  > the FGSM-defense floor with Wilson lower bound > 0; PGD-20 recall ≥ **50%** of PGD-10 recall and
  > the FGSM-defense floor; total false alarms below or comparable (within +10%) to same-seed Variant D;
  geometry improves. (Does not meet all STRONG-SUPPORT bars.)

- **WEAK SUPPORT / TRADE-OFF** — clean guard holds **and** geometry improves, **but** at least one of:
  PGD@0.030 recall is between the FGSM floor and 0.20; PGD-20 durability is weak (between technical
  non-collapse and the 50%-retention SUPPORT bar); or false alarms increase materially vs Variant D.
  (A real but qualified result.)

- **REJECT / DOES NOT GENERALIZE** — any of: clean guard fails; clean fall recall < 0.90; PGD@0.030
  recall ≤ FGSM-defense floor; PGD-20 recall collapses to 0 or to the noise floor; total false alarms
  exceed same-seed Variant D substantially; residual walk/run logit margin does **not** improve; or
  stronger-PGD behavior suggests gradient masking / instability.

These categories supersede a binary pass/fail: only **STRONG SUPPORT** (and, more cautiously, **SUPPORT**)
license a cross-seed claim (§8). **WEAK SUPPORT / TRADE-OFF** is reported as a qualified trade-off point;
**REJECT** means Variant F remains a seed-42 design result that did not generalize.

## 7. Required outputs after the seed-44 run

Under `results/safety_guided_defense/variantF_motion_margin/seed44/` (new namespace):
- seed-44 training log + metadata (per selected candidate); `selection_candidates.csv`.
- Clean / FGSM@0.030 / PGD@0.030 fixed-ε safety metrics (v2safety, v2lowFA).
- 18-ε FGSM sweep; 18-ε PGD sweep (test + legacy).
- Per-class probability/logit export (clean / FGSM / PGD).
- PGD-20 fixed-start check at ε=0.030.
- `wilson_intervals.csv` (PGD recall CIs).
- Pareto comparison vs available seed-44 baselines (and seed-42 cross-seed references).
- FN:FP cost curve (1,2,5,10,20,50 : 1).
- Logit-margin geometry comparison (residual walk/run `logit_fall − logit_true` vs reference).
- `VARIANT_F_SEED44_VALIDATION_REPORT.md` scoring every criterion in §3–§5 and stating SUPPORTS / WEAKENS / REJECTS.
- (If trained) Variant D seed-44 baseline artifacts in its standard namespace.

## 8. Thesis-safe interpretation rules

- Seed 44 **validates or weakens** Variant F; it does **not** prove clinical safety, certified
  robustness, or over-the-air robustness, and makes **no fall-risk prediction** claim.
- All claims remain **window-level, digital-domain, white-box, processed-CSI-tensor** evaluation.
- **If seed 44 succeeds** (§3, ideally §4): the thesis may report **two-seed (42+44) evidence for a
  margin-aware defense that improves the attacked recall/false-alarm trade-off vs Variant D and
  selection-v2**, with the honest clean-accuracy cost and n_f = 45 uncertainty stated.
- **If seed 44 fails** (§5): report Variant F as a **promising seed-42 design result that did not
  generalize on independent validation**; do not claim a generalized defense. Either way, frame as a
  **safety-proxy trade-off study**, not a solved defense.

## 9. Exact next prompt (run only after I approve this pre-registration)

```
Run the seed-44 independent validation of the frozen Variant F candidate (lambda_m=1.0, lambda_f=1.0,
gamma_m=gamma_f=0.5), per
results/safety_guided_defense/variantF_motion_margin/seed44_preregistration/VARIANT_F_SEED44_PREREGISTRATION.md.

Constraints:
- Seed 44 ONLY. Do NOT run seeds 43, 45, 46. Do NOT tune lambda, do NOT change margins, the loss, or the
  selection-v2 guard. The ONLY code change permitted is relaxing the seed-42-only eligibility check in
  scripts/train_variantF_motion_margin.py to allow seed 44 (or add a thin sibling that imports it);
  everything else in that script is frozen. New namespace
  variantF_motion_margin/seed44 (results + checkpoints). Do NOT modify any frozen Variant D / Variant E /
  selection-v2 / seed-42 Variant F artifacts. Do NOT edit thesis .tex.
- Train Variant F (1.0,1.0) on seed 44; save the selection-v2 candidate checkpoints (primary v2safety).
- Same-seed baselines: FGSM defense seed44 already exists (PGD recall 0.044) -- reuse it. Variant D seed44
  is MISSING: train it ONCE with the frozen Variant D recipe (scripts/train_safety_guided_defense.py
  --variant D --seed 44) and evaluate it as the same-seed false-alarm reference. Do NOT train prior E or
  selection-v2 on seed 44; cite the seed-42 references cross-seed for geometry/Pareto context.
- Evaluate v2safety and v2lowFA on test: clean, FGSM@0.030, PGD@0.030, 18-eps FGSM/PGD sweeps, per-class
  probability/logit export, and a PGD-20 fixed-start check. Report Wilson CIs (n_f=45), the Pareto
  comparison, the FN:FP cost curve, and the residual walk/run logit-margin geometry vs the reference.
- Score EVERY criterion in sections 3-5 of the pre-registration using the TIERED recall (criterion 4:
  >floor / >=0.20 / >=0.30) and PGD-20 retention (criterion 9: non-collapse / >=50% / >=75% of PGD-10)
  thresholds, then assign EXACTLY ONE Decision category from section 6
  (STRONG SUPPORT / SUPPORT / WEAK SUPPORT-TRADE-OFF / REJECT), with the honest clean-accuracy cost and
  uncertainty (Wilson CIs, n_f=45). Honest trade-off framing; no solved/certified/clinical/over-the-air
  claims. Do not commit until I review.
```
