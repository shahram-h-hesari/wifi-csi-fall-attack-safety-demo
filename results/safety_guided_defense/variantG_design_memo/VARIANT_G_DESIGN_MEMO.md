# Variant G — design & pre-registration memo

> **Documentation / pre-registration only — Variant G is NOT run.** No training, no attacks, no seeds
> 45–46, no training-script modification, no `.tex` edit, no artifact overwrite. Built from the committed
> Variant F seed-42 pilot, the seed-44 STRONG-SUPPORT validation, and the committed false-alarm
> diagnostic (`variantF_false_alarm_diagnostic/`, Diagnosis **C — Not filterable**). LeNet, UT-HAR/SenseFi
> split, test n=500 (45 fall windows), ε=0.030, white-box, digital-domain, window-level. **No solved /
> certified / clinical / over-the-air claim** is made or proposed.

---

## 1. Motivation from the diagnostic

Variant F is the best validated defense so far — **two-seed STRONG SUPPORT** (seed 42 design, seed 44
independent validation), Pareto-dominating the same-seed Variant D baseline on attacked recall **and**
false alarms, with a measurably improved residual-motion logit geometry (walk/run `z_fall−z_true` median
2.716 → ~0.96–0.99) and PGD-20 durability. That progress is real and stays the thesis headline.

But the committed false-alarm diagnostic shows the remaining errors are **not removable by post-hoc
tuning**:

- **Variant F improved geometry and validated on seed 44** — confirmed; Variant G must *preserve* this,
  not replace it. Variant G is **Variant F + extra terms**, not a new line.
- **But false alarms remain too high** — PGD FP = 115 (seed 42) / 112 (seed 44); walk/run→fall = 80 / 73,
  still 65–70% of all false alarms.
- **Post-hoc gating failed because of confidence inversion** — under PGD@0.030 the false alarms are *more
  confident* than the true falls Variant F detects: median P(fall) **0.518 vs 0.415** (seed 42) / **0.513
  vs 0.392** (seed 44); fall-vs-rest logit margin **0.88 vs 0.46** / **0.90 vs 0.42**; entropy **1.30 vs
  1.41** / **1.30 vs 1.40** (lower = more confident); confidence margin **0.31 vs 0.14** / **0.30 vs
  0.11**. No probability / margin / entropy rule met the FP-control targets on **both** seeds, and no
  single threshold is cross-seed stable.
- **Therefore the remaining failure is a learned decision-geometry problem, not a thresholding problem.**
  The model places adversarial nonfall windows *confidently* on the fall side of a learned boundary. Only
  a change to **what is trained** can move that boundary; a change to **where we threshold** cannot.

**Constraint inherited from the diagnostic:** clean accuracy is already at the guard boundary (Variant F
seed 42 clean acc 0.734; seed 44 0.700 — exactly at the 0.70 guard; macro-F1 0.658). Any Variant G that
buys FP reduction by further depressing the fall logit risks breaking the clean guard. **Variant G must
reduce confident nonfall→fall errors without crushing clean performance or attacked fall recall.**

---

## 2. Failure mode to target

Define the exact failure Variant G must fix (and nothing broader):

1. **Confident adversarial nonfall→fall mapping.** Adversarial walk/run/other-nonfall windows are mapped
   to fall with P(fall) ≈ 0.51 and a residual `z_fall − z_true` ≈ +1.0 — fall is the argmax *with margin*,
   not a coin-flip.
2. **Confidence inversion vs true falls.** The false alarms are more confident than the detected true
   falls on every scalar axis (§1). This is why filtering fails and why the fix must be at training time.
3. **walk/run dominate.** 80/115 (seed 42) and 73/112 (seed 44) of false alarms originate from walk or
   run. Variant G should concentrate corrective pressure on the motion manifold, where the residual
   margin is *smallest* (~0.9–1.1) and therefore most movable.
4. **Clean budget is already spent.** Clean acc/macro-F1 sit at the guard boundary. The design must add
   *targeted* negative pressure (only on adversarial motion→fall directions), not a global fall-logit
   penalty that would also suppress clean falls and tip the guard.

