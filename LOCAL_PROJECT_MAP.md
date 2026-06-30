# Local Project Map

> Path reference only. No experiment results are reproduced here.
> For result details and claim evidence see `README.md` and `EXPERIMENT_EVIDENCE_INDEX.md`.

---

## Repository Root

| Item | Path |
|---|---|
| Repo root | `C:\Users\Hesar\Documents\GitHub\wifi-csi-fall-attack-safety-demo` |
| Main documentation | `README.md` · `EXPERIMENT_EVIDENCE_INDEX.md` |
| This file | `LOCAL_PROJECT_MAP.md` |
| Dependencies | `requirements.txt` |
| Gitignore | `.gitignore` |
| Third-party notices | `THIRD_PARTY_NOTICES.md` |
| Root-level pilot logs | `A1_seed42_pilot_run.log`, `basat_*.log`, `bilstm_*.log`, `optionB_*.log` — local-only, gitignored |

---

## Scripts

| Folder | Purpose |
|---|---|
| `scripts/` | All experiment, training, evaluation, and analysis scripts |
| `scripts/archive/` | Older or superseded scripts |
| `scripts/__pycache__/` | Python byte-cache (local-only, gitignored) |

Key script groups:

| Group | Representative files |
|---|---|
| Smoke test / clean baseline | `run_sensefi_smoke_test.py`, `run_sensefi_clean_baseline_short.py`, `train_converged_clean_baseline.py` |
| Attack evaluation | `run_converged_attacks.py`, `export_*_predictions_*.py`, `export_attack_prediction_sweep_18eps.py` |
| Safety-proxy metrics | `compute_clean_safety_metrics.py`, `compute_fgsm_safety_metrics.py`, `compute_pgd_safety_metrics.py`, `compute_defended_safety_metrics.py` |
| FGSM adversarial training defense | `train_fgsm_adversarial_defense_short.py`, `train_converged_defense.py` |
| Safety-guided defense (Variants A–D) | `train_safety_guided_defense.py`, `build_safety_guided_comparison.py` |
| Capstone — BASAT | `train_basat.py`, `train_basat_gairat.py`, `train_basat_sat.py` |
| Capstone — BiLSTM | `train_bilstm_clean.py`, `train_bilstm_g1.py`, `train_bilstm_g1_finetune.py` |
| Capstone — DSGE gate | `gate_dual_specialist.py`, `adaptive_gate_attack.py` |
| Capstone — analysis/figures | `compute_g1_baseline_val_frontier.py`, `plot_dsge_stage_a.py`, `create_representation_ceiling_figure.py` |
| Multi-seed and cross-architecture | `run_multiseed_converged_pipeline.py`, `summarize_multiseed_robustness.py`, `model_factory.py` |
| Thesis table/figure generation | `create_thesis_table_*.py`, `create_thesis_figure_*.py` (Tables/Figures 1–27) |
| Analysis and diagnostics | `analyze_*.py`, `diagnose_*.py`, `audit_*.py` |
| Chapter artifact generation | `generate_ch04_converged_artifacts.py`, `generate_ch05_converged_artifacts.py`, `generate_ch06_converged_artifacts.py` |

---

## Data

| Item | Path | Status |
|---|---|---|
| UT-HAR dataset root | `Data/` (verify path locally) | Local-only, gitignored |
| SenseFi / WiFi-CSI-Sensing-Benchmark clone | `third_party/WiFi-CSI-Sensing-Benchmark/` | Local-only, gitignored |
| UT-HAR original source clone | `third_party/WiFi_Activity_Recognition/` (verify path locally) | Local-only, gitignored |

---

## Results

