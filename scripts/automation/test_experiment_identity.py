#!/usr/bin/env python
"""D2e-1 acceptance tests for the experiment-identity validator.

Synthetic temporary fixtures ONLY -- never edits the real committed registries. Confirms both:
(a) the real committed automation/registry/experiment_identity.yaml validates cleanly (N1-style
    check against the real repo, read-only), and
(b) a battery of synthetic failure/success cases (N1-N15) exercise every safety rule in
    automation/acceptance/experiment-identity.yaml individually.

Run: python scripts/automation/test_experiment_identity.py
"""
from __future__ import annotations

import copy
import sys
import tempfile
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_experiment_identity as vei  # noqa: E402

REPO = Path(__file__).resolve().parents[2]


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def _base_sources(tmp_path: Path) -> dict:
    """Minimal synthetic goals/datasets/reference-evidence registries mirroring the real schemas,
    plus a synthetic identity registry with ONE valid run + ONE valid evaluation (N1 baseline)."""
    goals_yaml = _write(tmp_path / "goals.yaml", """\
        schema_version: 1
        goals:
          - id: fall_detection
            allowed_evidence_levels: [frozen-test, validation-only, test-post-hoc]
        """)
    datasets_yaml = _write(tmp_path / "datasets.yaml", """\
        schema_version: 1
        datasets:
          - id: sensefi_ut_har
            family: SenseFi
            name: UT-HAR
            supported_goals: [fall_detection]
            unsupported_goals: []
        """)
    ref_yaml = _write(tmp_path / "reference_evidence.yaml", """\
        schema_version: 1
        reference_results:
          - key: H15_eps0015_frozen
            goal: fall_detection
            dataset: sensefi_ut_har
            attack: pgd
            epsilon: 0.015
            split: test
            evidence_level: frozen-test
          - key: AFAC_eps0030_F20_posthoc
            goal: fall_detection
            dataset: sensefi_ut_har
            attack: pgd
            epsilon: 0.03
            split: test
            evidence_level: test-post-hoc
        """)
    identity_yaml = _write(tmp_path / "experiment_identity.yaml", """\
        schema_version: 1
        naming_policy:
          epsilon_tokens: {0.015: eps0p015, 0.03: eps0p030}
          evidence_tokens: {frozen-test: frozen_test, test-post-hoc: test_posthoc}
        runs:
          - run_id: run_fall_detection_sensefi_ut_har_afac_seed42_v1
            display_name: "AFAC seed-42 checkpoint"
            goal: fall_detection
            dataset: sensefi_ut_har
            method_family: AFAC
            checkpoint_sha256: "deadbeef"
            identity_status: verified
            provenance: {checkpoint_path: "checkpoints/synthetic.pt"}
            legacy_aliases: []
        evaluations:
          - evaluation_id: eval_fall_detection_sensefi_ut_har_afac_pgd_eps0p015_frozen_test_v1
            display_name: "AFAC frozen-test evaluation under PGD epsilon=0.015"
            run_id: run_fall_detection_sensefi_ut_har_afac_seed42_v1
            run_link_status: verified
            reference_evidence_key: H15_eps0015_frozen
            goal: fall_detection
            dataset: sensefi_ut_har
            method_family: AFAC
            attack: pgd
            epsilon: 0.015
            split: test
            evidence_level: frozen-test
            identity_status: verified
            provenance: {confusion_csv: "results/synthetic_confusion.csv"}
            legacy_aliases:
              - value: H15
                alias_type: historical_milestone_label
                meaning: null
                meaning_status: unverified
                source_paths: ["results/synthetic_h15_doc.md"]
                note: "Historical internal label; expansion not asserted."
        legacy_alias_glossary: []
        """)
    return {
        "identity_yaml": str(identity_yaml),
        "reference_evidence_yaml": str(ref_yaml),
        "goals_yaml": str(goals_yaml),
        "datasets_yaml": str(datasets_yaml),
        "_tmp_root": tmp_path,
    }


def _mutate_identity(sources: dict, tmp_path: Path, new_identity_dict: dict, filename="mutated.yaml") -> dict:
    import yaml
    p = tmp_path / filename
    p.write_text(yaml.safe_dump(new_identity_dict, sort_keys=False), encoding="utf-8")
    return {**sources, "identity_yaml": str(p)}


