# Pre-registration — Defended BiLSTM under the frozen Variant-G/G1 objective (representation test)

> **PRE-REGISTRATION ONLY. NOT RUN. Do not start training until the user approves this spec.**
> A single controlled experiment to test whether a higher-clean-headroom backbone (BiLSTM), trained under the
> **identical frozen Variant-G G1 safety objective**, lifts the adversarial fall-recall / false-alarm frontier
> where LeNet could not. Window-level, digital-domain, white-box, processed UT-HAR CSI, ε=0.030.
> **No certified / clinical / deployment / product / over-the-air claim. The result is reportable whether it
> succeeds, partially succeeds, or fails.**

## 1. Motivation and hypothesis

The defense line (Variants E→H, Option A, Option B) and the DS-SGE Stage A gate established that the residual
barrier on LeNet is **representation-level**: under PGD the genuine-fall fall-probability collapses into the
upper tail of the non-fall fall-probability, two safety specialists trained to opposite errors are **nested
rather than complementary**, and post-hoc thresholding/gating cannot reach attacked recall ≥ 0.80 at
false-alarm rate ≤ 0.10. The committed cross-architecture pilots show BiLSTM has materially higher **clean**
headroom than LeNet (clean fall recall ≈ 0.89, clean accuracy ≈ 0.81, vs defended-LeNet ≈ 0.70) — and clean
headroom is exactly the axis on which A1 and Option B failed (their clean guard did not generalise from
validation to test). Note the refuted alternative: **undefended** BiLSTM (like every other undefended
backbone) collapses to ≈ 0 attacked fall recall under PGD@0.03, so capacity alone is *not* robustness; the
defense objective is what recovers attacked sensitivity.

**Hypothesis (H1, falsifiable):** trained under the frozen Variant-G G1 objective, a BiLSTM keeps the clean
guard above threshold *on the held-out test split* (where LeNet defenses failed) while the safety objective
recovers attacked fall recall, advancing the frontier beyond G1 LeNet seed 44.

**Null (H0):** the score-overlap barrier is representation-invariant; the defended BiLSTM does not advance the
frontier beyond G1 LeNet seed 44 (reported as a further informative negative).

## 2. The single variable

**Exactly one thing changes vs the frozen G1 LeNet run: the backbone (`build_model("lenet")` →
`build_model("bilstm")`).** Everything in §3–§6 is copied from the committed G1 configuration. This isolates
the representation as the sole independent variable.

## 3. Frozen objective (copied verbatim from `seed42_variantG_G1_metadata.json`)

    L_G = L_FWCE
        + λ_s · mean_{adv nonfall}   w_y · relu(γ_m + z_fall(x^adv)  − z_true(x^adv))      [B: src-weighted motion margin]
        + λ_f · mean_{adv true-fall}       relu(γ_f + max_{c≠fall} z_c(x^adv) − z_fall(x^adv)) [F: fall preservation]
        + λ_t · mean_{tgt nonfall}   w_y · relu(γ_t + z_fall(x̂)     − z_true(x̂))           [A: targeted nonfall→fall hard-neg]

Frozen G1 constants (unchanged): **λ_s = 1.0, λ_f = 1.0, λ_t = 1.0, w_wr = 2.0** (walk=run source weight; all
other classes weight 1), **γ_m = γ_f = γ_t = 0.5**, **fall_weight = 3.0**. `L_FWCE` is fall-weighted
cross-entropy over the mixed batch; targeted-to-fall PGD x̂ is **descent on CE-to-fall** (sign-flipped vs the
untargeted attack). The loss operates only on logits, so it is **architecture-agnostic and is not modified.**

**Frozen training protocol (unchanged):** batch-split mixing 50% clean / 25% FGSM / 25% PGD; multi-epsilon
training set {0.005, 0.015, 0.030} sampled per batch; training PGD = 7 steps, α = train_ε/4; Adam lr = 1e-3;
batch size 64; drop_last = True; up to 70 epochs. (Training-budget knobs — lr, epochs, early-stop patience —
are the *only* items that may be tuned, and only on validation, only if BiLSTM fails to converge under the
LeNet schedule; any such change is logged in metadata before the locked test eval. No loss term, λ, γ, or
fall_weight may change.)

## 4. Dataset split (frozen)

Committed UT-HAR / SenseFi split, byte-identical loader: **train 3977 / val 496 (44 fall) / test 500
(45 fall, 455 non-fall).** No re-split, no re-shuffle of split membership. The **test split is never used for
training, selection, early stopping, or tuning.**

## 5. Attacks and evaluation protocol (frozen, ε=0.030)

- **Clean**, **FGSM** (single-step, ε=0.030), **PGD** (steps=10, α=ε/6, ε=0.030) — the thesis evaluation
  protocol. Attacks operate directly on the processed-CSI input tensor; BiLSTM consumes the same
  `(N,1,250,90)` tensor (it reshapes internally to `(N,250,90)`), so the perturbation code is unchanged.
- **PGD-20 durability check** (steps=20) on the selected checkpoint(s), as in the G1 evaluation, to confirm
  attacked recall is not a weak-attack artefact.