**Non-goals (explicitly out of scope for G):** improving clean accuracy, changing the attack threat model,
certified/over-the-air robustness, or the non-motion tail (lie/pickup/sit/stand — only ~30–35% of FAs and
with *larger* residual margins ~1.7–3.7, i.e. harder to move and lower yield).

---

## 3. Candidate Variant G designs

Notation: `z_c(x)` = logit of class `c`; `fall` = fall index; adversarial example `x̃` from a PGD/FGSM
attack; `S_wr` = source class ∈ {walk, run}; `S_nf` = any nonfall source; `γ` margins; `λ` weights.

### Option A — Targeted nonfall→fall adversarial hard negatives
Generate adversarial examples by attacking nonfall windows **toward the fall class** (targeted PGD on
`z_fall`), then train the true nonfall class to stay above fall on those examples.

- **Math:** for `x̃_i = ProjPGD(x_i, target=fall)` with true class `t_i ∈ S_nf`,
  `L_A = mean_i max(0, γ_A + z_fall(x̃_i) − z_{t_i}(x̃_i))`.
  Differs from Variant F's `L_motion` in *how the adversary is generated*: F uses untargeted FGSM/PGD that
  happens to land some motion windows on fall; A **explicitly drives** windows toward fall, so it trains on
  the exact worst-case nonfall→fall directions the diagnostic flagged.
- **Targets:** failure modes 1 + 2 directly (confident nonfall→fall mapping; the very examples that invert
  confidence).
- **Expected benefit:** **highest** direct FP cut on the adversarial→fall manifold; should also *lower*
  the confidence of the residual FAs (attacks the inversion at its source).
- **Clean-acc risk:** **medium-high** — pushing fall down on many nonfall directions can depress clean fall
  recall and tip the 0.70 guard if `λ_A` is too large.
- **Fall-recall risk:** **medium** — over-suppression of `z_fall` could cost attacked recall; mitigated by
  keeping Variant F's `L_fall_margin` term that protects true falls.
- **Complexity:** **medium-high** — needs a new targeted-attack path in the training loop (new code; but
  the existing `pgd_perturb`/`fgsm_perturb` in `tsg` can be reused with a target label and sign flip).
- **Suitability:** **quick seed-42 pilot — highest priority single ingredient**, but pair with a clean
  guard and the F fall-margin term.

### Option B — Source-class-weighted motion margin
Keep Variant F's untargeted adversarial motion margin but **weight it by source class**, heaviest on
walk/run because they dominate residual FAs and have the smallest (most movable) margins.

- **Math:** replace `L_motion` with
  `L_B = mean_{i∈adv S_nf} w_{t_i} · max(0, γ_m + z_fall(x̃_i) − z_{t_i}(x̃_i))`, with `w_walk, w_run > w_other ≥ 0`
  (e.g. `w_walk = w_run = 2`, `w_other = 1`).
- **Targets:** failure mode 3 (motion dominance) using examples Variant F already generates.
- **Expected benefit:** **moderate** — focuses existing pressure where geometry is worst; cheaper and
  lower-risk than A, but bounded by whatever motion→fall examples the *untargeted* attack happens to make.
- **Clean-acc risk:** **low-medium** — same example pool as F, only re-weighted.
- **Fall-recall risk:** **low-medium.**
- **Complexity:** **low** — a per-sample weight vector inside the existing `L_motion`; smallest code delta.
- **Suitability:** **quick seed-42 pilot — natural cheap companion to A.**

### Option C — False-alert-budget checkpoint selection
Keep the Variant F loss **unchanged**; change only *selection*: among saved candidates, enforce a
validation false-alarm budget before maximizing recall.

- **Math (selection rule, not a loss):** choose
  `argmax_{ckpt} R_pgd^val(ckpt)` subject to `clean guards` ∧ `FP_pgd^val ≤ B_fp` ∧ `walkrun_pgd^val ≤ B_wr`.
- **Targets:** operationalizes the FP constraint without touching geometry.
- **Expected benefit:** **modest and bounded** — can only pick among already-trained points; the
  diagnostic showed the existing F candidates trade recall for FP along an *inverted* frontier, so the
  budget mostly buys FP by losing recall. **Does not fix the inversion.**
