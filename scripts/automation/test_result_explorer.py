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


# --------------------------------------------------------------- D2d-2: curated-registry fixtures
# The REAL curated values (automation/registry/reference_evidence.yaml), used verbatim so these
# tests double as a schema/value contract check against the production registry.
H15_METRICS = {"TP": 41, "FN": 4, "FP": 60, "TN": 395, "Rfall": 0.911111, "FAR": 0.131868}
AFAC_METRICS = {"TP": 36, "FN": 9, "FP": 91, "TN": 364, "Rfall": 0.800000, "FAR": 0.200000}


def _write_curated_yaml(path: Path, entries_yaml: str) -> Path:
    return _write(path, f"""\
        schema_version: 1
        reference_results:
        {textwrap.indent(textwrap.dedent(entries_yaml), '          ')}
        """)


@pytest.fixture()
def curated_sources(sources):
    """Base `sources` fixture PLUS a synthetic reference_evidence.yaml mirroring the real curated
    registry's two entries (real values) and matching manifest rows for their provenance paths.
    Distinct synthetic paths from the base fixture's ledger rows, to keep the two lookup paths
    (curated vs legacy ledger-filter) unambiguous in these tests."""
    curated_yaml = _write_curated_yaml(sources["_tmp_root"] / "registry" / "reference_evidence.yaml", """
        - key: H15_eps0015_frozen
          goal: fall_detection
          dataset: sensefi_ut_har
          attack: pgd
          epsilon: 0.015
          split: test
          evidence_level: frozen-test
          threshold: 0.168754
          metrics: {TP: 41, FN: 4, FP: 60, TN: 395, Rfall: 0.911111, FAR: 0.131868}
          protocol_id: "H15-TEST-EPS0015-AFAC-20260705"
          provenance:
            confusion_csv: "synthetic/curated_h15_confusion.csv"
            result_report: "synthetic/curated_h15_result.md"
            required_manifest_evidence_level: frozen-test
            frontier_registry_ref: "automation/frontier.yaml frozen_protocol_registry"
          clean_disclosure_companion:
            condition: clean_disclosure
            epsilon: 0.0
            threshold: 0.168754
            TP: 44
            FN: 1
            FP: 41
            TN: 414
            Rfall: 0.977778
            FAR: 0.09011
          disclosures:
            - "eps=0.015, NOT eps=0.030 -- this is not the R90F10 operating point"
            - "not R90F10 -- FAR (0.131868) remains above the 0.10 R90F10 ceiling"
            - "frozen-test evidence -- a one-shot protocol read, not clinical or deployment evidence"
            - "clean-condition disclosure recorded at the same threshold (see clean_disclosure_companion)"
        - key: AFAC_eps0030_F20_posthoc
          goal: fall_detection
          dataset: sensefi_ut_har
          attack: pgd
          epsilon: 0.030
          split: test
          evidence_level: test-post-hoc
          method: optionB_AFAC
          threshold: 0.153246
          threshold_rule: "post-hoc fall-score threshold sweep via fall_probability"
          metrics: {TP: 36, FN: 9, FP: 91, TN: 364, Rfall: 0.800000, FAR: 0.200000}
          provenance:
            selector: "F20_reached=True AND split=test AND attack=pgd AND epsilon=0.03"
            selector_note: "unique row in the ledger pool"
            source_file: "synthetic/curated_afac_posthoc.csv"
            required_manifest_evidence_level: test-post-hoc
          disclosures:
            - "post-hoc only -- a satisfying threshold exists on saved scores, not a frozen read"
            - "not a frozen read -- no frozen protocol was executed at eps=0.030 for this method"
            - "F20 knife-edge caveat -- treat as fragile, not robust"
            - "not R90F10 -- FAR (0.200000) is well above the 0.10 R90F10 ceiling"
        """)

    mh = MANIFEST_HEADER.split(",")
    with open(sources["manifest_csv"], "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=mh)
        for path, kind, sha, ev in [
            ("synthetic/curated_h15_confusion.csv", "csv", "h15confsha", "frozen-test"),
            ("synthetic/curated_h15_result.md", "report", "h15repsha", "frozen-test"),
            ("synthetic/curated_afac_posthoc.csv", "predictions", "afacposhsha", "test-post-hoc"),
        ]:
            w.writerow({**{c: "" for c in mh}, "path": path, "kind": kind, "sha256": sha,
                        "evidence_level": ev, "split": "test", "committed": "yes"})

    return {**sources, "reference_evidence_yaml": str(curated_yaml)}


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


# ---------------------------------------------------------------- D2d-2: F12-F15 curated registry
def test_f12_curated_h15_frozen_reference(explorer, curated_sources):
    before = _snapshot(curated_sources["_tmp_root"])
    out = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "H15_eps0015_frozen"}, curated_sources)
    assert out["status"] == "ok"
    assert len(out["rows"]) == 1
    row = out["rows"][0]
    assert row["attack"] == "pgd"
    assert row["epsilon"] == pytest.approx(0.015)
    assert row["split"] == "test"
    assert row["evidence_level"] == "frozen-test"
    assert row["threshold"] == pytest.approx(0.168754)
    for k, v in H15_METRICS.items():
        assert row["metrics"][k] == pytest.approx(v), k
    assert row["protocol_id"] == "H15-TEST-EPS0015-AFAC-20260705"
    assert row["provenance"]["manifest_cross_check"] == "pass"
    assert row["clean_disclosure_companion"]["Rfall"] == pytest.approx(0.977778)
    band = " ".join(row["warning_band"]).lower()
    assert "eps=0.015" in band and "0.030" not in band.split("eps=0.015")[0]
    assert "not r90f10" in band
    assert "frozen-test evidence" in band
    assert "clean-condition disclosure" in band
    assert _snapshot(curated_sources["_tmp_root"]) == before   # read-only proof


