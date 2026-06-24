# Priority 2 — Cross-Architecture Multi-Seed Summary

Thesis-ready roll-up of the adversarial window-level safety-proxy collapse across
**five architecture types/model configurations** — spanning shallow CNN, deep CNN,
recurrent, bidirectional recurrent, and attention-based designs — on the
UT-HAR/SenseFi pipeline. Built **only** from already-committed result files (no
experiment rerun; no raw file modified). This note supersedes the seed-42-only
pilot table (`notes/priority2_seed42_cross_architecture_pilot.md`) by folding in
the completed multi-seed results for LeNet, GRU, ResNet18, and now **BiLSTM**,
while keeping the Transformer clearly labelled as a single-seed pilot.

> Note on "architecture types": LeNet and ResNet18 are **both CNN-family** models
> (shallow vs deep), so this is **not** five distinct model families. It is five
> architecture types/configurations: shallow CNN (LeNet), deep CNN (ResNet18),
> recurrent (GRU), bidirectional recurrent (BiLSTM), and attention (Transformer/ViT).

All quantities are window-level fall-vs-non-fall safety proxies on the held-out
test split (n = 500 windows; 45 fall / 455 non-fall), at matched ε = 0.030
(FGSM single-step L∞; PGD L∞, 10 steps, α = ε/6). Means are across the
**clean-qualified** seeds for each architecture; SD is sample SD (ddof=1).

## Evidence tiers (do not conflate)
1. **LeNet — full five-seed result** (Priority 1; seeds 42–46). PGD@0.03 exact
   collapse 5/5 (zero variance).
2. **GRU — full five-seed result** (Priority 2; seeds 42–46). PGD@0.03 exact
   collapse 5/5 (zero variance).
3. **BiLSTM — full five-seed result** (Priority 2; seeds 42–46). PGD@0.03 exact
   collapse **4/5**; **all 5/5 reach PGD fall recall 0.000 by ε ≤ 0.035**. Seed 45
   is the exception at the matched budget (see below).
4. **ResNet18 — clean-qualified multi-seed result** (4/5 seeds; seed 45 excluded
   as non-converged/diverged, not a robustness signal). PGD@0.03 exact collapse
   4/4 clean-qualified.
5. **Transformer (ViT) — seed-42 pilot only** (single seed).

## Cross-architecture table
| Architecture | Type | Seeds (clean-qual.) | Clean fall recall | FGSM@0.03 fall recall | PGD@0.03 fall recall | Exact 0.000 @ε=0.03 (FGSM / PGD) | Evidence status |
|---|---|---|---|---|---|---|---|
| LeNet | shallow CNN | 5/5 (42–46) | 0.978 ± 0.016 | 0.049 ± 0.046 | **0.000 ± 0.000** | 2/5 / **5/5** | full five-seed |
| GRU | recurrent | 5/5 (42–46) | 0.920 ± 0.012 | 0.009 ± 0.012 | **0.000 ± 0.000** | 3/5 / **5/5** | full five-seed |
| BiLSTM | bidirectional recurrent | 5/5 (42–46) | 0.884 ± 0.043 | 0.022 ± 0.050 | 0.004 ± 0.010 | 4/5 / **4/5** † | full five-seed |
| ResNet18 | deep CNN | 4/5 (42,43,44,46) | 0.972 ± 0.011 | 0.011 ± 0.013 | **0.000 ± 0.000** | 2/4 / **4/4** | clean-qualified multi-seed |
| Transformer | attention (ViT) | 1 (42) | 0.978 (n=1) | 0.000 (n=1) | 0.000 (n=1) | 1/1 / 1/1 | seed-42 pilot |

SD is shown only where ≥ 2 clean-qualified seeds exist; the Transformer pilot
shows the point value with "(n=1)" and **carries no multi-seed reliability claim**.

† **BiLSTM seed 45 is the exception at ε=0.03** and must not be rounded away:
FGSM@0.03 fall recall = **0.111**, PGD@0.03 fall recall = **0.022**; its **FGSM
fall recall never reaches exactly 0.000 within the 0.0–0.075 grid** (bottoms at
0.022), and its **PGD fall recall reaches exactly 0.000 at ε=0.035**. The other
four BiLSTM seeds (42, 43, 44, 46) reach exactly 0.000 under both attacks at
ε=0.03. **All 5/5 BiLSTM seeds reach PGD fall recall 0.000 by ε ≤ 0.035.**

PGD reaches exactly 0.000 fall recall by a small budget in every clean-qualified
seed of every architecture: LeNet by ε ≤ 0.0125, GRU by ε ≤ 0.025, ResNet18 by
ε ≤ 0.010, BiLSTM by ε ≤ 0.035, Transformer (pilot) by ε ≤ 0.025.

ResNet18 seed 45 diverged under the fixed protocol (clean accuracy 0.294, clean
fall recall 0.000, val loss ~10¹⁵, walk-only predictor) and is excluded from the
clean-qualified aggregate; its attacked 0.000 is not adversarial-collapse evidence
(there was no clean capability to lose). The same seed (45) trains cleanly for the
GRU and BiLSTM, so the divergence was a ResNet18/optimizer interaction, not a
property of the seed value.

## What is consistent across all architecture types
- Every clean-qualified configuration is a clean classifier with meaningful fall
  recall (clean fall recall 0.884–0.978; BiLSTM is the weakest clean family).
- **Matched PGD at ε = 0.03 drives window-level fall recall to exactly 0.000 in
  every clean-qualified seed of LeNet, GRU, and ResNet18, and in 4/5 BiLSTM
  seeds.** Counting all clean-qualified seeds across all five types, PGD@0.03
  reaches exactly 0.000 in 18/19 seed-runs — the lone exception is BiLSTM seed 45
  (PGD@0.03 = 0.022), which still reaches exactly 0.000 by ε=0.035.
