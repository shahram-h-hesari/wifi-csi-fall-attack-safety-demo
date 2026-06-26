# Next-experiment decision memo — safety-guided defense (seed 42)

> **Analysis-only.** No models were trained, no seeds 43–46 were run, no existing result
> CSVs / figures / reports / scripts / `.tex` files were modified, and the frozen Variant D
> protocol was not changed. This memo and two derived CSVs under
> `results/safety_guided_defense/seed42/analysis/` are the only new artifacts.
> Source data: the committed seed-42 test-eval prediction CSVs (test split, n=500, ε=0.030).

**Main question:** proceed directly to frozen Variant D seeds 43–46, or first design a revised
safety-constrained defense that explicitly reduces false-fall alarms?

**Short answer:** Proceed to **Option A (frozen Variant D, seeds 43–46) now**, with one
logging-only addition (save per-class fall probabilities during eval) so that the false-alarm
fix — **threshold calibration (Option C)** — can be done across all seeds afterward without
retraining. Rationale and evidence below. The popular "hard-negative on lie-down/sit-down" idea
(Option D as phrased) is **contraindicated by the data** (false alarms come from walk/run, not
static postures).

---

## 1. What previous experiments already answered

- **Cross-architecture, five-seed study** (LeNet, GRU, BiLSTM, Transformer, ResNet18; 5
  clean-qualified seeds each) already established that the fall-recall collapse under FGSM/PGD
  is **real and not specific to one model or one seed**. PGD@0.030 fall recall collapses (≈0.000)
  across all five architectures. *(evidence: `results/cross_architecture/cross_architecture_multiseed_summary.csv`, commit `787705c`/`08ae96b`)*
- **Seed-42 safety-guided pilot** already established that **safety-proxy checkpoint selection can
  recover PGD fall recall** relative to both the generic FGSM defense and macro-F1 selection
  (≈0.44–0.49 vs 0.089). *(commit `f9e5ac5`)*
- **Implication:** the next experiment should **not** re-answer "is the gap real?" That is settled.
  It should decide **how to improve the safety trade-off** (PGD recall vs false-alarm burden vs
  clean collapse).

## 2. What seed 42 actually taught us

(test split, n=500, ε=0.030; full numbers in §4 and §6)

- **Existing FGSM defense baseline:** clean acc 0.834, clean fall recall 0.911; FGSM@0.030 fall
  recall 0.311; **PGD@0.030 fall recall 0.089** (the bar to beat); PGD false-alarms 54.
- **Variant B/C/D safety-guided:** all lift PGD@0.030 fall recall to **0.44–0.49** (≈5×), and FGSM
  recall to 0.49–0.78. The cost: **3–3.5× more false-fall alarms** and lower clean accuracy.
- **C maximizes raw PGD recall** (0.489) but at the **worst clean accuracy (0.642)** and the
  **highest false alarms (190)**.
- **D is best-balanced:** PGD recall 0.444, **clean fall recall 1.000**, **clean acc 0.746**
  (highest of any safety pick), FGSM recall 0.778, widest robust ε-range (collapse ε ≈0.030–0.045).
- **Macro-F1 vs safety-guided selection:** on the *same* trained weights (Variant B), safety
  selection gives PGD recall 0.444 vs **0.089** for macro-F1 selection. Selection is the lever.
  Conversely D-macro-F1 keeps clean acc higher (0.848) but PGD recall drops to 0.133.
- **Raw SafetyScore degeneracy / clean-collapse guard:** without the guard, the raw score
  (0.10 false-alarm penalty) selects a **degenerate always-fall predictor** (clean acc ≈0.09, ~all
  non-fall windows flagged) for the fall-weighted variants. The guard
  (`clean_acc ≥ 0.60 ∧ clean_macro_f1 ≥ 0.50`) is **required**; un-guarded picks are kept in
  metadata for transparency.
- **Why this is a trade-off, not a solved defense:** the PGD-recall gain is bought with a large
  false-alarm increase (PGD FPR over non-fall windows rises to ~0.35 for D — see §4). Even the best
  variant would raise many false alarms on a real deployment stream.

## 3. False-alarm source diagnosis

For each checkpoint, count of **true non-fall class → predicted fall** (false-fall alarms), by
true class, under clean / FGSM@0.030 / PGD@0.030 (test n=500).
*(derived file: `analysis/false_alarm_class_sources.csv`)*

