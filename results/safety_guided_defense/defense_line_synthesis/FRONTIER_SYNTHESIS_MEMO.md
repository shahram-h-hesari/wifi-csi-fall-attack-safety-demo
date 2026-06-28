# Frontier synthesis memo — what the safety-proxy defense line means

> **Writing/planning only — uncommitted, not final LaTeX.** No training, attacks, or evaluation were run for
> this memo; it interprets committed evidence through `c63ac92`. All metrics are window-level, white-box,
> digital-perturbation (PGD/FGSM L∞, ε=0.030), processed-CSI, research-stage. Test split n=500 (45 fall /
> 455 non-fall); validation n=496 (44 falls). **No clinical / deployment / product / certified /
> over-the-air claim.** The joint target — PGD fall recall > 80% AND attacked false-alarm rate < 10% — is
> **unmet**.

## 1. Purpose

The defense line evolved through Variants F → G → H → Option A (A1) → Option B (adaptive-Lagrangian
FAR-constrained). The aim of this memo is **not** to report another attempt but to interpret the line as a
whole now that the strongest mechanistic tools have been exhausted, and to decide what the results mean
scientifically and what (if anything) is worth doing next. The headline question throughout has been whether
any safety-proxy defense can hold **high attacked fall recall** and **low attacked false-alarm rate**
simultaneously on processed CSI under white-box PGD. The answer, on the committed evidence, is **no — and we
can now say *why*.**

## 2. Best prior frontier (the correct comparison point)

The defense line's strongest validated operating point is **Variant G G1, seed 44**:

> **PGD fall recall 0.600 (27/45), FP 65/455 (FAR 14.3%), clean guard held (clean acc 0.746).**

This — not A1 — is the correct baseline against which any later variant must be judged. (G1 seed 42 reaches
higher recall, 0.689, but at FP 104 / FAR 22.9%, a much worse false-alarm point.) Even G1 seed44 does **not**
meet the joint target; it is a *partial* operating point with FAR still above 10% and recall well below 80%.

## 3. Option B result (adaptive-Lagrangian FAR control)

Option B made the false-alarm-budget weight an adaptive Lagrange multiplier driven once per epoch by the
validation PGD false-alarm rate (rise when FAR > 10%, relax when FAR < 10%), with the fall-rescue floor
retained. Held-out test, the three validation-selected checkpoints:

| checkpoint | PGD recall | FP | FAR | clean acc | clean guard |
|---|---|---|---|---|---|
| maxscore | 0.422 (19/45) | 59 | 13.0% | 0.694 | **failed** |
| maxrec | 0.667 (30/45) | 85 | 18.7% | 0.668 | **failed** |
| minFA | 0.133 (6/45) | 36 | 7.9% | 0.698 | **failed** |

**Verdict: REJECT / informative negative.** The clean guard (clean acc ≥ 0.70) that held on *validation*
fails on *test* for all three checkpoints, and none matches G1 seed44's frontier with the guard intact.
maxrec's higher recall (0.667) comes with worse FP (85 vs 65) and a broken guard — a dominated trade, not a
frontier gain.

## 4. Threshold diagnostic conclusion

A post-hoc one-vs-rest threshold sweep on the PGD fall-probability (analysis of the committed test CSVs only)
shows the failure is **not** a poor choice of checkpoint or operating threshold:

- **No threshold on any Option B checkpoint reaches TP ≥ 37/45 and FP ≤ 45/455 simultaneously.**
- To detect **37/45** falls the model must accept **FP ≥ 95** (maxscore 95, maxrec 107, minFA 122) — roughly
  2–3× the 45-false-alarm budget.
- Holding **FP ≤ 45** caps recall at only **~0.24–0.33** (TP 11–15/45).

The target is unreachable *by any thresholding of these representations*. The limit is **representation /
frontier-level**, not checkpoint-selection or threshold-selection.

## 5. Score-overlap interpretation (plain thesis language)

The mechanism is a **distribution overlap**. Under PGD the model's fall-probability on genuine attacked
**fall** windows is pushed down (median ≈ 0.13–0.27) until it sits inside the **upper tail of the
fall-probability assigned to attacked non-fall windows** (non-fall upper quartile ≈ 0.07–0.15). When the
"this is a fall" scores for true falls and for adversarial non-falls overlap this much, **no single decision
threshold can separate them**: lowering the threshold to catch more falls necessarily admits a comparable
flood of false alarms. Error-routing confirms the locus — under attack, missed falls are predicted mostly as
**walk/run**, and false alarms originate mostly from **walk/run**. The **fall ↔ walk/run boundary** is the
persistent failure region; the adversary collapses fall and locomotion into one another, and a safety-proxy
loss reshaping the LeNet decision surface cannot pull them back apart.

## 6. Cross-architecture evidence

The repository's committed cross-architecture pilots (undefended, five seeds each) show that **every**
backbone — LeNet, GRU, BiLSTM, Transformer, ResNet18 — collapses to **≈ 0% attacked fall recall under
PGD@0.03** (mean 0.000, near-zero variance; all reach 0.000 by ε ≤ 0.035). **Capacity alone is not
robustness:** a deeper or recurrent or attention model, trained normally, is just as completely broken under
white-box PGD as the shallow CNN. What recovered any attacked recall at all was the *defense* (adversarial
training plus the safety-proxy objective), not the architecture.

