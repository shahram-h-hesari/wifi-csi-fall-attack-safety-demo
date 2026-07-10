#!/usr/bin/env python
"""D3 acceptance tests for the Markdown research-evidence dashboard renderer.

Spec: automation/acceptance/dashboard-research-summary.yaml. Contract:
    dashboard_research_summary.render_research_evidence(sources) -> str

Synthetic tmp_path fixtures ONLY -- never touches the real committed registries/results/ during
tests (that is proven separately by the real-data smoke render in the D3 claim receipt). Every
test drives the renderer through Result Explorer's real, unmodified run_query() -- this file never
reimplements scientific resolution or identity matching; it only proves the RENDERER consumes
Result Explorer's output faithfully and degrades honestly when a source is missing/inconsistent.

Run: python -m pytest scripts/automation/test_dashboard_research_summary.py -v
"""
from __future__ import annotations

import csv
import importlib
import sys
import textwrap
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

MANIFEST_HEADER = (
    "path,kind,sha256,size_bytes,generator_script,link_method,evidence_level,"
    "evidence_provenance,split,claim_boundary,overleaf_ready,overleaf_blockers,committed"
)
LEDGER_HEADER = (
    "method_internal_name,method_thesis_name,approach_group,seed,split,attack,epsilon,"
    "checkpoint_or_threshold_rule,threshold,source_file,source_type,result_status,"
    "TP,FN,FP,TN,Rfall,FAR,precision,F1,accuracy,macro_F1,AUROC,"
    "Rfall_at_FAR_005,Rfall_at_FAR_010,Rfall_at_FAR_015,Rfall_at_FAR_020,"
    "TP_at_FAR_020,FP_at_FAR_020,F20_reached,notes"
)

H15_METRICS = {"TP": 41, "FN": 4, "FP": 60, "TN": 395, "Rfall": 0.911111, "FAR": 0.131868}
AFAC_METRICS = {"TP": 36, "FN": 9, "FP": 91, "TN": 364, "Rfall": 0.800000, "FAR": 0.200000}


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


GOALS_YAML = """\
    schema_version: 1
    goals:
      - id: fall_detection
        display_name: "Fall Detection"
        aliases: ["fall"]
        task_type: binary_safety_critical_detection
        status: ACTIVE_THESIS_PRIMARY
        metrics: ["fall recall", "FAR"]
        primary_metric_keys: [Rfall, FAR, AUROC, TP, FN, FP, TN]
        success_targets:
          R90F10: { rule: "Rfall > 0.90 AND FAR < 0.10 @ PGD eps=0.030", status: not_met, evidence_level: none }
          F20: { rule: "Rfall >= 0.80 AND FAR <= 0.20 @ PGD eps=0.030", status: post_hoc_only, evidence_level: test-post-hoc }
        datasets_available: ["sensefi_ut_har"]
        data_needs: []
        evidence_rules: "frozen via protocol registry only"
        allowed_evidence_levels: [frozen-test, validation-only, test-descriptive, test-post-hoc, diagnostic-internal]
        default_query_fields: { attack: pgd, epsilon: 0.030, split: val, defense: any }
        reference_evidence_queries:
          H15_eps0015_frozen: { split: test, evidence_level: frozen-test, attack: pgd, epsilon: 0.015 }
          AFAC_eps0030_F20_posthoc: { split: test, evidence_level: test-post-hoc, attack: pgd, epsilon: 0.030 }
        grant_relevance: "core"
        clinical_caution: HIGH
        clinical_claim_boundary: { permitted: [], forbidden: ["clinical claim"] }
      - id: walking_detection
        display_name: "Walking Detection"
        aliases: ["walk"]
        task_type: binary_activity_detection
        status: DATA_AVAILABLE_NOT_EVALUATED
        metrics: ["walking recall"]
        primary_metric_keys: [walking_recall]
        success_targets: null
        datasets_available: ["sensefi_ut_har"]
        data_needs: []
        evidence_rules: "no results until verified rows exist"
        allowed_evidence_levels: [validation-only, test-descriptive, diagnostic-internal]
        default_query_fields: { attack: none, epsilon: null, split: val, defense: none }
        grant_relevance: "mobility"
        clinical_caution: MEDIUM
        clinical_claim_boundary: { permitted: [], forbidden: ["diagnostic claim"] }
      - id: gait_or_mobility_change_detection
        display_name: "Gait / Mobility Change Detection"
        aliases: ["mobility_change"]
        task_type: longitudinal_change_detection
        status: NO_DATA
        metrics: ["change sensitivity"]
        primary_metric_keys: [change_sensitivity]
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
        primary_metric_keys: [risk_AUROC]
        success_targets: null
        datasets_available: []
        data_needs: ["prospective cohort with adjudicated fall outcomes"]
        evidence_rules: "no dataset -> no claims"
        allowed_evidence_levels: []
        default_query_fields: { attack: none, epsilon: null, split: null, defense: none }
        grant_relevance: "aspirational"
        clinical_caution: MAX
        clinical_claim_boundary: { permitted: [], forbidden: ["any prognostic claim"] }
    """

