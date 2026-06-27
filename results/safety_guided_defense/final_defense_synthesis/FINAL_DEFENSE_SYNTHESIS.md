# Final defense-line synthesis: a designed safety-proxy defense framework

> **Documentation / synthesis only.** No training, no attacks, no new seeds, no script change, no `.tex`
> edit, no artifact overwrite. Synthesizes committed evidence through commit
> `656cd50 Add Variant G G1 seed44 validation`. All numbers trace to committed reports/CSVs under
> `results/safety_guided_defense/`. Window-level, digital-domain, white-box, processed CSI tensors;
> test n=500 (45 fall windows), validation 496 (44 falls), ε=0.030. **No solved / certified / clinical /
> over-the-air claim.**

## Executive summary

The defense line is a **designed framework**, not empirical trial-and-error: each variant is motivated by a
**named failure mode**, **formalized as a mathematical training objective**, **implemented in code**, and
**then evaluated** with safety-proxy metrics. Mathematically the objectives **define, motivate, and
constrain** an intended behavior; they do **not prove** the model will behave that way. The experiments
**validate, support, or fail to support** that intended mechanism. The framework ends at **two validated
operating points** on a **safety-relevant recall / false-alarm frontier**:

- **Variant F** — the **higher-attacked-recall** margin-aware defense (two-seed validated).
- **Variant G G1** — the **lower-false-alarm** validated defense (two-seed: seed-42 design + seed-44
  STRONG VALIDATION), built by a targeted nonfall→fall hard-negative objective designed to **reduce the
  confidence inversion** that the Variant F diagnostic isolated.

---

# Mathematical Design Before Empirical Evidence

This section states the design *before* any table. Each objective below is written as the intended
mathematical behavior; the empirical sections that follow report whether the evidence supports it. The math
**defines/motivates/constrains**; it does not **prove**. The experiments **validate / support / fail to
support**.

## Notation

| symbol | meaning |
|---|---|
| $x$ | processed CSI input window |
| $y$ | true class label |
| $z_\theta(x) \in \mathbb{R}^{7}$ | model logits; $z_c(x)$ = logit of class $c$ |
| $f = 1$ | fall class index |
| $\mathcal{C} = \{0,\dots,6\}$ | all classes; $\mathcal{N} = \mathcal{C}\setminus\{f\} = \{0,2,3,4,5,6\}$ | non-fall classes |
| $\mathcal{M} = \{\text{walk}, \text{run}\} = \{2,4\}$ | motion subset of $\mathcal{N}$ |
| $x^{adv}$ | **untargeted** FGSM/PGD adversarial example (from true label $y$) |
| $x^{tgt}$ | **targeted-to-fall** adversarial example (from a non-fall window $y\in\mathcal{N}$) |
| $w_y$ | fall-weighted-CE class weight ($w_f = 3$, else $1$) |
| $s_y$ | source-class weight in the non-fall margin ($s_y$ larger for $y\in\mathcal{M}$ in Variant G) |
| $\gamma_f,\gamma_m,\gamma_t$ | margins; $\lambda_f,\lambda_m,\lambda_s,\lambda_t$ | term weights |

## Adversarial-example definitions

- **Untargeted FGSM/PGD** $x^{adv}$ *increases* the loss w.r.t. the **true** label
  ($x^{adv}=x+\epsilon\,\mathrm{sign}(\nabla_x \mathrm{CE}(z_\theta(x),y))$ for FGSM; iterated, projected for
  PGD) — it pushes the window *away* from its true class.
- **Targeted-to-fall PGD** $x^{tgt}$ uses the **opposite sign — descent on CE to the fall target $f$**
  ($x^{tgt}\!\leftarrow\!\Pi_{\|\cdot\|_\infty\le\epsilon}(x^{tgt}-\alpha\,\mathrm{sign}(\nabla\,\mathrm{CE}(z_\theta(x^{tgt}),f)))$),
  so non-fall windows are pushed **toward the fall region** — the exact worst-case directions that create
  confident false alarms.

## Objective family

$$\text{(1) Fall-weighted cross-entropy:}\qquad \mathcal{L}_{FWCE} = w_y\,\mathrm{CE}(z_\theta(x), y)$$

$$\text{(2) Fall-preservation margin:}\qquad \mathcal{L}_{fall} = \mathbb{E}_{y=f}\Big[\max\!\big(0,\ \gamma_f + \max_{c\neq f} z_c(x^{adv}) - z_f(x^{adv})\big)\Big]$$

