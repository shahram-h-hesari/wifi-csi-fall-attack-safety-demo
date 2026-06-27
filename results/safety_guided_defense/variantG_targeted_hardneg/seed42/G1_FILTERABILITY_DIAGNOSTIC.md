# Variant G G1 — filterability & operating-point diagnostic

> **Analysis-only.** No training, no attacks, no seed44/45/46, no script change, no `.tex` edit, no artifact overwrite. Built from committed per-window probability/logit CSVs for **G1 v2safety** and **Variant F seed42 v2safety** (test, ε=0.030, n=500, 45 fall windows). Post-hoc decision rules below are a **test-output filterability probe, NOT a deployable threshold** (see §4). Window-level, digital-domain, white-box; no solved/certified/clinical/over-the-air claim.

## Decision: **A — Filterable enough to justify seed44**

## 1. Confidence-inversion comparison (PGD@0.030)

Medians over **A** = detected true falls, **B** = false alarms. Inversion present when B P(fall) > A.

| Model | group | n | median P(fall) | fall-vs-rest margin | entropy | conf margin |
|---|---|---|---|---|---|---|
| Variant F v2safety | A true-fall | 30 | 0.415 | 0.456 | 1.414 | 0.141 |
| Variant F v2safety | B false-alarm | 115 | 0.518 | 0.881 | 1.296 | 0.306 |
| Variant G G1 v2safety | A true-fall | 31 | 0.301 | 0.371 | 1.771 | 0.085 |
| Variant G G1 v2safety | B false-alarm | 104 | 0.313 | 0.421 | 1.694 | 0.106 |

- **Inversion gap (B−A median P(fall)):** Variant F **+0.103** → G1 **+0.012** (~89% smaller).
- **Does G1 reduce inversion enough to make filtering plausible?** **Geometrically yes** — the confidence ordering is nearly flat (FAs barely more fall-confident than true falls), so a gate no longer removes true falls *first* as severely as in Variant F. But 'plausible geometry' is necessary, not sufficient — the operating-point sweep (§2–§3) decides whether it converts into a usable FP cut.

## 2. Operating-point sweep on G1 v2safety (post-hoc, test)

Rules: **A** P(fall)≥τ · **B** fall-vs-rest margin≥τ · **C** entropy≤τ · **D** P(fall)≥τ_p ∧ entropy≤τ_h · **E** margin≥τ_m ∧ entropy≤τ_h. The gate only *removes* alerts on top of argmax=fall, so recall and FP fall together. Raw reference points (no gate):

| Point | PGD recall | FP | walk/run→fall |
|---|---|---|---|
| raw Variant F v2safety | 0.667 | 115 | 80 |
| raw Variant G G1 v2safety | 0.689 | 104 | 74 |

Best each rule achieves at **recall ≥ 0.50** (lowest FP); full sweep in `analysis/filterability/operating_point_sweep_G1.csv`:

| Rule | min-FP @ recall≥0.50 | recall | walk/run→fall | clean fall recall | clean FP | PGD-20 recall |
|---|---|---|---|---|---|---|
| A_pfall | FP 86 (τ=0.26) | 0.511 | 62 | 0.978 | 19 | 0.489 |
| B_margin | FP 104 (τ=-1.0) | 0.689 | 74 | 0.978 | 24 | 0.622 |
| C_entropy | FP 89 (τ=1.85) | 0.533 | 65 | 0.978 | 18 | 0.444 |
| D_pfall+entropy | FP 93 (τ=0.24,1.9) | 0.622 | 65 | 0.978 | 20 | 0.578 |
| E_margin+entropy | FP 102 (τ=-1.0,1.9) | 0.644 | 73 | 0.978 | 22 | 0.600 |

## 3. Target operating points

| Target | achieved | best rule | τ | recall | FP | walk/run→fall | clean fall recall | clean FP | PGD-20 |
|---|---|---|---|---|---|---|---|---|---|
| recall>=0.5 & FP<=100 | **YES** | A_pfall | 0.22 | 0.644 | 97 | 69 | 0.978 | 21 | 0.600 |
| recall>=0.5 & FP<=90 | **YES** | C_entropy | 1.85 | 0.533 | 89 | 65 | 0.978 | 18 | 0.444 |
| recall>=0.5 & FP<=80 | NO | — | — | — | — | — | — | — | — |
| recall>=0.4 & FP<=80 | **YES** | A_pfall | 0.28 | 0.467 | 74 | 54 | 0.978 | 15 | 0.378 |
| recall>=0.3 & FP<=60 | NO | — | — | — | — | — | — | — | — |

## 4. Validation-safe warning

These thresholds are tuned **on seed-42 test outputs** and therefore **cannot** be used as a final, selected deployment threshold:

- This is **diagnostic only** — it measures whether a filterable gap *exists*, not what threshold to ship.
- Any threshold chosen on the test set is **optimistically biased** (selection-on-test leakage).
- If a useful rule appears, it must be **re-defined on validation data** and then **independently tested on seed 44** before any claim — exactly the val→test discipline that selection-v2 enforces.

## 5. Diagnosis

**A — Filterable enough to justify seed44.**

A post-hoc rule on G1 plausibly reaches recall ≥ 0.50 at FP ≤ 90 without destroying clean performance — the reduced inversion converted into a usable false-alarm cut. This warrants a **validation-defined** rule and a seed-44 test.

## 6. Recommendation

- **Run a seed-44 validation of frozen G1** *and* a validation-defined gate — the post-hoc gap looks real enough to test honestly.
- Keep Variant F as the labelled final defense until seed-44 confirms.
- Write the thesis with Variant G as a **mechanistic positive with a candidate operating rule under validation**.

## Artifacts
- `analysis/filterability/inversion_comparison.csv`, `analysis/filterability/operating_point_sweep_G1.csv`, `analysis/filterability/target_satisfaction_G1.csv`
- `figures/filterability/fig_G1_fallprob_hist.png`, `figures/filterability/fig_G1_separability.png`