| Checkpoint | Condition | lie down | walk | pickup | run | sit down | stand up | **Total** |
|---|---|---|---|---|---|---|---|---|
| FGSM defense | clean | 0 | 0 | 4 | 1 | 1 | 2 | 8 |
| FGSM defense | FGSM@0.030 | 0 | 9 | 4 | 4 | 0 | 10 | 27 |
| FGSM defense | PGD@0.030 | 1 | 15 | 4 | 24 | 1 | 9 | 54 |
| C · safety | clean | 4 | 20 | 9 | 22 | 3 | 13 | 71 |
| C · safety | FGSM@0.030 | 15 | 48 | 13 | 52 | 4 | 14 | 146 |
| C · safety | PGD@0.030 | 16 | 71 | 15 | 68 | 5 | 15 | 190 |
| **D · safety** | clean | 0 | 10 | 12 | 8 | 2 | 6 | 38 |
| **D · safety** | FGSM@0.030 | 8 | 40 | 11 | 50 | 3 | 11 | 123 |
| **D · safety** | PGD@0.030 | 12 | 55 | 10 | 65 | 2 | 13 | 157 |
| D · macro-F1 | clean | 0 | 1 | 4 | 3 | 1 | 3 | 12 |
| D · macro-F1 | FGSM@0.030 | 2 | 15 | 7 | 37 | 1 | 8 | 70 |
| D · macro-F1 | PGD@0.030 | 5 | 19 | 7 | 42 | 1 | 5 | 79 |

**Dominant sources are walk and run (motion classes), not the fall-adjacent static postures.**
For D·safety under PGD: run (65) + walk (55) = **120 of 157 (76%)**; lie down (12) and sit down (2)
together are only **14 of 157 (9%)**. The same pattern holds for C·safety and D·macro-F1 (run is the
single largest source in every attacked condition). Sit down is consistently the *smallest*
contributor (≤5). This is the opposite of the intuitive "lie-down/sit-down look like falls"
hypothesis.

All required prediction files were present; **nothing was missing** for this diagnosis. (Caveat
for §8 Option C: per-class probabilities/logits were **not** saved — only argmax confidence — so
threshold calibration cannot be done from existing files; see §8/§10.)

## 4. Binary fall-alert metrics

Computed from the prediction CSVs *(derived file: `analysis/binary_alert_metrics.csv`)*.
FP = false-fall alarms; FPR = FP / non-fall windows; specificity = 1 − FPR.

| Checkpoint | Condition | Recall (sens.) | FP | Precision | Specificity | FPR | Binary F1 | Missed |
|---|---|---|---|---|---|---|---|---|
| FGSM defense | clean | 0.911 | 8 | 0.837 | 0.982 | 0.018 | 0.872 | 4 |
| FGSM defense | FGSM@0.030 | 0.311 | 27 | 0.341 | 0.941 | 0.059 | 0.326 | 31 |
| FGSM defense | PGD@0.030 | 0.089 | 54 | 0.069 | 0.881 | 0.119 | 0.078 | 41 |
| C · safety | clean | 0.978 | 71 | 0.383 | 0.844 | 0.156 | 0.550 | 1 |
| C · safety | FGSM@0.030 | 0.556 | 146 | 0.146 | 0.679 | 0.321 | 0.231 | 20 |
| C · safety | PGD@0.030 | 0.489 | 190 | 0.104 | 0.582 | 0.418 | 0.171 | 23 |
| **D · safety** | clean | 1.000 | 38 | 0.542 | 0.916 | 0.084 | 0.703 | 0 |
| **D · safety** | FGSM@0.030 | 0.778 | 123 | 0.222 | 0.730 | 0.270 | 0.345 | 10 |
| **D · safety** | PGD@0.030 | 0.444 | 157 | 0.113 | 0.655 | 0.345 | 0.180 | 25 |
| D · macro-F1 | clean | 0.956 | 12 | 0.782 | 0.974 | 0.026 | 0.860 | 2 |
| D · macro-F1 | FGSM@0.030 | 0.467 | 70 | 0.231 | 0.846 | 0.154 | 0.309 | 24 |
| D · macro-F1 | PGD@0.030 | 0.133 | 79 | 0.071 | 0.826 | 0.174 | 0.092 | 39 |

Clean guardrails (clean accuracy / clean macro-F1): FGSM defense 0.834 / 0.814; C·safety 0.642 /
0.584; D·safety 0.746 / 0.700; D·macro-F1 0.848 / 0.813.

- **Primary metrics:** PGD@0.030 fall recall (sensitivity) and false-fall-alarm burden (FP / FPR).
- **Guardrails (not objectives):** clean fall recall, clean accuracy, clean macro-F1 — used only to
  detect collapse / degeneracy.
- Observation: fall **precision under PGD is very low for every defended model** (0.07–0.11),
  because non-fall windows vastly outnumber fall windows and many are flipped to fall. Recall is
  bought at the expense of precision/specificity.

## 5. Accuracy interpretation

- The intended product is a **binary fall alert** (fall vs non-fall), so **seven-class accuracy is
  secondary** — it is not the safety objective and should not be optimized for its own sake.