- **Clean-acc / recall risk:** none beyond what selection already does (selection-only).
- **Complexity:** **very low** — extend selection-v2 scoring.
- **Suitability:** **fold in for free as the selection rule (see §6), but it is not a stand-alone G** — it
  cannot move the boundary, only pick on it.

### Option D — Auxiliary binary fall-alert head
Keep the 7-class activity head; add a **separate binary fall-vs-nonfall head** trained with its own
adversarial margins, decoupled from the (currently inverted) 7-way logits.

- **Math:** add head `g(x) ∈ ℝ` (fall-alert logit); train
  `L_D = BCE(σ(g(x)), 1[t=fall]) + λ_D1 mean_{adv S_nf} relu(γ + g(x̃)) + λ_D2 mean_{adv fall} relu(γ − g(x̃))`;
  alert = `σ(g(x)) ≥ 0.5`. The 7-way head keeps activity accuracy; the binary head owns the alert geometry.
- **Targets:** the inversion itself — provides a *new* decision axis that the 7-way softmax does not, the
  one axis the diagnostic showed is missing.
- **Expected benefit:** **potentially largest / most principled** — could restore a genuinely gatable
  confidence signal.
- **Clean-acc risk:** **low-medium** (shared backbone, extra head).
- **Fall-recall risk:** **medium** — the binary head must be tuned so its threshold doesn't itself become
  recall-fragile under PGD.
- **Complexity:** **high** — architecture change, new head, two-objective balance, new export/eval plumbing.
- **Suitability:** **thesis future work** — too large for a quick pilot; document as the principled next
  step if A+B underdeliver.

### Comparison summary

| Option | Targets | Benefit | Clean risk | Recall risk | Complexity | Verdict |
|---|---|---|---|---|---|---|
| A targeted nonfall→fall HN | confident nonfall→fall + inversion | **high** | med-high | medium | med-high | **pilot (primary ingredient)** |
| B source-weighted motion margin | motion dominance | moderate | low-med | low-med | low | **pilot (cheap companion)** |
| C FP-budget selection | FP constraint | modest (bounded) | none | none | very low | **fold in as selection rule** |
| D binary fall-alert head | the inversion (new axis) | high (principled) | low-med | medium | high | **future work** |

---

## 4. Recommended Variant G

**Recommendation (challenged below):** **Variant G = Variant F loss + Option A (targeted walk/run→fall
hard negatives) + Option B (source-class-weighted motion margin), selected under an Option-C false-alert
budget.** Seed-42-only pilot. D is documented as future work.

**Why this over the alternatives — challenge to the user's stated preference:**

- The user's preferred starting point (F + A + B + C) is **correct, with one refinement**: treat **C as a
  selection rule, not a loss term** (it cannot move the boundary; the diagnostic proved selection alone
  rides an inverted frontier). So G's *training objective* = F + A + B; C governs *which checkpoint we
  keep*. This avoids overclaiming that a budget penalty "fixes" geometry.
- **Why not C alone:** the committed diagnostic already ran the C experiment in spirit — post-hoc/selection
  trade-offs on existing F candidates do not beat the raw point and are not cross-seed stable. C cannot be
  the primary G.
- **Why not D first:** D is the most principled and may ultimately be the right answer, but it is an
  architecture change with two-objective tuning — too expensive for a *first* pilot whose job is to test
  "can targeted motion pressure move the boundary at all?" If A+B move the inversion measurably, D becomes
  a well-motivated follow-up; if A+B fail, D is the documented future direction. Sequencing A+B before D is
  the higher value-per-compute path.
- **Why A and B together, not A alone:** B is nearly free (a weight vector) and concentrates A's pressure
  on the dominant, most-movable motion classes; running them together in one pilot costs the same GPU as A
  alone and gives a cleaner attribution of the motion effect.

---

## 5. Proposed loss

**Start (frozen Variant F, verbatim from `train_variantF_motion_margin.py`):**

