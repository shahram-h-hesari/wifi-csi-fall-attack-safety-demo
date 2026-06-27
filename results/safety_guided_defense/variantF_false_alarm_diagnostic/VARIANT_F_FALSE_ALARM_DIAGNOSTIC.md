# Variant F — residual false-alarm geometry & operating-point diagnostic

> **Diagnostic / reporting only.** No training, no seeds 45–46, no Variant G run, no loss change, no
> threshold change to any saved metric, no `.tex` edit, no existing artifact overwritten. Built entirely
> from committed Variant F **v2safety** probability/logit exports (seed 42 + seed 44; clean + PGD@0.030),
> the Variant D seed-44 baseline, and the defense-line synthesis memo. Window-level, digital-domain,
> white-box; test n=500 (45 fall windows), ε=0.030. **No solved / certified / clinical / over-the-air
> claim.** Post-hoc decision rules below are a *diagnostic probe of filterability*, **not** a deployed
> operating point.

## Headline diagnosis: **C — Not filterable (new training objective needed)**

The residual Variant F false alarms are **not near-boundary**. On every confidence axis (fall
probability, top-vs-second logit margin, entropy, confidence margin) the false alarms are **more
confident than the true attacked falls that Variant F barely detects**. This is a *confidence inversion*:
any post-hoc gate strict enough to remove false alarms removes the true falls first. No probability,
margin, or entropy rule yields a useful operating point on **both** seeds, and no single threshold is
cross-seed stable. The remaining errors are **high-confidence logit-geometry failures**, so reducing them
requires a **new training objective (Variant G)**, not post-hoc filtering.

---

## 1. Residual false-alarm anatomy

Per-window anatomy: `analysis/residual_fa_anatomy_seed{42,44}.csv`. By-source-class summary:
`analysis/source_class_summary.csv`.

**Source-class breakdown (PGD@0.030, Variant F v2safety):**

| Seed | Source | n FA | % of FA | median P(fall) | median (z_fall−z_true) | median entropy | median conf-margin |
|---|---|---|---|---|---|---|---|
| 42 | walk | 40 | 34.8 | 0.518 | 1.058 | 1.314 | 0.302 |
| 42 | run  | 40 | 34.8 | 0.511 | 0.881 | 1.285 | 0.283 |
| 42 | stand up | 15 | 13.0 | 0.516 | 2.818 | 1.327 | 0.309 |
| 42 | lie/pickup/sit | 20 | 17.3 | ~0.54 | 2.5–3.7 | ~1.3 | ~0.36 |
| 42 | **TOTAL** | **115** | 100 | **0.518** | **1.091** | **1.296** | **0.306** |
| 44 | run  | 41 | 36.6 | 0.523 | 0.901 | 1.271 | 0.311 |
| 44 | walk | 32 | 28.6 | 0.528 | 1.129 | 1.296 | 0.274 |
| 44 | stand up | 14 | 12.5 | 0.512 | 2.515 | 1.310 | 0.334 |
| 44 | lie/pickup/sit | 25 | 22.3 | ~0.49 | 1.7–3.1 | ~1.3 | ~0.30 |
| 44 | **TOTAL** | **112** | 100 | **0.513** | **1.129** | **1.298** | **0.304** |

**Explicit answers:**

- **Still dominated by walk/run?** **Yes.** walk+run = 80/115 (69.6%) on seed 42 and 73/112 (65.2%) on
  seed 44. Motion classes remain the dominant source of attacked false alarms.
- **walk/run false alarms lower than Variant D?** **Yes.** walk/run→fall = 80 (seed 42) / 73 (seed 44)
  vs Variant D seed-44's 116, and the residual walk/run logit margin median fell to **0.99 / 0.96** (from
  prior-E 2.716 and Variant D seed-44's 1.733). Variant F genuinely compressed the motion geometry —
  consistent with the validation report.