def test_f13_provenance_mismatch_wrong_evidence_level(explorer, curated_sources):
    """Synthetic manifest row for the curated H15 path exists but claims a DIFFERENT evidence
    level than the curated entry declares -- must refuse, never render trusted metrics."""
    mh = MANIFEST_HEADER.split(",")
    with open(curated_sources["manifest_csv"], "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=mh)
        w.writerow({**{c: "" for c in mh}, "path": "synthetic/curated_mismatch.csv", "kind": "csv",
                    "sha256": "mismatchsha", "evidence_level": "validation-only",
                    "split": "test", "committed": "yes"})
    mismatched_yaml = _write_curated_yaml(
        curated_sources["_tmp_root"] / "registry" / "reference_evidence_mismatch.yaml", """
        - key: H15_wrong_level
          goal: fall_detection
          dataset: sensefi_ut_har
          attack: pgd
          epsilon: 0.015
          split: test
          evidence_level: frozen-test
          metrics: {TP: 41, FN: 4, FP: 60, TN: 395, Rfall: 0.911111, FAR: 0.131868}
          provenance:
            confusion_csv: "synthetic/curated_mismatch.csv"
            required_manifest_evidence_level: frozen-test
        """)
    src = {**curated_sources, "reference_evidence_yaml": str(mismatched_yaml)}
    out = explorer.run_query({"goal": "fall_detection", "reference_evidence_query": "H15_wrong_level"}, src)
    assert out["status"] == "refused"
    assert out["state_id"] == "provenance_mismatch"
    assert out["rows"] == []
    assert "H15_wrong_level" in out["message"]


def test_f13b_provenance_mismatch_missing_manifest_path(explorer, curated_sources):
    """Curated entry cites a path that simply is not in the manifest at all."""
    missing_yaml = _write_curated_yaml(
        curated_sources["_tmp_root"] / "registry" / "reference_evidence_missing.yaml", """
        - key: H15_missing_path
          goal: fall_detection
          dataset: sensefi_ut_har
          attack: pgd
          epsilon: 0.015
          split: test
          evidence_level: frozen-test
          metrics: {TP: 41, FN: 4, FP: 60, TN: 395, Rfall: 0.911111, FAR: 0.131868}
          provenance:
            confusion_csv: "synthetic/does_not_exist_in_manifest.csv"
        """)
    src = {**curated_sources, "reference_evidence_yaml": str(missing_yaml)}
    out = explorer.run_query({"goal": "fall_detection", "reference_evidence_query": "H15_missing_path"}, src)
    assert out["status"] == "refused"
    assert out["state_id"] == "provenance_mismatch"
    assert out["rows"] == []
    assert "not found in the artifact manifest" in out["message"]


def test_f13c_no_fallback_to_fabricated_manifest_only_row(explorer, curated_sources):
    """A provenance-mismatched curated query must never silently fall through to synthesizing a
    row purely from manifest metadata -- it must refuse, full stop."""
    missing_yaml = _write_curated_yaml(
        curated_sources["_tmp_root"] / "registry" / "reference_evidence_missing2.yaml", """
        - key: H15_no_fabrication
          goal: fall_detection
          dataset: sensefi_ut_har
          attack: pgd
          epsilon: 0.015
          split: test
          evidence_level: frozen-test
          metrics: {TP: 999, FN: 999, FP: 999, TN: 999, Rfall: 0.5, FAR: 0.5}
          provenance:
            confusion_csv: "synthetic/curated_h15_confusion.csv"
            required_manifest_evidence_level: validation-only
        """)
    src = {**curated_sources, "reference_evidence_yaml": str(missing_yaml)}
    out = explorer.run_query({"goal": "fall_detection", "reference_evidence_query": "H15_no_fabrication"}, src)
    assert out["status"] == "refused"
    assert out["rows"] == []   # never the 999-metrics row, never a manifest-only synthesized row


def test_f14_curated_afac_posthoc_reference(explorer, curated_sources):
    out = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "AFAC_eps0030_F20_posthoc"}, curated_sources)
    assert out["status"] == "ok"
    assert len(out["rows"]) == 1
    row = out["rows"][0]
    assert row["attack"] == "pgd"
    assert row["epsilon"] == pytest.approx(0.030)
    assert row["split"] == "test"
    assert row["evidence_level"] == "test-post-hoc"
    assert row["defense_or_method_name"] == "optionB_AFAC"
    assert row["threshold"] == pytest.approx(0.153246)
    for k, v in AFAC_METRICS.items():
        assert row["metrics"][k] == pytest.approx(v), k
    assert row["provenance"]["manifest_cross_check"] == "pass"
    band = " ".join(row["warning_band"]).lower()
    assert "post-hoc only" in band
    assert "not a frozen read" in band
    assert "knife-edge" in band
    assert "not r90f10" in band
    assert row["evidence_level"] != "frozen-test"   # never mislabeled as frozen
    assert row["epsilon"] != pytest.approx(0.015)   # never mislabeled as the H15 epsilon


