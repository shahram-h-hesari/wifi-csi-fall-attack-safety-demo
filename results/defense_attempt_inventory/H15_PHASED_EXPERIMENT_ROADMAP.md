# H15 Phased Experiment Roadmap — Recall > 0.85 @ FAR < 0.15 under PGD ε=0.030

Date: 2026-07-05. Status: **planning document only.** No training run, no test read, no `.tex`
edit, nothing committed. All numbers cited below come from
`results/defense_attempt_inventory/D10_D11_TRANSFER_FAILURE_DIAGNOSIS.md` (+ its
`d10_d11_transfer_diagnostics/` CSVs), the D13 stage-0 audit, and the D14 validation-gate reports —
i.e., saved train/validation/test artifacts already in the ledger. Existing test numbers are used
**only as diagnostic motivation**, never for tuning.

Target H15 (held-out test, PGD ε=0.030, window-level, white-box, seed-42-family claim boundary):
recall > 0.85 and FAR < 0.15 → **TP ≥ 39 / 45 falls and FP ≤ 68 / 455 non-falls.**

Authorization note: the D14 gate addendum records "No D15 is authorized. No fusion reopening is
authorized." Opening this H15 program therefore requires an explicit, recorded advisor
authorization of this roadmap (Phase 0–1 gates pre-registered) before any training starts. This
document is written to be that pre-registration basis.

---

## 1. Advisor-level conclusion (read this first)

**Is H15 realistic with the current D8/D10/D11/AFAC-style family? No.** Within the LeNet-family
score axes we have, H15 is not merely hard — it is above the *oracle*. Treat it as an **unlikely
target** that may be *pursued* only as the falsification-first program below, with the realistic
secondary prize being a stable frozen-threshold F20-level result.

**Strongest scientific reason.** Three independent measurements from the saved artifacts:

1. **H15 exceeds the family's post-hoc test oracle by +15 TP.** The best recall any current score
   axis can achieve at FAR ≤ 0.15 on the held-out test split, with a *perfect oracle threshold*,
   is 0.533 (D10 and D11b: TP 24 / FP 68). H15 requires 0.867 (TP 39) at the same FP budget. This
   is not a calibration gap; the windows are not ranked separably. (D8b: 0.489; D11a: 0.333.)
2. **H15 implies a ~+0.10 AUROC step change.** An ROC passing through (FPR 0.15, TPR 0.867)
   corresponds to test PGD-AUROC ≈ 0.94 (binormal approximation). Observed test PGD-AUROC:
   0.820–0.847. The validation frontier has been flat at 0.869–0.876 across TRADES, GAIRAT, SAT,
   AFAC/optionB, D14's pAUC-ranking objective, and a BiLSTM pivot (worse, 0.726). Fourteen-plus
   attempts moved it by < 0.01.
3. **H15 sits at the split's statistical resolution limit.** With 45 test falls, a model whose
   *true* recall is exactly 0.867 passes TP ≥ 39 with probability ≈ 0.5; jointly with FP ≤ 68 at
   true FAR 0.15, a single frozen read passes with probability ≈ 0.25. To make one frozen read a
   fair bet (≈ 2/3 joint pass), the true operating point must be ≈ (recall 0.90, FAR 0.135) —
   test AUROC ≈ 0.95. The D8b F20 knife-edge (window width 0.00028) is the small-sample warning
   already realized once.

**Most likely required change:** a **representation change** (new inductive bias) carrying a
**tail-targeted ranking objective** on top of PGD adversarial training. Calibration alone is
provably insufficient (diagnosis §4); fusion is vetoed by the pre-registered D13 stage-0 gate;
objective-only changes inside LeNet are exhausted (BASAT capstone + D14 gate failure);
dataset/split changes would change the thesis claim rather than meet it. The one mechanistic
opening the diagnosis leaves: false positives are dominated by **sustained periodic motion**
(run/walk ≈ 70% of the FP burden) while falls are **short transients** — a representation with
explicit temporal pooling/attention could in principle separate "transient burst" from "sustained
oscillation" in a way LeNet's local-conv-plus-flatten does not. That hypothesis is cheap to test
and is the only scientifically live route to a step change. It must be tested before any
objective engineering.

---

## 2. Phase design

Four phases. Each has a hard gate; failing a gate ends the program (see §8), it does not loop back.

### Phase 0 — Feasibility & hard-window inventory (analysis-only)