DATASETS_YAML = """\
    schema_version: 1
    datasets:
      - id: sensefi_ut_har
        family: SenseFi
        name: UT-HAR
        signal_type: wifi_csi_amplitude
        classes: ["lie down", "fall", "walk"]
        label_map: { 0: "lie down", 1: "fall", 2: "walk", fall_class_index: 1, walk_class_index: 2, source: "synthetic" }
        supported_goals: [fall_detection, walking_detection]
        unsupported_goals: [gait_or_mobility_change_detection, future_fall_risk_prediction]
        split_policy: "frozen test one-shot; val for selection"
        known_limitations: ["no real clinical falls"]
        exists_locally: true
        local_data_status: PRESENT_LOCAL
        local_paths_known: true
        supported_attack_families: [fgsm, pgd]
        supported_defense_families: [undefended, afac]
        recommended_first_query: { goal: fall_detection, attack: pgd, epsilon: 0.030, split: val, defense: any }
    """

REF_EVIDENCE_YAML = """\
    schema_version: 1
    reference_results:
      - key: H15_eps0015_frozen
        goal: fall_detection
        dataset: sensefi_ut_har
        attack: pgd
        epsilon: 0.015
        split: test
        evidence_level: frozen-test
        threshold: 0.168754
        metrics: {{TP: 41, FN: 4, FP: 60, TN: 395, Rfall: 0.911111, FAR: 0.131868}}
        protocol_id: "H15-TEST-EPS0015-AFAC-20260705"
        provenance:
          confusion_csv: "synthetic/curated_h15_confusion.csv"
          required_manifest_evidence_level: {h15_level}
        disclosures:
          - "eps=0.015, NOT eps=0.030 -- this is not the R90F10 operating point"
          - "not R90F10 -- FAR (0.131868) remains above the 0.10 R90F10 ceiling"
          - "frozen-test evidence -- a one-shot protocol read, not clinical or deployment evidence"
      - key: AFAC_eps0030_F20_posthoc
        goal: fall_detection
        dataset: sensefi_ut_har
        attack: pgd
        epsilon: 0.030
        split: test
        evidence_level: test-post-hoc
        method: optionB_AFAC
        threshold: 0.153246
        metrics: {{TP: 36, FN: 9, FP: 91, TN: 364, Rfall: 0.800000, FAR: 0.200000}}
        provenance:
          source_file: "synthetic/curated_afac_posthoc.csv"
          required_manifest_evidence_level: test-post-hoc
        disclosures:
          - "post-hoc only -- a satisfying threshold exists on saved scores, not a frozen read"
          - "F20 knife-edge caveat -- treat as fragile, not robust"
          - "not R90F10 -- FAR (0.200000) is well above the 0.10 R90F10 ceiling"
    """

IDENTITY_YAML = """\
    schema_version: 1
    naming_policy:
      epsilon_tokens: {{0.015: eps0p015, 0.03: eps0p030}}
    runs:
      - run_id: run_fall_detection_sensefi_ut_har_afac_optionb_seed42_maxscore_v1
        display_name: "AFAC optionB seed-42 (maxscore-selected) checkpoint"
        goal: fall_detection
        dataset: sensefi_ut_har
        method_family: AFAC
        method_variant: optionB_AFAC
        identity_status: verified
        legacy_aliases: []
    evaluations:
      - evaluation_id: eval_fall_detection_sensefi_ut_har_afac_pgd_eps0p015_frozen_test_v1
        display_name: "AFAC frozen-test evaluation under PGD epsilon=0.015"
        run_id: run_fall_detection_sensefi_ut_har_afac_optionb_seed42_maxscore_v1
        run_link_status: verified
        reference_evidence_key: H15_eps0015_frozen
        goal: fall_detection
        dataset: sensefi_ut_har
        method_family: AFAC
        method_variant: optionB_AFAC
        attack: pgd
        epsilon: {h15_id_epsilon}
        split: test
        evidence_level: {h15_id_evidence_level}
        protocol_id: "H15-TEST-EPS0015-AFAC-20260705"
        identity_status: verified
        legacy_aliases:
          - value: H15
            alias_type: historical_milestone_label
            meaning: null
            meaning_status: unverified
            source_paths: ["synthetic/h15_doc.md"]
            note: "Historical internal label; expansion not asserted."
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
            source_paths: ["synthetic/plot_d1_d12.py"]
            note: "Verified field-for-field match."
          - value: D8
            alias_type: historical_family_label
            meaning: null
            meaning_status: unverified
            source_paths: ["synthetic/plot_d1_d12.py"]
            note: "Broader family; deliberately separate from D8b; not equivalent."
    """


