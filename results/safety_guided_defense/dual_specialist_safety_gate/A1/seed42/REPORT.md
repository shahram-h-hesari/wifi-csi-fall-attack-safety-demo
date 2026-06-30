# DS-SGE Stage A — post-hoc dual-specialist safety-gate (seed 42)

> **Analysis of frozen checkpoints only — no training, no dataset-split change, no test-set tuning.**
> Evaluates whether a smooth safety gate `S(x)=α·p_R(fall|x)+(1−α)·p_B(fall|x)` (fall ⇔ `S≥τ`) over two
> frozen LeNet specialists improves the empirical adversarial fall-recall vs false-alarm frontier on UT-HAR.
> `(α,τ)` selected on **validation PGD only**; applied to the held-out test split once. Window-level,
> digital-domain, white-box, processed CSI, ε=0.030, PGD steps=10 (α=ε/6). Test n=500 (45 fall / 455 non-fall);
> validation n=496 (44 fall). **No certified / clinical / deployment / product / over-the-air claim.**
> **Verdict: the gate does NOT improve the frontier — informative negative.** The joint target
> (PGD recall ≥ 0.80 ∧ FAR ≤ 0.10) remains **unmet**.

## 1. What was run

Specialists are existing Variant-G G1 selection-v2 checkpoints (same architecture, LeNet, seed 42):
- **Recall specialist `f_R`** = `seed42_variantG_G1_v2maxrec_best.pt` (recall-leaning selection).
- **FAR-control specialist `f_B`** = `seed42_variantG_G1_v2lowFA_best.pt` (false-alarm-leaning selection).

Per-window 7-class probabilities/logits were exported for both specialists on **validation and test**, under
**clean / FGSM@0.03 / PGD@0.03**, via the committed `export_probability_predictions.py` (unmodified;
identical deterministic loader + `--seed 0`, so `sample_id` aligns the two specialists — verified by a
true-label alignment assertion). A **cross-family** confirmation pair was also run
(`f_R` = G1 maxrec × `f_B` = `seed42_optionB_minFA_best.pt`) to test whether the conclusion is an artifact of
same-training-run selection.

## 2. Validation-only calibration (primary pair)

Grid `α∈{0..1}`, `τ∈{0..1}` (step 0.01) on **validation PGD**, maximize recall s.t. FAR ≤ 0.10
(tie-break precision→F1→accuracy→lower τ). Full grid in `gate_grid_validation.csv`.

**Locked operating point: α = 0.48, τ = 0.23** (feasible on validation).
Validation PGD at locked point: **recall 0.500 (22/44), FAR 0.100 (45/451).**

## 3. Locked held-out TEST metrics (primary pair, α=0.48, τ=0.23)

| attack | system | recall | FAR | TP | FP | FN |
|---|---|---|---|---|---|---|
| clean | f_R alone | 0.978 | 0.053 | 44 | 24 | 1 |
| clean | f_B alone | 0.889 | 0.018 | 40 | 8 | 5 |
| clean | **DS-SGE gate** | 0.978 | 0.042 | 44 | 19 | 1 |
| FGSM | f_R alone | 0.844 | 0.163 | 38 | 74 | 7 |
| FGSM | f_B alone | 0.378 | 0.051 | 17 | 23 | 28 |
| FGSM | **DS-SGE gate** | 0.556 | 0.090 | 25 | 41 | 20 |
| PGD | f_R alone | 0.689 | 0.229 | 31 | 104 | 14 |
| PGD | f_B alone | 0.178 | 0.066 | 8 | 30 | 37 |
| PGD | **DS-SGE gate** | **0.400** | **0.121** | 18 | 55 | 27 |
| **adaptive full-gate PGD** | **DS-SGE gate** | **0.467** | **0.246** | 21 | 112 | 24 |

- On **PGD**, the locked gate gives **recall 0.400 at FAR 0.121** — *below* the best prior validated frontier
  (**G1 seed44: recall 0.600, FAR 0.143, clean guard held**) and still **above the 10% FAR budget on test**.
- Same **validation→test generalization gap** that sank A1/Option B: val FAR 0.100 → test FAR 0.121
  (FP 45→55), val recall 0.500 → test recall 0.400.

## 4. Adaptive full-gate attack (Athalye — mandatory; gradient-masking check)

The full pipeline `x→(f_R,f_B)→S(x)→decision` was attacked directly on the continuous `S` (loss
`mean(𝟙[y=fall]·(−S)+𝟙[y≠fall]·S)`, PGD-10, ε=0.03; τ applied only after the attack). Result:
**recall 0.467, FAR 0.246 (FP 112).** The adaptive attack drives FAR *far above* the component-PGD value
(0.121) — i.e. the attacker obtains useful gradients through the gate. **This is the opposite of gradient
masking:** the gate is genuinely (more) vulnerable, so the negative result is not a weak-attack artifact.
(The component-PGD evaluation combines two *different* per-model adversarial inputs, so its recall 0.400 is an
artifact of mixed inputs; the single-input adaptive recall 0.467 / FAR 0.246 is the trustworthy worst case.)