- **Purpose:** decide, at zero training cost, whether the fall windows H15 needs are rescuable at
  all, or whether they are data-intrinsic losses no representation can rank above the run/walk
  tail.
- **Hypothesis:** the fall low-tail and non-fall upper-tail windows are *model-specific* (they
  rotate across checkpoints), leaving headroom a new representation could realize. Null: the same
  windows are universally hard → H15 is dead on arrival.
- **Experiments:** H15-E0 (see §3).
- **Why from the diagnosis:** the diagnosis located the failure in 4–6 falls interleaved deep in
  the run/walk tail and showed the fall-score low tail is what shifted val→test. D13 already
  showed FN sets are weakly shared across models (three-way Jaccard 0.11) while FP sets are
  strongly shared (0.50–0.75) — Phase 0 quantifies exactly this at the H15 budget on validation.
- **Split:** saved validation scores (and, for the mining bank, new *train-split* forward
  passes/PGD with existing checkpoints — train and validation only; test untouched).
- **Cost:** < 1 CPU-hour (saved-score part); + ~1–2 CPU-hours if the train-split mining bank is
  built in this phase.
- **Outputs:** `results/h15_roadmap/phase0_hard_window_inventory/` (per-window rank-stability CSV,
  cross-model overlap matrix, union-oracle CSV, geometry memo MD).
- **Go/no-go gate (Gate 0):** proceed to Phase 1 only if BOTH:
  (a) union-oracle validation recall at per-model FAR ≤ 0.12 thresholds ≥ 40/44 (0.909) — i.e.,
  at most 4 of the 44 validation falls are missed by *every* saved model at the buffered budget;
  (b) ≥ 25% of each model's FAR-0.12 fall-misses are model-specific (rescued by some other model).
- **Failure interpretation:** ≥ 5 universally-hard falls means the H15 recall bar cannot be met
  even by an oracle over every representation tried to date → the missing falls are plausibly
  information-poor at the window level (or mislabeled/ambiguous) → **stop; H15 declared not
  plausible with current data; write the negative memo.**

### Phase 1 — Representation screening (validation-only, low-cost pilots)

- **Purpose:** test whether any different inductive bias moves validation PGD ranking quality by
  a step, before spending anything on objective engineering.
- **Hypothesis:** temporal-attention/residual representations separate transient falls from
  sustained run/walk under PGD better than LeNet, by ≥ +0.025 val PGD-AUROC over the 0.876
  ceiling.
- **Experiments:** H15-E1 (CNN + temporal attention pooling), H15-E2 (ResNet18), H15-E3
  (small temporal Transformer; conditional). One seed each, short budget, identical simple
  objective (screening must vary *only* the representation).
- **Why from the diagnosis:** the diagnosis classifies the failure as structural
  ranking/separability, and §4 of the diagnosis concludes only a change to the score function can
  reorder the interleaved windows. LeNet-internal objectives (BASAT family, D14 pAUC ranking) are
  already exhausted with pre-registered negative outcomes.
- **Split:** train for training; validation for screening metrics only. No test.
- **Cost (estimates):** E1 ≈ 2–6 CPU-h; E2 ≈ 12–36 CPU-h; E3 ≈ 12–48 CPU-h (PGD-10 AT dominates).
  Run serially cheapest-first.
- **Outputs:** `results/h15_roadmap/phase1_representation_screen/<arch>/` (training log, val PGD
  probability export in the standard CSV schema, screening summary MD).
- **Go/no-go gate (Gate 1):** some arm reaches **val PGD-AUROC ≥ 0.90 AND val recall ≥ 0.75 at
  val FAR ≤ 0.15 AND clean 7-class val accuracy ≥ 0.68** at screening budget. (0.90 ≈ what an ROC
  needs to plausibly grow toward the H15 gate with objective refinement; 0.876-ceiling arms fail
  this by construction.)
- **Failure interpretation:** the representation ceiling extends to attention/residual families →
  the frontier is a property of the data/threat model, not the architecture → **stop; H15 closed
  as not plausible; the capstone's ceiling claim gains cross-family test evidence-by-extension
  (validation-level).**

### Phase 2 — Tail-targeted objective + multi-seed confirmation (only if Gate 1 passes)

- **Purpose:** convert the winning representation's ranking headroom into the specific operating
  point H15 needs, and establish stability (the thing D10/D11 lacked).
