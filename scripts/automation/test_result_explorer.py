#!/usr/bin/env python
"""D2b test-first fixtures for Result Explorer v1 (spec: automation/acceptance/result-explorer.yaml).

Written BEFORE scripts/automation/result_explorer.py exists — every functional test fails with a
clear "not implemented yet" message until D2c lands. That is the expected test-first state.

Contract these tests define for D2c:

    result_explorer.run_query(query: dict, sources: dict) -> dict

    query keys   : goal, dataset_family, dataset, attack, epsilon, defense, split,
                   evidence_level, reference_evidence_query (all optional except goal unless a
                   named reference query is given)
    sources keys : goals_yaml, datasets_yaml, ledger_csv, manifest_csv, receipts_dir
    return value : {
        "status":   "ok" | "refused" | "empty",
        "state_id": None | "unsupported_pair" | "disallowed_evidence" | "supported_not_evaluated"
                    | "data_needed" | "query_too_broad" | "no_matching_artifact",
        "message":  str,
        "rows":     [ { goal, dataset, attack, epsilon, defense_or_method_name, split,
                        evidence_level, metrics: {..ledger-named..}, source_file,
                        provenance: {sha256?, commit?, receipt_id?, committed?},
                        warning_band: [str, ...] } ],
    }

    Evidence-level authority: JOIN ledger.source_file -> manifest.path; the manifest
    evidence_level column is authoritative (never derived, never upgraded).

Safety: synthetic temp-dir fixtures ONLY (no real results/ access); no subprocess; no command
containing a split flag; writes only inside pytest tmp_path.
"""
import csv
import importlib
import sys
import textwrap
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
EXPLORER_PATH = HERE / "result_explorer.py"
NOT_IMPLEMENTED_MSG = (
    "result_explorer.py not implemented yet — EXPECTED test-first failure (D2b); "
    "implementation arrives in D2c"
)


# ---------------------------------------------------------------------------- synthetic fixtures
def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


LEDGER_HEADER = (
    "method_internal_name,method_thesis_name,approach_group,seed,split,attack,epsilon,"
    "checkpoint_or_threshold_rule,threshold,source_file,source_type,result_status,"
    "TP,FN,FP,TN,Rfall,FAR,precision,F1,accuracy,macro_F1,AUROC,"
    "Rfall_at_FAR_005,Rfall_at_FAR_010,Rfall_at_FAR_015,Rfall_at_FAR_020,"
    "TP_at_FAR_020,FP_at_FAR_020,F20_reached,notes"
)

MANIFEST_HEADER = (
    "path,kind,sha256,size_bytes,generator_script,link_method,evidence_level,"
    "evidence_provenance,split,claim_boundary,overleaf_ready,overleaf_blockers,committed"
)