```
L_F = L_FWCE
    + λ_m · mean_{i ∈ adv walk/run}   max(0, γ_m + z_fall(x̃_i) − z_{t_i}(x̃_i))      [motion margin]
    + λ_f · mean_{i ∈ adv true-fall}  max(0, γ_f + max_{c≠fall} z_c(x̃_i) − z_fall(x̃_i))  [fall margin]
```
with `L_FWCE` = fall-weighted cross-entropy (fall weight 3) on the batch-split (50% clean / 25% FGSM /
25% PGD) mix; `γ_m = γ_f = 0.5`.

**Variant G adds two terms and a source weight (A + B); C is selection, not loss:**

```
L_G = L_FWCE
    + λ_m · mean_{i ∈ adv walk/run}  w_{t_i} · max(0, γ_m + z_fall(x̃_i) − z_{t_i}(x̃_i))   [B: source-weighted motion margin]
    + λ_f · mean_{i ∈ adv true-fall}          max(0, γ_f + max_{c≠fall} z_c(x̃_i) − z_fall(x̃_i))  [F: fall margin, UNCHANGED]
    + λ_t · mean_{i ∈ tgt nonfall}            max(0, γ_t + z_fall(x̂_i) − z_{t_i}(x̂_i))     [A: targeted nonfall→fall hard negative]
```

where:

- **B (source weight):** `w_walk = w_run = w_wr ≥ 1`, `w_other = 1`. Setting `w_wr = 1` recovers Variant F's
  motion term exactly (clean ablation anchor).
- **A (targeted hard negatives):** `x̂_i = Proj_{‖·‖∞≤ε}(x_i + PGD steps ascending z_fall(x_i))` is a
  **targeted** attack from a nonfall source window `t_i ∈ S_nf` *toward* fall (distinct from F's untargeted
  `x̃`). The margin pushes the true nonfall logit back above fall on exactly the adversarial direction that
  creates confident false alarms. `γ_t = 0.5`. To bound clean cost, A is applied to the **same 25% PGD
  sub-batch** budget (or a small dedicated fraction), not the whole batch.
- **Design intent (maps to §2):** the A term lowers `z_fall` *only along targeted nonfall→fall directions*
  → reduces confident nonfall→fall errors (failure 1) and should *raise* residual-FA entropy / lower
  residual P(fall) (failure 2 — the inversion); the B weight concentrates this on walk/run (failure 3);
  the unchanged `L_fall` term and the fall-weighted CE protect attacked + clean fall recall (failure 4).

**Optional (documented, NOT in the primary pilot):** a soft false-alert-budget penalty
`λ_b · relu(FP_batch_est − B_fp)` is **rejected** for the pilot — batch FP is a noisy, non-differentiable
proxy; the budget is enforced by **selection** (§6) instead, which is exactly Option C.

---

## 6. Checkpoint selection (seed-42 pilot)

Constrained, **not** recall-maximizing alone. Among all saved candidates, keep the one maximizing
validation PGD fall recall **subject to** all guards and the false-alert budget:

```
keep = argmax_{ckpt}  R_pgd^val(ckpt)
       s.t.  clean_acc^val      ≥ 0.70
             clean_macroF1^val  ≥ 0.65
             clean_fall_recall^val ≥ 0.90
             FP_pgd^val         ≤ B_fp
             walkrun_pgd^val    ≤ B_wr
```

Save the same top-k families as selection-v2 (v2safety / v2maxrec / v2lowFA / v2macroF1) so a budget-feasible
point is recoverable even if the headline candidate misses the budget.

**FP targets, justified against Variant F (seed 42 FP 115 / seed 44 FP 112; walk/run 80 / 73):**

| Tier | `B_fp` | `B_wr` | Rationale |
|---|---|---|---|
| Minimum improvement | **≤ 110** | **≤ 78** | strictly below Variant F seed-42 (115 / 80) — the floor that makes G "better than F" at all |
| Pilot target | **≤ 90** | **≤ 60** | ~22% FP cut, ~25% walk/run cut — meaningful but plausibly reachable by moving the smallest (~1.0) motion margins |
| Strong target | **≤ 80** | **≤ 60** | the diagnostic's unmet target (recall ≥ 0.50 & FP ≤ 80) — a genuine win if recall holds |