def test_f15_fallback_path_unaffected_by_curated_first(explorer, curated_sources):
    """Curated registry IS configured (curated_sources), but the requested key exists only via
    the legacy goals.yaml reference_evidence_queries + ledger-filter path -- proves introducing
    curated-first resolution does not break ordinary/legacy reference queries."""
    out = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "legacy_only_key_not_curated"},
        curated_sources)
    # not in the curated file and not in goals.yaml's reference_evidence_queries -> the ORIGINAL
    # unknown_reference_query refusal, exactly as before D2d-2.
    assert out["status"] == "refused"
    assert out["state_id"] == "unknown_reference_query"

    # the two EXISTING keys (H15_eps0015_frozen / AFAC_eps0030_F20_posthoc) also exist in
    # goals.yaml's own reference_evidence_queries stub -- but with curated_sources configured,
    # curated-first correctly WINS (same keys, curated takes precedence) -- confirmed by F12/F14.
    # An ordinary, non-reference ledger query must also behave identically to the no-curated case.
    ordinary = explorer.run_query(
        {"goal": "fall_detection", "dataset": "UT-HAR", "attack": "pgd",
         "epsilon": 0.03, "evidence_level": "validation-only"}, curated_sources)
    assert ordinary["status"] == "ok"
    assert ordinary["rows"][0]["metrics"]["Rfall"] == pytest.approx(0.600)