- **Hypothesis:** on a representation that clears 0.90 val AUROC, adding (i) a pairwise
  fall-vs-hard-non-fall ranking loss and (ii) an FP-tail CVaR penalty concentrates the gain in
  the FAR ≤ 0.15 region without destroying the clean guard; gains replicate across seeds.
- **Experiments:** H15-E4 (composite objective, 3 seeds, full budget); H15-E5 (single-seed term
  ablation, conditional).
- **Why from the diagnosis:** the diagnosis shows the binding constraint is 4–6 falls below the
  92nd–percentile non-fall tail; a pairwise ranking loss on exactly those pairs is the direct
  optimization of the diagnosed quantity. The CVaR term addresses the threshold-near FP excess.
  D14 already showed this objective family fails *on LeNet* — Phase 2 tests it only on a
  representation that passed screening, which is the specific condition D14 lacked.
- **Split:** train + validation. No test.
- **Cost:** ≈ 3 × screening-arm cost (3 seeds at full budget) + ablation.
- **Outputs:** `results/h15_roadmap/phase2_objective_refinement/seed{42,43,44}/` (checkpoints,
  logs, val exports, per-seed gate report), one cross-seed gate summary.
- **Go/no-go gate (Gate 2):** the full H15 validation gate of §6, on ≥ 2 of 3 seeds.
- **Failure interpretation:** representation headroom exists but cannot be steered to the low-FAR
  region stably → the H15 operating point is not reachable in this family either; report the
  (still thesis-valuable) improved AUROC frontier and stop.

### Phase 3 — Freeze, pre-register, and (later) one test read — **test read: DO NOT RUN NOW**

- **Purpose:** convert a Gate-2 pass into exactly one admissible frozen held-out test read.
- **Hypothesis:** none — this phase performs no experiment; it freezes protocol.
- **Contents:** write `H15_PREREGISTERED_TEST_PROTOCOL.md` (checkpoint hash, frozen tau, seed
  selection rule = median-validation seed, decision bands, disclosure list including the clean
  guard), obtain recorded advisor sign-off, then — and only then — the single test read per §9.
- **Split:** none until sign-off; then one test read.
- **Cost:** minutes.
- **Gate:** advisor signature. **Failure interpretation** of the eventual read: pre-declared in
  the protocol (see §9); no threshold or seed may be revisited afterward.

---

## 3. Experiment menu

Only experiments I consider scientifically justified. Deliberately short.

### H15-E0 — Hard-window inventory & union-oracle audit (Phase 0; analysis-only)

- **Model/representation:** none (saved scores of ≥ 8 existing checkpoints: AFAC/optionB, D10
  GR1 variants, D11a ST1b6, D11b SA1, ST1/beta3p0, variantD seeds, G1, D14 config-B seeds 43/44).
- **Objective/loss/AT:** N/A.
- **Hard fall handling:** identify per-model fall misses at per-model val FAR-0.12 thresholds;
  classify each of 44 validation falls as universally-hard / sometimes-hard / easy; rank-stability
  across models.
- **Hard non-fall handling:** identify "persistent impostors" — non-fall windows in the top-54
  scores of ≥ k models; build the train-split hard-negative mining bank (train-split PGD forward
  passes with 2–3 existing checkpoints) for later use by H15-E4.
- **Validation selection rule:** N/A (no selection).
- **Success gate:** Gate 0 (§2). **Failure gate:** ≥ 5 universally-hard falls → program stops.
- **Expected benefit:** decides for ~0 cost whether any training is worth running; produces the
  mining bank Phase 2 needs anyway.
- **Main risk:** union-oracle over existing models *underestimates* a genuinely new
  representation. Accepted: if even 8 diverse checkpoints all miss the same 5+ falls, the prior
  that a new architecture rescues them is too low to fund.

### H15-E1 — CNN trunk + temporal attention pooling (Phase 1 screening)

- **Model/representation:** LeNet-scale conv trunk (keep parameter count comparable), replace
  flatten with attention-weighted temporal pooling (transient-sensitive summary).
- **Objective:** screening objective `L_screen` (§4). **AT method:** PGD-10, ε=0.030, α=ε/6 —
  identical to the frozen eval attack.
- **Hard falls:** class weight w_fall only (no mining at screening — keep the arm clean).
- **Hard non-falls:** none at screening.
- **Validation selection rule:** best epoch by val PGD-AUROC; report recall@FAR∈{0.10,0.12,0.15}.
- **Success gate:** Gate 1 numbers. **Failure gate:** val PGD-AUROC < 0.885 at budget end.
- **Expected benefit:** cheapest direct test of the transient-vs-sustained mechanism suggested by
  the run/walk FP dominance.