**Trade-off honesty (do not make targets impossible):** the diagnostic showed FP ≤ 80 was unreachable
*by post-hoc filtering at fixed geometry*. G's premise is that **training** can move the boundary so that
FP ≤ 80 becomes reachable **with** recall ≥ 0.50 — but this is a hypothesis, not a guarantee. Therefore
the **pilot target (FP ≤ 90, walk/run ≤ 60)** is the primary bar; FP ≤ 80 is the **strong/stretch** bar.
Selection must **never** satisfy the budget by dropping below the clean guards or the recall floor (§8) —
a budget-feasible point that fails the recall floor is a **failure**, not a success (this is exactly the
"FP cut only by destroying recall" trap from §9).

---

## 7. Pilot plan (seed-42 only, minimal compute)

- **λ/weight settings — exactly 3 runs** (mirrors the disciplined Variant F 3-setting pilot):
  1. `(λ_m, λ_f, λ_t, w_wr) = (1.0, 1.0, 1.0, 2.0)` — **primary**: Variant F base + targeted HN at parity weight + motion ×2.
  2. `(1.0, 1.0, 0.5, 2.0)` — gentler targeted pressure (clean-guard insurance).
  3. `(1.0, 1.0, 1.0, 1.0)` — **ablation anchor**: targeted HN on, source weighting off → isolates A vs B.
  Fixed: `γ_m = γ_f = γ_t = 0.5`, fall weight 3, batch-split mix, train ε {0.005, 0.015, 0.030}, eval ε
  0.030 — all identical to Variant F so the only changes are the A term and the B weight.
- **Baseline reuse — no retraining of baselines:** reuse committed **Variant F seed-42 v2safety** (115 / 80)
  and **Variant D seed-42** as references. Do **not** retrain D, E, selection-v2, or F. (Variant F seed-42
  is the head-to-head comparator.)
- **Metrics:** clean acc / macro-F1 / fall recall; PGD@0.030 fall recall, FP, walk/run→fall, specificity,
  precision, F1; 18-ε sweep + collapse-ε; logit-margin geometry (walk/run `z_fall−z_true`).
- **PGD-20 check:** evaluate PGD-20 recall; require non-collapse and recall non-increasing PGD-10→20
  (gradient-masking screen), same protocol as F.
- **Wilson intervals:** 95% Wilson CIs on PGD-10 and PGD-20 fall recall (n_f = 45).
- **False-alarm diagnostic reuse:** re-run the committed
  `scripts/diagnose_variantF_false_alarms.py`-style anatomy on the G v2safety PGD outputs (probability/logit
  export) and compare the **confidence-inversion** signature (median P(fall) and entropy of FAs vs detected
  true falls) against Variant F. **Reduced inversion is the mechanistic success signal**, independent of
  the raw FP count.
- **Gate to seed 44:** **no seed 44 / 45 / 46** until seed 42 shows a *genuine* improvement (§8 pilot
  target met **and** reduced inversion). If seed 42 only ties Variant F, stop and write it up as a negative.
- **Compute:** 3 training runs + eval ≈ one Variant F pilot's budget; bounded and pre-committed.

---

## 8. Success criteria (pre-registered before any training)

A seed-42 G candidate (v2safety unless noted) **succeeds** if **all** baseline conditions hold and at
least the **pilot target** tier is reached:

**Baseline (must all hold):**
- Clean acc ≥ 0.70
- Clean macro-F1 ≥ 0.65
- Clean fall recall ≥ 0.90
- PGD-10 fall recall ≥ **Variant F seed-42 v2safety (0.667) − 0.10 tolerance ⇒ floor 0.567**, and in no
  case below an absolute floor of **0.50**
- PGD FP **< 115** (strictly below Variant F seed 42)
- walk/run→fall **< 80** (strictly below Variant F seed 42)
- PGD-20 recall nonzero **and** ≥ 50% of PGD-10 recall
- No gradient-masking signature (recall non-increasing PGD-10→20)
- False-alarm diagnostic shows **reduced confidence inversion** vs Variant F (FA median P(fall) closer to
  or below detected-true-fall median, and/or FA entropy raised toward true-fall entropy)