- **Every clean-qualified seed of every architecture reaches exactly 0.000 PGD
  fall recall by ε ≤ 0.035.**
- FGSM at ε = 0.03 is near-total but more architecture/seed-variable (mean fall
  recall 0.009–0.049; exact-0.000 at ε=0.03 in only a minority of seeds per type),
  so FGSM should be described as "severe/near-total," not "exact collapse," at the
  matched budget.

## Thesis-ready table text (LaTeX; not yet inserted into any .tex)
```latex
% Cross-architecture multi-seed safety-proxy collapse (UT-HAR, eps=0.03).
% Window-level fall recall, mean +/- SD over clean-qualified seeds.
\begin{tabular}{l l c c c c l}
\toprule
Architecture & Type & Seeds (cq) & Clean recall & PGD$_{0.03}$ recall
  & PGD exact @0.03 & Evidence \\
\midrule
LeNet       & shallow CNN            & 5/5 & $0.978\pm0.016$ & $0.000\pm0.000$ & 5/5 & full five-seed \\
GRU         & recurrent              & 5/5 & $0.920\pm0.012$ & $0.000\pm0.000$ & 5/5 & full five-seed \\
BiLSTM      & bidirectional recurrent& 5/5 & $0.884\pm0.043$ & $0.004\pm0.010$ & 4/5 & full five-seed \\
ResNet18    & deep CNN               & 4/5 & $0.972\pm0.011$ & $0.000\pm0.000$ & 4/4 & clean-qual.\ multi-seed \\
Transformer & attention (ViT)        & 1   & $0.978$ (n=1)   & $0.000$ (n=1)   & 1/1 & seed-42 pilot \\
\bottomrule
\end{tabular}
% Note: BiLSTM seed 45 retains PGD@0.03 fall recall 0.022 (reaches 0.000 by eps=0.035);
% all 5/5 BiLSTM seeds reach PGD fall recall 0.000 by eps<=0.035.
```

## Generated package files
- `results/cross_architecture/cross_architecture_multiseed_summary.csv` (this roll-up)
- Per-architecture aggregates / sources:
  - LeNet: `results/multiseed_robustness/multiseed_summary_stats.csv` (+ `notes/thesis_ready_multiseed_summary.md`)
  - GRU: `results/cross_architecture/gru/gru_clean_qualified_summary.csv` (+ `notes/priority2_gru_5seed_aggregate.md`)
  - BiLSTM: `results/cross_architecture/bilstm/bilstm_clean_qualified_summary.csv` (+ `notes/priority2_bilstm_5seed_aggregate.md`)
  - ResNet18: `results/cross_architecture/resnet/resnet18_clean_qualified_summary.csv` (+ `notes/priority2_resnet18_multiseed_summary.md`)
  - Transformer: `results/cross_architecture/transformer/transformer_seed42_*`

## Thesis-safe interpretation
Holding the dataset, split, preprocessing, attack settings, and metric definitions
fixed, the adversarial window-level safety-proxy collapse reproduces across five
architecture types — a shallow CNN (LeNet), a deep CNN (ResNet18), a recurrent
network (GRU), a bidirectional recurrent network (BiLSTM), and an attention-based
network (Transformer/ViT). For the four multi-seed configurations, matched PGD at
ε = 0.030 drives window-level fall recall to exactly 0.000 in every clean-qualified
seed of LeNet, GRU, and ResNet18 (zero variance for LeNet and GRU across five seeds
each), and in four of five BiLSTM seeds; the single exception, BiLSTM seed 45,
retains PGD@0.03 fall recall 0.022 but still reaches exactly 0.000 by ε = 0.035, so
**every clean-qualified seed of every architecture reaches total PGD fall-recall
collapse by ε ≤ 0.035**. Clean fall recall is high to moderate beforehand
(0.884–0.978). Because the collapse reproduces across shallow CNN, deep CNN,
recurrent, bidirectional-recurrent, and attention architectures under an identical
data split, attack configuration, and metric definition, the missed-fall
safety-proxy failure is not an artifact of one architecture type or one training
seed. FGSM at the same budget is severe but more variable and should not be
described as exact collapse at ε=0.03.

## Boundary language (must accompany any use of these numbers)
- **Full five-seed multi-seed reliability is established for LeNet, GRU, and
  BiLSTM** (BiLSTM with the seed-45 ε=0.03 caveat above — 4/5 exact at ε=0.03,
  5/5 by ε ≤ 0.035). **ResNet18 is a 4-seed clean-qualified result** (1 excluded
  divergence). **The Transformer is a single-seed (seed-42) pilot** and must be
  reported as such — do **not** claim multi-seed reliability or full five-seed
  coverage for it.
- **Do not state that all five BiLSTM seeds collapse to exactly 0.000 at ε=0.03.**
  Correct: BiLSTM has a full five-seed clean-qualified result showing severe
  adversarial degradation; 4/5 seeds reach exact fall-recall collapse at ε=0.03,
  and all 5/5 reach PGD fall recall 0.000 by ε ≤ 0.035.
- These are **UT-HAR**, **processed-tensor**, **digital white-box** adversarial
  results — **window-level safety-proxy** metrics on software CSI feature tensors.
  They are **not** clinical fall-risk prediction, clinical deployment evidence,
  over-the-air / physical-layer / packet-level attacks, or certified robustness.
- See [[project_overview]], `notes/priority2_seed42_cross_architecture_pilot.md`,
  `notes/thesis_ready_multiseed_summary.md`, `notes/priority2_gru_5seed_aggregate.md`,
  `notes/priority2_bilstm_5seed_aggregate.md`, and
  `notes/priority2_resnet18_multiseed_summary.md` for full per-architecture detail.