| Folder | Contents |
|---|---|
| `results/` | All experiment result CSVs, JSON metadata, and markdown reports |
| `results/converged_baseline/` | Converged clean LeNet baseline metrics and predictions |
| `results/converged_attacks/` | FGSM and PGD attack metrics, epsilon sweeps, confusion CSVs |
| `results/converged_defense/` | FGSM adversarial training defense metrics |
| `results/multiseed_robustness/` | LeNet 5-seed (42–46) attack robustness summary |
| `results/cross_architecture/` | 5-architecture × 5-seed attack robustness summary |
| `results/epsilon_sweep_predictions/` | 18-epsilon FGSM/PGD prediction sweep CSVs |
| `results/converged_ch04_artifacts/` | Chapter 4 converged result artifacts |
| `results/converged_ch05_artifacts/` | Chapter 5 converged result artifacts |
| `results/converged_ch06_artifacts/` | Chapter 6 converged defense figures |
| `results/safety_guided_defense/` | All safety-guided defense variants and capstone experiments |
| `results/thesis_table_*.csv` | Thesis table CSVs (Tables 1–27), committed at root of `results/` |

---

## Safety-Guided Defense Results

| Subfolder | Contents | Git status |
|---|---|---|
| `results/safety_guided_defense/MULTISEED_PLAN.md` | Frozen multi-seed Variant D protocol | Committed |
| `results/safety_guided_defense/seed42/` | Variant A–D pilot: logs, test_eval, figures, SEED42_REPORT.md, comparison CSV | Committed |
| `results/safety_guided_defense/seed43/` · `seed44/` | Multi-seed partial results | Committed |
| `results/safety_guided_defense/decision_analysis/` | False-alarm decision analysis: threshold sweeps, probability CSVs, figures | Committed |
| `results/safety_guided_defense/defense_line_synthesis/` | Defense-line and frontier synthesis memos | Committed |
| `results/safety_guided_defense/final_defense_synthesis/` | Capstone synthesis memos and figures | Committed |
| `results/safety_guided_defense/variantE_*` | Variant E (motion hard-negative) design memo and results | Committed |
| `results/safety_guided_defense/variantF_*` | Variant F (motion margin) design memo and results | Committed |
| `results/safety_guided_defense/variantG_targeted_hardneg/` · `variantG_design_memo/` | Variant G experiments | Committed |
| `results/safety_guided_defense/variantH_*` | Variant H (dual-tail budget) design memo and results | Committed |
| `results/safety_guided_defense/boundary_aware_selective_at/` | BASAT seed-42: frontier JSON/MD, stage closeouts | Committed |
| `results/safety_guided_defense/dual_specialist_safety_gate/` | DSGE A1/seed-42: gate config, grid, frontier, metrics, probabilities, report, draft | Committed |
| `results/safety_guided_defense/representation_bilstm/` | BiLSTM G1 representation test — `NON_CONVERGENCE_DO_NOT_CITE.md` | Committed |
| `results/safety_guided_defense/variantG_bilstm_representation_test/` | BiLSTM G1 preregistration and go/no-go decision | Committed |
| `results/safety_guided_defense/final_defense_synthesis/REPRESENTATION_CEILING_CAPSTONE.md` | Capstone synthesis memo | Committed |
| `results/safety_guided_defense/final_defense_synthesis/figures/representation_ceiling.png` | Representation ceiling figure | Committed |

---

## Figures

| Folder | Contents |
|---|---|
| `figures/` | Thesis Figures 1–27 and supporting plots (committed) |
| `figures/converged_ch04_artifacts/` | Chapter 4 figure set |
| `figures/converged_ch06_artifacts/` | Chapter 6 defense figure set (FGSM AT baseline) |
| `figures/multiseed_robustness/` | Multi-seed robustness figures |
| `results/safety_guided_defense/seed42/figures/` | Seed-42 pilot figures (fig1–fig3) |
| `results/safety_guided_defense/decision_analysis/figures/` | False-alarm decision analysis figures |
| `results/safety_guided_defense/final_defense_synthesis/figures/` | Capstone figures — `representation_ceiling.png` (committed) |
| `thesis_artifacts/chapter*/figures/` | Chapter-specific committed thesis figures |

---

## Thesis Artifacts