However, those same architectures carry **substantially higher clean headroom** — clean fall recall 0.89
(BiLSTM), 0.95 (Transformer), 0.98 (ResNet18), and clean accuracy ≈ 0.81 (BiLSTM) versus defended-LeNet's
≈ 0.70. Clean headroom is precisely the axis on which A1 and Option B failed (their clean guard did not
generalize from validation to test). So a *defended* stronger backbone is **not** ruled out — it is the one
remaining narrow hypothesis worth a single controlled test (Section 8), distinct from the refuted
"capacity = robustness" claim.

## 7. Why to stop LeNet loss-reweighting

On LeNet the line has now tried: motion-margin hard negatives (E/F), targeted nonfall→fall hard negatives
with source weighting (G), static dual-tail TopK rescue + budget (H1), a rebalanced static dual-tail with a
fall-rescue floor (A1), and an **adaptive** Lagrangian FAR controller (Option B). H1, A1, and Option B are
all rejects, and the Option B threshold diagnostic shows the residual barrier is the **overlap of the
attacked fall and non-fall score distributions** — a property of the learned representation, not of the loss
weights. Reweighting the same two margin terms on the same LeNet features therefore cannot, even in
principle, reach a threshold that separates the two classes. **Another LeNet λ variant is not scientifically
justified; the loss-reweighting question on this backbone is settled (negative).**

## 8. Recommended next experiment — only if time allows

A **single pre-registered** experiment, not a grid:

- **One** stronger-clean-headroom backbone (**BiLSTM** preferred — highest clean headroom in the
  recurrent/attention set — or Transformer), **seed 42 only**, using the **frozen Variant G1 objective**
  (no new loss tuning), the same UT-HAR split, ε=0.030, same selection-v2-style guard, same Gate-5 held-out
  test protocol.
- **Hypothesis:** a backbone with more clean headroom keeps the clean guard above 0.70 **on test** (where
  LeNet defenses failed) while the safety objective still recovers attacked recall.
- **Success criteria:** compare against **G1 seed44** (recall ≥ 0.60, FP ≤ 65, clean guard holds on test) and
  the **final target** (recall ≥ 0.80, FP ≤ 45). Anything short is reported honestly as a further partial /
  negative result.
- **Cost/odds caveat:** defended training of a recurrent/attention backbone is materially more expensive than
  LeNet, and the score-overlap barrier may persist even with better features. Treat this as a *bounded test
  of one hypothesis*, not a likely solution.

## 9. Future work

**Temporal / event-level aggregation** (declaring "fall" only when several neighboring windows agree) is a
plausible way to suppress *isolated* false alarms, but it is **future work**, for two reasons: (a) the
current per-window CSVs do not carry verified temporal contiguity or event identity, so it **cannot** be
tested post-hoc — it requires reconstructing window ordering/event grouping from the raw UT-HAR sequence;
and (b) it **changes the evaluation unit** from window to event, so any gain must be reported as an
event-level post-processing result, not a window-level robustness improvement, and must not be framed as
deployment readiness. Under a white-box adaptive adversary, a temporal rule can itself be attacked across a
run of windows, so its robustness benefit is not assumed.

## 10. Thesis wording (draft paragraphs for later Chapter 6/7 adaptation)

> Across a graduated sequence of safety-proxy defenses — motion-margin hard negatives, targeted
> non-fall→fall hard negatives, static dual-tail rescue/budget terms, and an adaptive Lagrangian controller
> that regulates the false-alarm budget directly against the validation attacked false-alarm rate — no
> window-level configuration achieved high attacked fall recall and a low attacked false-alarm rate
> simultaneously under white-box L∞ PGD on processed CSI. The strongest validated operating point (Variant G,
> seed 44) detects 60% of attacked falls at a 14.3% false-alarm rate while preserving clean performance; the
> later variants either reduced false alarms by collapsing recall or raised recall at the cost of more false
> alarms and a clean-accuracy guard that failed to generalize from validation to the held-out test.

> A post-hoc threshold analysis of the best adaptive-controller checkpoints explains why. The attacked
> fall-probability distribution for genuine falls overlaps the upper tail of the attacked fall-probability
> distribution for non-fall activities, so no decision threshold separates them: detecting 37 of 45 attacked
> falls requires accepting at least 95 false alarms, while constraining false alarms to the 10% budget caps
> recall near one third. The barrier is therefore representation-level rather than a matter of loss weighting
> or threshold choice, and it is concentrated at the fall–versus–walk/run boundary, where the perturbation
> collapses falls and locomotion into one another. A complementary observation — that undefended recurrent,
> attention, and deeper convolutional backbones all collapse to near-zero attacked fall recall under the same
> perturbation — indicates that model capacity alone does not confer robustness; the safety-proxy training is
> what recovers any attacked sensitivity at all.

> These findings are research-stage and window-level, measured under white-box digital perturbations of
> processed CSI tensors with quantified uncertainty; they are not claims of clinical, deployment, product,
> certified, or over-the-air performance. Their contribution is diagnostic: they delineate a safety-proxy
> recall / false-alarm frontier that conventional accuracy or single-operating-point reporting would obscure,
> and they localize the residual obstacle to a representation-level overlap at the fall/locomotion boundary —
> motivating, as bounded future work, a single controlled test of a stronger clean backbone under the frozen
> defense objective and, separately, an event-level aggregation analysis, rather than further loss-weight
> tuning on the shallow model.

### Scope reminder
Writing/planning only — no training/attacks/evaluation/`.tex`/result-file change. Interprets the committed
defense line as a representation-frontier-limited negative result, recommends stopping LeNet loss-reweighting,
and frames one bounded architecture test plus event-level aggregation as future work. Starts nothing.