- **Main risk:** attention pooling under-trains on ~small fall count; mitigate with the class
  weight and early-epoch monitoring (D14-style health review).

### H15-E2 — ResNet18 (SenseFi UT-HAR config) + PGD-AT (Phase 1 screening)

- **Model/representation:** ResNet18 as used in the chapter-4 cross-architecture artifacts
  (baseline pipeline already exists in-repo).
- **Objective/AT/selection/gates:** identical to E1 (only the representation varies).
- **Hard falls / hard non-falls:** as E1.
- **Expected benefit:** tests whether depth/residual features (rather than temporal pooling) buy
  separability; reuses existing model code, low integration risk.
- **Main risk:** CPU cost of PGD-10 through 18 layers; cap wall-clock (§8) and use the screening
  budget honestly rather than extending it.

### H15-E3 — Small temporal Transformer encoder (Phase 1; conditional)

- **Model/representation:** 2–4 layer encoder over time-step tokens of the CSI window,
  class-token readout.
- **Objective/AT/selection/gates:** identical to E1.
- **Run condition:** only if E1 AND E2 both land in the near-gate band (val PGD-AUROC ∈
  [0.885, 0.90)) — i.e., evidence that inductive bias moves the number but not far enough. If
  both are ≤ 0.885, skip (ceiling confirmed); if either passes, skip (winner exists).
- **Expected benefit:** strongest architectural departure available.
- **Main risk:** most expensive arm, data-hungry on ~small window counts; that is why it is
  conditional and last.

### H15-E4 — Winning representation + tail-targeted composite objective (Phase 2)

- **Model/representation:** the Gate-1 winner, unchanged.
- **Objective:** `L_full` (§4): adversarial CE + focal fall-rescue weighting + pairwise
  fall-vs-hard-negative ranking + FP-tail CVaR penalty + clean CE guard term.
- **AT method:** PGD-10 ε=0.030 on every term's adversarial inputs (single shared attack pass per
  batch for cost).
- **Hard falls:** focal-style up-weighting of adversarial fall CE (low-tail rescue), plus the
  ranking loss pulls the lowest-ranked falls specifically.
- **Hard non-falls:** mined bank from H15-E0 (train-split persistent impostors, refreshed each
  epoch by current scores: top-q% non-fall by adversarial fall-probability); these populate the
  ranking pairs and the CVaR term.
- **Validation selection rule (frozen before training):** best epoch by val recall at
  val FAR ≤ 0.12 (buffered cap), tie-break higher pAUC(FAR ≤ 0.15), then earlier epoch; threshold
  by the standard max-recall-s.t.-FAR≤cap rule.
- **Success gate:** full §6 gate on ≥ 2/3 seeds. **Failure gate:** median seed misses any §6 line;
  one hyperparameter repair round allowed (λ re-balance only), then stop.
- **Expected benefit:** converts generic ranking headroom into the low-FAR operating point —
  the direct optimization of the quantity the diagnosis identified (fall low-tail vs non-fall
  tail interleaving).
- **Main risk:** D14 precedent — ranking objectives destabilized training and failed clean
  guards on 4/6 runs; mitigations: representation pre-qualified by Gate 1, clean-CE term retained,
  per-epoch health review identical to D14's.

### H15-E5 — Term ablation (Phase 2; conditional, 1 seed)

- Run only if E4 passes Gate 2 (attribute the gain for the thesis chapter) or misses it by ≤ 1 TP
  (diagnose which term failed before the single repair round). Drop each of {ranking, CVaR,
  focal} in turn at fixed budget. Gates: none (descriptive).

**Explicitly skipped (with reasons):** any further LeNet-objective arm (BASAT capstone + D14:
pre-registered negatives at the same frontier); calibration-only or threshold-stability-only arms
(diagnosis §4: provably insufficient — nothing to select on a score axis where the operating
point does not exist); fusion/ensemble arms (D13 stage-0 transfer veto FAIL; its addendum bars
reopening absent a materially larger transfer gap or a new distinct candidate — the latter only
exists if Phase 1 succeeds, at which point a fusion revisit would be a separate authorization);
GRU/BiLSTM arms (BiLSTM pivot already measured at 0.726 val PGD-AUROC — far below the ceiling,
and GRU is a weaker member of the same family); dataset/split redefinition (changes the claim,
not the result).

