# Variant H — H1 seed-42 pilot report

> **Single-seed pilot — NOT validated.** H1 only, seed 42 only, LeNet only. No H2/H3, no seed 44/45/46, no
> architecture change, no automatic follow-up. Window-level, digital-domain, white-box; test n=500 (45 fall
> / 455 non-fall windows), ε=0.030. **No deployment / clinical / product / certified / over-the-air claim.**
> All metrics from per-window probability/logit exports (same method as prior committed diagnostics).

## Final category: **REJECT**

Variant H H1 **does not improve** the Variant G G1 seed-42 trade-off. On the held-out test set the clean
guard **fails** (acc 0.662 < 0.70, macro-F1 0.591 < 0.65 — a val→test gap; selection was valid on
validation), PGD fall recall **drops** to 0.489 (< 0.60; G1 0.689), and the small false-alarm reduction
(FP 94 vs 104) comes **only at the cost of recall**. The two code-review MEDIUM risks materialised: the
nonfall-budget term suppressed fall recall, and the (k≈1) fall-rescue term was too weak to compensate.

## 1. Exact command(s) run

- Pilot: `python scripts/train_variantH_dual_tail_budget.py --setting H1 --seed 42 --pilot`
- Eval (v2safety): `export_probability_predictions.py … --split test --pgd-steps 10`;
  `… --run-name H_H1_v2safety_pgd20 --pgd-steps 20`; `run_converged_attacks.py … --epsilon-sweep --attacks both`

## 2. Git commit at run time

`44e2870de61c0d6480710312e047604032a8fc70` (the `--pilot` gate modification was applied locally and is
**uncommitted** at run time, per instruction — to be committed with this report only after review).

## 3–4. Scope confirmation

- ✅ **H1 only** (balanced dual-tail). ✅ **seed 42 only.** ✅ **LeNet only.**
- ✅ **No H2/H3 ran** (pilot gate restricts to H1). ✅ **No seed 44/45/46 ran** (seed gate). ✅ No
  architecture change. ✅ No automatic follow-up.

## 5. Training summary

- 70 epochs (no early stop), 8586 s. Objective: Variant G G1 base (λ_s=λ_f=λ_t=1.0, w_wr=2.0, γ=0.5, fall
  weight 3) + **λ_b=0.5 nonfall-budget + λ_r=0.5 fall-rescue** (k_frac=0.25, γ_b=γ_r=0.5).
- Cold-start recovery confirmed (guard-eligible from epoch 57; v2safety selected **epoch 61**). All loss
  components finite throughout; nonfall_budget and fall_rescue nonzero every epoch (TopK selected ≈ 8 / 1).
- Selected v2safety (validation): acc 0.708, macro-F1 0.680, PGD recall 0.523, PGD FP 87.

## 6. Clean test metrics (v2safety)

| acc | macro-F1 | fall recall | fall precision | fall F1 | clean FP | walk/run→fall | specificity |
|---|---|---|---|---|---|---|---|
| **0.662** | **0.591** | 0.911 | 0.651 | 0.759 | 22 | 3 | 0.952 |

Fall confusion (clean): **TP 41 / FN 4 / FP 22 / TN 433**. Clean fall recall 0.911 ≥ 0.90 holds, but
**acc 0.662 and macro-F1 0.591 fail the 0.70/0.65 clean guard on test** (G1: 0.716 / 0.670).

## 7. FGSM@0.030 metrics (secondary)

| acc | macro-F1 | fall recall | FP | FA rate | walk/run→fall | TP/FN/FP/TN |
|---|---|---|---|---|---|---|
| 0.370 | 0.304 | 0.622 | 69 | 15.2 % | 44 | 28/17/69/386 |

## 8. PGD@0.030 metrics (primary)

| acc | macro-F1 | fall recall [95% Wilson] | precision | F1 | FP | FA rate | walk/run→fall | TP/FN/FP/TN |
|---|---|---|---|---|---|---|---|---|
| 0.292 | 0.244 | **0.489 [0.350, 0.630]** | 0.190 | 0.273 | **94** | **20.7 %** | 67 | **22/23/94/361** |

## 9. PGD-20 durability

| PGD-10 recall | PGD-20 recall | ratio | PGD-20 FP | PGD-20 FA rate |
|---|---|---|---|---|
| 0.489 | 0.467 | 0.95 | 103 | 22.6 % |

Recall is durable in *ratio* (95 % of PGD-10, no masking) but **low in absolute terms**.

## 10. Epsilon-sweep collapse thresholds

| sweep | clean(ε=0) recall | recall drop ≥0.10 at ε | recall < 0.50 at ε | recall = 0 at ε |
|---|---|---|---|---|
| PGD | 0.911 | 0.0175 | 0.030 | none (within grid ≤0.075) |
| FGSM | 0.911 | 0.020 | 0.040 | none |

PGD fall recall crosses below 0.50 exactly at the headline ε=0.030.

## 11. False-alarm source anatomy (PGD@0.030, 94 FAs)

| run | walk | stand up | lie down | pickup | sit down | walk+run |
|---|---|---|---|---|---|---|
| 37 | 30 | 9 | 8 | 8 | 2 | **67 (71.3 %)** |