- **High-confidence or near-boundary?** **High-confidence relative to the decision the gate must make.**
  Median fall probability of the false alarms is ~0.51–0.52 in a 7-class problem (i.e. fall wins by a
  wide margin over each other class), with a residual fall-vs-true-class logit gap of ~1.0–1.1 and entropy
  *below* that of true detected falls. They are not sitting at the 1/7 argmax boundary.

---

## 2. False alarms vs true attacked falls — the inversion

Group stats: `analysis/group_distributions.csv`. Figures:
`figures/fig_hist_fallprob_margin_seed{42,44}.png`, `figures/fig_separability_seed{42,44}.png`.

**A = true falls detected under PGD · B = all false alarms · C = walk/run false alarms** (medians):

| Seed | Group | n | P(fall) | z_fall−z_maxnonfall | entropy | conf-margin |
|---|---|---|---|---|---|---|
| 42 | A true-fall | 30 | **0.415** | 0.456 | **1.414** | **0.141** |
| 42 | B false-alarm | 115 | **0.518** | 0.881 | **1.296** | **0.306** |
| 42 | C walk/run FA | 80 | 0.512 | 0.844 | 1.290 | 0.293 |
| 44 | A true-fall | 28 | **0.392** | 0.420 | **1.401** | **0.111** |
| 44 | B false-alarm | 112 | **0.513** | 0.901 | **1.298** | **0.304** |
| 44 | C walk/run FA | 73 | 0.524 | 0.889 | 1.286 | 0.297 |

*(For true-fall windows the true class **is** fall, so z_fall−z_true≡0 by construction; the meaningful
fall-vs-rest margin for group A is z_fall−z_maxnonfall, shown above.)*

**Explicit answers:**

- **Do true falls and false alarms overlap?** **Yes — and worse, the order is inverted.** False alarms
  have **higher** median fall probability (0.518 vs 0.415; 0.513 vs 0.392), **larger** fall-vs-rest logit
  margin (0.88 vs 0.46; 0.90 vs 0.42), **lower** entropy (1.30 vs 1.41 — more confident), and **larger**
  confidence margin (0.31 vs 0.14) than the true falls Variant F correctly detects.
- **Separability after Variant F?** **No — separability is reversed.** Every scalar that would gate false
  alarms out also gates the true falls out *first*. The scatter panels
  (`fig_separability_seed{42,44}.png`) show the true-fall cloud sitting at *lower* fall-prob / *higher*
  entropy than the false-alarm cloud, with heavy overlap.
- **Did Variant F make thresholding/margin gating more plausible than prior E?** **No.** Variant F
  improved the *training-time* motion geometry (z_fall−z_true 2.716 → ~0.96–0.99) and tightened the
  false-alarm count, but it did **not** create a post-hoc-gatable confidence gap. The probability
  inversion that defeated thresholding for prior E persists — thresholding remains implausible.

---

## 3. Post-hoc operating-point sweep (no retraining)

Full sweeps: `analysis/operating_point_sweep_seed{42,44}.csv`. Target search:
`analysis/target_satisfaction.csv`. Rules: **A** P(fall)≥τ · **B** (z_fall−z_second)≥τ · **C** entropy≤τ
· **D** P(fall)≥τ_p ∧ entropy≤τ_h · **E** (z_fall−z_second)≥τ_m ∧ entropy≤τ_h. The "alert" gate can only
*remove* alerts on top of argmax=fall, so it slides toward lower recall **and** lower FP together.

**Best each rule can do at recall ≥ 0.40 (lowest FP); and best F1 overall:**