def _build_sources(tmp_path, h15_manifest_level="frozen-test",
                    h15_id_epsilon="0.015", h15_id_evidence_level="frozen-test",
                    with_identity=True):
    goals_yaml = _write(tmp_path / "registry" / "goals.yaml", GOALS_YAML)
    datasets_yaml = _write(tmp_path / "registry" / "datasets.yaml", DATASETS_YAML)
    ref_yaml = _write(tmp_path / "registry" / "reference_evidence.yaml",
                      REF_EVIDENCE_YAML.format(h15_level=h15_manifest_level))

    ledger_csv = tmp_path / "ledger.csv"
    with ledger_csv.open("w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=LEDGER_HEADER.split(",")).writeheader()

    mh = MANIFEST_HEADER.split(",")
    manifest_csv = tmp_path / "manifest.csv"
    with manifest_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=mh)
        w.writeheader()
        for path, ev in [("synthetic/curated_h15_confusion.csv", h15_manifest_level),
                         ("synthetic/curated_afac_posthoc.csv", "test-post-hoc")]:
            w.writerow({**{c: "" for c in mh}, "path": path, "kind": "csv", "sha256": "abc123",
                        "evidence_level": ev, "split": "test", "committed": "yes"})

    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()

    sources = {
        "goals_yaml": str(goals_yaml),
        "datasets_yaml": str(datasets_yaml),
        "ledger_csv": str(ledger_csv),
        "manifest_csv": str(manifest_csv),
        "receipts_dir": str(receipts_dir),
        "reference_evidence_yaml": str(ref_yaml),
    }
    if with_identity:
        identity_yaml = _write(tmp_path / "registry" / "experiment_identity.yaml",
                               IDENTITY_YAML.format(h15_id_epsilon=h15_id_epsilon,
                                                     h15_id_evidence_level=h15_id_evidence_level))
        sources["identity_yaml"] = str(identity_yaml)
    return sources


@pytest.fixture()
def result_explorer():
    return importlib.import_module("result_explorer")


@pytest.fixture()
def drs():
    return importlib.import_module("dashboard_research_summary")


@pytest.fixture()
def sources(tmp_path):
    return _build_sources(tmp_path)


# =============================================================== D3-1: successful reference rendering
def test_d3_1_two_curated_references_render_via_result_explorer(drs, sources):
    out = drs.render_research_evidence(sources)
    assert "AFAC frozen-test evaluation under PGD epsilon=0.015" in out
    assert "AFAC post-hoc F20 operating point under PGD epsilon=0.030" in out
    # canonical display names are the primary (### header) labels, not the bare legacy codes
    assert "### AFAC frozen-test evaluation under PGD epsilon=0.015" in out
    assert "### AFAC post-hoc F20 operating point under PGD epsilon=0.030" in out
    assert "### H15" not in out
    assert "### D8b" not in out


# =============================================================== D3-2: H15 identity rendering
def test_d3_2_h15_identity_rendering(drs, sources):
    out = drs.render_research_evidence(sources)
    assert "eval_fall_detection_sensefi_ut_har_afac_pgd_eps0p015_frozen_test_v1" in out
    assert "run_fall_detection_sensefi_ut_har_afac_optionb_seed42_maxscore_v1" in out
    assert "`H15` — unverified" in out
    assert "frozen-test" in out
    # eps=0.015 is never confused with eps=0.030 in the H15 block
    h15_block = out.split("### AFAC frozen-test evaluation under PGD epsilon=0.015")[1]
    h15_block = h15_block.split("### AFAC post-hoc")[0]
    assert "epsilon `0.015`" in h15_block
    assert "epsilon `0.03`" not in h15_block


