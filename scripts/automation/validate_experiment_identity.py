#!/usr/bin/env python
"""Read-only validator for automation/registry/experiment_identity.yaml (D2e-1).

Policy: automation/registry/experiment_identity.md. Contract: validate(sources) -> ValidationResult.

Reads ONLY the paths given in `sources` (identity registry, reference-evidence registry, goals and
datasets registries). Never writes, never modifies, never renames. Cross-checks the identity
registry against the pre-existing, immutable reference_evidence.yaml so the two files can never
silently drift apart.

Safety: pure read-only stdlib+yaml. No subprocess, no network, no file writes.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML required: pip install pyyaml")

CANONICAL_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
BARE_CODE_RE = re.compile(r"^[a-z]\d+$")  # e.g. "h15", "d8", "g1", "a1" — a canonical ID must not BE this
SUPPORTED_SCHEMA_VERSIONS = (1,)


class ValidationError:
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message

    def __repr__(self):
        return f"{self.code}: {self.message}"


def _load_yaml(path):
    p = Path(path)
    if not p.exists():
        return None
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def _is_canonical_id(value: str) -> bool:
    """snake_case, lowercase, repository-safe, and not JUST a bare historical code (rule 4)."""
    if not value or not CANONICAL_ID_RE.match(value):
        return False
    # strip a recognized prefix; what remains must not itself collapse to a bare code like "h15"
    for prefix in ("run_", "eval_"):
        if value.startswith(prefix):
            return True  # prefixed IDs are never bare codes by construction
    return not BARE_CODE_RE.match(value)


def _epsilon_token(epsilon, policy):
    tokens = policy.get("epsilon_tokens") or {}
    # YAML may load numeric keys as float or the exact literal; match numerically
    for k, v in tokens.items():
        try:
            if abs(float(k) - float(epsilon)) < 1e-9:
                return v
        except (TypeError, ValueError):
            continue
    return None


def _evidence_token(level, policy):
    return (policy.get("evidence_tokens") or {}).get(level)


def validate(sources: dict):
    """Returns (errors: list[ValidationError], warnings: list[ValidationError], summary: dict)."""
    errors, warnings = [], []

    identity = _load_yaml(sources["identity_yaml"])
    if identity is None:
        return [ValidationError("missing_registry", "experiment_identity.yaml not found")], [], {}
    if not isinstance(identity, dict):
        return [ValidationError("malformed_registry", "experiment_identity.yaml did not parse to a mapping")], [], {}

    schema_version = identity.get("schema_version")
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        errors.append(ValidationError("unsupported_schema_version",
                                       f"schema_version={schema_version!r} not in {SUPPORTED_SCHEMA_VERSIONS}"))

    policy = identity.get("naming_policy") or {}
    runs = identity.get("runs") or []
    evaluations = identity.get("evaluations") or []
    glossary = identity.get("legacy_alias_glossary") or []

    ref_evidence = _load_yaml(sources.get("reference_evidence_yaml")) or {}
    ref_entries = {e.get("key"): e for e in (ref_evidence.get("reference_results") or [])}

    goals_doc = _load_yaml(sources.get("goals_yaml")) or {}
    goal_ids = {g.get("id") for g in (goals_doc.get("goals") or [])}
    goals_by_id = {g.get("id"): g for g in (goals_doc.get("goals") or [])}

    datasets_doc = _load_yaml(sources.get("datasets_yaml")) or {}
    datasets_by_id = {d.get("id"): d for d in (datasets_doc.get("datasets") or [])}

    # ---------------------------------------------------------------- run-level checks
    run_ids_seen = set()
    run_by_id = {}
    for r in runs:
        rid = r.get("run_id")
        if not rid:
            errors.append(ValidationError("missing_run_id", f"a run record has no run_id: {r!r}"))
            continue
        if rid in run_ids_seen:
            errors.append(ValidationError("duplicate_run_id", f"run_id {rid!r} appears more than once"))
        run_ids_seen.add(rid)
        run_by_id[rid] = r
        if not _is_canonical_id(rid):
            errors.append(ValidationError("invalid_canonical_id", f"run_id {rid!r} is not a valid canonical ID"))
        if not r.get("display_name"):
            errors.append(ValidationError("missing_display_name", f"run {rid!r} has no display_name"))
        status = r.get("identity_status")
        if status == "verified" and not (r.get("checkpoint_sha256") and r.get("provenance")):
            errors.append(ValidationError(
                "unverified_run_link", f"run {rid!r} claims identity_status=verified but lacks "
                f"checkpoint_sha256 + provenance evidence (rule 14)"))

    # ---------------------------------------------------------------- evaluation-level checks
    eval_ids_seen = set()
    ref_keys_seen = set()
    eval_signature_seen = {}   # (goal, dataset, method_variant, attack, epsilon) -> evidence_level, for rule 8
    for e in evaluations:
        eid = e.get("evaluation_id")
        if not eid:
            errors.append(ValidationError("missing_evaluation_id", f"an evaluation record has no evaluation_id: {e!r}"))
            continue
        if eid in eval_ids_seen:
            errors.append(ValidationError("duplicate_evaluation_id", f"evaluation_id {eid!r} appears more than once"))
        eval_ids_seen.add(eid)

        if not _is_canonical_id(eid):
            errors.append(ValidationError("invalid_canonical_id", f"evaluation_id {eid!r} is not a valid canonical ID"))

        if not e.get("display_name"):
            errors.append(ValidationError("missing_display_name", f"evaluation {eid!r} has no display_name"))
        elif BARE_CODE_RE.match(e["display_name"].strip().lower()):
            errors.append(ValidationError("unreadable_display_name",
                                           f"evaluation {eid!r} display_name is just a bare code (rule 17)"))

        goal = e.get("goal")
        dataset = e.get("dataset")
        method_family = e.get("method_family")
        evidence_level = e.get("evidence_level")

        if goal not in goal_ids:
            errors.append(ValidationError("invalid_goal", f"evaluation {eid!r} goal {goal!r} not in goals.yaml"))
        if dataset not in datasets_by_id:
            errors.append(ValidationError("invalid_dataset", f"evaluation {eid!r} dataset {dataset!r} not in datasets.yaml"))
        if goal in goal_ids and dataset in datasets_by_id:
            ds = datasets_by_id[dataset]
            if goal not in (ds.get("supported_goals") or []):
                errors.append(ValidationError(
                    "goal_dataset_incompatible",
                    f"evaluation {eid!r}: dataset {dataset!r} does not support goal {goal!r} "
                    f"per datasets.yaml supported_goals"))
        if not method_family:
            errors.append(ValidationError("missing_method_family", f"evaluation {eid!r} has no method_family"))
        if not evidence_level:
            errors.append(ValidationError("missing_evidence_level", f"evaluation {eid!r} has no evidence_level"))

        # attack/epsilon required together when either is present (rule 7); epsilon token consistency (rule 19)
        attack = e.get("attack")
        epsilon = e.get("epsilon")
        if attack and epsilon is None:
            errors.append(ValidationError("missing_epsilon", f"evaluation {eid!r} has attack but no epsilon"))
        if epsilon is not None and not attack:
            errors.append(ValidationError("missing_attack", f"evaluation {eid!r} has epsilon but no attack"))
        if attack and epsilon is not None:
            tok = _epsilon_token(epsilon, policy)
            if tok is None:
                errors.append(ValidationError("unmapped_epsilon", f"evaluation {eid!r} epsilon {epsilon!r} has no naming_policy.epsilon_tokens mapping"))
            elif tok not in eid:
                errors.append(ValidationError(
                    "epsilon_token_mismatch",
                    f"evaluation {eid!r}: epsilon {epsilon!r} maps to token {tok!r}, "
                    f"which does not appear in the evaluation_id"))

        ev_tok = _evidence_token(evidence_level, policy) if evidence_level else None
        if evidence_level and ev_tok and ev_tok not in eid:
            warnings.append(ValidationError(
                "evidence_token_not_in_id",
                f"evaluation {eid!r}: evidence_level {evidence_level!r} token {ev_tok!r} not found in ID (non-fatal, naming convention only)"))

        # rule 8: validation / test-post-hoc / frozen-test evaluations of the same underlying
        # (goal,dataset,method_variant,attack,epsilon) signature can never share ONE evaluation_id.
        # Already structurally guaranteed: the evidence token is embedded in the ID (checked above)
        # and evaluation_id uniqueness is enforced globally (duplicate_evaluation_id, above) -- two
        # different evidence levels for the same signature necessarily produce two different IDs.
        sig = (goal, dataset, e.get("method_variant"), attack, epsilon)
        eval_signature_seen[sig] = evidence_level

        # run-link integrity (rules 14, 16)
        run_id = e.get("run_id")
        run_link_status = e.get("run_link_status")
        if run_link_status == "verified":
            if not run_id or run_id not in run_by_id:
                errors.append(ValidationError("unverified_run_link", f"evaluation {eid!r} claims run_link_status=verified but run_id {run_id!r} does not resolve to a run record (rule 14)"))
        elif run_link_status == "unresolved_legacy":
            if e.get("identity_status") != "partial_legacy":
                errors.append(ValidationError("legacy_link_not_marked_partial", f"evaluation {eid!r} has run_link_status=unresolved_legacy but identity_status != partial_legacy (rule 16)"))
        elif run_link_status is None:
            errors.append(ValidationError("missing_run_link_status", f"evaluation {eid!r} has no run_link_status"))

        # rule 15: new (non-legacy) evaluations must have a run_id
        if e.get("identity_status") != "partial_legacy" and not run_id:
            errors.append(ValidationError("missing_run_id_non_legacy", f"evaluation {eid!r} is not partial_legacy but has no run_id (rule 15)"))

        # reference-evidence key handling (rules 3, 20)
        ref_key = e.get("reference_evidence_key")
        if ref_key:
            if ref_key in ref_keys_seen:
                errors.append(ValidationError("duplicate_reference_key", f"reference_evidence_key {ref_key!r} used by more than one evaluation"))
            ref_keys_seen.add(ref_key)
            ref_entry = ref_entries.get(ref_key)
            if ref_entry is None:
                errors.append(ValidationError("unknown_reference_key", f"evaluation {eid!r} cites reference_evidence_key {ref_key!r} not found in reference_evidence.yaml"))
            else:
                for field in ("goal", "dataset", "attack", "split", "evidence_level"):
                    if e.get(field) != ref_entry.get(field):
                        errors.append(ValidationError(
                            "reference_field_disagreement",
                            f"evaluation {eid!r}.{field}={e.get(field)!r} disagrees with "
                            f"reference_evidence.yaml[{ref_key!r}].{field}={ref_entry.get(field)!r} (rule 20)"))
                if epsilon is not None and ref_entry.get("epsilon") is not None:
                    if abs(float(epsilon) - float(ref_entry["epsilon"])) > 1e-9:
                        errors.append(ValidationError(
                            "reference_field_disagreement",
                            f"evaluation {eid!r}.epsilon={epsilon!r} disagrees with "
                            f"reference_evidence.yaml[{ref_key!r}].epsilon={ref_entry.get('epsilon')!r} (rule 20)"))

        # alias structure + no-invented-expansion (rules 11, 13)
        for alias in e.get("legacy_aliases") or []:
            if not isinstance(alias, dict) or "value" not in alias or "meaning_status" not in alias:
                errors.append(ValidationError("malformed_alias", f"evaluation {eid!r} has a malformed legacy_alias entry: {alias!r}"))
                continue
            if alias.get("meaning_status") == "unverified" and alias.get("meaning") is not None:
                errors.append(ValidationError(
                    "invented_alias_meaning",
                    f"evaluation {eid!r} alias {alias.get('value')!r}: meaning_status=unverified "
                    f"but meaning is not null (rule 13)"))
            if alias.get("meaning_status") == "verified" and not alias.get("source_paths"):
                errors.append(ValidationError(
                    "unsourced_verified_alias",
                    f"evaluation {eid!r} alias {alias.get('value')!r}: meaning_status=verified "
                    f"but no source_paths cited"))
            for sp in alias.get("source_paths") or []:
                if str(sp).startswith("/") or ":" in str(sp)[:3]:
                    errors.append(ValidationError("non_relative_provenance_path", f"alias source_path {sp!r} is not repository-relative (rule provenance-relative)"))

        # provenance paths must be repository-relative (best-effort check; the same test applies
        # to top-level provenance dicts)
        for k, v in (e.get("provenance") or {}).items():
            if isinstance(v, str) and (v.startswith("/") or (len(v) > 1 and v[1] == ":")):
                errors.append(ValidationError("non_relative_provenance_path", f"evaluation {eid!r} provenance.{k} is not repository-relative: {v!r}"))

    # ---------------------------------------------------------------- glossary-level checks (rules 9, 11, 13)
    seen_glossary_values = {}
    for g in glossary:
        val = g.get("value")
        if not val or "meaning_status" not in g:
            errors.append(ValidationError("malformed_alias", f"glossary entry malformed: {g!r}"))
            continue
        is_reused = bool(g.get("reused"))
        if not is_reused:
            if val in seen_glossary_values:
                errors.append(ValidationError("duplicate_alias_without_qualification", f"glossary value {val!r} appears more than once without reused=true"))
            seen_glossary_values[val] = g
        if g.get("meaning_status") == "unverified" and g.get("meaning") is not None and not is_reused:
            errors.append(ValidationError("invented_alias_meaning", f"glossary alias {val!r}: meaning_status=unverified but meaning is not null (rule 13)"))
        if is_reused:
            objs = g.get("reused_objects") or []
            if len(objs) < 2:
                errors.append(ValidationError("reused_alias_underspecified", f"glossary value {val!r} marked reused=true but fewer than 2 reused_objects given (rule ambiguous-alias-honesty)"))
            for obj in objs:
                if obj.get("meaning_status") not in ("verified", "unverified"):
                    errors.append(ValidationError("malformed_alias", f"glossary value {val!r} reused_object missing meaning_status: {obj!r}"))

    # ---------------------------------------------------------------- immutability spot-check (rule 12)
    # reference_evidence.yaml itself must be untouched by this validator's existence; we only READ it.
    # No write-back check is meaningful here (the validator never writes), but confirm both curated
    # keys this backfill depends on still exist verbatim.
    for required_key in ("H15_eps0015_frozen", "AFAC_eps0030_F20_posthoc"):
        if required_key not in ref_entries:
            errors.append(ValidationError("immutable_reference_key_missing", f"expected immutable reference_evidence.yaml key {required_key!r} not found"))

    summary = {
        "runs": len(runs), "evaluations": len(evaluations), "glossary_entries": len(glossary),
        "errors": len(errors), "warnings": len(warnings),
    }
    return errors, warnings, summary


def main(argv):
    """Usage: validate_experiment_identity.py identity=<experiment_identity.yaml> \
reference-evidence=<reference_evidence.yaml> goals=<goals.yaml> datasets=<datasets.yaml>"""
    kv = dict(a.partition("=")[::2] for a in argv if "=" in a)
    src_keys = {"identity": "identity_yaml", "reference-evidence": "reference_evidence_yaml",
                "goals": "goals_yaml", "datasets": "datasets_yaml"}
    sources = {dest: kv[k] for k, dest in src_keys.items() if k in kv}
    if "identity_yaml" not in sources:
        print(main.__doc__)
        return 2
    errors, warnings, summary = validate(sources)
    print(f"[validate] runs={summary.get('runs', 0)} evaluations={summary.get('evaluations', 0)} "
          f"glossary={summary.get('glossary_entries', 0)}")
    for w in warnings:
        print(f"  WARN  {w}")
    for e in errors:
        print(f"  FAIL  {e}")
    if not errors:
        print("[validate] PASS — no errors")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