def test_duplicate_curated_key_refused(explorer, curated_sources):
    dup_yaml = _write_curated_yaml(
        curated_sources["_tmp_root"] / "registry" / "reference_evidence_dup.yaml", """
        - key: DUP_KEY
          goal: fall_detection
          dataset: sensefi_ut_har
          attack: pgd
          epsilon: 0.015
          split: test
          evidence_level: frozen-test
          metrics: {TP: 1, FN: 1, FP: 1, TN: 1, Rfall: 0.5, FAR: 0.5}
          provenance: {confusion_csv: "synthetic/curated_h15_confusion.csv"}
        - key: DUP_KEY
          goal: fall_detection
          dataset: sensefi_ut_har
          attack: pgd
          epsilon: 0.015
          split: test
          evidence_level: frozen-test
          metrics: {TP: 2, FN: 2, FP: 2, TN: 2, Rfall: 0.6, FAR: 0.6}
          provenance: {confusion_csv: "synthetic/curated_h15_confusion.csv"}
        """)
    src = {**curated_sources, "reference_evidence_yaml": str(dup_yaml)}
    out = explorer.run_query({"goal": "fall_detection", "reference_evidence_query": "DUP_KEY"}, src)
    assert out["status"] == "refused"
    assert out["state_id"] == "duplicate_curated_key"
    assert out["rows"] == []


def test_missing_curated_registry_falls_back(explorer, sources):
    """sources has NO reference_evidence_yaml key at all (the pre-D2d-2 shape) -- must behave
    exactly like before: falls straight through to the legacy path."""
    assert "reference_evidence_yaml" not in sources
    out = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "H15_eps0015_frozen"}, sources)
    # legacy goals.yaml stub -> ledger-filter path (same as test_f2), NOT a curated result
    assert out["status"] == "ok"
    assert out["rows"][0]["evidence_level"] == "frozen-test"
    assert out["rows"][0]["metrics"]["FAR"] == pytest.approx(0.1319)   # legacy synthetic value, not 0.131868


def test_missing_curated_registry_file_path_falls_back(explorer, sources):
    """reference_evidence_yaml key present but points at a nonexistent file -- must not crash,
    must fall back cleanly."""
    src = {**sources, "reference_evidence_yaml": str(sources["_tmp_root"] / "does_not_exist.yaml")}
    out = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "H15_eps0015_frozen"}, src)
    assert out["status"] == "ok"
    assert out["rows"][0]["metrics"]["FAR"] == pytest.approx(0.1319)


def test_malformed_curated_entry_no_provenance(explorer, curated_sources):
    malformed_yaml = _write_curated_yaml(
        curated_sources["_tmp_root"] / "registry" / "reference_evidence_malformed.yaml", """
        - key: MALFORMED_NO_PROVENANCE
          goal: fall_detection
          dataset: sensefi_ut_har
          attack: pgd
          epsilon: 0.015
          split: test
          evidence_level: frozen-test
          metrics: {TP: 1, FN: 1, FP: 1, TN: 1, Rfall: 0.5, FAR: 0.5}
        """)
    src = {**curated_sources, "reference_evidence_yaml": str(malformed_yaml)}
    out = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "MALFORMED_NO_PROVENANCE"}, src)
    assert out["status"] == "refused"
    assert out["state_id"] == "provenance_mismatch"
    assert out["rows"] == []


def test_curated_exact_key_no_fuzzy_matching(explorer, curated_sources):
    """A near-miss key (case/substring variant) must NOT resolve -- exact match only."""
    out = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "h15_eps0015_frozen"}, curated_sources)
    assert out["status"] == "refused"
    assert out["state_id"] in ("unknown_reference_query",)
    out2 = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "H15_eps0015"}, curated_sources)
    assert out2["status"] == "refused"


def test_ordinary_queries_unchanged_with_curated_configured(explorer, curated_sources):
    """Non-reference (ordinary filter) queries must produce IDENTICAL results whether or not a
    curated registry is configured in sources -- curated-first only ever engages via
    reference_evidence_query."""
    out = explorer.run_query({"goal": "walking_detection", "dataset": "UT-HAR"}, curated_sources)
    assert out["status"] == "empty"
    assert out["state_id"] == "supported_not_evaluated"