@pytest.fixture()
def sources(tmp_path: Path) -> dict:
    """Synthetic registries + ledger + manifest mirroring the real committed schemas."""
    goals_yaml = _write(tmp_path / "registry" / "goals.yaml", """\
        schema_version: 1
        goals:
          - id: fall_detection
            display_name: "Fall Detection"
            aliases: ["fall"]
            task_type: binary_safety_critical_detection
            status: ACTIVE_THESIS_PRIMARY
            metrics: ["fall recall", "FAR", "AUROC"]
            primary_metric_keys: [Rfall, FAR, AUROC, TP, FN, FP, TN]
            success_targets:
              R90F10: { rule: "Rfall > 0.90 AND FAR < 0.10 @ PGD eps=0.030", status: not_met, evidence_level: none }
            datasets_available: ["sensefi_ut_har"]
            data_needs: []
            evidence_rules: "frozen via protocol registry only"
            allowed_evidence_levels: [frozen-test, validation-only, test-descriptive, test-post-hoc, diagnostic-internal]
            default_query_fields: { attack: pgd, epsilon: 0.030, split: val, defense: any }
            reference_evidence_queries:
              H15_eps0015_frozen:
                split: test
                evidence_level: frozen-test
                attack: pgd
                epsilon: 0.015
                protocol_id: "H15-TEST-EPS0015-AFAC-20260705"
              AFAC_eps0030_F20_posthoc:
                split: test
                evidence_level: test-post-hoc
                attack: pgd
                epsilon: 0.030
            grant_relevance: "core"
            clinical_caution: HIGH
            clinical_claim_boundary: { permitted: [], forbidden: ["clinical claim"] }
          - id: walking_detection
            display_name: "Walking Detection"
            aliases: ["walk"]
            task_type: binary_activity_detection
            status: DATA_AVAILABLE_NOT_EVALUATED
            metrics: ["walking recall"]
            primary_metric_keys: [walking_recall, precision, F1]
            success_targets: null
            datasets_available: ["sensefi_ut_har"]
            data_needs: []
            evidence_rules: "no results until verified rows exist"
            allowed_evidence_levels: [validation-only, test-descriptive, diagnostic-internal]
            default_query_fields: { attack: none, epsilon: null, split: val, defense: none }
            grant_relevance: "mobility"
            clinical_caution: MEDIUM
            clinical_claim_boundary: { permitted: [], forbidden: ["diagnostic claim"] }
          - id: walking_pattern_recognition
            display_name: "Walking Pattern Recognition"
            aliases: ["gait_pattern"]
            task_type: fine_grained_multiclass_recognition
            status: NO_DATA
            metrics: ["per-pattern recall"]
            primary_metric_keys: [per_pattern_recall, macro_F1]
            success_targets: null
            datasets_available: []
            data_needs: ["gait-pattern-labelled CSI dataset"]
            evidence_rules: "no dataset -> no claims"
            allowed_evidence_levels: [diagnostic-internal]
            default_query_fields: { attack: none, epsilon: null, split: null, defense: none }
            grant_relevance: "high, blocked on data"
            clinical_caution: HIGH
            clinical_claim_boundary: { permitted: [], forbidden: ["any clinical claim"] }
          - id: gait_or_mobility_change_detection
            display_name: "Gait / Mobility Change Detection"
            aliases: ["mobility_change"]
            task_type: longitudinal_change_detection
            status: NO_DATA
            metrics: ["change sensitivity"]
            primary_metric_keys: [change_sensitivity, change_specificity]
            success_targets: null
            datasets_available: []
            data_needs: ["longitudinal per-subject CSI"]
            evidence_rules: "no dataset -> no claims"
            allowed_evidence_levels: [diagnostic-internal]
            default_query_fields: { attack: none, epsilon: null, split: null, defense: none }
            grant_relevance: "very high, blocked on data"
            clinical_caution: HIGH
            clinical_claim_boundary: { permitted: [], forbidden: ["any clinical claim"] }
          - id: future_fall_risk_prediction
            display_name: "Future Fall-Risk Prediction"
            aliases: ["fall_risk"]
            task_type: prognostic_prediction
            status: NO_DATA_ASPIRATIONAL
            metrics: ["risk AUROC"]
            primary_metric_keys: [risk_AUROC, brier]
            success_targets: null
            datasets_available: []
            data_needs: ["prospective cohort with adjudicated fall outcomes"]
            evidence_rules: "no dataset -> no claims"
            allowed_evidence_levels: []
            default_query_fields: { attack: none, epsilon: null, split: null, defense: none }
            grant_relevance: "aspirational"
            clinical_caution: MAX
            clinical_claim_boundary: { permitted: [], forbidden: ["any prognostic claim"] }
        """)

    datasets_yaml = _write(tmp_path / "registry" / "datasets.yaml", """\
        schema_version: 1
        datasets:
          - id: sensefi_ut_har
            family: SenseFi
            name: UT-HAR
            signal_type: wifi_csi_amplitude
            classes: ["lie down", "fall", "walk", "pickup", "run", "sit down", "stand up"]
            label_map: { 0: "lie down", 1: "fall", 2: "walk", 3: "pickup", 4: "run", 5: "sit down", 6: "stand up",
                         fall_class_index: 1, walk_class_index: 2, source: "synthetic-fixture" }
            supported_goals: [fall_detection, walking_detection]
            unsupported_goals: [walking_pattern_recognition, gait_or_mobility_change_detection, future_fall_risk_prediction]
            split_policy: "frozen test one-shot; val for selection"
            known_limitations: ["no real clinical falls"]
            exists_locally: true
            local_data_status: PRESENT_LOCAL
            local_paths_known: true
            supported_attack_families: [fgsm, pgd]
            supported_defense_families: [undefended, safety_guided, afac]
            recommended_first_query: { goal: fall_detection, attack: pgd, epsilon: 0.030, split: val, defense: any }
        """)

    # three ledger rows: val hit / frozen H15 / post-hoc AFAC (source_file joins to manifest)
    rows = [
        dict(method_internal_name="G1_seed42", method_thesis_name="G1", approach_group="safety_guided",
             seed="42", split="val", attack="pgd", epsilon="0.03", source_file="synthetic/g1_val_metrics.csv",
             source_type="validation", result_status="selection",
             TP="27", FN="18", FP="20", TN="120", Rfall="0.600", FAR="0.143", AUROC="0.876"),
        dict(method_internal_name="AFAC_maxscore", method_thesis_name="AFAC", approach_group="afac",
             seed="42", split="test", attack="pgd", epsilon="0.015", source_file="synthetic/h15_frozen_metrics.csv",
             source_type="frozen_protocol", result_status="frozen",
             TP="41", FN="4", FP="19", TN="120", Rfall="0.9111", FAR="0.1319", AUROC=""),
        dict(method_internal_name="AFAC_maxscore", method_thesis_name="AFAC", approach_group="afac",
             seed="42", split="test", attack="pgd", epsilon="0.03", source_file="synthetic/afac_posthoc_metrics.csv",
             source_type="post_hoc", result_status="post_hoc",
             TP="36", FN="9", FP="27", TN="112", Rfall="0.800", FAR="0.194", AUROC="0.851"),
    ]
    header_cols = LEDGER_HEADER.split(",")
    ledger_csv = tmp_path / "ledger.csv"
    with ledger_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header_cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in header_cols})

    manifest_rows = [
        ("synthetic/g1_val_metrics.csv", "csv", "aaa111", "validation-only", "val", "yes"),
        ("synthetic/h15_frozen_metrics.csv", "csv", "bbb222", "frozen-test", "test", "yes"),
        ("synthetic/afac_posthoc_metrics.csv", "csv", "ccc333", "test-post-hoc", "test", "yes"),
    ]
    mh = MANIFEST_HEADER.split(",")
    manifest_csv = tmp_path / "manifest.csv"
    with manifest_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=mh)
        w.writeheader()
        for path, kind, sha, ev, split, committed in manifest_rows:
            w.writerow({**{c: "" for c in mh}, "path": path, "kind": kind, "sha256": sha,
                        "evidence_level": ev, "split": split, "committed": committed})

    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()

    return {
        "goals_yaml": str(goals_yaml),
        "datasets_yaml": str(datasets_yaml),
        "ledger_csv": str(ledger_csv),
        "manifest_csv": str(manifest_csv),
        "receipts_dir": str(receipts_dir),
        "_tmp_root": tmp_path,
    }


