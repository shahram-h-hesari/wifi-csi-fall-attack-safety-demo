# Final defense-line closure — Variant F / G / H

> **Analysis & synthesis only.** No training, attacks, evaluation, H2/H3, seed 44/45/46; no script change,
> no `.tex` edit, no artifact overwrite, no commit until reviewed. Closes the safety-proxy defense
> experiment line on committed evidence through `737a559`. Window-level, digital-domain, white-box,
> processed CSI tensors; test n=500 (45 fall / 455 non-fall), ε=0.030. **No product / clinical / deployment
> / certified / over-the-air claim.**

## 1. Executive conclusion

The defense line does **not** produce a single universally dominant defense. It identifies **two validated
safety-proxy operating points** on a recall / false-alarm frontier:

1. **Variant F — higher-recall operating point** (two-seed validated; attacked recall 0.62–0.67 at FP ≈ 112–115).
2. **Variant G G1 — lower-false-alarm operating point** (two-seed validated; FP cut ~42% to 65 at matched recall).

**Variant H H1** was tested as a balanced dual-tail extension and was **REJECTED**: its modest false-alarm
reduction came at the cost of attacked fall recall, clean accuracy, macro-F1, and confidence inversion.

Therefore:
- **Variant F and Variant G G1 remain the validated defense results for Chapter 6.**
- **Variant H H1 is reported as a useful negative pilot / future-work boundary**, not a successful defense.
- **H2/H3 must not be run automatically.**
- **No H1 seed-44 validation is warranted.**
- **Any further Variant H work requires a new pre-registration.**

## 2. Evidence-chain timeline

| Stage / Variant | Purpose | Key result (committed) | Decision | Thesis role |
|---|---|---|---|---|
| **Variant F** (seed44 valid.) | margin-aware defense to raise attacked fall recall | clean acc 0.700, mF1 0.658, clean fall recall 0.978, **PGD recall 0.622**, PGD FP 112, walk/run→fall 73, PGD-20 0.511, inversion gap +0.121 | **Validated higher-recall point** (STRONG SUPPORT), but high false-alarm burden | Primary defense result (higher recall) |
| **Variant G G1** (seed44 valid.) | targeted nonfall→fall hard negatives + source-weighted motion margin to cut false alarms | clean acc 0.746, mF1 0.692, clean fall recall 0.956, **PGD recall 0.600**, **PGD FP 65 (14.3%)**, walk/run→fall 48, PGD-20 0.600 raw / 0.578 gated, inversion gap +0.043 | **Validated lower-false-alarm point** (STRONG VALIDATION). **Not** strict dominance over F (recall ~1 fall window lower) but large FP & walk/run improvement | Primary defense result (lower FP) |
| **False-alarm mechanism investigation** | why G1 still raises 65 FAs; what reaches <10% | residual FAs are upper-tail walk/run; <10% needs **FP ≤ 45**; current FP 65 → **≥ 20 fewer FP needed**; post-hoc gating **cannot** reach FP ≤ 45 at recall ≥ 0.50; **max recall at FP ≤ 45 = 0.356** | **<10% FP needs a new objective, not thresholding** | Motivates dual-tail design |
| **High-recall / low-FP feasibility** | can G1 reach recall > 80% & FP < 10%? | recall > 80% needs **≥ 37/45** falls; G1 seed44 **TP 27 → +10 needed**; FP ≤ 45 → **−20 needed**; gating **cannot create true positives**, so target is unreachable post-hoc; it is a **two-tail separation** problem | **Motivates Variant H** (future objective design) | Frames the aspirational target & two-tail framing |
| **Variant H H1** (seed42 pilot) | balanced dual-tail TopK objective (`L_nonfall-budget` + `L_fall-rescue`) | clean acc 0.662, mF1 0.591, clean fall recall 0.911, **PGD recall 0.489**, **PGD FP 94 (20.7%)**, TP/FN/FP/TN 22/23/94/361, PGD-20 0.467, inversion gap +0.061 | **REJECT** — clean guard fails; PGD recall < 0.60; FP gain small & only by sacrificing recall; inversion worsened | Negative pilot / future-work boundary (NOT a defense result) |