$$\text{(3) Motion / source-weighted non-fall margin:}\qquad \mathcal{L}_{src} = \mathbb{E}_{y\in\mathcal{N}}\Big[s_y\,\max\!\big(0,\ \gamma_m + z_f(x^{adv}) - z_y(x^{adv})\big)\Big]$$

$$\text{(4) Targeted non-fall}\to\text{fall hard-negative:}\qquad \mathcal{L}_{tgt} = \mathbb{E}_{y\in\mathcal{N}}\Big[\max\!\big(0,\ \gamma_t + z_f(x^{tgt}) - z_y(x^{tgt})\big)\Big]$$

$$\text{(5) Variant F objective:}\qquad \mathcal{L}_{F} = \mathcal{L}_{FWCE} + \lambda_m\,\mathcal{L}_{motion} + \lambda_f\,\mathcal{L}_{fall}$$

$$\text{(6) Variant G objective:}\qquad \mathcal{L}_{G} = \mathcal{L}_{FWCE} + \lambda_s\,\mathcal{L}_{src} + \lambda_f\,\mathcal{L}_{fall} + \lambda_t\,\mathcal{L}_{tgt}$$

> **Math-to-code abstraction note.** This notation is a faithful abstraction of the **implemented** loss, not
> a separate formalism. In code, $\mathcal{L}_{motion}$ (Variant F) is the **walk/run-restricted special case**
> of $\mathcal{L}_{src}$ with $s_y=1$ (set $\mathcal{M}$ only); Variant G generalizes it to all $y\in\mathcal{N}$
> with $s_y>1$ for $\mathcal{M}$. Implemented values: $\lambda_s=\lambda_f=1.0$, $\lambda_t=1.0$ (G1),
> $s_{\text{walk}}=s_{\text{run}}=2.0$ (else $1.0$), $\gamma_m=\gamma_f=\gamma_t=0.5$, $w_f=3$. The expectations
> $\mathbb{E}$ are batch means over the relevant adversarial sub-batch (the 25% PGD / 25% FGSM / targeted
> sub-batches), matching `variantG_margin_terms()`.

## Expected Mechanism

Stated **before** the evidence — what each term is *designed* to do:

- **Fall-preservation margin $\mathcal{L}_{fall}$** is designed to **protect attacked fall recall** by keeping
  $z_f$ above the largest non-fall logit on adversarial true-fall windows.
- **Motion / source-weighted non-fall margin $\mathcal{L}_{src}$** is designed to **reduce walk/run→fall false
  alarms** by pushing the true motion logit above $z_f$ on adversarial non-fall windows (weighted toward
  walk/run in Variant G).
- **Targeted non-fall→fall hard-negative $\mathcal{L}_{tgt}$** is designed to **reduce the confidence
  inversion** by training *directly* against the non-fall examples that can be pushed into the fall region
  ($x^{tgt}$), lowering the model's confidence on exactly those false-alarm directions.
- **Validation-selected gates** are to be used **only after training**, and **only if** the learned
  representation has made false alarms *less overconfident* — i.e., the gate is a post-hoc readout of a
  training-time change, chosen on validation, never tuned on test.

## Math-to-Code Mapping

Each mathematical component, the mechanism it is designed to produce, where it lives in committed code, its
key hyperparameters, and the evidence checked for it.