Still motion-dominated (run-largest), as for G1 — the budget term did not eliminate the upper-tail motion
false alarms.

## 12. Missed-fall anatomy (PGD@0.030)

23 missed falls (FN) vs 22 detected (G1 had 18 missed / 27 detected). The fall-rescue term did **not**
reduce missed falls — it increased them (more falls pushed below the boundary), consistent with the clean
fall recall and PGD recall both dropping.

## 13. Confidence-inversion diagnostics (PGD@0.030)

| model | detected-fall median P(fall) | false-alarm median P(fall) | gap (B−A) |
|---|---|---|---|
| Variant F seed42 | 0.415 | 0.518 | +0.103 |
| **Variant G G1 seed42** | 0.301 | 0.313 | **+0.012** |
| **Variant H H1 seed42** | 0.282 | 0.343 | **+0.061** |

H1's inversion gap (+0.061) is **worse than G1's (+0.012)** (though still below Variant F's +0.103) — the
dual-tail budget did **not** further flatten the inversion; it regressed relative to G1.

## 14. Upper-/lower-tail diagnostics

- Lower tail (falls): clean fall recall fell 0.978→0.911 and PGD recall 0.689→0.489 — the **fall-rescue
  term (k≈1 per batch) was under-powered** and the lower tail worsened.
- Upper tail (non-fall): PGD FP fell only 104→94 while recall dropped 0.20 — the nonfall-budget term moved
  FP marginally but at a disproportionate recall cost.

## 15. Comparison to Variant G G1 seed-42

| metric | Variant G G1 seed42 | **Variant H H1 seed42** | direction |
|---|---|---|---|
| clean acc | 0.716 | 0.662 | ↓ (guard fails) |
| clean macro-F1 | 0.670 | 0.591 | ↓ (guard fails) |
| clean fall recall | 0.978 | 0.911 | ↓ (≥0.90 holds) |
| PGD recall [Wilson] | 0.689 | 0.489 [0.350, 0.630] | ↓ −0.20 |
| PGD FP (rate) | 104 (22.9 %) | 94 (20.7 %) | ↓ small |
| walk/run→fall | 74 | 67 | ↓ small |
| PGD-20 recall | 0.622 | 0.467 | ↓ |
| inversion gap | +0.012 | +0.061 | ↑ worse |

H1 is **dominated by G1**: lower recall, lower clean acc/macro-F1, worse inversion, only a marginal FP
reduction bought by recall loss. (Aspirational target recall > 0.80 / FP ≤ 45: **not approached** — recall
0.489, FP 94.)

## 16. Success-category decision: **REJECT**

Triggered REJECT conditions: clean guard fails (acc 0.662 < 0.70 **and** macro-F1 0.591 < 0.65); PGD recall
0.489 < 0.60; FP reduction occurs **only by recall loss**; confidence inversion **worsens** vs G1; and H1
does **not** improve the G1 recall/FP trade-off.

## 17. Honest interpretation

At the balanced setting (λ_b=λ_r=0.5, k_frac=0.25), the dual-tail budget objective **over-suppressed the
fall class**: the source-weighted nonfall-budget term (k≈8/batch) added strong downward pressure on the
fall logit for motion windows, while the fall-rescue term (k≈1/batch) was **too weak** to protect the
hardest falls — net effect: clean accuracy fell below guard, attacked recall dropped 0.20, and the small FP
gain came at the cost of recall. The two MEDIUM risks flagged in the committed code review (budget
suppresses recall; per-batch fall-rescue under-power at k≈1) **both materialised**. This is an honest
negative result for H1 as configured; it does not invalidate the Variant H *design*, but the *balanced*
weights/k_frac are not the operating point that achieves the high-recall/low-FP target.

## 18. Validation status

**This is a seed-42 pilot only — NOT validated.** No seed-44 validation was run (and none is warranted: H1
did not reach pilot-success on seed 42). Single-seed, n_f = 45 (wide Wilson interval [0.350, 0.630]).

## 19. Scope boundary

Window-level, processed CSI tensor, digital-domain, white-box. **No deployment, clinical, product,
certified, or over-the-air claim.** Variant F (higher recall) and Variant G G1 (lower false alarms) remain
the two validated operating points; **H1 does not displace either.**

## 20. Recommendation (no automatic run)

- **STOP after this report and review.** Do **not** auto-run H2/H3, seed 44/45/46, or any follow-up.
- **Keep Variant F / Variant G G1 as the validated defenses;** H1 (REJECT) is a committed negative result.
- **If Variant H is pursued further** (a *future, separately reviewed* step — not now): the diagnosis points
  to (a) a `k_abs` floor for the **fall-rescue** term so it is not k≈1 per batch, and (b) a **lower λ_b**
  and/or **higher λ_r** to rebalance toward recall, with the clean guard re-checked on test. This would
  require a new pre-registration; **H2/H3 as currently defined (both keep λ_r=0.5) are unlikely to fix the
  recall collapse** and should not be run on the strength of this result.
- **No seed-44 pre-registration** is warranted for H1 (it failed the seed-42 pilot).

### Scope reminder
Seed-42 pilot only; H1 only; not validated. Window-level, digital-domain, white-box; not
solved/certified/clinical/over-the-air.