- Safety-proxy metrics (identical definitions): fall recall, missed-fall rate, false-alarm rate
  (FP/455 on test), fall precision, fall F1, accuracy, TP/FN/FP/TN; plus the **SafetyScore**
  = 0.35·clean_fall_recall + 0.45·pgd_fall_recall + 0.10·fgsm_fall_recall − 0.10·normalized_false_alarm_burden.

## 6. Selection-v2 and clean guard (frozen)

Per-epoch validation selection writes four checkpoints — **v2safety, v2maxrec, v2lowFA, v2macroF1** — under
the frozen selection-v2 rule, with the **clean-collapse guard: clean validation accuracy ≥ 0.70 AND clean
validation macro-F1 ≥ 0.65** (lowFA additionally enforces a fall-recall floor of 0.10). Selection uses
**validation only**.

## 7. Implementation requirements (to resolve before the run; no training yet)

1. Generalise the Variant-G trainer to accept `--model bilstm` and call `build_model(args.model)`; **make no
   other change** to the loss, mixing, attacks, selection, or guard. (The frozen LeNet path must remain
   reproducible: `--model lenet` must still reproduce G1.)
2. Verify the BiLSTM forward path accepts the `(N,1,250,90)` tensor (model_factory documents the internal
   `x.view(-1,250,90)`); confirm gradients flow to the input for FGSM/PGD and targeted-to-fall PGD.
3. **Self-check gate** (no training, no checkpoint): class-index assertions, targeted-PGD sign check, and a
   one-batch loss decomposition on BiLSTM, mirroring the G1 self-check.
4. **Smoke gate** (2-epoch tiny run in a `_smoke` namespace): confirms the loss decreases, the four selection
   checkpoints are written, and per-epoch validation diagnostics populate. Only after self-check + smoke pass
   is the full run proposed for approval to launch.

## 8. Pre-registered decision criteria (seed 42)

Comparisons are made on the **held-out test split**, against two reference points:
- **G1 LeNet seed 44 (best prior frontier):** PGD recall 0.600, FP 65/455 (FAR 14.3%), clean guard held.
- **DS-SGE Stage A (LeNet gate):** locked PGD recall 0.400 / FAR 0.121; adaptive full-gate PGD 0.467 / 0.246;
  nested specialists (no frontier gain).

| Outcome | Criteria (held-out test) |
|---|---|
| **Strong / target** | PGD recall ≥ 0.80 **and** FP ≤ 45 (FAR ≤ 10%) **and** clean guard holds on test **and** PGD-20 durable. |
| **Frontier advance** | Clean guard holds on test **and** (PGD recall ≥ 0.60 at FP < 65) **or** (FP ≤ 65 at PGD recall > 0.60) — i.e. strictly dominates G1 seed 44 on at least one axis without losing the other or the guard. |
| **Minimum useful** | Clean guard holds on test **and** PGD recall ≥ 0.60 **and** FP ≤ 65 **and** PGD-20 recall > 0. |
| **Informative negative** | Guard fails on test, **or** no checkpoint matches G1 seed 44 with the guard intact (frontier not advanced). Report honestly; this still answers whether the barrier is representation-invariant. |

A pre-registered **independent seed (seed 44)** confirmation is required **only if** seed 42 reaches *frontier
advance* or better, under a separate brief pre-registration. No multi-seed sweep is authorised by this
document.

## 9. Outputs (non-overwriting)

New namespace, mirroring the committed variant layout; nothing prior is overwritten:

    results/safety_guided_defense/variantG_bilstm_representation_test/seed42/
        logs/        (training_log.csv, console)
        metadata/    (metadata.json incl. frozen-objective hash + git commit + the single backbone change)
        analysis/    (selection_candidates.csv)
        test_eval/   (clean/fgsm/pgd per-window probability CSVs via export_probability_predictions.py --model bilstm;
                      PGD-20 durability; safety metrics CSVs)
        REPORT.md
    checkpoints/safety_guided_defense/variantG_bilstm_representation_test/seed42/
        seed42_variantGbilstm_G1_{v2safety,v2maxrec,v2lowFA,v2macroF1}_best.pt, _last.pt

## 10. Rules, cost, risks

- **No test tuning. No dataset-split change. No loss change. No claim of certified / clinical / deployment /
  OTA robustness.** Report negatives honestly.
- **CPU cost estimate:** defended training of a recurrent backbone is materially more expensive than LeNet
  (G1 LeNet was ≈ 1.8 h / 70 epochs on CPU; BiLSTM with per-batch FGSM+PGD+targeted-PGD generation may run
  several×). A self-check + 2-epoch smoke will calibrate the per-epoch time before the full run is launched.
- **Risks:** (1) the score-overlap barrier may be representation-invariant — BiLSTM may collapse under PGD just
  as LeNet did (then H0, informative negative); (2) BiLSTM's clean guard may *also* fail to generalise
  val→test; (3) recurrent adversarial training may be unstable on CPU under the LeNet lr/epoch schedule
  (mitigated by the smoke gate and validation-only budget tuning). The experiment is a **bounded test of one
  hypothesis**, not an expected solution.

## 11. Approval gate

**This spec starts nothing.** On approval: run §7 self-check → §7 smoke → report timing/sanity → request
explicit go for the full seed-42 run → locked test eval → REPORT.md. Each step is reviewed before the next.