**Pilot target (the bar that justifies seed-44 validation):**
- PGD FP ≤ **90** and walk/run→fall ≤ **60**, with PGD recall ≥ **0.50**

**Strong success (stretch — a clear thesis result):**
- PGD FP ≤ **80** with PGD recall ≥ **0.50** and walk/run→fall ≤ **60**, clean guards intact, inversion
  measurably reduced

Only a candidate meeting the **pilot target** (not merely the baseline floor) advances to a pre-registered
seed-44 validation.

---

## 9. Failure criteria (pre-registered)

Variant G **fails** (do not advance to seed 44; write up as negative) if **any** hold:

- **Clean guard fails** — clean acc < 0.70 or macro-F1 < 0.65 or clean fall recall < 0.90 on test.
- **Fall recall collapses** — PGD-10 recall < 0.50 (below the absolute floor), regardless of FP.
- **FP reduction only by destroying recall** — FP < 115 is achieved but only at recall below the 0.567
  tolerance floor, i.e. the selected point sits on the same inverted frontier the diagnostic already
  mapped (no genuine boundary movement).
- **Confidence inversion unchanged** — FA median P(fall) still exceeds detected-true-fall median by a
  similar gap and FA entropy still below true-fall entropy → the geometry did not move (the core G
  hypothesis is falsified even if FP nudges down).
- **PGD-20 collapses** — PGD-20 recall ≈ 0 or < 50% of PGD-10, or recall *increases* PGD-10→20 (masking).
- **Improvement too small** — G ties Variant F within noise (FP not strictly < 115 by a margin beyond
  Wilson/run-to-run noise, or pilot target unmet) → not worth seed-44 compute.

---

## 10. Advisor recommendation

**Best research value per compute hour: write the thesis now; keep Variant G as a *pre-registered,
optional* single seed-42 pilot to run only if time permits after the draft.**

- **Should we run the Variant G seed-42 pilot?** **Optional, and only after the Chapter-6 draft.** The
  thesis claim is already complete and defensible: a margin-aware safety-proxy defense (Variant F) with
  two-seed STRONG SUPPORT, *plus* an honest diagnostic showing its residual false alarms are
  high-confidence and not post-hoc filterable. That arc — including the *negative* result — is a finished,
  committee-ready story. Variant G is an **enhancement**, not a gap that blocks the thesis.
- **Or write thesis now and make Variant G future work?** **Yes — primary recommendation.** Draft Chapter
  6 (and the rest) from committed evidence first. Variant G is well-specified here and can be cited as
  "pre-registered future work" with this memo as the artifact, costing zero compute now.
- **Best value per hour:** (1) **write the thesis** (near-zero compute, unblocks submission); (2) *if*
  time/GPU remain, **the G seed-42 pilot** (3 runs, ~one F-pilot budget) — high information value because
  it directly tests whether the *inversion* (the diagnostic's central finding) is trainable away; (3)
  seeds 45–46 last (confirmatory breadth, no new mechanism). The G pilot beats seeds 45–46 on
  value-per-hour because it tests a *new mechanism*; seeds 45–46 only widen CIs on a known one.
- **What would convince a committee this is worth doing?** The committed diagnostic already does the
  convincing: it shows (a) Variant F improved geometry but (b) residual FAs are confidence-inverted and
  unfilterable, so (c) the *only* remaining lever is a new training objective. Variant G is the direct,
  pre-registered response to (c) with falsifiable success/failure criteria and a bounded compute budget —
  textbook "diagnose, then design the targeted intervention." Whether it is *run* before submission or
  cited as pre-registered future work, the memo demonstrates the research reasoning a committee rewards.

**Bottom line:** Variant G is fully designed and pre-registered here. Recommended path — **thesis first,
G pilot optional-after-draft, seeds 45–46 last.** Do not run anything until you approve.

---

## Scope reminder
Documentation/pre-registration only. No training, no attacks, no seeds 45–46, no script change, no `.tex`
edit, no artifact overwrite. Window-level, digital-domain, white-box; **not** solved, **not** certified,
**not** clinical, **not** over-the-air. Variant G is **not** run.
