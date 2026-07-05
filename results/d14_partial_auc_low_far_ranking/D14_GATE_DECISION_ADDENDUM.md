# D14 Validation-Gate Decision Addendum

This is a human decision/provenance addendum to the generated D14 validation-gate report. It does
not modify, replace, or supersede the generated report; it records explicit provenance statements
that the auto-generated report does not itself narrate, alongside the decision already reflected in
that report.

## References

- Generated report: `results/d14_partial_auc_low_far_ranking/D14_FAIL_VALIDATION_GATE.md` (not
  edited by this addendum).
- Local gate-report commit: `623edccaabfe8aa7fd66a6fa27127fb1f9932eb1` ("Add D14 validation gate
  failure report").

## Final D14 decision

**D14 validation gate = FAIL.**

- **No held-out test read is authorized.**
- **No held-out test read was performed.** No test-split file was accessed at any point in D14
  Phase 0 through Phase 3 (preflight, implementation, seeds 42/43/44 training, and the validation
  gate run itself).
- **No frozen-threshold JSON was written**, because the gate failed. The gate script only writes
  `d14_frozen_gate_thresholds.json` on a `D14_GATE_PASS_NEEDS_APPROVAL` verdict; since the verdict
  was `D14_FAIL_VALIDATION_GATE`, that file was never created. This was independently verified by
  file-existence check at the time of the gate run: no such file exists under
  `results/d14_partial_auc_low_far_ranking/`.
- **The fixed AFAC 36/44 comparison was sensitivity only** and was not used for the gate decision.
  The gate's condition 3 was evaluated exclusively on the paired stratified bootstrap result;
  the fixed-reference figure (observed 0.030) is reported in the generated report strictly as a
  sensitivity check, per the D14 clarification commit `06c93abb635b3bcaf2e5591f214bd57d00faf831`.
- **Paired bootstrap was the primary Gate-3 criterion.** Delta TP = TP_D14 - TP_AFAC, computed on
  the same resampled validation window IDs for D14 and the AFAC reference, was the criterion that
  determined condition 3's PASS/FAIL status (observed 0.062, below the required 0.70 threshold).

## Stop-rule implications

- **D14 is closed as a validation-gate failure.**
- **No D15 is authorized.**
- **No fusion reopening is authorized.**
- **No gate relaxation is authorized.**
- **No test tuning is authorized.**

## Next step

The D9 TRADES/MART baseline-completeness rerun may proceed, but only as baseline/reporting
completeness for the missing D9 artifact, **not** as a new F20 chase.

## Thesis-safe wording

"D14 did not receive a held-out test evaluation because it failed the pre-registered validation
gate. Therefore, D14 has no locked test recall/FAR result. Its official result is validation-gate
failure."
