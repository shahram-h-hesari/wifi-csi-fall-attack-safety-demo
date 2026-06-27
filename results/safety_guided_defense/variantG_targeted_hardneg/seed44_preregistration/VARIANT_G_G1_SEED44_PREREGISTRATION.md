# Variant G G1 — seed-44 validation pre-registration

> **Pre-registration only — frozen BEFORE any seed-44 run.** No seed-44 training, no attacks, no script
> change, no `.tex` edit, no artifact overwrite. This document fixes the frozen model, the allowed gate
> families, the validation-only threshold-selection rule, the test-reporting protocol, and the
> success/failure categories **before** seed-44 outputs are seen, so the seed-44 result is an honest
> out-of-sample test rather than a tuned one. Window-level, digital-domain, white-box; test n=500 (45 fall
> windows), ε=0.030. **No solved / certified / clinical / over-the-air claim.**

## Why this validation

The committed seed-42 evidence says: Variant G **G1** (targeted nonfall→fall hard-negative + source-class-
weighted motion margin on the frozen Variant F base) **Pareto-improves** Variant F (PGD recall 0.689 vs
0.667, FP 104 vs 115, walk/run 74 vs 80) and **reduces the confidence inversion ~89%** (median P(fall)
gap +0.103 → +0.012). The committed **G1 filterability diagnostic** then found **Decision A — filterable
enough to justify seed44**: on seed-42 *test* outputs an entropy gate (entropy ≤ 1.85) reaches recall
0.533 / FP 89 and a probability gate (P(fall) ≥ 0.26) reaches recall 0.511 / FP 86, with clean fall recall
preserved (0.978). **Those seed-42 test thresholds are diagnostic only and optimistically biased.** This
pre-registration defines how to test, honestly and once, whether (a) the raw G1 operating point replicates
on an independent seed and (b) a **validation-selected** gate transfers to seed-44 test.

## Committed seed-44 references (anchors; from prior committed reports)

| Model (seed 44, test, ε=0.030) | clean acc | clean macro-F1 | clean fall recall | PGD recall [Wilson] | PGD FP | walk/run→fall | wr logit margin | PGD-20 |
|---|---|---|---|---|---|---|---|---|
| FGSM defense (floor) | 0.928 | — | 1.000 | 0.044 [0.012, 0.148] | 42 | 25 | — | — |
| Variant D (FP ref) | 0.722 | — | 0.978 | 0.378 [0.251, 0.524] | 167 | 116 | 1.733 | — |
| **Variant F v2safety** | **0.700** | **0.658** | **0.978** | **0.622 [0.476, 0.749]** | **112** | **73** | **0.961** | **0.511** |

G1 seed-42 v2safety (design, for context only — **not** a seed-44 target): clean acc 0.716, macro-F1
0.670, PGD recall 0.689, FP 104, walk/run 74, PGD-20 0.622, inversion gap +0.012.

---

## 1. Frozen model

- **Variant G setting: G1 only** — λ_s = 1.0, λ_f = 1.0, **λ_t = 1.0**, **w_wr = 2.0**, γ_m = γ_f = γ_t = 0.5,
  fall weight 3 (exactly the committed `SETTINGS["G1"]`).
- **Seed: 44 only.** No seed 42 re-run, no seed 45/46.
- **Same Variant G loss** as committed (`L_FWCE + λ_s·w·motion-margin[adv nonfall] + λ_f·fall-margin[adv fall]
  + λ_t·w·targeted-margin[targeted nonfall]`). **Unchanged.**
- **Same class indices** (FALL=1, NUM=7, WALK=2, RUN=4, nonfall {0,2,3,4,5,6}) — asserted at startup.
- **Same targeted-PGD sign** (descent on CE-to-fall; the mandatory pre-train sign check must pass).
- **Same source weighting** (w_walk = w_run = 2.0, w_other = 1.0).
- **Same training recipe** — batch-split 50/25/25 clean/FGSM/PGD, train ε {0.005,0.015,0.030}, train PGD/
  targeted M=7 α=ε/4, Adam lr 1e-3, bs 64, epochs 70 / patience 15 / min 35, selection-v2 guard
  (0.70/0.65) + candidates v2safety/v2maxrec/v2lowFA/v2macroF1.
- **No G2/G3, no extra settings, no tuning after seeing seed-44 results.** The **only** permitted code change
  is relaxing the G-script seed gate from `args.seed != 42` to allow seed 44 (exactly as Variant F relaxed
  its gate for its own seed-44 validation) — **loss / λ / weights / margins / guard / sign unchanged.**
- **Primary checkpoint:** the **v2safety** candidate selected by the frozen selection-v2 rule (validation-only).

## 2. Gate family (the ONLY allowed post-hoc gates)

