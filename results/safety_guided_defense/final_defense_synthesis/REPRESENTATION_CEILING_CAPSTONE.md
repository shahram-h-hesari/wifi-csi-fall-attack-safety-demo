# Capstone synthesis — the adversarial fall‑detection frontier is a representation‑level ceiling

> **Analysis & synthesis only.** Consolidates the committed safety‑proxy defense line (Variants E→H,
> Option A/B, DS‑SGE), the paper‑driven BASAT pilots (TRADES / GAIRAT / SAT), and the BiLSTM representation
> pivot into one conclusion. Window‑level, digital‑domain, white‑box, processed UT‑HAR CSI; val 496 (44 fall /
> 452 non‑fall), test 500 (45 fall / 455 non‑fall); ε = 0.030. **No certified / clinical / deployment / OTA
> claim. The TEST split was never used for any selection or go/no‑go in the BASAT + pivot work; all decisions
> were made on validation.** Extends `FINAL_DEFENSE_LINE_CLOSURE.md`; supersedes nothing prior (adds the
> new‑objective and representation evidence the prior closure said was still needed).

---

## 1. Executive conclusion

The safety objective — **maximize adversarial fall recall s.t. false‑alarm rate ≤ 10%** (operationally, on
test: **TP ≥ 36/45 and FP ≤ 45/455** under PGD@0.03) — is **not reached by any method tried**, and the
evidence now localizes *why*: the bottleneck is the **PGD‑conditional separability of the learned fall
representation**, and it is **representation‑spanning**, not specific to one model or one training trick.

- **Every model classifies clean falls almost perfectly** (clean AUROC of P(fall) ≈ 0.99).
- **PGD@0.03 collapses that separability** to ≈ 0.69–0.88 AUROC depending on model — and *no* intervention
  pushes it into the region needed for (recall ≥ 0.80, FAR ≤ 0.10).
- **Six training‑time interventions on a LeNet CNN all stall at AUROC ≈ 0.876.**
- **A representation change to a BiLSTM — higher clean headroom — is *worse* under PGD (AUROC ≈ 0.73), not
  better.**

The defensible thesis result: *paper‑driven boundary‑aware / selective adversarial training and a temporal
representation change both fail to reach the target safety region on UT‑HAR at ε=0.030; the fall↔locomotion
overlap under L∞ PGD is a representation‑level frontier ceiling that spans a CNN and an RNN.*

---

## 2. Methodology — why the primary endpoint is threshold‑free

At n_fall = 44 (val) / 45 (test), a single fall flips recall by ~2.2 points and the 95% Wilson CI on a recall
of 0.60 is ≈ [0.46, 0.73] (±14 pts). Operating‑point numbers (argmax recall / FAR) are therefore too noisy
to adjudicate "did the frontier move." The primary endpoint is the **threshold‑free AUROC of P(fall) under
PGD‑10 (α=ε/6, ε=0.030)** — it uses all 44×452 ranked pairs, is not gameable by operating‑point selection,
and is compared with a **paired bootstrap on the same validation windows**. Operating‑point metrics
(recall@FAR≤10%, argmax recall/FAR) are reported as secondary, always with their CIs. Selection and all
go/no‑go decisions are validation‑only; the go/no‑go bar is the **best** G1 LeNet checkpoint
(val PGD AUROC **0.876**, recall@FAR≤10% **0.477**), not the matched selector, so the baseline cannot be gamed.

---

## 3. The complete evidence chain (validation PGD unless noted)

| approach | mechanism (independent variable) | clean AUROC | **PGD AUROC** of P(fall) | recall@FAR≤10% | verdict |
|---|---|---|---|---|---|
| **G1 LeNet** (baseline) | fall‑weighted AT + margins + targeted PGD | 0.99 | **0.876** | 0.477 | reference frontier |
| DS‑SGE gate | post‑hoc dual‑specialist combination | — | ~0.81 (recall specialist) | — | NO — specialists nested |
| Option B | adaptive Lagrangian dual‑tail (FAR‑constrained) | — | 0.840 | ~0.34 | NO |
| BASAT‑1 TRADES (β=3) | clean/adv fall‑prob consistency | 0.99 | 0.876 | 0.477 | NO‑GO |
| BASAT‑1 TRADES (β=6) | "" stronger dose | 0.99 | 0.869 | 0.364 | NO‑GO |
| BASAT‑2 GAIRAT | boundary‑margin instance reweighting | 0.99 | 0.871 | 0.341 | NO‑GO |
| BASAT‑3 SAT | calibrated asymmetric adv selection | 0.99 | 0.873 | 0.523\* | NO‑GO |
| **BiLSTM G1** | **representation change (CNN→RNN)** | **0.99** | **0.726** | ~0.00 | **NO‑GO (H0)** — worse |

