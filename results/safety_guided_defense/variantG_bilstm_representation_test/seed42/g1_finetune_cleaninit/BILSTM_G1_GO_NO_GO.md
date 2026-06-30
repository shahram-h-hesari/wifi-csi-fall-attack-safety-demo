# BiLSTM G1 (clean-init fine-tune) seed-42 go/no-go (VALIDATION only)

_BiLSTM initialized from clean-qualified cross-arch checkpoint bilstm_seed42_best.pt (val acc 0.837,
fall recall 0.841), fine-tuned with the EXACT frozen Variant-G G1 objective + grad clip 5.0 + lr 3e-4
(RNN budget accommodation; pre-reg-permitted; documented deviation from from-scratch single-variable).
60 epochs (5234 s), early-stopped. Selection-v2 + clean guard. NO test set used. Eval PGD-10 (a=eps/6),
identical protocol to the LeNet G1 baseline. Bar = LeNet G1 (val PGD AUROC 0.876 / recall@FAR<=10% 0.477)._

## Verdict: **NO-GO — H0 (informative negative). The representation change does NOT lift the frontier; it is WORSE under PGD.**

## Validation, by selected checkpoint

| checkpoint (epoch) | clean AUROC | FGSM AUROC | **PGD AUROC** [CI95] | recall@FAR≤10% | clean guard |
|---|---|---|---|---|---|
| v2safety (45) | 0.990 | 0.758 | 0.710 [0.649, 0.770] | 0.023 | acc 0.728 / mF1 0.706 PASS |
| v2maxrec (57) | 0.993 | 0.746 | 0.692 [0.643, 0.740] | 0.000 | acc 0.722 / mF1 0.696 PASS |
| v2macroF1 (60) | 0.994 | 0.776 | **0.726** [0.675, 0.776] | 0.000 | acc 0.734 / mF1 0.718 PASS |
| v2lowFA | — | — | — | never selected | PGD recall never reached the 0.10 floor |

## Bar vs achieved

| criterion | LeNet G1 bar | best BiLSTM G1 | result |
|---|---|---|---|
| val PGD AUROC of P(fall) | 0.876 | **0.726** | **WORSE by ~0.15** (CIs disjoint) |
| val recall@FAR≤10% | 0.477 | ~0.02 | **WORSE** (near-zero) |
| clean guard | acc≥.70, mF1≥.65 | held (acc ~0.73) | pass |
| clean AUROC | ~0.99 | ~0.99 | equal |

## Reading

The BiLSTM has the **same excellent clean separability** as LeNet (clean AUROC ~0.99) but is **markedly
more fragile under PGD** (PGD AUROC 0.69-0.73 vs LeNet 0.876). The clean-init fine-tune trained stably
(clean guard held from ~ep17, grad-clip kept the ~14-17 grad norm in check) and the defense did lift PGD
fall recall above the undefended BiLSTM (~0.004 -> ~0.05 argmax), but nowhere near LeNet G1. Higher clean
headroom did NOT translate into adversarial robustness; the recurrent representation appears to let the
L-inf CSI perturbation propagate/compound through the temporal recurrence, collapsing fall probability
more than the CNN does.

## Conclusion for the representation hypothesis (pre-reg H0)

Pre-registration H1 (BiLSTM advances the frontier beyond G1 LeNet seed 44) is **rejected**; H0 (the
score-overlap barrier is representation-invariant) is supported and strengthened: a higher-clean-capacity
temporal backbone is **not more robust — it is less robust** under PGD@0.03. Combined with the five LeNet
interventions at ~0.876, the fall<->locomotion overlap under eps=0.03 L-inf PGD is a barrier that spans
both a CNN and a recurrent representation. TEST not touched (validation decisively NO-GO). PGD-20 moot
(no PGD-10 robustness to durability-check).

## Caveats / non-claims

Seed 42 only; clean-init deviation documented; n_fall(val)=44. This does not prove the barrier is
universal across ALL architectures/training regimes — it shows two representations (LeNet CNN, BiLSTM) and
six training interventions do not reach the target region. Not solved/certified/clinical/OTA.