The seed-42 diagnostic identified exactly two candidate families; no other rule search is permitted:

- **Entropy gate:** `alert = (predicted_class == fall) AND (entropy(x) <= tau_h)`
- **Probability gate:** `alert = (predicted_class == fall) AND (P(fall | x) >= tau_p)`

**No** combined rules, **no** margin gate, **no** multi-threshold search beyond a single τ per family. Exactly
**one** threshold per family is selected on validation; at most one gate (the better of the two on validation,
§3) is carried to test, alongside the raw (ungated) G1.

## 3. Threshold-selection rule — VALIDATION DATA ONLY

The seed-44 **test set must not be used to choose τ.** Procedure, fixed in advance:

1. Train frozen G1 on seed 44; pick the v2safety checkpoint by the frozen selection-v2 rule (validation-only).
2. Generate **per-window VALIDATION outputs** (clean + PGD@0.030) for that checkpoint — probabilities, logits,
   entropy, P(fall). (Implementation note: this requires a validation-split per-window export; it is an
   eval-only addition, no training/loss/selection change.)
3. For **each** family, sweep its single threshold over the validation outputs and keep the **feasible set** —
   thresholds satisfying ALL of:
   - validation PGD fall recall **≥ 0.50**
   - validation PGD FP **≤ 90**
   - validation clean fall recall **≥ 0.90**
   - validation clean FP **≤ raw-G1 validation clean FP + 5** (small tolerance; the gate must not create clean
     false alarms)
4. **Pick τ within the feasible set** by: highest validation binary-F1; tie-break lowest validation PGD FP
   among recall ≥ 0.50. Do this independently for the entropy family and the probability family.
5. **Choose ONE gate to carry to test:** the family whose chosen τ has the higher validation F1 (tie-break
   lower validation FP). Record both families' chosen τ and metrics regardless.
6. **If neither family has a non-empty feasible set on validation** (no τ meets recall ≥ 0.50 AND FP ≤ 90):
   mark **gated validation = FAILED**, carry **no gate** to test, and report **raw G1 only** on seed-44 test.
   Do **not** relax the rule or force a gate.

τ is frozen at the end of step 5 (or step 6) — **before** any seed-44 test evaluation.

## 4. Test reporting (once, after τ is frozen)

Evaluate **once** on the seed-44 **test** set and report side by side:

- **raw G1 v2safety** (ungated),
- **gated G1** (validation-selected entropy or probability τ; or "no gate" if §3 step 6),
- **Variant F seed44** v2safety (0.622 / FP 112 / wr 73 / PGD-20 0.511),
- **Variant D seed44** (0.378 / FP 167 / wr 116),
- **FGSM defense seed44 floor** (0.044 / FP 42).

Report for raw and gated G1: clean acc / macro-F1 / clean fall recall / clean FP; PGD@0.030 recall [Wilson]
/ FP / walk/run→fall / specificity / precision / F1; PGD-20 recall and ratio; confidence-inversion table vs
Variant F seed44; false-alarm source anatomy; 18-ε sweeps + collapse-ε.

## 5. Success criteria (frozen)

Assign exactly one category (evaluated on the seed-44 **test** set; "gated" = the §3 gate if one was carried,
else raw).