| Seed | Rule | min-FP @ recall≥0.40 | best-F1 point |
|---|---|---|---|
| 42 | A P(fall) | rec 0.489, FP 95, wr 64 (τ=0.38) | F1 0.323 @ rec 0.667, FP 111 |
| 42 | B margin | rec 0.511, FP 102, wr 70 (τ=0.25) | F1 0.316 @ rec 0.667, FP 115 |
| 42 | C entropy | rec 0.444, FP 95, wr 67 (τ=1.45) | F1 0.323 @ rec 0.667, FP 111 |
| 42 | D P+H | rec 0.467, FP 93, wr 65 | F1 0.323 @ rec 0.667, FP 111 |
| 42 | E margin+H | rec 0.489, FP 96, wr 68 | F1 0.317 @ rec 0.667, FP 114 |
| 44 | A P(fall) | rec 0.422, FP 99, wr 65 (τ=0.36) | F1 0.303 @ rec 0.622, FP 112 |
| 44 | B margin | rec 0.422, FP 103, wr 70 | F1 0.303 @ rec 0.622, FP 112 |
| 44 | C entropy | rec 0.400, FP 95, wr 63 (τ=1.6) | F1 0.303 @ rec 0.622, FP 112 |
| 44 | D / E | rec 0.400, FP 95, wr 63 | F1 0.303 @ rec 0.622, FP 112 |

Two facts kill every rule:

1. **Best F1 is always the ungated raw point** (no τ improves F1) — because each false alarm removed
   costs a true fall at a comparable or faster rate.
2. **Meaningful FP cuts demand catastrophic recall loss.** To get FP from ~113 down even to ~95 costs
   recall ~0.67→~0.44–0.49 (seed 42) or ~0.62→~0.40–0.42 (seed 44). Pushing P(fall)≥0.50 (cross-seed
   table) drops recall to **0.089 / 0.067** while FP only falls to 68 / 62.

**Target satisfaction (recall/FP gates):**

| Target | seed 42 | seed 44 |
|---|---|---|
| recall ≥ 0.50 & FP ≤ 100 | **met** — A, P≥0.36: rec 0.556, FP 99 | **not met** |
| recall ≥ 0.50 & FP ≤ 80 | not met | not met |
| recall ≥ 0.40 & FP ≤ 80 | not met | not met |
| recall ≥ 0.40 & FP ≤ 60 | not met | not met |
| recall ≥ 0.30 & FP ≤ 50 | not met | not met |

**Does any rule give a useful operating point on both seeds? No.** Exactly one target is met, on one seed
only (seed 42, recall≥0.50 & FP≤100), and even that point (rec 0.556 / FP 99) is *dominated in spirit* by
the raw checkpoint (rec 0.667 / FP 115 — 16 fewer FP is not worth 5 fewer detected falls at typical
fall-detection cost ratios, §4). No target ≤80 FP is reachable on either seed; nothing is reachable on
both seeds.

---

## 4. Cost-curve & constrained selection

`analysis/cost_curve_gated.csv`. Cost = (FN:FP)·FN + FP, FN = (1−recall)·45.

| Seed | Point | recall | FP | 1:1 | 2:1 | 5:1 | 10:1 | 20:1 | 50:1 |
|---|---|---|---|---|---|---|---|---|---|
| 42 | raw Variant F | 0.667 | 115 | 130 | 145 | 190 | 265 | 415 | 865 |
| 42 | best gated | 0.667 | 111 | 126 | 141 | 186 | 261 | 411 | 861 |
| 44 | raw Variant F | 0.622 | 112 | 129 | 146 | 197 | 282 | 452 | 962 |
| 44 | best gated | 0.622 | 112 | 129 | 146 | 197 | 282 | 452 | 962 |

- **When is raw Variant F preferred?** At **every** FN:FP ≥ ~2:1 — i.e. across the entire range relevant
  to fall detection, where a missed fall costs more than a false alarm. The "best gated" point that
  *preserves recall* shaves only 0–4 FP (seed 42: 115→111; seed 44: no change), so raw and gated are
  effectively tied and raw is never beaten.
- **When are gated points preferred?** Only at extreme **FN:FP < 1:1** (a false alarm costs more than a
  missed fall) — the opposite of a safety-critical fall monitor, and not a regime this thesis claims.