# =============================================================== D3-3: AFAC post-hoc rendering
def test_d3_3_afac_posthoc_rendering(drs, sources):
    out = drs.render_research_evidence(sources)
    afac_block = out.split("### AFAC post-hoc F20 operating point under PGD epsilon=0.030")[1]
    afac_block = afac_block.split("### C. Target Assessment")[0]   # this reference's own B-section entry only
    assert "`D8b` — verified" in afac_block
    assert "`D8` — unverified" in afac_block
    assert "evidence `test-post-hoc`" in afac_block
    assert "evidence `frozen-test`" not in afac_block   # AFAC's own evidence level is never mislabeled
    # F20 boundary qualification appears in the target-assessment table for this reference
    assert "F20 boundary, test-post-hoc" in out


# =============================================================== D3-4: scientific metric fidelity
def test_d3_4_scientific_metric_fidelity(drs, result_explorer, sources):
    expected = result_explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "H15_eps0015_frozen"}, sources)
    row = expected["rows"][0]
    out = drs.render_research_evidence(sources)
    m = row["metrics"]
    assert f"TP {m['TP']} / FN {m['FN']} / FP {m['FP']} / TN {m['TN']}" in out
    assert f"Rfall {m['Rfall']}" in out
    assert f"FAR {m['FAR']}" in out
    assert f"threshold {row['threshold']}" in out


# =============================================================== D3-5: target assessment
def test_d3_5_target_assessment_comparators(drs, sources):
    out = drs.render_research_evidence(sources)
    assert "| `H15_eps0015_frozen` | R90F10 | R90 recall component reached, FAR component not reached; frozen-test at ε=0.015 |" in out
    assert "| `AFAC_eps0030_F20_posthoc` | F20 | F20 boundary, test-post-hoc |" in out
    # H15 never receives a full R90F10 pass
    assert "R90F10 reached" not in out
    assert "R90F10 boundary" not in out


def test_d3_5b_assess_target_exact_comparators(drs):
    ok = drs.assess_target("F20", "Rfall >= 0.80 AND FAR <= 0.20 @ PGD eps=0.030",
                           {"Rfall": 0.80, "FAR": 0.20}, "test-post-hoc", 0.03)
    assert ok["status"] == "reached" and ok["boundary"] is True
    fail = drs.assess_target("R90F10", "Rfall > 0.90 AND FAR < 0.10 @ PGD eps=0.030",
                             {"Rfall": 0.911111, "FAR": 0.131868}, "frozen-test", 0.015)
    assert fail["status"] == "not_reached"
    assert fail["checks"][0]["ok"] is True and fail["checks"][1]["ok"] is False


# =============================================================== D3-6: identity unavailable
def test_d3_6_identity_unavailable_keeps_metrics_no_fabricated_id(drs, tmp_path):
    sources_no_identity = _build_sources(tmp_path, with_identity=False)
    out = drs.render_research_evidence(sources_no_identity)
    assert "Identity unavailable:" in out
    assert "TP 41 / FN 4 / FP 60 / TN 395" in out   # metrics still visible
    assert "eval_fall_detection_sensefi_ut_har_afac_pgd_eps0p015_frozen_test_v1" not in out
    assert "AFAC frozen-test evaluation under PGD epsilon=0.015" not in out   # no fabricated canonical name


# =============================================================== D3-7: identity mismatch
def test_d3_7_identity_mismatch_suppresses_canonical_id_keeps_metrics(drs, tmp_path):
    sources_mismatch = _build_sources(tmp_path, h15_id_epsilon="0.03")  # wrong epsilon on purpose
    out = drs.render_research_evidence(sources_mismatch)
    assert "Identity mismatch — canonical identity suppressed:" in out
    assert "TP 41 / FN 4 / FP 60 / TN 395" in out
    assert "eval_fall_detection_sensefi_ut_har_afac_pgd_eps0p015_frozen_test_v1" not in out


# =============================================================== D3-8: provenance mismatch
def test_d3_8_provenance_mismatch_suppresses_metrics_shows_refusal(drs, tmp_path):
    sources_prov = _build_sources(tmp_path, h15_manifest_level="validation-only")  # disagrees with declared frozen-test
    out = drs.render_research_evidence(sources_prov)
    assert "REFUSED" in out
    assert "provenance_mismatch" in out
    h15_section = out.split("### H15_eps0015_frozen")[1].split("###")[0]
    assert "TP 41" not in h15_section
    assert "Rfall 0.911111" not in h15_section


# =============================================================== D3-9: missing reference
def test_d3_9_missing_reference_honest_empty_state(drs):
    result = {"status": "empty", "state_id": "no_matching_artifact",
              "message": "NO MATCH — valid query, zero rows under these filters", "rows": []}
    out = drs._render_reference_entry("SOME_KEY_eps9999", result)
    assert "no result" in out
    assert "NO MATCH" in out
    assert "TP" not in out and "Rfall" not in out   # no stale metrics retained


