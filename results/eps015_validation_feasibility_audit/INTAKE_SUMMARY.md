# Intake-Ready Summary — Task 3 Validation-Only Feasibility Audit @ PGD eps=0.015

**This is a prepared summary for a later, separately approved Research OS intake task.
`research-os` was NOT modified by Task 3.**

## Claim identifiers

- Analysis task: Task 3 (validation-only false-positive audit and operating-point feasibility
  sweep at PGD eps=0.015), following `research-os` decision receipt
  `automation/receipts/2026-07-12T000000Z_target-freeze_GOAL-EPS015-TARGET-FREEZE.json`
  (research-os commit `5fef192`).
- Experiment-repo commit at analysis time: `0d9ff96b15b7caf23b95b54a9feb6405251674c3`
  (branch `feature/safety-proxy-guided-defense`).

## Evidence paths (experiment repository, read-only inputs)

- `results/defense_attempt_inventory/pgd_epsilon_frontier/val_sweep/eps0015/*.csv` (5 axes,
  PGD condition; see hashes below)
- `results/defense_attempt_inventory/pgd_epsilon_frontier/h15_frozen_test_gate_numbers_eps0015.csv`
  (frozen validation-threshold source for AFAC_maxscore/ST1b6_lowFA/SA1_lowFA)
- `scripts/run_converged_attacks.py` (attack-norm verification source)

## New evidence artifact paths (this task's outputs, experiment repository)

- `results/eps015_validation_feasibility_audit/REPORT.md`
- `results/eps015_validation_feasibility_audit/inventory.csv`
- `results/eps015_validation_feasibility_audit/operating_point_sweep.csv`
- `results/eps015_validation_feasibility_audit/per_axis_summary.csv`
- `results/eps015_validation_feasibility_audit/false_positive_source_summary.csv`
- `results/eps015_validation_feasibility_audit/score_axis_overlap.csv`
- `results/eps015_validation_feasibility_audit/provenance_manifest.csv` (full hash list)

## Artifact hashes (inputs; full list in `provenance_manifest.csv`)

| Path | SHA256 |
|---|---|
| `.../val_sweep/eps0015/AFAC_maxscore_eps0015_pgd_probabilities_val_epsilon_0_015.csv` | `13a6012bbb77c93ff9f20d3202a939da073dd47c0bec91d309d28a25b66d3721` |
| `.../val_sweep/eps0015/D14B_seed44_eps0015_pgd_probabilities_val_epsilon_0_015.csv` | `bbf75df3df4a504d6113902702edf629273396ea40e809cf63c58b7abad4fa83` |
| `.../val_sweep/eps0015/GR1_macroF1_eps0015_pgd_probabilities_val_epsilon_0_015.csv` | `cfebd6f801637ca8d0d013cebdc445c96e0973915e33e3dbd5b64f5a4cb2c540` |
| `.../val_sweep/eps0015/SA1_lowFA_eps0015_pgd_probabilities_val_epsilon_0_015.csv` | `2cd6b5ae3ab935bad7bb7facb3f4fe297e75c3d91ebd320ba1e0f0ee555429f0` |
| `.../val_sweep/eps0015/ST1b6_lowFA_eps0015_pgd_probabilities_val_epsilon_0_015.csv` | `9bada3d24549692af932ee720124a1934a26a573a627069c2c78d29f31a6fb8f` |

## Protocol metadata (context; unchanged, not re-derived)

- Frozen test protocol: `H15-TEST-EPS0015-AFAC-20260705` (already READ-CONSUMED; 1/1 permitted
  test read used; this task did not touch it).
- Attack: PGD, 10 steps, alpha=epsilon/6, epsilon=0.015, seed 42.

## Attack-norm verification status

**VERIFIED_LINF** — `scripts/run_converged_attacks.py` line ~103, code comment "PGD: untargeted
L-infinity, projected after each step," immediately preceding an L-infinity epsilon-ball
projection (`torch.clamp(perturbation, min=-epsilon, max=epsilon)`). Resolves the `NOT RECORDED`
status left open by the `research-os` target-freeze receipt.

## Validation-only scope (must be preserved by the intake task)

- Every finding in this task's outputs derives exclusively from the 5 validation-split score
  axes listed above (496 windows, 44 fall / 452 non-fall each, verified by filename + shape).
- No held-out-test file was opened; the only test-split numbers appearing anywhere in this
  task's outputs are the already-published aggregate (TP 41, FN 4, FP 60, TN 395) cited as fixed
  context, never re-derived.
- All reported operating points are explicitly labeled `retrospective validation feasibility` /
  `candidate operating point` / `not yet protocol-frozen` / `not evaluated on held-out test`.

## Exact limitations

- This is window-level analysis only; no event/temporal aggregation was evaluated.
- No new ensemble or gate was built or evaluated; Section 6 of `REPORT.md` is descriptive overlap
  evidence only.
- Feasibility on validation does not guarantee held-out-test success (see this program's own
  D8b/D10/D11 knife-edge and transfer-decay history); any future selection must still go through
  a separate, explicit protocol-freeze step before any test read.
- Two of five axes (GR1_macroF1, ST1b6_lowFA) reach the R90/F10 @ eps=0.015 target on validation;
  three (AFAC_maxscore, D14B_seed44, SA1_lowFA) do not, with AFAC_maxscore and SA1_lowFA
  specifically sitting at a knife-edge (recall already sufficient, FAR narrowly over 0.10).
- This summary does not recommend a specific next experiment; that selection is a separate,
  later, human-approved step per the Research OS Validation Pilot Gate process.