- **Lower-FP operating point without unacceptable recall loss?** **No.** Every FP reduction beyond ~4
  windows is bought with recall the cost curve will not justify at ≥2:1.

---

## 5. Cross-seed stability

`analysis/cross_seed_threshold_stability.csv` (shared P(fall) threshold on both seeds):

| τ | s42 rec | s42 FP | s44 rec | s44 FP |
|---|---|---|---|---|
| 0.50 | 0.089 | 68 | 0.067 | 62 |
| 0.70 | 0.022 | 3 | 0.022 | 5 |
| 0.80 | 0.000 | 1 | 0.000 | 1 |

- **Does one threshold work on both seeds?** **No.** The single point meeting any target (seed 42,
  P≥0.36) yields rec 0.422 / FP 99 on seed 44 — fails recall≥0.50 & FP≤100. Each near-useful operating
  point needs a *different* per-seed threshold, and even then only seed 42 reaches a target.
- **Conclusion:** **Thresholding is not stable enough across seeds** to be a defensible operating rule.
  There is **no** single cross-seed threshold/margin to put forward as a candidate operating rule for the
  thesis. (Document this as a negative result, not an operating point.)

---

## 6. Diagnosis: filterable vs training-needed

**Diagnosis C — Not filterable.** The residual false alarms are high-confidence and **invert** the
confidence ordering relative to true attacked falls: on fall probability, fall-vs-rest logit margin,
entropy, and confidence margin, the false alarms are *more confident* than the true falls Variant F
detects (§2). Consequently (§3–§5): best F1 is always the ungated point; meaningful FP reduction forces
catastrophic recall loss (rec → ~0.07 at P≥0.50); no rule meets the FP-control targets on both seeds; and
no cross-seed threshold is stable. Post-hoc probability / margin / entropy gating **fails**. Reducing
these errors requires a **new training objective** that attacks the residual ~1.0 walk/run logit margin
directly — not a post-hoc filter.

*(Why not B "partially filterable": the recall/FP trade-off is not merely "too costly" — the signal is
inverted, so gating removes true falls first and the cost curve never prefers a gated point at ≥2:1.
Why not D "inconclusive": all outputs are present and the two seeds agree on the inversion and on the
failure of every rule.)*

---

## 7. Proposed Variant G (design only — **not run**)

Targets the *observed* failure: adversarial walk/run windows that land on fall with a high-confidence
~1.0 logit margin over their true class, indistinguishable post-hoc from true falls. **Do not run yet.**

| # | Option | Why it targets the failure | Expected benefit | Clean-acc risk | Fall-recall risk | When |
|---|---|---|---|---|---|---|
| G1 | **Targeted nonfall→fall PGD hard negatives** for walk/run (attack *toward* fall, add as adv negatives) | The FAs are walk/run windows pushed *into* fall; training on exactly those examples directly suppresses the fall logit where the attack lives | Largest direct FP cut on the dominant (motion) source | **Medium-high** — extra negative pressure on fall can depress clean fall recall | **Medium** — over-suppression could cost attacked recall | **Quick seed-42 pilot** (highest value) |
| G2 | **Source-class-weighted motion margin** (heavier λ on walk/run than other nonfall in the margin term) | walk/run are 65–70% of FAs with the smallest residual margin (~0.9–1.1); weight the loss where the geometry is worst | Focused motion-FP reduction, cheaper than G1 | **Low-medium** | **Low-medium** | **Quick seed-42 pilot** (cheap variant of current loss) |
| G3 | **False-alert-budget constrained selection** (pick checkpoint minimizing recall loss s.t. FP ≤ budget) | Re-uses existing v2 candidates; encodes the operating constraint into model *selection*, not the loss | Modest; bounded by candidates already trained | None (selection only) | Low | **Now, free** — fold into selection-v2 scoring; weakest effect |
| G4 | **Binary fall-alert auxiliary head** (separate fall-vs-rest logit trained with its own margin) | Gives a decision signal decoupled from the 7-way logits that are currently inverted | Could restore a *gatable* axis the 7-way softmax lacks | Low-medium | Medium | **Future work** — architecture change, larger effort |
| G5 | **Calibration-aware penalty** (ECE/temperature term so confidence tracks correctness) | Attacks the inversion itself — make P(fall) on FAs actually low | Would *enable* §3 gating if it works | Low | Low-medium | **Future work** — uncertain it survives PGD |
| G6 | **Hard-negative replay** from the residual FAs in `residual_fa_anatomy_*.csv` | Trains on the literal failing windows | Cheap, targeted | Low-medium | Low | **Quick seed-42 pilot** (pairs naturally with G1/G2) |