\* SAT recall@FAR≤10% 0.523 is a 2‑fall (n=44) operating‑point blip; its threshold‑free AUROC (0.873) is
statistically identical to G1 (paired Δ = −0.003), so it is not an envelope gain and is not claimed.

**Paired best‑vs‑best AUROC differences vs G1 (0.876), same val windows:** TRADES β3 +0.0004
[−0.024, +0.026]; GAIRAT −0.004 [−0.036, +0.027]; SAT −0.003 [−0.025, +0.020]; BiLSTM −0.150 (CIs disjoint).
Only the BiLSTM differs significantly — and in the wrong direction.

**Validated test operating points (prior closure, for grounding):** Variant F PGD recall 0.622 / FP 112
(24.6%); **G1 PGD recall 0.600 / FP 65 (14.3%)**, PGD‑20 0.600. Target needs FP ≤ 45 at recall ≥ 0.80
(TP ≥ 36) — i.e. simultaneously **+9 true positives and −20 false positives** under an adaptive attacker.

---

## 4. Three independent diagnostics converge on "representation‑level"

1. **Nested specialists (DS‑SGE Stage A).** A recall specialist and a FAR specialist trained to opposite
   errors are *nested, not complementary*: on test PGD, `missed_by_R_only = 0` and
   `argmax_union_recall = recall_R = 0.689` exactly. Every fall the FAR model catches, the recall model also
   catches — so a convex gate can only interpolate the *same* ROC, never dominate it. Output combination is
   ruled out.

2. **Inseparable attacked score distributions (Option B threshold sweep).** Across the entire P(fall)
   threshold range on test PGD, no threshold reaches TP ≥ 37 ∧ FP ≤ 45 on any checkpoint; the attacked
   fall‑P(fall) median (~0.27) sits inside the non‑fall‑P(fall) upper tail (q3 ~0.15). Thresholding/checkpoint
   selection is ruled out.

3. **Clean→PGD separability collapse, across models.** Clean AUROC ≈ 0.99 everywhere; PGD AUROC ranges
   0.69–0.88 and is *invariant* to six LeNet training interventions (~0.876) and *degraded* by the recurrent
   representation (0.73). The barrier is in how each representation places fall windows relative to the
   fall↔locomotion boundary under perturbation — not in the loss, the gate, the threshold, or model capacity.

---

## 5. The negatives are informative, not null — what each mechanism *did*

- **TRADES consistency** is real and dose‑dependent: at the matched selector the val PGD AUROC rises
  0.808 → 0.824 → 0.847 across G1/β3/β6 (paired +0.039 at β=6, CI excludes 0). It *tightens the weakest
  checkpoint toward the envelope* but cannot expand the envelope.
- **GAIRAT** correctly up‑weighted boundary‑adjacent fall adversarials (~1.4×) — the most targeted lever —
  and still did not expand the envelope.
- **SAT** asymmetric filtering protected 100 % of falls; the converged, temperature‑sharpened model had
  almost nothing to filter (keep‑rate → 1.0), i.e. "harmful collapsed adversarials" are a cold‑model
  phenomenon, so SAT ≈ G1 at the selected checkpoints.
- **BiLSTM** trained stably from a clean‑qualified init with gradient clipping (it would not converge
  from scratch under the adversarial recipe — a documented non‑convergence, not a result), held the clean
  guard, lifted PGD fall recall above the undefended BiLSTM (~0.004 → ~0.05), but its PGD separability is
  *below* LeNet's — the L∞ CSI perturbation appears to compound through the temporal recurrence.

---

## 6. The representation result in full (pre‑registration H0)

The pre‑registered hypothesis (a higher‑clean‑headroom BiLSTM, under the identical frozen G1 objective,
advances the frontier beyond G1 LeNet) is **rejected**. The undefended BiLSTM collapses under PGD like every
undefended backbone (PGD fall recall ≈ 0.004), and the *defended* BiLSTM, despite identical clean
separability (0.99) and higher clean accuracy headroom, reaches only PGD AUROC 0.726 with recall@FAR≤10% ≈ 0
— **less robust than the defended LeNet**. Capacity / temporal modeling is not the missing ingredient;
the null (representation‑invariant barrier) is supported and, for the RNN, exceeded (it is worse).