---

## 4. Objective-level detail

Notation: model f_θ; fall score s_θ(x) = softmax fall-probability; adversarial example
x′ = PGD¹⁰_{ε=0.03, α=ε/6}(x, θ) regenerated per step (white-box, matching the frozen eval
attack); B = batch, F = fall indices, N = non-fall indices.

**Screening objective (H15-E1/E2/E3)** — deliberately minimal; the arm tests representation only:

    L_screen = (1/|B|) Σ_i w_yi · [ ½·CE(f_θ(x_i), y_i) + ½·CE(f_θ(x′_i), y_i) ]
    w_yi = w_fall (∈ {2, 4}) if y_i = fall, else 1.

**Full objective (H15-E4):**

    L_full = L_clean + λ_adv·L_adv + λ_rank·L_rank + λ_cvar·L_cvar

    L_clean = (1/|B|) Σ_i CE(f_θ(x_i), y_i)                          [clean guard — keep]
    L_adv   = (1/|B|) Σ_i ρ_i · CE(f_θ(x′_i), y_i)                   [adversarial CE — keep]
              ρ_i = (1 − s_θ(x′_i))^γ  for i ∈ F (fall low-tail rescue, focal form, γ ≈ 2);
              ρ_i = 1 otherwise.
    L_rank  = (1/|P|) Σ_{(i,j)∈P} softplus( m − (s_θ(x′_i) − s_θ(x′_j)) )
              P = F × H, H = mined hard non-fall set (top-q% non-fall windows by s_θ(x′),
              q ≈ 10–15%, bank refreshed per epoch from the TRAIN split only); margin m ≈ 0.15.
              [pairwise fall-vs-hard-non-fall ranking — the direct pAUC surrogate; KEEP: it
               optimizes exactly the interleaving the diagnosis identified]
    L_cvar  = mean of the top-k values of { s_θ(x′_j) : j ∈ N },  k = ⌈0.15·|N|⌉
              [hard FP-tail penalty at the operating FAR — KEEP: targets the threshold-near
               excess-FP mass]

Starting weights λ_adv = 1, λ_rank = 0.5, λ_cvar = 0.25; the single Phase-2 repair round may
re-balance λ only.

**Considered and skipped:**
- *Threshold-stability regularization* — skip as a loss (no honest differentiable surrogate for
  "wide feasible tau window"); enforced instead by the Gate-2 window requirement.
- *Calibration loss (temperature/ECE)* — skip: monotone recalibration cannot change ranking, and
  ranking is the diagnosed failure.
- *Source-class-aware penalty (explicit run/walk term)* — skip: the score-mined hard-negative set
  H is already ~70% run/walk by construction, subsumes the class signal, additionally covers the
  high-rate stand-up tail, and avoids overfitting to class identity.
- *Representation change as a "loss term"* — handled properly as Phase 1, not as a term.

---

## 5. Representation decision

The next serious attempt must **not** stay with LeNet. Verdicts:

| Candidate | Worth trying? | Why | Evidence to move it forward |
|---|---|---|---|
| CNN + temporal (attention) pooling | **Yes — first** | Cheapest departure; directly targets the diagnosed FP mechanism (sustained run/walk periodicity vs fall transients); minimal integration risk | Gate 1 numbers at screening budget |
| ResNet18 | **Yes — second** | Different capacity/feature depth; pipeline already exists in-repo (ch. 4 cross-arch); moderate cost | Gate 1 numbers |
| Transformer / attention encoder | **Conditional third** | Strongest inductive-bias departure; but most expensive on CPU and data-hungry at this window count | Run only in the near-gate band (both E1/E2 in [0.885, 0.90)); then Gate 1 |
| BiLSTM | **No** | Direct negative evidence: G1 representation pivot measured val PGD-AUROC 0.726 — far below the 0.876 ceiling | — |
| GRU | **No** | Same recurrent family as BiLSTM with less capacity; no reason to expect a sign flip | — |
| Learned embedding + shallow calibrated fall detector | **Not now** | Requires a good trunk to exist first; if Phase 1 produces one, this becomes a Phase-2 *variant* of E4 (frozen trunk + margin head), not a separate program | Gate-1 winner exists |
| Ensemble / fusion | **No** | D13 stage-0 pre-registered shared-input transfer veto FAILED; its addendum bars reopening. Only a Phase-1 winner (a genuinely distinct candidate) could justify a *separate, newly authorized* revisit | New architecture passing Gate 1 + a new transfer audit clearing the 0.15 gap |