# ---------------------------------------------------------------- D2e-2: identity enrichment (I1-I15)
def _write_identity_yaml(path: Path, runs_yaml: str, evaluations_yaml: str) -> Path:
    """Assembles the identity YAML directly (not via _write's dedent-based helper, whose outer
    dedent collides with the indentation applied here) so nested list items land at the correct
    YAML indentation level."""
    content = (
        "schema_version: 1\n"
        "naming_policy:\n"
        "  epsilon_tokens: {0.015: eps0p015, 0.03: eps0p030}\n"
        "runs:\n"
        + textwrap.indent(textwrap.dedent(runs_yaml), "  ")
        + "evaluations:\n"
        + textwrap.indent(textwrap.dedent(evaluations_yaml), "  ")
        + "legacy_alias_glossary: []\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


_RUN_YAML = """\
- run_id: run_fall_detection_sensefi_ut_har_afac_optionb_seed42_maxscore_v1
  display_name: "AFAC optionB seed-42 (maxscore-selected) checkpoint"
  goal: fall_detection
  dataset: sensefi_ut_har
  method_family: AFAC
  identity_status: verified
"""

_H15_EVAL_YAML = """\
- evaluation_id: eval_fall_detection_sensefi_ut_har_afac_pgd_eps0p015_frozen_test_v1
  display_name: "AFAC frozen-test evaluation under PGD epsilon=0.015"
  run_id: run_fall_detection_sensefi_ut_har_afac_optionb_seed42_maxscore_v1
  run_link_status: verified
  reference_evidence_key: H15_eps0015_frozen
  goal: fall_detection
  dataset: sensefi_ut_har
  method_family: AFAC
  attack: pgd
  epsilon: 0.015
  split: test
  evidence_level: frozen-test
  protocol_id: "H15-TEST-EPS0015-AFAC-20260705"
  identity_status: verified
  legacy_aliases:
    - value: H15
      alias_type: historical_milestone_label
      meaning: null
      meaning_status: unverified
      source_paths: ["results/synthetic_h15_doc.md"]
      note: "Historical internal label; expansion not asserted."
"""

_AFAC_EVAL_YAML = """\
- evaluation_id: eval_fall_detection_sensefi_ut_har_afac_pgd_eps0p030_test_posthoc_v1
  display_name: "AFAC post-hoc F20 operating point under PGD epsilon=0.030"
  run_id: run_fall_detection_sensefi_ut_har_afac_optionb_seed42_maxscore_v1
  run_link_status: verified
  reference_evidence_key: AFAC_eps0030_F20_posthoc
  goal: fall_detection
  dataset: sensefi_ut_har
  method_family: AFAC
  method_variant: optionB_AFAC
  attack: pgd
  epsilon: 0.03
  split: test
  evidence_level: test-post-hoc
  identity_status: verified
  legacy_aliases:
    - value: D8b
      alias_type: historical_appendix_target_label
      meaning: "AFAC-score post-hoc FAR<=0.20 operating point"
      meaning_status: verified
      source_paths: ["scripts/analysis/plot_d1_d12_recall_far.py"]
      note: "Verified field-for-field match."
"""


@pytest.fixture()
def identity_sources(curated_sources):
    """curated_sources PLUS a synthetic experiment_identity.yaml mirroring the real registry's one
    run + two evaluations for H15/AFAC."""
    identity_yaml = _write_identity_yaml(
        curated_sources["_tmp_root"] / "registry" / "experiment_identity.yaml",
        _RUN_YAML, _H15_EVAL_YAML + _AFAC_EVAL_YAML)
    return {**curated_sources, "identity_yaml": str(identity_yaml)}


def test_i1_h15_exact_identity_enrichment(explorer, identity_sources):
    before = _snapshot(identity_sources["_tmp_root"])
    out = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "H15_eps0015_frozen"}, identity_sources)
    assert out["status"] == "ok"
    row = out["rows"][0]
    # scientific fields exactly as in F12 (unchanged by enrichment)
    for k, v in H15_METRICS.items():
        assert row["metrics"][k] == pytest.approx(v), k
    assert row["evidence_level"] == "frozen-test"
    assert row["epsilon"] == pytest.approx(0.015)
    ei = row["experiment_identity"]
    assert ei["state"] == "matched"
    assert ei["evaluation_id"] == "eval_fall_detection_sensefi_ut_har_afac_pgd_eps0p015_frozen_test_v1"
    assert ei["display_name"] == "AFAC frozen-test evaluation under PGD epsilon=0.015"
    assert ei["run_id"] == "run_fall_detection_sensefi_ut_har_afac_optionb_seed42_maxscore_v1"
    assert ei["run_link_status"] == "verified"
    aliases = ei["legacy_aliases"]
    assert len(aliases) == 1 and aliases[0]["value"] == "H15"
    assert aliases[0]["meaning"] is None
    assert aliases[0]["meaning_status"] == "unverified"
    assert _snapshot(identity_sources["_tmp_root"]) == before   # read-only proof