**Recommended Variant G, if run:** a single seed-42 pilot combining **G1 + G2** (targeted walk/run→fall
hard negatives with a source-class-weighted motion margin), optionally seeded with **G6** replay of the
committed residual FA windows. This is the minimal change that attacks the exact ~1.0 motion logit margin
the diagnostic isolated, under the frozen selection-v2 clean guard. **Not run here.**

---

## 8. Advisor recommendation

**Best research value per compute hour: write the thesis now; add this diagnostic as a negative/limitation
result in Chapter 6; treat Variant G as an optional, clearly-scoped single seed-42 pilot — *after* the
draft.**

- **Stop and write the thesis now?** **Yes — primary recommendation.** The defense line already has a
  complete, honest arc (D → E → selection-v2 → F) with a STRONG-SUPPORT two-seed validation. This
  diagnostic *adds* a clean, defensible result: *Variant F's residual false alarms are high-confidence,
  confidence-inverted, and not post-hoc filterable* — exactly the kind of limitation a committee respects.
- **Add post-hoc operating-point analysis to Chapter 6?** **Yes.** It is zero additional compute and
  strengthens the chapter: it proves the team tried the cheap fix (thresholding/gating) and shows *with
  data* why it fails, motivating the margin-based training direction.
- **Run a Variant G seed-42 pilot?** **Optional, lower priority, after the draft.** If run, scope it to
  **one** seed-42 pilot (G1+G2) and pre-register success criteria as before. It is a *nice-to-have*
  confirmation of the mechanism, not required for the thesis claim.
- **Run seeds 45–46 first?** **No.** Two seeds (42+44) already give CI-separated evidence over the FGSM
  floor and a replicated operating point; seeds 45–46 add confirmatory breadth but no new mechanism, and
  cost more compute than the Chapter-6 writing they would delay. Lowest value per hour right now.

**Priority order:** (1) write Chapter 6 incl. this diagnostic → (2) optional Variant G seed-42 pilot →
(3) optional seeds 45–46 confirmation. The diagnostic itself was the high-value, near-zero-compute step;
spend the next hours on the draft, not on more GPU.

---

## Artifacts

- Report: `VARIANT_F_FALSE_ALARM_DIAGNOSTIC.md`
- Per-window FA anatomy: `analysis/residual_fa_anatomy_seed{42,44}.csv`
- Source-class summary: `analysis/source_class_summary.csv`
- Group distributions: `analysis/group_distributions.csv`
- Operating-point sweeps: `analysis/operating_point_sweep_seed{42,44}.csv`
- Target satisfaction: `analysis/target_satisfaction.csv`
- Cost curves: `analysis/cost_curve_gated.csv`
- Cross-seed stability: `analysis/cross_seed_threshold_stability.csv`
- Figures: `figures/fig_hist_fallprob_margin_seed{42,44}.png`,
  `figures/fig_separability_seed{42,44}.png`
- Script: `scripts/diagnose_variantF_false_alarms.py`

**Scope reminder:** diagnostic/reporting only; post-hoc rules are a filterability probe, not a deployed
decision rule; window-level, digital-domain, white-box; **not** solved, **not** certified, **not**
clinical, **not** over-the-air.