| mathematical term | intended mechanism | script / function | key hyperparameters | evidence checked |
|---|---|---|---|---|
| $\mathcal{L}_{FWCE}$ (1) | weight missed falls more | `train_variantG_targeted_hardneg.py` (batch CE with class weights) | $w_f=3$ | clean fall recall ≥ 0.90 |
| $x^{adv}$ untargeted | adversarial training signal | `tsg.fgsm_perturb` / `tsg.pgd_perturb` | train ε{0.005,0.015,0.030}, M=7, α=ε/4 | PGD recall above FGSM floor |
| $x^{tgt}$ targeted-to-fall | worst-case nonfall→fall dirs | `targeted_fall_pgd()` (descent on CE-to-fall, **opposite sign**) | ε=0.030, M=7, α=ε/4 | pre-train sign check: median $z_f$/P(fall) ↑ on $\mathcal{N}$ |
| $\mathcal{L}_{fall}$ (2) | protect fall recall | `variantG_margin_terms()` (fall branch) | $\gamma_f=0.5$, $\lambda_f=1.0$ | PGD recall, PGD-20 durability |
| $\mathcal{L}_{src}$ (3) | cut walk/run→fall FAs | `variantG_margin_terms()` (nonfall branch) + `source_weights()` | $\gamma_m=0.5$, $\lambda_s=1.0$, $s_{\mathcal{M}}=2.0$ | walk/run→fall count |
| $\mathcal{L}_{tgt}$ (4) | reduce confidence inversion | `variantG_margin_terms()` (targeted branch) | $\gamma_t=0.5$, $\lambda_t=1.0$ (G1) | inversion gap (B−A median P(fall)) |
| source weighting $s_y$ | focus pressure on motion | `source_weights()` ($w_{wr}=2.0$ for $\mathcal{M}$) | $s_{\mathcal{M}}=2$, else 1 | ablation G2 (no weight) vs G1/G3 |
| selection-v2 checkpoint rule | clean-stable, FA-aware pick | `train_variantG_targeted_hardneg.py` (`run_full` selection) | guard acc≥0.70 ∧ mF1≥0.65; SafetyScore | validation-only selection; candidate CSV |
| validation-split export | enable val-only thresholding | `export_probability_predictions.py` (`--split val`, eval-only) | clean + PGD@0.030 per-window | val outputs distinct from test |
| validation-selected gate | post-hoc FA readout | `analyze_variantG_g1_seed44.py` (`select_threshold` → `alert_for`) | carried gate $P(f)\ge 0.19$ (val-chosen) | τ chosen on val; tested once on test |

**Reading guide:** every claim in the empirical sections below points back to a row here — the objective was
written first (this section), implemented (the code column), and only then tested (the evidence column and
the tables that follow).

---

# Empirical defense line (evidence)

Reported **after** the design. Each stage names the failure mode it addresses and the metric that validates
or fails to support the intended mechanism.

### 1. FGSM adversarial-training baseline
FGSM adversarial training hardens against the single-step attack it trains on but **collapses under
iterative PGD**: PGD@0.030 fall recall **0.089** (seed 42) / **0.044** (seed 44). The seed-44 figure (Wilson
[0.012, 0.148]) is the **same-seed recall floor**. *Mechanism check:* untargeted adversarial training alone
does not validate robustness to a stronger attack than it trains on.

### 2. Variant D — $\mathcal{L}_{FWCE}$ + adversarial mixing: recover recall, pay false alarms
Fall-weighted CE + batch-split clean/FGSM/PGD mixing + multi-ε recovers attacked recall but at heavy
false-alarm cost: seed-42 PGD recall **0.444** at FP **157** (walk/run 120); seed-44 **0.378** at FP **167**
(walk/run 116). *Mechanism check:* $\mathcal{L}_{FWCE}$ supports recall recovery but, alone, does not
constrain false alarms — the motivation for margin terms.

### 3. Variant E / selection-v2 — first non-fall penalty: FA down, recall unstable
A motion *probability* hard-negative penalty (Variant E) cut false alarms (seed-42 FP 117) but was
**selection-sensitive** (seed-43 clean collapse). selection-v2 (guard 0.70/0.65 + multi-candidate saving)
repaired clean stability but exposed **recall fragility** (seed-43 PGD recall 0.111, collapsing under
stronger PGD). *Mechanism check:* a probability penalty reduces FA *count* but does not constrain the
*margin* geometry — residual false alarms stay confident, motivating margin-based terms.

### 4. Variant F — $\mathcal{L}_F$ (motion + fall margins): two-seed validated
The two margin terms (2)+(3, with $s_y=1$) give the first stable, **two-seed validated** improvement.
Seed-42 (design): PGD recall **0.667** at FP **115**, PGD-20 **0.644**. Seed-44 (pre-registered independent
validation): PGD recall **0.622 [0.476, 0.749]** at FP **112**, walk/run **73**, PGD-20 **0.511** —
**STRONG SUPPORT**, Pareto-dominating same-seed Variant D. *Mechanism check:* the fall-preservation margin
**supports** recall; the motion margin **supports** lower FA than Variant D. **But** ~112–115 false alarms
remain — the next failure mode.