---

## 7. Committee‑grade interpretation and the claimable result

- **Is this just heuristics that didn't work?** No. The endpoint is threshold‑free with paired statistics;
  the mechanisms are published methods (TRADES/MART/GAIRAT/SAT) adapted to a safety‑asymmetric WiFi‑CSI
  objective; the conclusion is supported by three independent diagnostics and a controlled representation
  swap. Each mechanism's *intended effect was verified to occur* — they simply do not move the envelope.
- **What is the claim?** A bounded, falsifiable negative + characterization: *on UT‑HAR at ε=0.030, the
  adversarial fall‑recall / false‑alarm frontier is limited by representation‑level fall↔locomotion overlap
  under L∞ PGD; it is not crossed by output gating, constrained optimization, boundary‑consistency,
  boundary‑reweighting, or selective adversarial training on a CNN, nor by a temporal representation with
  more clean capacity.*
- **No test peeking, no overclaiming.** All BASAT + pivot decisions are validation‑only; test remains
  locked. No certified/clinical/OTA/solved claim.

---

## 8. Scope, limitations, honest future directions

- **Seed 42** for the BASAT + pivot pilots (the prior F/G operating points are two‑seed validated). A
  single‑seed negative is strengthened by the threshold‑free endpoint and the consistency across six
  interventions, but multi‑seed confirmation of the BASAT/BiLSTM negatives is future work.
- **Not a universal impossibility proof.** Two representations (LeNet CNN, BiLSTM) and six interventions do
  not reach the target; this does not prove *no* architecture/training regime can. Untested same‑family
  options (defended ResNet/GRU/transformer — clean checkpoints exist) and threat‑model characterization
  (defended frontier vs ε sweep — does the target hold at ε ≤ 0.01?) are the natural next probes if the
  thesis wants to bound *where* the barrier begins rather than only that it exists at 0.030.
- **Clean‑guard val→test generalization gap** (observed for Option B, and to watch for any future positive):
  validation guard passing did not always transfer to test; any future GO must re‑confirm on locked test.

---

## 9. Artifact index (provenance)

- Baseline + go/no‑go bar: `boundary_aware_selective_at/seed42/g1_baseline_val_frontier.{json,md}` (script
  `scripts/compute_g1_baseline_val_frontier.py`).
- BASAT Stage 1 (TRADES): `boundary_aware_selective_at/seed42/{beta3p0,beta6p0}/…`, `STAGE1_CLOSEOUT.md`
  (script `scripts/train_basat.py`).
- BASAT Stage 2 (GAIRAT): `boundary_aware_selective_at/gairat/seed42/GR1/GR1_GO_NO_GO.md`
  (script `scripts/train_basat_gairat.py`).
- BASAT Stage 3 (SAT): `boundary_aware_selective_at/sat/seed42/SA1/SA1_GO_NO_GO.md`
  (script `scripts/train_basat_sat.py`).
- Within‑training closeout: `boundary_aware_selective_at/seed42/BASAT_WITHIN_TRAINING_CLOSEOUT.md`.
- Representation pivot: from‑scratch non‑convergence `representation_bilstm/seed42/G1/NON_CONVERGENCE_DO_NOT_CITE.md`
  (script `scripts/train_bilstm_g1.py`); clean‑init fine‑tune
  `variantG_bilstm_representation_test/seed42/g1_finetune_cleaninit/BILSTM_G1_GO_NO_GO.md`
  (scripts `scripts/train_bilstm_g1_finetune.py`, clean assets reused from `cross_architecture/bilstm/`).
- Prior closure this extends: `final_defense_synthesis/FINAL_DEFENSE_LINE_CLOSURE.md`,
  `…/HIGH_RECALL_LOW_FP_FEASIBILITY.md`, `…/FALSE_ALARM_MECHANISM_INVESTIGATION.md`; DS‑SGE
  `dual_specialist_safety_gate/A1/seed42/`; pre‑registration
  `variantG_bilstm_representation_test/BILSTM_G1_REPRESENTATION_TEST_PREREGISTRATION.md`.