- However, **clean accuracy / macro-F1 still matter as a collapse guard.** If clean accuracy
  collapses toward chance (~0.09–0.31 here), the model has likely degenerated (e.g., the always-fall
  predictor) or its representation is too poor to be trusted; §2/§10 show this is exactly the failure
  the clean-collapse guard prevents.
- **A useful defense must not become an always-fall predictor.** "Perfect" fall recall with
  near-zero specificity is operationally useless. The guard (clean_acc ≥ 0.60, clean_macro_f1 ≥ 0.50)
  encodes this minimum. D·safety (0.746 / 0.700) clears it comfortably; C·safety (0.642 / 0.584)
  clears it but is the weakest non-degenerate point.

## 6. Pareto / operating-point analysis

Ranked on the safety trade-off (PGD@0.030 unless noted; test n=500).

| Candidate | PGD recall | PGD FP | Clean fall recall | Clean acc | Fall precision (PGD) | PGD collapse ε | Role |
|---|---|---|---|---|---|---|---|
| C · safety | **0.489** | 190 | 0.978 | 0.642 | 0.104 | 0.030 | **best raw recall** (costly) |
| **D · safety** | 0.444 | 157 | 1.000 | 0.746 | 0.113 | 0.030 | **best balanced** |
| B · safety | 0.444 | 182 | 0.978 | 0.580 | ~0.10 | 0.025 | high recall, weak clean |
| D · macro-F1 | 0.133 | 79 | 0.956 | 0.848 | 0.071 | 0.025 | low-FP, weak recall |
| FGSM defense | 0.089 | 54 | 0.911 | 0.834 | 0.069 | 0.018 | **lowest FP w/ some robustness** |
| Clean baseline | 0.000 | 48 | 0.956 | 0.970 | 0.000 | 0.005 | undefended reference |
| (raw-ungated always-fall) | ~1.0 (val) | ~all non-fall | 1.000 | ~0.09 | ~0.09 | n/a | **degenerate / unacceptable** (guard-excluded) |

- **Best raw PGD recall:** C·safety (0.489) — but worst clean acc and highest false alarms.
- **Best balanced:** **D·safety** — highest clean acc among safety picks, clean fall recall 1.000,
  lowest PGD FP among the high-recall (>0.4) options, widest collapse ε.
- **Lowest false-alarm point with meaningful robustness:** trade-off-dependent — D·macro-F1 (FP 79)
  if a recall ≈0.13 is acceptable; otherwise D·safety (157) is the lowest-FP among recall>0.4 points.
- **Unacceptable/degenerate point:** the raw-ungated always-fall predictor (guard-excluded; logged
  in metadata).
- **Does D remain best-balanced?** **Yes.** Among all evaluated points it is the only one combining
  recall>0.4, clean fall recall 1.000, clean acc ≥0.74, and the widest robust ε-range.

## 7. Why false alarms increased (interpretation, with uncertainty)

Mapping to the offered hypotheses:

- **A. Mainly fall-adjacent (lie down/sit down):** **Rejected by the data.** Those classes are the
  *smallest* contributors (sit down ≤5; lie down 1–16). The intuitive story does not hold here.
- **B. Broadly from many non-fall classes:** **Partially.** All non-fall classes contribute some,
  but it is not uniform.
- **C. The model became generally fall-biased, concentrated on motion classes:** **Best supported.**
  walk + run dominate (≈70–80% of attacked false alarms), and run scales most steeply with attack
  strength (D·safety run: 8 clean → 50 FGSM → 65 PGD). The model appears to map high-motion windows
  to "fall," and the adversary exploits exactly that direction.
- **D. Mechanism = checkpoint selection / loss weighting / thresholding / objective:** **Likely a
  contributor.** Fall-weighting (×3) plus a safety score that rewards recall while only weakly
  penalizing false alarms pushes the decision boundary toward fall; argmax over seven classes with
  no fall-specific threshold then converts motion windows into fall alerts. This is consistent with
  the macro-F1 vs safety-selection gap (same weights, very different FP).

**Uncertainty:** this is inferred from one seed and from argmax predictions only. Without per-class
probabilities we cannot tell whether walk/run false falls are low-margin (threshold-fixable) or
high-confidence (objective-level). That distinction decides whether Option C or Option B/D is the
right fix — and we currently **cannot** answer it from saved data. This is the key gap to close.

## 8. Candidate next experiments