@pytest.fixture()
def explorer():
    """Import the (future) implementation; fail loudly-but-expectedly until D2c exists."""
    if not EXPLORER_PATH.exists():
        pytest.fail(NOT_IMPLEMENTED_MSG)
    sys.path.insert(0, str(HERE))
    try:
        return importlib.import_module("result_explorer")
    finally:
        sys.path.remove(str(HERE))


def _snapshot(root: Path) -> set:
    return {(p, p.stat().st_size) for p in root.rglob("*") if p.is_file()}


# ---------------------------------------------------------------------------- F1-F5: fall lookups
def test_f1_val_hit_fall_ut_har_pgd_eps030(explorer, sources):
    before = _snapshot(sources["_tmp_root"])
    out = explorer.run_query(
        {"goal": "fall_detection", "dataset": "UT-HAR", "attack": "pgd",
         "epsilon": 0.03, "evidence_level": "validation-only"}, sources)
    assert out["status"] == "ok"
    assert len(out["rows"]) == 1
    row = out["rows"][0]
    assert row["evidence_level"] == "validation-only"
    assert row["split"] == "val"
    assert row["metrics"]["Rfall"] == pytest.approx(0.600)        # ledger-named metric key
    assert row["metrics"]["FAR"] == pytest.approx(0.143)
    assert all(k in row["metrics"] for k in ("TP", "FN", "FP", "TN"))
    assert row["source_file"] == "synthetic/g1_val_metrics.csv"
    assert row["provenance"].get("sha256") == "aaa111"
    # runtime read-only proof: nothing under the temp root changed
    assert _snapshot(sources["_tmp_root"]) == before


