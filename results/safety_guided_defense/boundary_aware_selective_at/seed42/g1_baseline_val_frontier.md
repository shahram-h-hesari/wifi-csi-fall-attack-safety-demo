# G1 seed-42 validation frontier baseline (Safety-TRADES / BASAT Stage 1 reference)

_Generated 2026-06-29T15:35:18.744059+00:00. Read-only; no training; no test tuning._

Eval attack: committed `pgd` = PGD-10 (alpha=eps/6); `pgd20` = 20-step audit.
Bar is set against the **best** G1 selection-v2 checkpoint, not the matched selector, so the baseline cannot be gamed.

## Validation per-checkpoint (the go/no-go reference)

| checkpoint | val PGD AUROC P(fall) | val recall@FAR<=10% | argmax op-point |
|---|---|---|---|
| v2safety(=maxrec,ep58) val pgd | 0.8079 [0.764,0.852] | 0.2045 (TP=9/44, FP=43, FAR=0.095) | rec=0.568 / FAR=0.206 |
| v2lowFA(ep68) val pgd | 0.8756 [0.835,0.910] | 0.4773 (TP=21/44, FP=42, FAR=0.093) | rec=0.273 / FAR=0.053 |

## Go/no-go bar for Safety-TRADES Stage 1 (beat the BEST G1 checkpoint)

- best G1 val PGD AUROC = **0.8756** (v2lowFA(ep68) val pgd)
- best G1 val recall@FAR<=10% = **0.4773** (v2lowFA(ep68) val pgd)
- matched-selector v2safety AUROC = 0.8079, recall@FAR<=10% = 0.2045

**GO requires all of:**
1. best Safety-TRADES val PGD AUROC > 0.9056 (best G1 0.8756 + 0.03 meaningful margin)
2. best Safety-TRADES val recall@FAR<=10% >= 0.4773 (no worse than best G1)
3. clean guard holds (val acc>=0.70, macro_f1>=0.65)
4. PGD-20 reveals no gradient masking/collapse
5. confirm with paired bootstrap on matched-selector AUROC difference (CI excludes 0)

_Caveat: n_fall(val)=44; single-checkpoint AUROC CI half-width ~0.04. +0.03 is suggestive, not conclusive; matched-selector paired bootstrap + (deferred) seed replication confirm._

## Test reference (already-evaluated; NOT used for go/no-go)

- v2safety test pgd (PGD-10, ref): AUROC P(fall) = 0.8045 CI95[0.7599, 0.8453]
- v2safety test pgd20 (PGD-20, ref): AUROC P(fall) = 0.7822 CI95[0.7365, 0.8242]