### 5. Variant F false-alarm diagnostic — confidence inversion, *not filterable*
Dedicated diagnostic: residual Variant F false alarms are **not removable by post-hoc thresholding**
(Diagnosis **C — Not filterable**) because of a **confidence inversion** — under PGD the false alarms are
*more* fall-confident than the detected true falls: seed-42 median P(fall) **0.518 (FA) vs 0.415 (true),
gap +0.103**; seed-44 **+0.121**. *Mechanism check:* the residual failure is **learned decision geometry**,
not threshold placement — formally motivating $\mathcal{L}_{tgt}$ (term 4).

### 6. Variant G seed-42 — $\mathcal{L}_G$ ($+\mathcal{L}_{tgt}$, source-weighted): mechanism, MINIMUM USEFUL
$\mathcal{L}_G$ adds the targeted hard-negative term (4) and source weighting ($s_{\mathcal{M}}=2$). Seed-42
pilot (G1/G2/G3): best setting **G1** Pareto-improves Variant F (PGD recall **0.689** vs 0.667, FP **104**
vs 115, walk/run **74** vs 80) and **reduces the inversion gap ~89%** (+0.103 → **+0.012**). The **ablation
supports the design**: the **targeted term is the active ingredient** (G3, source-weighted only, is weakest).
Honest tier: **MINIMUM USEFUL** — clears minimum-useful bars but misses the aggressive FP ≤ 90 bar, at a
small clean-accuracy cost.

### 7. Variant G G1 filterability diagnostic — *filterable enough to justify seed44*
Re-running the probe on G1: **Diagnosis A — filterable enough to justify seed44**. The near-flat inversion
(+0.012) lets a post-hoc gate reach recall ≥ 0.50 at FP ≤ 90 on seed-42 *test* (entropy ≤ 1.85 → 0.533/89;
$P(f)\ge0.26$ → 0.511/86). Strictly a **test-output probe** (optimistically biased) — its role was to
justify a **pre-registered, validation-selected** seed-44 test, not to ship a threshold.

### 8. Variant G G1 seed-44 validation — STRONG VALIDATION (lower-false-alarm point)
Pre-registered seed-44 validation; gate selected on **validation only** ($P(f)\ge0.19$). Outcome: **STRONG
VALIDATION**. Raw G1 **matches** Variant F's attacked recall (**0.600 [0.455, 0.730]** vs 0.622, overlapping
CIs) while **cutting false alarms ~42% (65 vs 112)** and walk/run→fall (**48 vs 73**), with **higher clean
accuracy (0.746 vs 0.700)**, **more durable PGD-20 (0.600 vs 0.511)**, and **reduced inversion (+0.121 →
+0.043)**. The validation-defined gate was essentially a no-op — the training-time inversion reduction
already made the *raw* operating point low-FP. *Mechanism check:* the seed-42 mechanism (lower inversion →
lower FA) **replicates on an independent seed**. This is a **large false-alarm reduction at matched recall**,
**not** strict Pareto dominance (recall ~1 fall window below F, not significant).

---

## Final comparison table

Test, ε=0.030. Inversion gap = median P(fall) of false alarms − of detected true falls (smaller = less
inverted). `—` = not computed for that row. *(Presented after the mathematical design and code mapping above.)*

| Model | clean acc | clean mF1 | clean fall recall | PGD recall | PGD FP | walk/run→fall | PGD-20 recall | inversion gap | decision label |
|---|---|---|---|---|---|---|---|---|---|
| FGSM defense — seed42 | 0.834 | 0.814 | 0.911 | 0.089 | 54 | 39 | — | — | weak-PGD baseline |
| Variant D — seed42 | 0.746 | 0.700 | 1.000 | 0.444 | 157 | 120 | — | — | high recall / high FA |
| **Variant F — seed42** | 0.734 | 0.690 | 0.978 | **0.667** | 115 | 80 | 0.644 | +0.103 | margin-aware (design) |
| **Variant G G1 — seed42** | 0.716 | 0.670 | 0.978 | **0.689** | 104 | 74 | 0.622 | **+0.012** | MINIMUM USEFUL |
| **Variant F — seed44** | 0.700 | 0.658 | 0.978 | **0.622** | 112 | 73 | 0.511 | +0.121 | STRONG SUPPORT (F) |
| **Variant G G1 — seed44** | 0.746 | 0.692 | 0.956 | **0.600** | **65** | **48** | **0.600** | **+0.043** | STRONG VALIDATION |
| Variant D — seed44 | 0.722 | — | 0.978 | 0.378 | 167 | 116 | — | — | high recall / high FA |
| FGSM defense — seed44 | 0.928 | — | 1.000 | 0.044 | 42 | 25 | — | — | recall floor |