| Folder / File | Contents | Git status |
|---|---|---|
| `thesis_artifacts/chapter4/tables/` · `figures/` | Ch. 4 tables (CSV) and figures (PNG) | Committed |
| `thesis_artifacts/chapter5/tables/` · `figures/` | Ch. 5 tables (CSV) and figures (PNG) | Committed |
| `thesis_artifacts/chapter6/tables/` | Ch. 6 tables (CSV) — Tables 6.1–6.6 | Committed |
| `thesis_artifacts/chapter6/figures/ch06_figure_6_1` through `_6_7` | Ch. 6 defense figures | Committed |
| `thesis_artifacts/chapter6/figures/ch06_figure_6_9_pgd_separability_frontier.png` | PGD separability frontier (Figure 6.9) | Committed |
| `thesis_artifacts/chapter6/ch06_capstone_additions.tex` | Ch. 6 capstone LaTeX draft | Committed |
| Pre-capstone backup (outside repo) | `C:\Users\Hesar\Documents\GitHub\_backups\ch06_backup_pre_capstone_20260630.tex` | Local-only, outside repo; do not cite |
| `tables/` | LaTeX table source files | Committed |

Thesis Overleaf source lives in a **separate repo**:
`C:\Users\Hesar\Documents\GitHub\thesis-overleaf-local`

The authoritative Ch. 6 source file is:
`thesis-overleaf-local\overleaf_upload_ch06\ch06_robustness_enhancement.tex`

---

## Checkpoints

| Folder | Contents | Status |
|---|---|---|
| `checkpoints/converged_clean_baseline/` | Converged LeNet clean checkpoint(s) | Local-only, gitignored (`*.pt`) |
| `checkpoints/converged_defense/` | FGSM adversarial training checkpoint | Local-only, gitignored |
| `checkpoints/cross_architecture/` | Per-architecture checkpoints | Local-only, gitignored |
| `checkpoints/safety_guided_defense/seed42/` | Variant A–D seed-42 checkpoints | Local-only, gitignored |
| BASAT / BiLSTM / DSGE checkpoints | Verify path locally | Local-only, gitignored |

Regeneration information (exact command, seed, selection metric) is recorded in committed `*_metadata.json` files for every checkpoint.

---

## Backups and Scratch

| Item | Path | Notes |
|---|---|---|
| Script archive | `scripts/archive/` | Older or superseded scripts |
| Ch. 6 pre-capstone backup | `C:\Users\Hesar\Documents\GitHub\_backups\ch06_backup_pre_capstone_20260630.tex` | Moved outside repo; local-only; do not cite |
| Root-level pilot logs | `A1_seed42_pilot_run.log`, `basat_*.log`, `bilstm_*.log`, `optionB_seed42_pilot_run.log` | Local-only, gitignored (`*.log`) |

---

## Third-Party Dependencies

| Item | Local path | Notes |
|---|---|---|
| SenseFi / WiFi-CSI-Sensing-Benchmark | `third_party/WiFi-CSI-Sensing-Benchmark/` | Gitignored; source: SenseFi GitHub |
| WiFi Activity Recognition (UT-HAR raw) | `third_party/WiFi_Activity_Recognition/` (verify locally) | Gitignored |

---

## Recommended First Files to Read

| Priority | File | Why |
|---|---|---|
| 1 | `README.md` | Full project overview, milestones, all result numbers, claim boundary |
| 2 | `EXPERIMENT_EVIDENCE_INDEX.md` | Claim-to-evidence mapping with commit IDs and file paths |
| 3 | `results/safety_guided_defense/seed42/SEED42_REPORT.md` | Seed-42 safety-guided defense pilot summary |
| 4 | `results/safety_guided_defense/MULTISEED_PLAN.md` | Frozen multi-seed Variant D protocol |
| 5 | `results/safety_guided_defense/final_defense_synthesis/FINAL_DEFENSE_SYNTHESIS.md` | Capstone defense synthesis |
| 6 | `results/safety_guided_defense/final_defense_synthesis/REPRESENTATION_CEILING_CAPSTONE.md` | Representation ceiling capstone |
| 7 | `notes/final_fgsm_pgd_attack_safety_lab_report.md` | Attack-safety lab report (baseline evidence) |
| 8 | `thesis_artifacts/chapter6/ch06_capstone_additions.tex` | Ch. 6 capstone LaTeX draft |