def test_i2_afac_posthoc_identity_enrichment(explorer, identity_sources):
    out = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "AFAC_eps0030_F20_posthoc"}, identity_sources)
    assert out["status"] == "ok"
    row = out["rows"][0]
    for k, v in AFAC_METRICS.items():
        assert row["metrics"][k] == pytest.approx(v), k
    assert row["evidence_level"] == "test-post-hoc"
    ei = row["experiment_identity"]
    assert ei["state"] == "matched"
    assert ei["evaluation_id"] == "eval_fall_detection_sensefi_ut_har_afac_pgd_eps0p030_test_posthoc_v1"
    assert ei["display_name"] == "AFAC post-hoc F20 operating point under PGD epsilon=0.030"
    assert ei["run_id"] == "run_fall_detection_sensefi_ut_har_afac_optionb_seed42_maxscore_v1"
    aliases = ei["legacy_aliases"]
    assert len(aliases) == 1 and aliases[0]["value"] == "D8b"   # never bare D8
    assert aliases[0]["meaning_status"] == "verified"
    assert row["evidence_level"] != "frozen-test"   # never mislabeled


def test_i3_scientific_fields_unchanged_by_enrichment(explorer, curated_sources, identity_sources):
    """Same query, with vs without an identity source configured -- every scientific/provenance
    field is byte/value equivalent; only experiment_identity differs."""
    plain = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "H15_eps0015_frozen"}, curated_sources)
    enriched = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "H15_eps0015_frozen"}, identity_sources)
    row_plain = dict(plain["rows"][0])
    row_enriched = dict(enriched["rows"][0])
    # both sides carry a supplemental experiment_identity block (curated_sources has no identity
    # source configured -> state=unavailable; identity_sources -> state=matched); pop both to
    # compare only the SCIENTIFIC/provenance fields, which must be byte/value equivalent.
    assert row_plain.pop("experiment_identity")["state"] == "unavailable"
    assert row_enriched.pop("experiment_identity")["state"] == "matched"
    assert row_plain == row_enriched


def test_i4_missing_identity_registry(explorer, curated_sources):
    """No identity_yaml key in sources at all -- scientific result still returns; identity state
    unavailable; nothing fabricated."""
    assert "identity_yaml" not in curated_sources
    out = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "H15_eps0015_frozen"}, curated_sources)
    assert out["status"] == "ok"
    row = out["rows"][0]
    for k, v in H15_METRICS.items():
        assert row["metrics"][k] == pytest.approx(v), k
    ei = row["experiment_identity"]
    assert ei["state"] == "unavailable"
    assert "evaluation_id" not in ei


def test_i4b_identity_file_path_does_not_exist(explorer, curated_sources):
    src = {**curated_sources, "identity_yaml": str(curated_sources["_tmp_root"] / "nope.yaml")}
    out = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "H15_eps0015_frozen"}, src)
    assert out["status"] == "ok"
    assert out["rows"][0]["experiment_identity"]["state"] == "unavailable"


