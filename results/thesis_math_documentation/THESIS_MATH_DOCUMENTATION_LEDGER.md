# Thesis math documentation ledger

> **Documentation/planning only.** No model trained, no experiment run, no thesis `.tex`
> edited, no experiment artifact modified or overwritten. This ledger and its companion files
> (`thesis_math_snippets.tex`, `notation_table.tex`, `chapter_math_placement_plan.csv`,
> `math_overclaim_audit.md`) collect every formula/notation needed and where it should go.
> Scope of all math: **window-level, digital-domain, white-box** evaluation on processed CSI
> tensors; safety-proxy metrics; not clinical, certified, or over-the-air.

## 1. Executive summary

The thesis (chapters 1–7, `thesis-overleaf-local/extracted/`) is **structurally complete in prose
but contains zero LaTeX equations** — every chapter that needs math already has the right *section*
for it (Ch2 OFDM/CSI estimation; Ch3 dataset + threat model; Ch4 FGSM/PGD/metrics; Ch5 safety-proxy
framework; Ch6 adversarial training + defenses; Ch7 analysis/limitations). This package supplies
**41 numbered formulas across 4 layers**, a master **notation table** (Eqs. cross-referenced), a
**chapter placement plan**, and an **overclaim audit**. All numeric constants (tensor shape
`1×250×90`, PGD steps 10 / α=ε/6, ε-sweep grid, λ_motion=1.0, fall weight 3, guard 0.70/0.65,
SafetyScore weights, n_f=45) are taken from committed code and committed result artifacts.

## 2. Existing math in thesis

- **Equations present:** none (0 `equation`/`align`/`$$` environments across all chapter files).
- **Math described in prose (needs formalization):** CSI-from-preamble (Ch1/Ch2), OFDM/CSI
  estimation (Ch2), white-box attack formulation + FGSM + PGD + perturbation budgets + standard
  robustness metrics (Ch4), error→safety-proxy mapping (Ch5), adversarial-training objective +
  FGSM-defense baseline + recovery metrics (Ch6).
- **Already careful in prose (preserve):** Ch3 "Formal Threat Model … digital-domain and white-box";
  Ch5 "Safety-Proxy Interpretation Boundaries / What This Chapter Does Not Claim". The added math must
  inherit these qualifications (see `math_overclaim_audit.md`).

## 3. Missing math by layer

- **Layer 1 (CSI/signal, Ch2–3):** OFDM rx model, CSI estimate, amplitude/phase, CSI tensor, processed
  window `x_i∈ℝ^{1×250×90}`, dataset `D`, normalization statement, perturbation-domain clarification.
- **Layer 2 (classifier/attacks, Ch3–4):** logits/softmax/argmax, CE, FGSM, PGD (with steps/α), ε-sweep
  `R_f(ε)`, collapse-ε thresholds, fall-weighted CE.
- **Layer 3 (safety/defenses, Ch5–6):** binary fall-alert reduction + confusion counts; recall/miss/FFA/
  FFAR/spec/PPV/F1/macro-F1; class-normalized false alarms; Variant D loss; **Variant E motion
  hard-negative loss**; logit-margin geometry; future margin loss; selection-v2 guard + SafetyScore + NFAB.
- **Layer 4 (decision/stats, Ch7):** Pareto dominance; cost-sensitive `Cost`; Wilson interval; val→test
  gaps; ECE/Brier/NLL; stronger-PGD monotonicity screen; seed-44 pre-registration.

## 4. Full formula ledger

All formulas are written, with unique labels, in **`thesis_math_snippets.tex`**. Index by label:

| Layer | Topic | Labels |
|---|---|---|
| 1 | OFDM rx; CSI estimate; polar; tensor; window; dataset; normalization; perturb domain | `eq:ofdm-rx`, `eq:csi-estimate`, `eq:csi-polar`, `eq:csi-tensor`, `eq:processed-window`, `eq:dataset`, `eq:normalization`, `eq:perturb-domain` |
| 2 | logits/softmax/argmax; CE; FWCE; FGSM; PGD; ε-sweep; collapse-ε | `eq:logits`, `eq:softmax`, `eq:argmax`, `eq:ce`, `eq:fwce`, `eq:fgsm`, `eq:pgd`, `eq:eps-sweep`, `eq:collapse-half`, `eq:collapse-zero`, `eq:collapse-drop` |
| 3 | binary reduction; confusion; metrics; macro-F1/BA; class-norm FA; Variant D; **Variant E**; margin geometry; future margin loss; selection-v2 | `eq:fall-binary`, `eq:tpfn`, `eq:fptn`, `eq:recall-miss`, `eq:ffa`, `eq:spec-ppv`, `eq:f1-macro`, `eq:balanced-acc`, `eq:class-fa`, `eq:motion-fa`, `eq:variantD-loss`, `eq:variantE-loss`, `eq:variantE-motion`, `eq:variantE-set`, `eq:margin-def`, `eq:margin-loss-future`, `eq:v2-guard`, `eq:safetyscore`, `eq:nfab` |
| 4 | Pareto; cost; Wilson; val→test; ECE/Brier/NLL; stronger-PGD | `eq:pareto`, `eq:cost`, `eq:wilson`, `eq:valtest-gap`, `eq:ece`, `eq:brier`, `eq:nll`, `eq:stronger-pgd` |