def test_f1b_default_query_never_returns_test_rows(explorer, sources):
    out = explorer.run_query({"goal": "fall_detection"}, sources)  # filterless -> registry defaults
    assert all(r["split"] != "test" for r in out.get("rows", [])), \
        "no-test-leakage: default exploration must never surface split=test rows"


def test_f2_named_frozen_reference_query(explorer, sources):
    out = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "H15_eps0015_frozen"}, sources)
    assert out["status"] == "ok"
    row = out["rows"][0]
    assert row["evidence_level"] == "frozen-test"
    assert float(row["epsilon"]) == pytest.approx(0.015)
    assert row["provenance"].get("sha256") == "bbb222"


def test_f3_named_posthoc_reference_query(explorer, sources):
    out = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "AFAC_eps0030_F20_posthoc"}, sources)
    assert out["status"] == "ok"
    row = out["rows"][0]
    assert row["evidence_level"] == "test-post-hoc"
    assert float(row["epsilon"]) == pytest.approx(0.03)


def test_f4_validation_only_warning_mandatory(explorer, sources):
    out = explorer.run_query(
        {"goal": "fall_detection", "dataset": "UT-HAR", "attack": "pgd",
         "epsilon": 0.03, "evidence_level": "validation-only"}, sources)
    band = " ".join(out["rows"][0]["warning_band"]).lower()
    assert "validation-only" in band
    assert "not r90f10" in band          # mandatory on every fall row until R90F10 is met


def test_f5_posthoc_warning_mandatory(explorer, sources):
    out = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "AFAC_eps0030_F20_posthoc"}, sources)
    band = " ".join(out["rows"][0]["warning_band"]).lower()
    assert "post-hoc" in band
    assert "not r90f10" in band


# ---------------------------------------------------------------------------- F6-F8: honest empties
def test_f6_walking_supported_but_not_evaluated(explorer, sources):
    out = explorer.run_query({"goal": "walking_detection", "dataset": "UT-HAR"}, sources)
    assert out["status"] == "empty"
    assert out["state_id"] == "supported_not_evaluated"
    assert out["rows"] == []             # never a fabricated metric


def test_f7_gait_pattern_data_needed(explorer, sources):
    out = explorer.run_query({"goal": "walking_pattern_recognition"}, sources)
    assert out["status"] == "empty"
    assert out["state_id"] == "data_needed"
    assert "gait-pattern-labelled" in out["message"]


def test_f8_fall_risk_data_needed(explorer, sources):
    out = explorer.run_query({"goal": "future_fall_risk_prediction"}, sources)
    assert out["status"] in ("empty", "refused")
    assert out["state_id"] == "data_needed"
    assert out["rows"] == []


# ---------------------------------------------------------------------------- F9-F10: refusals
def test_f9_unsupported_pair_refused(explorer, sources):
    out = explorer.run_query(
        {"goal": "gait_or_mobility_change_detection", "dataset": "UT-HAR"}, sources)
    assert out["status"] == "refused"
    assert out["state_id"] == "unsupported_pair"


def test_f10_disallowed_evidence_level_refused(explorer, sources):
    out = explorer.run_query(
        {"goal": "walking_detection", "dataset": "UT-HAR", "evidence_level": "frozen-test"}, sources)
    assert out["status"] == "refused"
    assert out["state_id"] == "disallowed_evidence"


# ---------------------------------------------------------------------------- F11: read-only static
def test_f11_read_only_static_check():
    if not EXPLORER_PATH.exists():
        pytest.fail(NOT_IMPLEMENTED_MSG)
    src = EXPLORER_PATH.read_text(encoding="utf-8")
    forbidden = [
        "--split",                              # never builds a split command
        "export_probability_predictions",       # never calls the export script
        "adaptive_gate_attack",                 # never calls the gate script
        "subprocess",                           # no subprocesses at all in v1
        "os.system",
    ]
    hits = [tok for tok in forbidden if tok in src]
    assert not hits, f"forbidden tokens in result_explorer.py: {hits}"
    # stdout-only: no file-write idioms
    write_idioms = [".write_text(", "'w'", '"w"', "'a'", '"a"']
    writing = [tok for tok in write_idioms if tok in src]
    assert not writing, f"write idioms found (stdout-only tool): {writing}"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