*Variant H H1 vs the same-seed reference (Variant G G1 seed42): G1 PGD recall 0.689, PGD FP 104, clean acc/mF1
0.716/0.670, PGD-20 0.622, inversion gap +0.012 — **H1 is dominated by G1 on every axis**.*

## 3. Final operating-point interpretation

| model | seed | clean acc | macro-F1 | clean fall recall | PGD recall | PGD FP (rate) | walk/run→fall | PGD-20 | inversion gap | status |
|---|---|---|---|---|---|---|---|---|---|---|
| **Variant F** | 44 (validated) | 0.700 | 0.658 | 0.978 | **0.622** | 112 (24.6%) | 73 | 0.511 | +0.121 | validated higher-recall point |
| **Variant G G1** | 44 (validated) | 0.746 | 0.692 | 0.956 | 0.600 | **65 (14.3%)** | 48 | 0.600 | +0.043 | validated lower-FP point |
| Variant H H1 | **42 (pilot, NOT validated)** | 0.662 | 0.591 | 0.911 | 0.489 | 94 (20.7%) | 67 | 0.467 | +0.061 | **REJECT (negative pilot)** |

> **Comparison caveat:** Variant H H1 is a **seed-42 pilot** and must **not** be over-compared to the
> seed-44 *validated* Variant F / G1 numbers as if it were a validation. The honest same-seed comparison is
> H1 seed42 **vs Variant G G1 seed42** (§2 footnote), where H1 is dominated. H1 appears here only as a
> **negative pilot**, not a frontier point.

**Interpretation:**
- **Variant F** is the **higher-recall** point, at a **larger false-alarm burden** (FP ≈ 112).
- **Variant G G1** is the **lower-false-alarm** point (FP 65) with **comparable, slightly lower** attacked
  recall (0.600 vs 0.622, overlapping Wilson intervals).
- **Variant H H1 does not improve the frontier** and **should not be used as a final defense**.

## 4. Mechanistic interpretation

Variant G established that **targeted nonfall→fall hard negatives + a source-weighted motion margin** reduce
walk/run false-fall confusion (FP 112→65 at matched recall, inversion +0.121→+0.043). Variant H H1 then
tested whether adding **balanced TopK tail pressure** could improve *both* tails at once — the high-risk
non-fall upper tail (`L_nonfall-budget`) and the weak fall-margin lower tail (`L_fall-rescue`).

H1 showed the **two tails are tightly coupled at the fall↔motion boundary**:
- `L_nonfall-budget` reduced false positives only modestly (104→94 same-seed), **but also suppressed
  attacked fall recall** (0.689→0.489) — pushing the fall logit down on motion windows spilled onto true falls.
- `L_fall-rescue` was **under-powered**: with `k_frac = 0.25` and ~2–5 fall windows per batch, its effective
  TopK was **k ≈ 1 fall/batch**, too weak to protect the hardest falls.
- **clean accuracy and macro-F1 dropped** below the guard (0.716/0.670 → 0.662/0.591 on test).
- **confidence inversion worsened** vs G1 (+0.012 → +0.061).

**Therefore H1 does not solve the recall/false-alarm frontier** — naive balanced dual-tail pressure trades
recall for a small FP reduction rather than separating the two distributions.

## 5. Final thesis-safe claim