def test_i5_missing_reference_key_mapping(explorer, curated_sources):
    """Identity file exists and parses, but has zero evaluations referencing this key -- no fuzzy
    alias fallback, just an honest unavailable state."""
    empty_identity = _write_identity_yaml(
        curated_sources["_tmp_root"] / "registry" / "empty_identity.yaml", _RUN_YAML, "[]\n")
    src = {**curated_sources, "identity_yaml": str(empty_identity)}
    out = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "H15_eps0015_frozen"}, src)
    assert out["status"] == "ok"
    ei = out["rows"][0]["experiment_identity"]
    assert ei["state"] == "unavailable"
    assert "evaluation_id" not in ei


def test_i6_duplicate_identity_mapping(explorer, curated_sources):
    dup_eval_yaml = _H15_EVAL_YAML + _H15_EVAL_YAML   # same reference_evidence_key twice
    dup_identity = _write_identity_yaml(
        curated_sources["_tmp_root"] / "registry" / "dup_identity.yaml", _RUN_YAML, dup_eval_yaml)
    src = {**curated_sources, "identity_yaml": str(dup_identity)}
    out = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "H15_eps0015_frozen"}, src)
    assert out["status"] == "ok"          # scientific result still returns
    row = out["rows"][0]
    assert row["metrics"]["Rfall"] == pytest.approx(H15_METRICS["Rfall"])
    ei = row["experiment_identity"]
    assert ei["state"] == "mismatch"
    assert "duplicate" in ei["reason"].lower()
    assert "evaluation_id" not in ei      # no canonical ID attached, no arbitrary pick


def test_i7_epsilon_conflict(explorer, curated_sources):
    bad_eval = _H15_EVAL_YAML.replace("epsilon: 0.015", "epsilon: 0.03")   # wrong epsilon for H15
    bad_identity = _write_identity_yaml(
        curated_sources["_tmp_root"] / "registry" / "eps_conflict.yaml", _RUN_YAML, bad_eval)
    src = {**curated_sources, "identity_yaml": str(bad_identity)}
    out = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "H15_eps0015_frozen"}, src)
    row = out["rows"][0]
    assert row["epsilon"] == pytest.approx(0.015)   # scientific epsilon UNCHANGED
    ei = row["experiment_identity"]
    assert ei["state"] == "mismatch"
    assert "epsilon" in ei["reason"].lower()
    assert "evaluation_id" not in ei


def test_i8_evidence_level_conflict(explorer, curated_sources):
    bad_eval = _H15_EVAL_YAML.replace("evidence_level: frozen-test", "evidence_level: validation-only")
    bad_identity = _write_identity_yaml(
        curated_sources["_tmp_root"] / "registry" / "evlevel_conflict.yaml", _RUN_YAML, bad_eval)
    src = {**curated_sources, "identity_yaml": str(bad_identity)}
    out = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "H15_eps0015_frozen"}, src)
    row = out["rows"][0]
    assert row["evidence_level"] == "frozen-test"   # trusted evidence level UNCHANGED
    ei = row["experiment_identity"]
    assert ei["state"] == "mismatch"
    assert "evidence_level" in ei["reason"].lower()


def test_i9_missing_run_record(explorer, curated_sources):
    bad_eval = _H15_EVAL_YAML.replace(
        "run_id: run_fall_detection_sensefi_ut_har_afac_optionb_seed42_maxscore_v1",
        "run_id: run_does_not_exist_v1")
    bad_identity = _write_identity_yaml(
        curated_sources["_tmp_root"] / "registry" / "run_missing.yaml", _RUN_YAML, bad_eval)
    src = {**curated_sources, "identity_yaml": str(bad_identity)}
    out = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "H15_eps0015_frozen"}, src)
    assert out["status"] == "ok"
    ei = out["rows"][0]["experiment_identity"]
    assert ei["state"] == "mismatch"
    assert "run_id" in ei["reason"] or "does not resolve" in ei["reason"]
    assert "run_id" not in ei or ei.get("run_id") is None   # no run fabricated into the block


