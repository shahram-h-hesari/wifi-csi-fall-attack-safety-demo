# Priority 2 — Cross-Architecture Multi-Seed Summary

Thesis-ready roll-up of the adversarial window-level safety-proxy collapse across
**five model families** on the UT-HAR/SenseFi pipeline. Built **only** from
already-committed result files (no experiment rerun; no raw file modified). This
note supersedes the seed-42-only pilot table
(`notes/priority2_seed42_cross_architecture_pilot.md`) by folding in the completed
multi-seed results for LeNet, GRU, and ResNet18, while keeping BiLSTM and
Transformer clearly labelled as **single-seed pilots**.

All quantities are window-level fall-vs-non-fall safety proxies on the held-out
test split (n = 500 windows; 45 fall / 455 non-fall), at matched ε = 0.030
(FGSM single-step L∞; PGD L∞, 10 steps, α = ε/6). Means are across the
**clean-qualified** seeds for each architecture; SD is sample SD (ddof=1).

## Evidence tiers (do not conflate)
1. **LeNet — full five-seed result** (Priority 1; seeds 42–46).
2. **GRU — full five-seed result** (Priority 2; seeds 42–46).
3. **ResNet18 — clean-qualified multi-seed result** (4/5 seeds; seed 45 excluded
   as non-converged/diverged, not a robustness signal).
4. **BiLSTM — seed-42 pilot only** (single seed).
5. **Transformer (ViT) — seed-42 pilot only** (single seed).

## Cross-architecture table
| Architecture | Family | Seeds (clean-qual.) | Clean fall recall | FGSM@0.03 fall recall | PGD@0.03 fall recall | PGD collapse | Evidence status |
|---|---|---|---|---|---|---|---|
| LeNet | CNN | 5/5 (42–46) | 0.978 ± 0.016 | 0.049 ± 0.046 | **0.000 ± 0.000** | 5/5 | full five-seed |
| GRU | recurrent | 5/5 (42–46) | 0.920 ± 0.012 | 0.009 ± 0.012 | **0.000 ± 0.000** | 5/5 | full five-seed |
| ResNet18 | deep CNN | 4/5 (42,43,44,46) | 0.972 ± 0.011 | 0.011 ± 0.013 | **0.000 ± 0.000** | 4/4 | clean-qualified multi-seed |
| BiLSTM | recurrent | 1 (42) | 0.889 (n=1) | 0.000 (n=1) | **0.000 (n=1)** | 1/1 | seed-42 pilot |
| Transformer | attention (ViT) | 1 (42) | 0.978 (n=1) | 0.000 (n=1) | **0.000 (n=1)** | 1/1 | seed-42 pilot |

SD is shown only where ≥ 2 clean-qualified seeds exist; single-seed pilots show
the point value with "(n=1)" and **carry no multi-seed reliability claim**.

ResNet18 seed 45 diverged under the fixed protocol (clean accuracy 0.294, clean
fall recall 0.000, val loss ~10¹⁵, walk-only predictor) and is excluded from the
clean-qualified aggregate; its attacked 0.000 is not adversarial-collapse evidence
(there was no clean capability to lose). The same seed (45) trains cleanly for the
GRU, so the divergence was a ResNet18/optimizer interaction, not a property of the
seed value.

## What is consistent across all five families
- Every clean-qualified configuration is a strong clean classifier (clean fall
  recall 0.889–0.978).
- **Matched PGD at ε = 0.03 drives window-level fall recall to exactly 0.000 in
  every clean-qualified seed of every architecture tested** — CNN (LeNet), deep
  CNN (ResNet18), recurrent (GRU, BiLSTM), and attention (Transformer). For the
  two full five-seed families (LeNet, GRU) this is a zero-variance collapse across
  five seeds each.
- FGSM at ε = 0.03 is near-total but more architecture/seed-variable
  (mean fall recall 0.000–0.049).

## Thesis-ready table text (LaTeX; not yet inserted into any .tex)
```latex
% Cross-architecture multi-seed safety-proxy collapse (UT-HAR, eps=0.03).
% Window-level fall recall, mean +/- SD over clean-qualified seeds.
\begin{tabular}{llccc l}
\toprule
Architecture & Family & Seeds (cq) & Clean recall & PGD$_{0.03}$ recall & Evidence \\
\midrule
LeNet       & CNN        & 5/5 & $0.978\pm0.016$ & $0.000\pm0.000$ & full five-seed \\
GRU         & recurrent  & 5/5 & $0.920\pm0.012$ & $0.000\pm0.000$ & full five-seed \\
ResNet18    & deep CNN   & 4/5 & $0.972\pm0.011$ & $0.000\pm0.000$ & clean-qual.\ multi-seed \\
BiLSTM      & recurrent  & 1   & $0.889$ (n=1)   & $0.000$ (n=1)   & seed-42 pilot \\
Transformer & ViT        & 1   & $0.978$ (n=1)   & $0.000$ (n=1)   & seed-42 pilot \\
\bottomrule
\end{tabular}
```

## Generated package files
- `results/cross_architecture/cross_architecture_multiseed_summary.csv` (this roll-up)
- Per-architecture aggregates / sources:
  - LeNet: `results/multiseed_robustness/multiseed_summary_stats.csv` (+ `notes/thesis_ready_multiseed_summary.md`)
  - GRU: `results/cross_architecture/gru/gru_clean_qualified_summary.csv` (+ `notes/priority2_gru_5seed_aggregate.md`)
  - ResNet18: `results/cross_architecture/resnet/resnet18_clean_qualified_summary.csv` (+ `notes/priority2_resnet18_multiseed_summary.md`)
  - BiLSTM: `results/cross_architecture/bilstm/bilstm_seed42_*`
  - Transformer: `results/cross_architecture/transformer/transformer_seed42_*`

## Thesis-safe interpretation
Holding the dataset, split, preprocessing, attack settings, and metric definitions
fixed, the adversarial window-level safety-proxy collapse reproduces across five
distinct model families — a shallow CNN (LeNet), a deep CNN (ResNet18), two
recurrent networks (GRU, BiLSTM), and an attention-based network (Transformer/ViT).
In every clean-qualified seed of every architecture, matched PGD at ε = 0.030
drives window-level fall recall to exactly 0.000 despite strong clean fall recall
(0.889–0.978). For the two families with completed five-seed sweeps (LeNet and
GRU), this collapse is zero-variance across all five seeds; ResNet18 shows the same
collapse across its four clean-qualified seeds. The failure is therefore not
specific to one architecture, one architecture family, or one training seed.

## Boundary language (must accompany any use of these numbers)
- **Multi-seed reliability is established for LeNet and GRU only** (full five
  seeds each); **ResNet18 is a 4-seed clean-qualified result** (1 excluded
  divergence). **BiLSTM and Transformer are single-seed (seed-42) pilots** and
  must be reported as such — do **not** claim multi-seed reliability, full
  five-seed coverage, or cross-architecture *reliability* for these two.
- These are **UT-HAR**, **processed-tensor**, **digital white-box** adversarial
  results — **window-level safety-proxy** metrics on software CSI feature tensors.
  They are **not** clinical fall-risk prediction, clinical deployment evidence,
  over-the-air / physical-layer / packet-level attacks, or certified robustness.
- See [[project_overview]], `notes/priority2_seed42_cross_architecture_pilot.md`,
  `notes/thesis_ready_multiseed_summary.md`, `notes/priority2_gru_5seed_aggregate.md`,
  and `notes/priority2_resnet18_multiseed_summary.md` for full per-family detail.