> This thesis demonstrates that **safety-proxy-guided adversarial training can recover part of the attacked
> fall-detection performance** of a WiFi-CSI classifier under white-box PGD on processed CSI tensors. Rather
> than solving robustness, the defense line **exposes a recall / false-alarm frontier**: a margin-aware
> defense (**Variant F**) recovers attacked fall recall to 0.62–0.67 but leaves a high false-alarm burden,
> while a diagnostic-derived targeted hard-negative defense (**Variant G G1**) cuts attacked false alarms
> ~42% at matched recall — two **validated operating points** along the same frontier, each with two-seed
> evidence. A balanced dual-tail extension (**Variant H H1**) is reported as a **negative pilot**:
> naive simultaneous tail pressure degraded attacked recall, clean accuracy, macro-F1, and the
> confidence-inversion geometry, showing the two tails are coupled and not jointly improvable by this
> construction. All results are **research-stage, benchmark-level, window-level, digital-domain, white-box**
> evaluations with quantified uncertainty (Wilson intervals, n_f = 45). **No clinical validation, deployment
> readiness, product claim, certified robustness, or over-the-air result is claimed.**

*(Deliberately avoided: "solves fall detection", "clinically acceptable", "deployment-ready", "certified",
"guaranteed robust", "worst-case secure".)*

## 6. Chapter 6 recommendation

Recommended Chapter 6 structure (objective → code → evidence → interpretation, per the committed CH6 outline):
1. **Baseline FGSM adversarial training** (weak-PGD baseline / recall floor).
2. **Variant F** as the **higher-recall** validated defense (with its false-alarm cost).
3. **Variant G G1** as the **lower-false-alarm** validated defense (targeted hard-negative mechanism).
4. **Mechanism investigation** showing why **< 10% FP and > 80% recall** is hard (confidence inversion;
   upper-tail walk/run; gating cannot create true positives; two-tail problem).
5. **Variant H H1** as a **rejected pilot / boundary analysis** — *not* a main result.
6. **Final interpretation:** the defense **improves but does not solve** safety-proxy robustness; two
   validated operating points; honest residual limitations.

Explicit constraints on the chapter:
- Chapter 6 **must not** present H1 as a successful defense.
- Chapter 6 **must not** imply H2/H3 were run.
- Chapter 6 **must not** claim seed-44 validation for H1.
- Chapter 6 **may** use H1 to demonstrate **disciplined negative experimentation** and to motivate future work.

## 7. Stop / continue decision

**Current decision — STOP the current defense experiment line:**
- Do **not** run H2/H3 as currently defined.
- Do **not** run H1 seed 44.
- Do **not** start architecture changes.
- Do **not** run new hyperparameter search.
- **Move to synthesis and Chapter 6 writing** using Variant F + Variant G G1 as the validated results.

**Future work — only under a new written pre-registration:**
- lower `lambda_b` (less FP-suppression pressure),
- higher `lambda_r` (stronger fall rescue),
- a `k_abs` floor for `L_fall-rescue` (so it is not k ≈ 1/batch),
- validation-only operating-point selection (no test tuning),
- temporal / event-level aggregation (orthogonal, non-window-level route to a lower operational FA rate),
- an architecture-controlled study (ResNet18 / GRU / BiLSTM with the *same* loss, everything else fixed).

## 8. No-claim boundary

> ┌─────────────────────────────────────────────────────────────────────────────┐
> │ **NO-CLAIM BOUNDARY.** This work does **NOT** claim:                          │
> │ • clinical performance        • deployment readiness     • product readiness   │
> │ • certified robustness        • over-the-air attack resistance                 │
> │ • a universal defense         • robustness across all architectures            │
> │ • robustness across all datasets                                               │
> │ • < 10% false alarms with > 80% recall (this remains an *unmet* research target)│
> │ All results are window-level, processed-CSI-tensor, digital-domain, white-box,  │
> │ benchmark-level, research-stage, with quantified uncertainty.                   │
> └─────────────────────────────────────────────────────────────────────────────┘

## 9. Final recommendation

**Recommended next action:** update Chapter 6 using Variant F and Variant G G1 as the validated defense
operating points, include Variant H H1 only as a rejected pilot / future-work boundary, and stop further
defense experiments unless a new pre-registration is approved.

### Scope reminder
Synthesis only — no training/attacks/evaluation/H2/H3/seed44-46/script change/`.tex` edit/artifact
overwrite. Window-level, digital-domain, white-box; **not** solved, **not** certified, **not** clinical,
**not** deployment-ready, **not** over-the-air.