**STRONG VALIDATION** — all of:
- clean guard holds: acc ≥ 0.70 **and** macro-F1 ≥ 0.65
- clean fall recall ≥ 0.90
- raw **or** gated PGD recall ≥ 0.50
- gated PGD FP ≤ 90
- walk/run→fall ≤ 60
- PGD-20 recall ≥ 50% of PGD-10
- confidence inversion reduced vs Variant F seed44 (G1 median-P(fall) B−A gap < Variant F seed44's gap)
- no gradient-masking red flag (recall non-increasing PGD-10 → PGD-20)

**VALIDATION SUPPORT** — all of:
- clean guard holds (acc ≥ 0.70 and macro-F1 ≥ 0.65)
- clean fall recall ≥ 0.90
- raw **or** gated PGD recall ≥ 0.50
- gated PGD FP **< 112** (Variant F seed44 FP)
- walk/run→fall **< 73** (Variant F seed44 walk/run)
- PGD-20 recall > 0
- confidence inversion reduced vs Variant F seed44

**WEAK / TRADE-OFF** — any of:
- recall improves **or** FP improves, but not both (no Pareto move vs Variant F seed44)
- the gate reduces FP only by pushing PGD recall below 0.50
- clean guard barely holds **or** the clean-accuracy cost is high (acc materially below Variant F's 0.700)

**REJECT** — any of:
- clean guard fails (acc < 0.70 or macro-F1 < 0.65)
- clean fall recall < 0.90
- PGD recall < 0.50 (raw and gated)
- FP not improved over Variant F seed44 (≥ 112)
- confidence inversion not reduced vs Variant F seed44
- PGD-20 collapses (≈ 0 or recall increases PGD-10 → PGD-20)
- the validation-selected threshold fails badly on test (e.g., gated test recall ≪ validation recall, a
  val→test selection failure)

Precedence: REJECT conditions are checked first; then STRONG VALIDATION; then VALIDATION SUPPORT; else
WEAK / TRADE-OFF.

## 6. Required outputs after the future run

- training metadata (`metadata/seed44_variantG_G1_metadata.json`: seed, λ/weights, git commit, command,
  env, split sizes, selected epochs, `test_set_used:false`)
- selected-checkpoint metadata + selection-candidates CSV (validation-only)
- **validation threshold-selection CSV** (both families' sweep over validation outputs + the feasible set +
  chosen τ)
- raw and gated **test** safety metrics (clean / PGD@0.030 / PGD-20)
- clean metrics (acc, macro-F1, clean fall recall, clean FP, clean walk/run→fall, clean precision/specificity)
- PGD@0.030 metrics (recall + Wilson, FP, walk/run, specificity, precision, F1)
- PGD-20 metrics (recall, ratio, masking screen)
- 18-ε FGSM + PGD sweeps + collapse-ε
- per-window probability/logit exports (validation + test; clean / FGSM / PGD-10 / PGD-20)
- confidence-inversion table (detected falls vs FAs; G1 seed44 vs Variant F seed44)
- false-alarm source anatomy (by source class, PGD@0.030)
- Wilson intervals (PGD-10 and PGD-20 recall, n_f = 45)
- Pareto / FN:FP cost figure (raw G1, gated G1, Variant F, Variant D, FGSM floor)
- final **seed-44 validation report** (`VARIANT_G_G1_SEED44_VALIDATION_REPORT.md`) with one assigned category.

## 7. Thesis-promotion rule

- **Variant F remains the final validated implemented defense** until G1 passes this seed-44 validation.
- **G1 can challenge Variant F only if the validation-defined gate transfers to seed-44 test** — i.e., the
  category is **STRONG VALIDATION** or **VALIDATION SUPPORT** with a genuine Pareto move (recall ≥ Variant F
  *and* FP < Variant F) and reduced inversion. A WEAK/TRADE-OFF or REJECT outcome keeps Variant F final and
  records Variant G as a committed **mechanistic positive** (Pareto move + ~89% inversion cut on seed 42),
  not the final defense.
- **Seed-42 diagnostic thresholds cannot be reported as final thresholds** — only a validation-selected,
  seed-44-tested gate may be reported, and even then as a window-level digital-domain white-box operating
  point.
- **No solved / certified / clinical / over-the-air / deployment-readiness claim** is made under any outcome.

## 8. Exact next prompt (run ONLY after this pre-registration is approved + committed)

> Run the seed-44 validation of frozen Variant G **G1**, per
> `results/safety_guided_defense/variantG_targeted_hardneg/seed44_preregistration/VARIANT_G_G1_SEED44_PREREGISTRATION.md`.
> Seed 44 ONLY; G1 ONLY; do not run G2/G3, do not run seeds 45–46, do not change the loss / class indices /
> targeted-PGD sign / source weighting / selection-v2 rule (the only permitted code change is relaxing the
> G-script seed gate to allow seed 44). Steps: (1) train frozen G1 on seed 44; run the mandatory targeted-PGD
> sign check first. (2) Select the v2safety checkpoint by the frozen selection-v2 rule (validation only). (3)
> Export per-window VALIDATION probabilities (clean + PGD@0.030); select τ for the entropy gate and the
> probability gate using the §3 feasible-set rule on validation ONLY; freeze the single carried gate; if
> neither family is feasible, carry no gate. (4) Export seed-44 TEST probabilities/logits and run the eval
> suite (clean, FGSM@0.030, PGD@0.030, 18-ε FGSM+PGD sweeps, PGD-20, probability/logit export). (5) Compute
> raw + gated test metrics, confidence-inversion vs Variant F seed44, source anatomy, Wilson intervals,
> Pareto/cost figure. (6) Assign exactly one category (STRONG VALIDATION / VALIDATION SUPPORT / WEAK-TRADE-OFF
> / REJECT) per §5, write `VARIANT_G_G1_SEED44_VALIDATION_REPORT.md`, and do NOT commit until I review. Do
> NOT edit thesis/Overleaf `.tex`. Do NOT use the seed-44 test set to choose τ.

---

### Scope reminder
Pre-registration only — no seed-44 run, no training, no attacks, no script change, no `.tex` edit, no
artifact overwrite. Window-level, digital-domain, white-box; **not** solved, **not** certified, **not**
clinical, **not** over-the-air.