def _load(sources):
    import yaml
    return yaml.safe_load(Path(sources["identity_yaml"]).read_text(encoding="utf-8"))


def _codes(errors):
    return {e.code for e in errors}


# ---------------------------------------------------------------------------------- test runner
_RESULTS = []


def _case(name, condition, detail=""):
    _RESULTS.append((name, bool(condition), detail))


def run():
    tmp_path = Path(tempfile.mkdtemp(prefix="expid_"))
    sources = _base_sources(tmp_path)

    # ---- N1: valid initial registry
    errors, warnings, summary = vei.validate(sources)
    _case("N1 valid initial registry", not errors, str(errors))

    # ---- N2: duplicate evaluation ID rejected
    d = _load(sources)
    dup_eval = copy.deepcopy(d["evaluations"][0])
    d["evaluations"].append(dup_eval)  # exact same evaluation_id twice
    src2 = _mutate_identity(sources, tmp_path, d, "n2.yaml")
    errors, _, _ = vei.validate(src2)
    _case("N2 duplicate evaluation ID rejected", "duplicate_evaluation_id" in _codes(errors), str(errors))

    # ---- N3: duplicate reference key rejected
    d = _load(sources)
    dup_ref = copy.deepcopy(d["evaluations"][0])
    dup_ref["evaluation_id"] = "eval_fall_detection_sensefi_ut_har_afac_pgd_eps0p030_test_posthoc_v1"
    dup_ref["epsilon"] = 0.03
    dup_ref["evidence_level"] = "test-post-hoc"
    dup_ref["legacy_aliases"] = []
    # deliberately reuse the SAME reference_evidence_key as the first evaluation
    d["evaluations"].append(dup_ref)
    src3 = _mutate_identity(sources, tmp_path, d, "n3.yaml")
    errors, _, _ = vei.validate(src3)
    _case("N3 duplicate reference key rejected", "duplicate_reference_key" in _codes(errors), str(errors))

    # ---- N4: missing display name rejected
    d = _load(sources)
    d["evaluations"][0]["display_name"] = ""
    src4 = _mutate_identity(sources, tmp_path, d, "n4.yaml")
    errors, _, _ = vei.validate(src4)
    _case("N4 missing display name rejected", "missing_display_name" in _codes(errors), str(errors))

    # ---- N5: invalid canonical ID rejected (bare historical code as the ID)
    d = _load(sources)
    d["evaluations"][0]["evaluation_id"] = "h15"
    src5 = _mutate_identity(sources, tmp_path, d, "n5.yaml")
    errors, _, _ = vei.validate(src5)
    _case("N5 invalid canonical ID rejected", "invalid_canonical_id" in _codes(errors), str(errors))

    # ---- N6: epsilon token mismatch rejected
    d = _load(sources)
    d["evaluations"][0]["epsilon"] = 0.03   # ID still says eps0p015 -> mismatch
    src6 = _mutate_identity(sources, tmp_path, d, "n6.yaml")
    errors, _, _ = vei.validate(src6)
    _case("N6 epsilon token mismatch rejected", "epsilon_token_mismatch" in _codes(errors), str(errors))

    # ---- N7: invalid goal/dataset pairing rejected
    d = _load(sources)
    d["evaluations"][0]["dataset"] = "unsupported_dataset_xyz"
    src7 = _mutate_identity(sources, tmp_path, d, "n7.yaml")
    errors, _, _ = vei.validate(src7)
    _case("N7 invalid goal/dataset pairing rejected",
          "invalid_dataset" in _codes(errors), str(errors))

    # N7b: dataset exists but does not support the goal
    ds_yaml = _write(tmp_path / "datasets_n7b.yaml", """\
        schema_version: 1
        datasets:
          - id: sensefi_ut_har
            family: SenseFi
            name: UT-HAR
            supported_goals: [walking_detection]
            unsupported_goals: [fall_detection]
        """)
    src7b = {**sources, "datasets_yaml": str(ds_yaml)}
    errors, _, _ = vei.validate(src7b)
    _case("N7b goal/dataset incompatibility rejected", "goal_dataset_incompatible" in _codes(errors), str(errors))

    # ---- N8: frozen/post-hoc evidence mismatch rejected (evaluation disagrees with its cited
    # reference_evidence_key's declared evidence_level)
    d = _load(sources)
    d["evaluations"][0]["evidence_level"] = "test-post-hoc"   # ref key says frozen-test
    src8 = _mutate_identity(sources, tmp_path, d, "n8.yaml")
    errors, _, _ = vei.validate(src8)
    _case("N8 frozen/post-hoc evidence mismatch rejected",
          "reference_field_disagreement" in _codes(errors), str(errors))

    # ---- N9: unverified alias with invented meaning rejected
    d = _load(sources)
    d["evaluations"][0]["legacy_aliases"][0]["meaning"] = "Hypothesis 15"  # invented, meaning_status still unverified
    src9 = _mutate_identity(sources, tmp_path, d, "n9.yaml")
    errors, _, _ = vei.validate(src9)
    _case("N9 unverified alias with invented meaning rejected",
          "invented_alias_meaning" in _codes(errors), str(errors))

    # ---- N10: unresolved legacy run link allowed ONLY with partial_legacy
    d = _load(sources)
    d["evaluations"][0]["run_id"] = None
    d["evaluations"][0]["run_link_status"] = "unresolved_legacy"
    d["evaluations"][0]["identity_status"] = "verified"   # should have been partial_legacy
    src10bad = _mutate_identity(sources, tmp_path, d, "n10bad.yaml")
    errors, _, _ = vei.validate(src10bad)
    _case("N10a unresolved link without partial_legacy rejected",
          "legacy_link_not_marked_partial" in _codes(errors), str(errors))

    d2 = _load(sources)
    d2["evaluations"][0]["run_id"] = None
    d2["evaluations"][0]["run_link_status"] = "unresolved_legacy"
    d2["evaluations"][0]["identity_status"] = "partial_legacy"   # correctly marked
    src10good = _mutate_identity(sources, tmp_path, d2, "n10good.yaml")
    errors, _, _ = vei.validate(src10good)
    _case("N10b unresolved link WITH partial_legacy allowed",
          "legacy_link_not_marked_partial" not in _codes(errors) and "missing_run_id_non_legacy" not in _codes(errors),
          str(errors))

    # ---- N11: new non-legacy evaluation without run_id rejected
    d = _load(sources)
    d["evaluations"][0]["run_id"] = None
    d["evaluations"][0]["run_link_status"] = None
    # identity_status stays "verified", i.e. NOT partial_legacy -> must be rejected
    src11 = _mutate_identity(sources, tmp_path, d, "n11.yaml")
    errors, _, _ = vei.validate(src11)
    _case("N11 new evaluation without run_id rejected",
          "missing_run_id_non_legacy" in _codes(errors), str(errors))

    # ---- N12: H15 canonical identity and legacy alias preserved (real registry check)
    real_sources = {
        "identity_yaml": REPO / "automation" / "registry" / "experiment_identity.yaml",
        "reference_evidence_yaml": REPO / "automation" / "registry" / "reference_evidence.yaml",
        "goals_yaml": REPO / "automation" / "registry" / "goals.yaml",
        "datasets_yaml": REPO / "automation" / "registry" / "datasets.yaml",
    }
    real_identity = vei._load_yaml(real_sources["identity_yaml"])
    h15_eval = next((e for e in real_identity["evaluations"]
                      if e.get("reference_evidence_key") == "H15_eps0015_frozen"), None)
    _case("N12 H15 canonical evaluation exists", h15_eval is not None)
    if h15_eval:
        h15_alias = next((a for a in h15_eval.get("legacy_aliases", []) if a["value"] == "H15"), None)
        _case("N12b H15 legacy alias present with unverified meaning",
              h15_alias is not None and h15_alias["meaning"] is None and h15_alias["meaning_status"] == "unverified",
              str(h15_alias))
        _case("N12c H15 evaluation_id follows canonical pattern",
              h15_eval["evaluation_id"] == "eval_fall_detection_sensefi_ut_har_afac_pgd_eps0p015_frozen_test_v1")

    # ---- N13: AFAC post-hoc canonical identity preserved
    afac_eval = next((e for e in real_identity["evaluations"]
                       if e.get("reference_evidence_key") == "AFAC_eps0030_F20_posthoc"), None)
    _case("N13 AFAC post-hoc canonical evaluation exists", afac_eval is not None)
    if afac_eval:
        _case("N13b AFAC evidence_level is test-post-hoc, never frozen-test",
              afac_eval["evidence_level"] == "test-post-hoc")
        _case("N13c AFAC evaluation_id follows canonical pattern",
              afac_eval["evaluation_id"] == "eval_fall_detection_sensefi_ut_har_afac_pgd_eps0p030_test_posthoc_v1")
        d8b_alias = next((a for a in afac_eval.get("legacy_aliases", []) if a["value"] == "D8b"), None)
        _case("N13d D8b alias verified with source citation",
              d8b_alias is not None and d8b_alias["meaning_status"] == "verified" and d8b_alias.get("source_paths"))

    # ---- N14: H15 and AFAC reference keys remain unchanged (immutability)
    real_ref = vei._load_yaml(real_sources["reference_evidence_yaml"])
    ref_keys = {e["key"] for e in real_ref["reference_results"]}
    _case("N14 H15_eps0015_frozen key unchanged", "H15_eps0015_frozen" in ref_keys)
    _case("N14b AFAC_eps0030_F20_posthoc key unchanged", "AFAC_eps0030_F20_posthoc" in ref_keys)
    errors, _, _ = vei.validate({k: str(v) if isinstance(v, Path) else v for k, v in real_sources.items()})
    _case("N14c real registry validates with zero errors", not errors, str(errors))

    # ---- N15: ambiguous/reused alias (A1) handled honestly
    a1 = next((g for g in real_identity.get("legacy_alias_glossary", []) if g["value"] == "A1"), None)
    _case("N15 A1 present in glossary", a1 is not None)
    if a1:
        _case("N15b A1 marked reused=true", a1.get("reused") is True)
        _case("N15c A1 has >=2 distinct reused_objects", len(a1.get("reused_objects", [])) >= 2)
        _case("N15d A1 top-level meaning stays null (no false disambiguation)", a1.get("meaning") is None)
    # negative: a glossary with a reused=true alias but only 1 object must be rejected
    d = _load(sources)
    d.setdefault("legacy_alias_glossary", []).append({
        "value": "X1", "alias_type": "ambiguous", "meaning": None, "meaning_status": "unverified",
        "reused": True, "reused_objects": [{"object": "only one", "meaning_status": "unverified"}],
    })
    src15 = _mutate_identity(sources, tmp_path, d, "n15.yaml")
    errors, _, _ = vei.validate(src15)
    _case("N15e underspecified reused alias rejected", "reused_alias_underspecified" in _codes(errors), str(errors))

    # ---- extra: malformed alias rejected
    d = _load(sources)
    d["evaluations"][0]["legacy_aliases"] = [{"value": "BROKEN"}]  # missing meaning_status
    srcX = _mutate_identity(sources, tmp_path, d, "malformed.yaml")
    errors, _, _ = vei.validate(srcX)
    _case("extra: malformed alias rejected", "malformed_alias" in _codes(errors), str(errors))

    # ---- extra: verified alias without source_paths rejected
    d = _load(sources)
    d["evaluations"][0]["legacy_aliases"][0]["meaning_status"] = "verified"
    d["evaluations"][0]["legacy_aliases"][0]["meaning"] = "something"
    d["evaluations"][0]["legacy_aliases"][0]["source_paths"] = []
    srcY = _mutate_identity(sources, tmp_path, d, "unsourced.yaml")
    errors, _, _ = vei.validate(srcY)
    _case("extra: verified alias without source_paths rejected", "unsourced_verified_alias" in _codes(errors), str(errors))

    # ---- extra: missing registry file handled cleanly (no crash)
    errors, _, _ = vei.validate({**sources, "identity_yaml": str(tmp_path / "does_not_exist.yaml")})
    _case("extra: missing registry file reported, no crash", errors and errors[0].code == "missing_registry", str(errors))

    # ---- extra: unsupported schema version rejected
    d = _load(sources)
    d["schema_version"] = 999
    srcZ = _mutate_identity(sources, tmp_path, d, "badschema.yaml")
    errors, _, _ = vei.validate(srcZ)
    _case("extra: unsupported schema_version rejected", "unsupported_schema_version" in _codes(errors), str(errors))

    ok = True
    print("=== D2e-1 experiment-identity validator test suite ===")
    for name, passed, detail in _RESULTS:
        ok &= passed
        print(f"[{'PASS' if passed else 'FAIL'}] {name}" + (f"  {detail}" if not passed and detail else ""))
    print("\nRESULT:", "ALL PASS" if ok else "FAILURES")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(run())