---

## 6. Validation gate for H15 (Gate 2 — required before any test-read discussion)

Designed strictly tighter than H15 because (a) validation→test transfer already failed once
(recall drop up to −0.22 at frozen thresholds; FAR drift +0.014 to +0.034) and (b) the binomial
fragility of TP ≥ 39/45 and FP ≤ 68/455 requires the true operating point to be ≈ (0.90, 0.135)
for a single read to be a fair bet. Validation split: 44 falls / 452 non-falls.

All of the following, computed on validation PGD (ε=0.030) exports with the pre-frozen selection
rule (max recall s.t. FAR ≤ cap; tie-break lower FAR, then higher tau):

1. **Recall:** ≥ 40/44 = **0.909** at the buffered cap **FAR ≤ 0.12** (FP ≤ 54/452). (Buffer
   absorbs the observed +0.03 FAR drift and the recall decay simultaneously.)
2. **Clean guard (D14 wording, unchanged):** clean 7-class accuracy ≥ 0.70, clean macro-F1
   ≥ 0.65, clean fall recall ≥ 0.90 at the same frozen tau.
3. **Threshold-stability window:** the set of tau simultaneously giving val recall ≥ 39/44
   (0.886) and val FAR ≤ 0.15 must span a width **≥ 0.03** on the score axis (D8b's fatal window
   was 0.00028; D10/D11's were negative).
4. **Bootstrap stability (2,000 stratified resamples):** at the frozen tau, recall ≥ 0.85 in
   ≥ 80% of resamples; 95% CI upper bound of FAR ≤ 0.16; 95% CI of the *selected threshold*
   under re-selection ≤ 0.06 wide.
5. **Multi-seed consistency:** ≥ 2 of 3 seeds (42/43/44) pass lines 1–4; cross-seed recall spread
   at frozen taus ≤ 0.07; the promoted checkpoint is the **median-validation seed**, not the best.
6. **Paired-superiority check (D14 lesson):** paired stratified bootstrap ΔTP vs the saved AFAC
   validation reference ≥ +4 in ≥ 70% of resamples (H15 needs +15 TP on test oracle; a candidate
   that cannot beat AFAC by 4 on validation pairs is not a candidate).

---

## 7. Phase ordering (exact run order)

| # | Item | Decision |
|---|---|---|
| 1 | H15-E0 hard-window inventory + union oracle (Phase 0) | **Run now** (analysis-only) |
| 2 | Gate 0 evaluation + advisor authorization of Phase 1 | Run when E0 done |
| 3 | H15-E1 CNN + temporal attention pooling screening | **Run only if Gate 0 passes** |
| 4 | H15-E2 ResNet18 screening | Run only if Gate 0 passes (after E1, serially) |
| 5 | H15-E3 Transformer screening | Run only if E1 AND E2 both land in [0.885, 0.90) |
| 6 | Gate 1 evaluation | After the last screening arm |
| 7 | H15-E4 composite objective, 3 seeds | **Run only if Gate 1 passes** |
| 8 | H15-E5 ablation | Run only per its condition |
| 9 | Gate 2 (full §6 gate) | After E4 |
| 10 | Phase 3 freeze + pre-registered protocol + sign-off | Only if Gate 2 passes |
| 11 | Single frozen held-out test read | **DO NOT RUN NOW** (§9) |
| — | Any further LeNet objective arm; calibration-only arm; fusion arm; GRU/BiLSTM arm | **Do not run** |

---

## 8. Stopping rules (each is terminal for the H15 chase)

1. **Phase-0 data-limit stop:** ≥ 5 of 44 validation falls missed by every saved model at
   FAR-0.12 budgets (union-oracle recall < 0.909) → stop before any training.
2. **Validation-failure stop:** Gate 1 fails (no arm ≥ 0.90 val PGD-AUROC) → stop; the
   representation-ceiling claim extends and H15 is closed as not plausible.
3. **Multi-seed instability stop:** in Phase 2, < 2/3 seeds pass, or recall spread > 0.07, after
   the single permitted λ-repair round → stop (D10/D11 taught us thin single-seed margins do not
   transfer).
4. **Threshold-window instability stop:** feasible validation tau window < 0.02 for the Phase-2
   winner → stop regardless of point metrics (this is exactly the D8b knife-edge failure mode).
5. **Representation-ceiling stop (global):** if E1–E3 all land ≤ 0.885 val PGD-AUROC, no further
   architecture arms may be added ad hoc; the program ends rather than becoming a fishing trip.
6. **Compute/time stop:** cumulative training budget cap ≈ 10 CPU-days or 3 calendar weeks,
   whichever first; hitting the cap without a Gate-2 pass ends the program with a documented
   negative.
7. **Scope guard:** none of this blocks or precedes the proposal defense; the defense narrative
   (F20 chase closed; operating-region characterization) stands independent of this program's
   outcome.

---

## 9. Frozen held-out test rule — **DO NOT RUN NOW**

A single held-out test read is permitted only after ALL of:

1. **Protocol saved:** `H15_PREREGISTERED_TEST_PROTOCOL.md` committed to the ledger folder before
   the read, containing the decision bands below.
2. **Model/checkpoint frozen:** exact checkpoint file + SHA256 recorded; no retraining after.
3. **Threshold rule frozen:** the numeric tau (from the median-validation seed at the FAR-0.12
   buffered cap) written into the protocol; no re-selection of cap, rule, or tau afterward.
4. **Seed/ensemble rule frozen:** single median-validation seed; explicitly NO ensembling, NO
   per-seed best-picking.
5. **Validation gate passed:** full §6 gate, with the gate report saved.

Pre-declared outcome bands (written into the protocol verbatim):
- **SUCCESS:** test TP ≥ 39 and FP ≤ 68 → H15 met (single-read evidence; report with binomial CI).
- **INFORMATIVE NEAR-MISS:** TP ≥ 36 and FP ≤ 80 → H15 not met; result reported as the new best
  frozen-threshold operating point; **no second read, no threshold adjustment.**
- **FAILURE:** anything else → H15 chase ends permanently for this data/model family.
One read total. Any future read beyond this one requires a new advisor authorization and a new
pre-registration from scratch.

---

## 10. First safe action (exactly one)

**Build the hard-window inventory from train/validation only (H15-E0). Run now.**

Justification: it is the only action that can *kill the program before it costs anything*. The
diagnosis proved the failure lives in a specific handful of fall windows interleaved with the
run/walk tail; whether those windows are model-specific or data-intrinsic is the single fact that
determines if H15 is worth one CPU-hour of training. All inputs are already saved validation
score CSVs (≥ 8 checkpoints in the ledger); the outputs (universally-hard-fall count,
union-oracle recall, persistent-impostor bank) are simultaneously the Gate-0 evidence and the
mining infrastructure Phase 2 would need. Designing training scripts first would invert the
evidence order; running any pilot first would spend compute a Gate-0 failure would waste.

---

## 11. Final advisor recommendation

- **Best experiment family for improving recall/FAR:** representation change with a
  transient-vs-sustained inductive bias (CNN + temporal attention pooling first, ResNet18
  second), followed — only on a Gate-1 pass — by the pairwise fall-vs-hard-negative ranking +
  FP-tail CVaR objective (H15-E4). This is the only family the diagnosis leaves mechanistically
  open: calibration is proven insufficient, fusion is vetoed, LeNet objectives are frontier-flat.
- **H15 status: unlikely target.** Not a main target; not even a comfortable stretch target. It
  exceeds the current family's post-hoc test oracle by +15 TP at the FP budget and implies a
  ~0.94–0.95 test AUROC against an observed 0.82–0.85 with a flat 0.876 validation ceiling. Fund
  it only as this falsification-first program; the realistic prizes are (a) a fast, cheap,
  publishable negative that closes the question, or (b) a stable F20-level frozen-threshold
  result discovered en route (which would already beat everything in the ledger).
- **Evidence that would convince me to authorize one frozen test read:** a full Gate-2 pass —
  val recall ≥ 0.909 at FAR ≤ 0.12 with the D14 clean guard, a ≥ 0.03-wide feasible threshold
  window, bootstrap recall ≥ 0.85 in ≥ 80% of resamples with FAR CI ≤ 0.16, ≥ 2/3 seeds
  consistent (spread ≤ 0.07), and paired ΔTP ≥ +4 over AFAC in ≥ 70% of paired resamples — all
  from a pre-frozen selection rule, with the protocol of §9 signed before the read.