| Option | What | Pros | Cons / blockers |
|---|---|---|---|
| **A** | Proceed with frozen Variant D seeds 43–46 | Protects against seed-42 over-interpretation; directly confirms reliability; already frozen/committed | May replicate the high false-alarm burden 4× without improving it |
| **B** | Revise safety score with a stronger false-alarm penalty, *then* multi-seed | Directly targets the current weakness | Pilot-driven protocol redesign after seeing seed-42; must be documented; tuning to one seed risks overfit |
| **C** | Threshold-calibrate the binary fall alert on validation (no retraining) | Matches the binary-alert use case; could cut false alarms without retraining; reuses frozen checkpoints | **Blocked:** per-class fall probabilities were not saved (only argmax confidence). Needs a small no-retrain re-eval that exports fall-class probability |
| **D** | Hard-negative adversarial training on classes that become false-fall | Targeted to the observed source | More complex; **as commonly phrased (lie-down/sit-down) it is mis-targeted** — the data say walk/run. Would need re-derivation and retraining |
| **E** | More architectures/datasets | Generality | **Lower priority now** — the robustness gap is already established cross-architecture/cross-seed; adds breadth, not the missing trade-off evidence |

## 9. Recommendation

**Primary recommendation: Option A now — run the frozen Variant D protocol on seeds 43–46,
unchanged — with one logging-only addition: save per-class fall probabilities during evaluation.**

Evidence-based reasoning:
1. **The frozen protocol is the scientific gate.** Seed 42 is n=1; redesigning the safety score
   (Option B) or the training objective (Option D) before confirming the seed-42 trade-off
   replicates would be tuning to a single seed and would weaken the multi-seed evidence. Confirm
   first, then improve.
2. **The cheapest, best-matched false-alarm fix is Option C (threshold calibration), and it is
   currently blocked only by missing data.** Adding a per-class-probability dump to the eval is a
   **logging change, not a hyperparameter/training/selection change**, so it does not alter the
   frozen Variant D recipe. Doing it during the multi-seed run yields calibration data on all five
   seeds at once, so the false-alarm fix is built on multi-seed footing rather than one seed.
3. **The diagnosis rules out the obvious redesign.** False alarms are walk/run-driven, so Option D
   targeted at lie-down/sit-down is contraindicated; any hard-negative work should wait for the
   probability data (to confirm whether walk/run false falls are threshold-fixable) and for
   multi-seed confirmation.
4. **Option E is not the bottleneck.** Generality is already demonstrated.

**Sequenced plan:** A (multi-seed D + probability logging) → then C (threshold calibration on the
saved probabilities, no retraining) → only if C is insufficient, consider B or a walk/run-targeted D
as a clearly-documented, pilot-driven redesign.

**Caveat / honest framing:** if you judge the current PGD false-alarm burden (FPR ≈0.35) too high to
be worth confirming at all, the alternative is to do Option C-enabling first — i.e. a tiny no-retrain
re-eval of the existing seed-42 D checkpoints that exports probabilities, run threshold calibration,
and only then decide on multi-seed. This trades scientific sequencing for a faster read on whether
false alarms are even fixable. The recommendation above prefers confirmation-first, but this is the
reasonable second choice.

## 10. Proposed next prompt (give me this after you review)

If you accept the primary recommendation (multi-seed first, with probability logging):

```
Run the frozen Variant D multi-seed confirmation, seeds 43–46 only.

Constraints:
- Variant D only (FGSM+PGD multi-epsilon, fall-weighted loss, safety-guided selection
  with the existing clean-collapse guard). No hyperparameter search. No score/guard change.
- Keep macro-F1 selection as the standard-selection comparison.
- LeNet only, same UT-HAR/SenseFi split.
- Evaluation: same protocol (eps 0.030 headline + 18-eps FGSM/PGD sweep, test + legacy).
- ADDITION (logging only, does not change the recipe): during test-eval, also export the
  per-class softmax probabilities (at least the fall-class probability) per window, so that
  binary fall-alert threshold calibration can be done later without re-running. If this needs
  a new eval script, create one new script; do not modify existing scripts.
- Do not modify thesis .tex files. Do not change the frozen protocol beyond the logging addition.
- After running, aggregate seeds 42–46 (mean ± spread) for PGD@0.030 fall recall, false-fall
  alarms, clean fall recall, clean accuracy, and report the trade-off honestly.
```

If instead you prefer the false-alarm fix first (no retraining):

```
Analysis/calibration only — no training, no seeds 43–46.

Re-evaluate the EXISTING seed-42 Variant D checkpoints (bySafetyScore and byValMacroF1) on the
test and validation splits, exporting per-class softmax probabilities per window (new script;
do not modify existing scripts or checkpoints). Then, using validation only, calibrate a
fall-class probability threshold for the binary fall alert, and report how PGD@0.030 fall recall
vs false-fall alarms move along the threshold sweep on the test split. Do not change the frozen
protocol; document this as a derived, no-retraining calibration study.
```