**Two validated points:** **Variant F** = higher attacked recall (0.667/0.622) at FP ~112–115; **Variant G
G1** = lower-false-alarm point (seed-44 FP 65 vs 112, walk/run 48 vs 73) at recall ≈ F within CI, with better
clean accuracy and PGD-20 and a much smaller inversion gap. Both seeds agree on the direction.

---

# Interpretation (thesis-safe conclusions)

1. **Two validated operating points, not one dominant solution** — both two-seed validated on a
   safety-relevant recall/false-alarm frontier.
2. **Variant F is the higher-recall reference defense** (attacked recall 0.667 / 0.622).
3. **Variant G G1 is the lower-false-alarm validated defense** (seed-44 FP 65 vs 112; walk/run 48 vs 73),
   produced by an objective ($\mathcal{L}_{tgt}$) **designed to** reduce the confidence inversion.
4. **Not strict Pareto dominance on seed 44** — G1's PGD recall (0.600) is ~1 fall window below Variant F
   (0.622) with overlapping Wilson intervals; the win is **lower false alarms at matched recall**, not
   dominance. Stated explicitly to avoid overclaiming.
5. **Main contribution (methodological):** a measurable failure mode (the confidence inversion) can be
   **diagnosed, formalized as a training objective, implemented, and then validated** — moving the classifier
   along a **safety-relevant** recall/false-alarm frontier, with the movement **replicating across seeds**.
   *(We deliberately say "safety-relevant," not "clinically meaningful": no clinical claim is made.)*
6. **Scope.** All results are **window-level, processed-CSI-tensor, digital-domain, white-box** evaluations
   with quantified uncertainty (Wilson, n_f=45). **Not** solved, **not** certified, **not** clinical, **not**
   over-the-air.

## How to report this (one paragraph, thesis-safe)

> On processed WiFi-CSI windows under white-box PGD@0.030, a designed sequence of safety-proxy-aware
> adversarial-training objectives moves a fall/activity classifier along a safety-relevant recall /
> false-alarm frontier. A margin-aware objective (**Variant F**, $\mathcal{L}_F$) recovers attacked fall
> recall to 0.62–0.67 with two-seed validation but leaves ~112–115 false fall alarms whose
> confidence-inversion geometry makes them un-filterable. A targeted hard-negative objective (**Variant G
> G1**, $\mathcal{L}_G$), **designed from that diagnostic** to reduce the inversion, on an independent
> pre-registered seed **cuts false alarms ~42% (112 → 65) at matched attacked recall** with higher clean
> accuracy and more durable recall. The two defenses are reported as **two validated operating points** —
> Variant F (higher recall) and Variant G G1 (lower false alarms) — not a single dominant model. These are
> window-level, digital-domain, white-box trade-offs, not solved/certified/clinical/over-the-air robustness.

---

## Artifacts referenced (all committed)
- FGSM/D/E/selection-v2/F: `defense_line_synthesis/DEFENSE_LINE_SYNTHESIS_MEMO.md`, `seed42/`, `seed44/`,
  `variantE_motion_hard_negative/`, `variantF_motion_margin/seed42|seed44/`.
- Math package: `thesis_math_documentation/thesis_math_snippets.tex` (+ Variant G math-to-code spec
  `variantG_design_memo/VARIANT_G_MATH_TO_CODE_SPEC.md`).
- F diagnostic: `variantF_false_alarm_diagnostic/VARIANT_F_FALSE_ALARM_DIAGNOSTIC.md`.
- G seed42 pilot + ablation: `variantG_targeted_hardneg/seed42/VARIANT_G_SEED42_PILOT_REPORT.md`, `analysis/`.
- G filterability: `variantG_targeted_hardneg/seed42/G1_FILTERABILITY_DIAGNOSTIC.md`.
- G seed44 validation: `variantG_targeted_hardneg/seed44/VARIANT_G_G1_SEED44_VALIDATION_REPORT.md`.

### Scope reminder
Synthesis only — no training/attacks/new seeds/script change/`.tex` edit/artifact overwrite. Window-level,
processed CSI tensor, digital-domain, white-box; **not** solved, **not** certified, **not** clinical,
**not** over-the-air.