# =============================================================== D3-10: goal/dataset readiness
def test_d3_10_goal_dataset_readiness(drs, sources):
    out = drs.render_research_evidence(sources)
    assert "| `walking_detection` | dataset-supported but not yet evaluated (dataset: UT-HAR) |" in out
    assert "| `gait_or_mobility_change_detection` | data needed" in out
    assert "| `future_fall_risk_prediction` | data needed / aspirational" in out
    assert "| `fall_detection` | supported and evaluated (dataset: UT-HAR) |" in out


# =============================================================== D3-11: deterministic rendering
def test_d3_11_deterministic_rendering(drs, sources):
    a = drs.render_research_evidence(sources)
    b = drs.render_research_evidence(sources)
    assert a == b


# =============================================================== D3-12: idempotent dashboard refresh
def test_d3_12_idempotent_full_dashboard_refresh():
    sys.path.insert(0, str(HERE))
    import update_dashboard as ud
    a_md, a_js, _ = ud.do_render(write=False)
    b_md, b_js, _ = ud.do_render(write=False)
    assert a_md == b_md
    assert a_js == b_js


# =============================================================== D3-13: no production hardcoded evidence
def test_d3_13_no_hardcoded_scientific_constants_in_production_module():
    src = (HERE / "dashboard_research_summary.py").read_text(encoding="utf-8")
    forbidden = [
        "eval_fall_detection_sensefi_ut_har_afac_pgd_eps0p015_frozen_test_v1",
        "eval_fall_detection_sensefi_ut_har_afac_pgd_eps0p030_test_posthoc_v1",
        "run_fall_detection_sensefi_ut_har_afac_optionb_seed42_maxscore_v1",
        "AFAC frozen-test evaluation under PGD epsilon=0.015",
        "AFAC post-hoc F20 operating point under PGD epsilon=0.030",
        "0.911111", "0.131868", "0.168754",  # H15 metrics/threshold
        "0.153246",                           # AFAC threshold
        "395", "364",                         # confusion counts unlikely to appear for any other reason
    ]
    for literal in forbidden:
        assert literal not in src, f"production renderer hardcodes {literal!r}"


def test_d3_13b_no_independent_alias_mapping():
    src = (HERE / "dashboard_research_summary.py").read_text(encoding="utf-8")
    # the renderer must never itself decide that "H15" means the frozen eval, or "D8b" the post-hoc
    # one -- it only ever reads back experiment_identity.legacy_aliases as already resolved by
    # Result Explorer.
    assert '"H15"' not in src and "'H15'" not in src
    assert '"D8b"' not in src and "'D8b'" not in src


# =============================================================== D3-14: no HTML changes
def test_d3_14_no_html_touched():
    src = (HERE / "dashboard_research_summary.py").read_text(encoding="utf-8")
    assert ".html" not in src
    assert "dashboard/index" not in src


# =============================================================== D3-15: Result Explorer regression
def test_d3_15_result_explorer_unchanged_behavior(result_explorer, sources):
    out = result_explorer.run_query(
        {"goal": "fall_detection", "reference_evidence_query": "AFAC_eps0030_F20_posthoc"}, sources)
    assert out["status"] == "ok"
    row = out["rows"][0]
    for k, v in AFAC_METRICS.items():
        assert row["metrics"][k] == pytest.approx(v), k
    assert row["evidence_level"] == "test-post-hoc"


# =============================================================== defensive: real committed sources smoke
def test_real_sources_render_without_crashing():
    """Read-only smoke check against the REAL committed registries (not a synthetic fixture) --
    proves the renderer works against production data too. No results/ mutation; no --split."""
    repo = Path(__file__).resolve().parents[2]
    aut = repo / "automation"
    real_sources = {
        "goals_yaml": str(aut / "registry" / "goals.yaml"),
        "datasets_yaml": str(aut / "registry" / "datasets.yaml"),
        "ledger_csv": str(repo / "results" / "defense_attempt_inventory" / "defense_attempt_results_long.csv"),
        "manifest_csv": str(aut / "artifact_manifest.csv"),
        "receipts_dir": str(aut / "receipts"),
        "reference_evidence_yaml": str(aut / "registry" / "reference_evidence.yaml"),
        "identity_yaml": str(aut / "registry" / "experiment_identity.yaml"),
    }
    drs_mod = importlib.import_module("dashboard_research_summary")
    out = drs_mod.render_research_evidence(real_sources)
    assert "AFAC frozen-test evaluation under PGD epsilon=0.015" in out
    assert "AFAC post-hoc F20 operating point under PGD epsilon=0.030" in out