def test_i10_protocol_conflict(explorer, curated_sources):
    """Both the scientific row and the identity evaluation carry a protocol_id, but they disagree."""
    conflicting_eval = _H15_EVAL_YAML.replace(
        'protocol_id: "H15-TEST-EPS0015-AFAC-20260705"', 'protocol_id: "DIFFERENT-PROTOCOL-ID"')
    bad_identity = _write_identity_yaml(
        curated_sources["_tmp_root"] / "registry" / "protocol_conflict.yaml", _RUN_YAML, conflicting_eval)
    src = {**curated_sources, "identity_yaml": str(bad_identity)}
    out = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "H15_eps0015_frozen"}, src)
    row = out["rows"][0]
    assert row["protocol_id"] == "H15-TEST-EPS0015-AFAC-20260705"   # scientific value unchanged
    ei = row["experiment_identity"]
    assert ei["state"] == "mismatch"
    assert "protocol_id" in ei["reason"].lower()


def test_i11_ordinary_ledger_query_unchanged(explorer, curated_sources, identity_sources):
    """A non-reference ledger query never receives an experiment_identity block, identity source
    configured or not."""
    plain = explorer.run_query(
        {"goal": "fall_detection", "dataset": "UT-HAR", "attack": "pgd",
         "epsilon": 0.03, "evidence_level": "validation-only"}, curated_sources)
    enriched = explorer.run_query(
        {"goal": "fall_detection", "dataset": "UT-HAR", "attack": "pgd",
         "epsilon": 0.03, "evidence_level": "validation-only"}, identity_sources)
    assert "experiment_identity" not in plain["rows"][0]
    assert "experiment_identity" not in enriched["rows"][0]
    assert plain["rows"][0] == enriched["rows"][0]


def test_i12_existing_curated_fallback_behavior_unchanged(explorer, curated_sources):
    """D2d-2 curated-first + legacy-fallback tests (F2/F3/F15-equivalent) still hold with the
    identity-enrichment code present but not configured."""
    out_val = explorer.run_query({"goal": "fall_detection"}, curated_sources)
    assert all(r["split"] != "test" for r in out_val.get("rows", []))
    out_legacy = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "legacy_only_key_not_curated"},
        curated_sources)
    assert out_legacy["status"] == "refused"
    assert out_legacy["state_id"] == "unknown_reference_query"


def test_i13_no_alias_only_fuzzy_lookup(explorer, identity_sources):
    """H15 and D8b must never resolve as a reference_evidence_query key on their own -- only the
    real keys (H15_eps0015_frozen, AFAC_eps0030_F20_posthoc) are valid query values."""
    for bogus_key in ("H15", "D8b", "D8", "A1", "H1"):
        out = explorer.run_query(
            {"goal": "fall_detection", "reference_evidence_query": bogus_key}, identity_sources)
        assert out["status"] == "refused", bogus_key
        assert out["state_id"] == "unknown_reference_query", bogus_key


def test_i14_structured_alias_preservation(explorer, identity_sources):
    """Alias metadata is returned as structured dicts, never flattened into a string, never
    inventing a meaning."""
    out = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "H15_eps0015_frozen"}, identity_sources)
    aliases = out["rows"][0]["experiment_identity"]["legacy_aliases"]
    assert isinstance(aliases, list) and isinstance(aliases[0], dict)
    assert set(aliases[0].keys()) >= {"value", "alias_type", "meaning", "meaning_status", "source_paths", "note"}
    assert aliases[0]["meaning"] is None
    assert aliases[0]["meaning_status"] == "unverified"


def test_i15_identity_does_not_require_checkpoint_existence(explorer, curated_sources):
    """A run record whose checkpoint_or_artifact path is synthetic/nonexistent must still enrich
    successfully -- identity resolution never touches the filesystem checkpoint."""
    run_with_fake_checkpoint = _RUN_YAML.replace(
        "identity_status: verified",
        'checkpoint_or_artifact: "checkpoints/does_not_exist_anywhere.pt"\n  identity_status: verified')
    identity_yaml = _write_identity_yaml(
        curated_sources["_tmp_root"] / "registry" / "fake_checkpoint_identity.yaml",
        run_with_fake_checkpoint, _H15_EVAL_YAML)
    assert not Path("checkpoints/does_not_exist_anywhere.pt").exists()
    src = {**curated_sources, "identity_yaml": str(identity_yaml)}
    out = explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "H15_eps0015_frozen"}, src)
    assert out["status"] == "ok"
    assert out["rows"][0]["experiment_identity"]["state"] == "matched"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