## 5. Error-overlap — the decisive complementarity test

A safety gate can exceed a single specialist's recall **only if** the two specialists detect *different* falls
(DVERGE condition). They do not.

**Primary pair (G1 maxrec × G1 lowFA), TEST PGD, n_fall = 45:**
- missed by **R only = 0**, missed by **B only = 23**, missed by **both = 14**.
- recall R=0.689, recall B=0.178, **UNION = 0.689 (= R exactly)**, intersection = 0.178 (= B).
- false alarms: R-only = 74, **B-only = 0**, both = 30.

→ **B's detections are a strict subset of R's** (every fall B catches, R catches; every fall R misses, B
misses; same nesting for false alarms). Zero recall complementarity.

**Cross-family pair (G1 maxrec × Option B minFA), TEST PGD:**
- missed by R only = 1, B only = 26, both = 13. recall R=0.689, B=0.133, **UNION = 0.711**, intersection 0.111.
- false alarms: R-only = 70, B-only = 2, both = 34.

→ Even across training families, `f_B` rescues only **1 of 45** falls that `f_R` misses (union recall 0.711).
Complementarity is negligible; the gate's locked test point is again ~0.40 recall / ~0.125 FAR.

## 6. Frontier interpretation (does it move OUT or only ALONG?)

`fig_recall_far_frontier.png`: the per-window P(fall) threshold curves of `f_R`, `f_B`, and the gate are
**effectively coincident**, and **none enters the target zone** (recall ≥ 0.80 ∧ FAR ≤ 0.10). At FAR = 0.10
the best recall on any curve is ≈ 0.42. The gate **moves along the shared frontier, not out of it.** Because
the two specialists are near-nested, the convex combination cannot separate falls from non-falls any better
than the single representation already does — it only re-selects an operating point on the same curve.

This corroborates and sharpens the committed line: the barrier is the **representation-level overlap of the
attacked fall vs non-fall score distributions at the fall↔walk/run boundary**, not the choice of
checkpoint, threshold, or combination rule.

## 7. Committee Q&A

1. **Contribution of "two models"?** A quantified negative: gating two operating points of the *same* LeNet
   representation gains nothing because their adversarial vulnerabilities are **nested, not complementary**
   (union recall = max single recall). This is direct, gate-based evidence for a representation-level barrier.
2. **Full ensemble or per-model?** Both: per-model PGD *and* the adaptive full-gate PGD on `S(x)` (§4).
3. **Gate hiding gradients?** No — adaptive attack is *stronger* than component PGD (FAR 0.121→0.246).
4. **Tuned on test?** No — `(α,τ)` from validation PGD only; full grid + `gate_config.json` written before
   test was scored.
5. **Frontier out or along?** Along (§5–§6). Not out.
6. **FAR ≤ 10% stable?** No — the validation-feasible point (FAR 0.100) generalized to FAR 0.121 on test
   (455 non-fall windows; 1 FP ≈ 0.22% FAR). Small-sample + val→test gap make sub-10% fragile.
7. **Certified?** No. Empirical, window-level, white-box, L∞-bounded only.
8. **Why not just threshold one model?** Single-model thresholding is exactly what these curves show; the gate
   does not beat it. The recall ceiling (union of two near-nested specialists) is ~0.69–0.71, far below 0.80.

## 8. Conclusion and recommendation

**A post-hoc dual-specialist safety gate over existing LeNet checkpoints does not improve the adversarial
recall/FAR frontier and does not reach the target region.** The core research question is answered for this
configuration: the gate fails *because the specialists are not complementary* — their attacked fall
detections are (near-)nested along one shared fall-risk axis, so no convex gate can move the frontier outward.

Because the binding constraint is the **shared representation**, training two *new* LeNet specialists
(Stage B) is unlikely to help: the same fall↔walk/run overlap would be inherited. The scientifically warranted
next step is the **representation-level test already pre-registered in the repo** — a single defended
BiLSTM (higher clean headroom) under the frozen Variant-G objective, seed 42, same split and Gate-5 protocol —
now independently motivated by this gate-level evidence. Stage B/C (specialist training, cross-model
adversarial exposure) are **not** recommended on LeNet.

This is a valid, committee-defensible **informative-negative / characterization** result for the thesis.

## 9. File manifest

`probabilities/` (12 + 6 cross-family per-window CSVs), `validation_probabilities.csv`,
`test_probabilities.csv`, `gate_grid_validation.csv`, `gate_config.json`, `metrics_{clean,fgsm,pgd}*.csv`,
`metrics_adaptive_gate_pgd_eps003.csv`, `adaptive_gate_perwindow_test_epsilon_0_03.csv`, `error_overlap.csv`,
`frontier_points.csv`, `figures/fig_{recall_far_frontier,error_overlap,confusion_clean,confusion_pgd}.png`,
and `cross_family_check/` (same outputs for the G1maxrec × optBminFA pair).
Scripts: `scripts/gate_dual_specialist.py`, `scripts/adaptive_gate_attack.py`, `scripts/plot_dsge_stage_a.py`.
