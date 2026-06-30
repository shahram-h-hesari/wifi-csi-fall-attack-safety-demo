# Chapter 6 subsection draft — Dual-Specialist Safety-Gated Ensemble (DS-SGE)

> **Draft thesis prose — not final LaTeX.** Interprets the committed Stage A artifacts under
> `results/safety_guided_defense/dual_specialist_safety_gate/A1/seed42/`. All numbers are window-level,
> white-box, digital-perturbation (L∞, ε=0.030, PGD steps=10, α=ε/6) on processed UT-HAR CSI; test n=500
> (45 fall / 455 non-fall), validation n=496 (44 fall). **No certified / clinical / deployment / product /
> over-the-air claim.**

## 6.x A gated-ensemble probe of the adversarial recall / false-alarm frontier

### 6.x.1 Objective

The preceding variants established that, on the LeNet backbone, no single-model loss reweighting reached the
joint safety target of attacked fall recall ≥ 0.80 with an attacked false-alarm rate ≤ 0.10, and that
post-hoc thresholding of any one model could not exceed an attacked recall of about 0.60. A natural question
remained: if one model cannot separate attacked falls from attacked non-falls, can a **combination of two
models specialised to opposite errors** do so? We therefore evaluated a Dual-Specialist Safety-Gated Ensemble
(DS-SGE). Two frozen specialists were used: a **recall specialist** f_R (the Variant-G G1 checkpoint selected
to maximise attacked fall recall) and a **false-alarm-control specialist** f_B (the same Variant-G G1 run
selected to minimise the attacked false-alarm rate). Their fall-class probabilities were combined by a smooth,
low-parameter safety gate

    S(x) = α · p_R(fall | x) + (1 − α) · p_B(fall | x),    decision: fall ⇔ S(x) ≥ τ,

following the smooth mixture-of-experts formulation (a fixed differentiable gate, deliberately not a learned
router, to avoid routing instability and gradient masking). The scientific question is precise: does gating
move the recall / false-alarm frontier **outward**, or merely **along** the existing trade-off?

### 6.x.2 Validation-only gate calibration

The two gate parameters (α, τ) were selected on the **validation split only**, under the PGD@0.030 condition
(the operative threat), by maximising validation fall recall subject to validation false-alarm rate ≤ 0.10,
with ties broken by precision, then F1, then accuracy, then lower τ. The full 101 × 101 grid was retained for
audit. The selected operating point was **α = 0.48, τ = 0.23**, which on validation PGD detected 22 of 44
falls (recall 0.500) at a false-alarm rate of exactly 0.100. The test split was not consulted during
selection; the locked (α, τ) was then applied to the test split once.

### 6.x.3 Locked held-out test result

| condition | system | fall recall | false-alarm rate | TP | FP | FN |
|---|---|---|---|---|---|---|
| clean | DS-SGE gate | 0.978 | 0.042 | 44 | 19 | 1 |
| FGSM | DS-SGE gate | 0.556 | 0.090 | 25 | 41 | 20 |
| **PGD** | **DS-SGE gate** | **0.400** | **0.121** | 18 | 55 | 27 |
| PGD | f_R alone (argmax) | 0.689 | 0.229 | 31 | 104 | 14 |
| PGD | f_B alone (argmax) | 0.178 | 0.066 | 8 | 30 | 37 |

Under PGD the gate attained fall recall 0.400 at a false-alarm rate of 0.121. This is **below the strongest
prior validated operating point** (Variant G G1, seed 44: recall 0.600 at false-alarm rate 0.143 with the
clean guard intact) and still exceeds the 0.10 false-alarm budget on the held-out test split. The same
validation-to-test generalisation gap observed for the earlier rebalanced and adaptive-controller variants
recurred here: the validation-feasible false-alarm rate of 0.100 rose to 0.121 on test.

### 6.x.4 Error-overlap finding

The decisive measurement is whether the two specialists make **complementary** mistakes, because a gate can
raise recall above a single model only by rescuing falls that the other model misses. On the held-out test
set under PGD (45 fall windows), the recall specialist missed 14 falls and the false-alarm specialist missed
37; of these, **every** fall missed by f_R was also missed by f_B (falls missed by f_R only = 0; missed by
f_B only = 23; missed by both = 14). Equivalently, the union of the two specialists' detections equalled the
recall specialist's detections exactly (union recall 0.689 = recall of f_R alone), and their intersection
equalled the weaker specialist (0.178 = recall of f_B). The false alarms were nested in the same direction
(false alarms from f_B only = 0; the 30 false alarms of f_B were a subset of the 104 of f_R). A cross-family
replication, pairing the recall specialist with the most aggressive false-alarm controller from a different
training run (Option B minFA), changed this only marginally: the false-alarm specialist rescued exactly **one**
of 45 falls that the recall specialist missed (union recall 0.711). In both pairings the two specialists are
**nested operating points on a single shared score axis**, not complementary detectors.

### 6.x.5 Adaptive full-gate attack

To ensure the negative result was not an artefact of a weak attack or of gradient masking, the complete gated
pipeline was attacked directly on the continuous score S(x) (loss
mean(𝟙[y = fall]·(−S) + 𝟙[y ≠ fall]·S), PGD, ε=0.030, with the decision threshold applied only after the
attack so that the attack never sees the hard threshold). The adaptive attack drove the false-alarm rate to
0.246 (112 of 455 non-fall windows raised as falls) at recall 0.467 — substantially **more harmful** than the
component-wise PGD evaluation. The fact that the white-box attack on the full gate is stronger than the
component attacks is the expected signature of an **honestly differentiable** defence: the attacker obtains
useful gradients through S, so the gate provides no hidden robustness. The negative result is therefore real,
not a masking illusion.

### 6.x.6 Conclusion: nested, not complementary

DS-SGE does not improve the empirical adversarial recall / false-alarm frontier. Across same-family and
cross-family specialist pairs the two models are nested rather than complementary: the false-alarm specialist
detects a strict (or near-strict) subset of the falls the recall specialist detects, so the convex gate can
only re-select an operating point **along** the recall specialist's existing frontier and cannot push it
**outward**. The locked gate landed below the best prior single-model point and still violated the false-alarm
budget under attack, and an adaptive full-pipeline attack confirmed genuine vulnerability.

### 6.x.7 Implication: a representation-level bottleneck

This result localises the obstacle. Because two LeNet models trained toward opposite safety errors share the
same adversarial vulnerabilities at the fall ↔ walk/run boundary, the limit is **representation-level** — a
property of the learned features — rather than a matter of gate design, threshold choice, or model
combination. Consistent with the earlier threshold and score-overlap diagnostics (under attack the genuine
falls' fall-probability collapses into the upper tail of the non-falls' fall-probability), the evidence
indicates that further work on the **same LeNet representation** — including training new specialists or more
elaborate gates — is unlikely to reach the target. The scientifically warranted next step is therefore a
single, controlled test of whether a **higher-capacity backbone with greater clean headroom**, trained under
the identical (frozen) safety objective, can separate the two classes where the shallow convolutional model
could not. That experiment is pre-registered separately; DS-SGE's contribution here is diagnostic, delineating
that the residual barrier is in the representation and not in the decision rule.