Key constants (committed): `(C,T,S)=(1,250,90)`; PGD eval `M=10, α=ε/6`, headline `ε=0.030`; train PGD
`M=7, α=ε/4`; ε-sweep `{0,0.0025,…,0.075}` (18 pts); Variant D/E multi-ε `{0.005,0.015,0.030}`;
`w_{c_f}=3`; `λ_motion=1.0`; guard `0.70/0.65` (orig `0.60/0.50`); SafetyScore `0.35/0.45/0.10/−0.10`;
`n_f`: test 45, val 44; non-fall test 455.

## 5. Notation table

See **`notation_table.tex`** (`\label{tab:notation}`) — every symbol with meaning, the equation where
it is introduced, and notes. Includes all symbols the task required (`x_i,y_i,D,f_θ,z_θ,p_θ,c_f,δ,ε,α,
TP_f,FN_f,FP_f,TN_f,R_f,NFAB,λ_motion,λ_FN,λ_FP`).

## 6. Chapter placement plan

See **`chapter_math_placement_plan.csv`** — formula/topic → layer → chapter/section → priority →
reason → source artifact → suggested label. Summary: Ch2 (CSI/OFDM), Ch3 (window/dataset/threat
model + binary reduction), Ch4 (attacks + ε-sweep + collapse-ε), Ch5 (safety-proxy metrics +
class-normalized FA), Ch6 (Variant D/E + selection-v2 + margin geometry), Ch7 (Pareto/cost/uncertainty/
calibration/stronger-PGD + future margin loss + pre-registration).

## 7. Overclaim-risk notes

See **`math_overclaim_audit.md`** (14 items + general rule). Highest-risk for math insertion:
(i) calling `δ` an RF/OTA attack; (ii) "certified"/"clinical"; (iii) over-reading recall differences at
`n_f=45`; (iv) calling selection-v2 a solved defense; (v) implying thresholding fixes residual false
alarms; (vi) presenting the future margin loss as implemented.

## 8. Top 10 must-add formulas (highest value, lowest risk)

1. Perturbation-domain clarification `eq:perturb-domain` (Ch3) — anchors the central non-claim.
2. Processed window + dataset `eq:processed-window`,`eq:dataset` (Ch3) — defines `x_i`, `D`, `K=7`.
3. Logits/softmax/argmax `eq:logits`–`eq:argmax` (Ch4) — classifier.
4. Cross-entropy `eq:ce` (Ch4) — attack objective.
5. FGSM `eq:fgsm` (Ch4).
6. PGD `eq:pgd` (Ch4) with steps=10, α=ε/6.
7. Binary fall-alert reduction + confusion `eq:fall-binary`,`eq:tpfn`,`eq:fptn` (Ch5).
8. Safety-proxy metrics `eq:recall-miss`,`eq:ffa`,`eq:spec-ppv`,`eq:f1-macro` (Ch5).
9. Fall-weighted CE `eq:fwce` + Variant E loss `eq:variantE-loss`,`eq:variantE-motion`,`eq:variantE-set` (Ch6) — the novel defense.
10. Wilson interval `eq:wilson` (Ch7) — the guardrail against recall overclaim at `n_f=45`.

## 9. Top 10 should-add formulas

1. OFDM rx model `eq:ofdm-rx` + CSI estimate `eq:csi-estimate` (Ch2).
2. CSI amplitude/phase `eq:csi-polar` (Ch2).
3. ε-sweep `eq:eps-sweep` + collapse-ε `eq:collapse-half` (Ch4).
4. Class-normalized false alarms `eq:class-fa`,`eq:motion-fa` (Ch5).
5. Variant D loss `eq:variantD-loss` (Ch6).
6. selection-v2 guard + SafetyScore + NFAB `eq:v2-guard`,`eq:safetyscore`,`eq:nfab` (Ch6).
7. Logit-margin geometry `eq:margin-def` (Ch6).
8. Pareto dominance `eq:pareto` (Ch7).
9. Cost-sensitive analysis `eq:cost` (Ch7).
10. Stronger-PGD monotonicity `eq:stronger-pgd` (Ch7).

## 10. Optional advanced formulas

- CSI tensor `eq:csi-tensor`, normalization `eq:normalization`, balanced accuracy `eq:balanced-acc`.
- Val→test gaps `eq:valtest-gap`; calibration ECE/Brier/NLL `eq:ece`–`eq:nll`.
- Future-work margin loss `eq:margin-loss-future` (Ch7, clearly labeled future work).
- Drop-threshold collapse-ε `eq:collapse-drop`; zero-recall collapse-ε `eq:collapse-zero`.

## 11. Exact next prompt (for inserting formulas into the thesis, later)

```
Insert the MUST-ADD math (Top 10 in THESIS_MATH_DOCUMENTATION_LEDGER.md §8) into the thesis,
ONE CHAPTER AT A TIME, starting with Chapter 4 (FGSM/PGD).

Constraints:
- Use the exact snippets and labels from results/thesis_math_documentation/thesis_math_snippets.tex
  and the notation from notation_table.tex; do not change notation between chapters.
- Insert into the existing sections named in chapter_math_placement_plan.csv; do not restructure chapters.
- Add the scope tag ("window-level, digital-domain, white-box; safety-proxy; not clinical/certified/OTA")
  in surrounding prose per math_overclaim_audit.md; do not introduce any avoided claim.
- Do NOT invent citations; keep "% citation needed" markers where present and ask me to supply refs.
- Edit only the specified chapter .tex file in thesis-overleaf-local; show a diff for my review BEFORE
  saving; do not run experiments; do not commit until I approve.
- Verify the chapter still compiles (or, if no local LaTeX, that braces/math environments are balanced).
Begin with Chapter 4 only and stop for my review.
```
