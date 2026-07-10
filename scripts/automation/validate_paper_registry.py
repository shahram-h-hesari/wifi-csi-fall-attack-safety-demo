#!/usr/bin/env python
"""Read-only validator for the academic paper registry (D4a-1).

Registry: automation/literature/paper_registry.yaml. Policy: automation/literature/README.md.
Acceptance: automation/acceptance/paper-registry.yaml.

Usage:
    python scripts/automation/validate_paper_registry.py \
        [registry=automation/literature/paper_registry.yaml] \
        [goals=automation/registry/goals.yaml]

Pure read-only stdlib+yaml: never writes, never opens a network connection, never requires a PDF
or checkpoint to exist, never runs a subprocess. Exit 0 = PASS, 1 = FAIL. Output is deterministic
for identical inputs (errors are reported in a stable order).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML required: pip install pyyaml")

REPO = Path(__file__).resolve().parents[2]

SUPPORTED_SCHEMA = {1}

METADATA_STATUSES = {"complete_local", "partial_local", "conflicting_local"}
VERIFICATION_STATUSES = {"local_bib_only", "externally_verified"}
PAPER_TYPES = {"method", "theory_or_analysis", "survey_or_review", "dataset_or_benchmark",
               "evaluation_or_metrics", "clinical_or_epidemiology", "data_platform"}
INTERPRETATION_STATUSES = {"local_interpretation", "none"}
FULL_TEXT_STATUSES = {"not_stored_locally", "cited_only"}
SOURCE_TYPES = {"bibliography", "literature_framing", "chapter_citation", "decision_memo",
                "result_summary"}
RELATIONSHIPS = {"direct", "indirect", "background", "not_established"}
DEFENSE_LINES = {f"D{i}" for i in range(1, 15)}   # D1..D14 (D13/D14 are documented ledger lines)
EXTRA_TASK_TAGS = {"activity_recognition", "adversarial_robustness"}
METHOD_TAGS = {
    "fgsm", "pgd", "adversarial_training", "trades", "gairat", "sat", "basat", "calibration",
    "threshold_selection", "neyman_pearson", "partial_auc", "temporal_filtering",
    "event_level_detection", "ensemble", "gating", "wifi_csi",
    # extensions used by the local seed set (documented in the acceptance spec):
    "cost_sensitive_learning", "class_balancing", "margin_objectives", "hard_example_mining",
    "knowledge_distillation", "recurrent_representation", "curriculum_or_multi_budget",
    "instance_reweighting", "robustness_evaluation", "gait_analysis", "fall_risk_epidemiology",
    "in_home_sensing", "consistency_regularization", "constrained_optimization", "data_selection",
}
CANDIDATE_DIRECTIONS = {
    "low_far_afac_calibration", "neyman_pearson_far_control", "low_far_partial_auc_objective",
    "temporal_false_alarm_reduction", "ensemble_or_gating", "walking_detection_baseline",
    "gait_or_fall_risk_data_acquisition",
    # gap-only directions (used by literature_gaps records):
    "dataset_provenance", "walking_pattern_recognition",
}
GAP_STATUSES = {"not_locally_cited", "partially_supported_locally", "wrong_modality_anchors_only"}
DATASET_TAGS = {"sensefi_ut_har"}
# task tags a dataset-tagged (UT-HAR) paper may NOT imply support for (mirrors
# automation/registry/datasets.yaml unsupported_goals):
UT_HAR_UNSUPPORTED_TASKS = {"walking_pattern_recognition", "gait_or_mobility_change_detection",
                            "future_fall_risk_prediction"}

# internal experiment/ledger labels that are never papers (rule 16)
INTERNAL_LABEL_RE = re.compile(
    r"^(afac|basat|dsge|h\d{1,2}|d\d{1,2}[ab]?|g[0-9]|a[0-9])$", re.I)

# assertive clinical/deployment overclaims (rule 22); negated forms ("not clinically proven",
# "does not establish clinical...") are allowed and are exactly what claim_boundaries contain.
CLINICAL_OVERCLAIM_RE = re.compile(
    r"(?<!not )(?<!never )(?<!no )(clinically (proven|validated|certified)"
    r"|proves? clinical|establishes clinical (efficacy|validity)"
    r"|deployment[- ]ready|ready for (clinical )?deployment|certified for clinical)", re.I)

MAX_TEXT_FIELD_CHARS = 900   # rule 21: long verbatim extracts are never stored

ABS_PATH_RE = re.compile(r"^[A-Za-z]:[\\/]|^\\\\|^/(Users|home|mnt|var|etc)\b")
YEAR_MIN, YEAR_MAX = 1900, 2100


def _norm_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()


def _walk_strings(node, path=""):
    if isinstance(node, dict):
        for k, v in sorted(node.items(), key=lambda kv: str(kv[0])):
            yield from _walk_strings(v, f"{path}.{k}" if path else str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk_strings(v, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


def validate(doc, goals_doc) -> list[str]:
    """Return a deterministic (stable-order) list of error strings; empty == PASS."""
    errors: list[str] = []
    err = errors.append

    if not isinstance(doc, dict):
        return ["registry root is not a mapping"]

    # 2. schema version
    if doc.get("schema_version") not in SUPPORTED_SCHEMA:
        err(f"unsupported schema_version {doc.get('schema_version')!r} (supported: {sorted(SUPPORTED_SCHEMA)})")

    scope = doc.get("registry_scope") or {}
    if scope.get("source_policy") != "local_cited_sources_only":
        err("registry_scope.source_policy must be local_cited_sources_only in D4a-1")
    if scope.get("clinical_claims_allowed") is not False:
        err("registry_scope.clinical_claims_allowed must be false")
    verification_pending = scope.get("external_metadata_verification") == "pending"
    allowed_repos = set(scope.get("allowed_repositories") or [])
    if not allowed_repos:
        err("registry_scope.allowed_repositories must list the permitted repository aliases")

    goal_ids = {g.get("id") for g in (goals_doc.get("goals") or [])} if goals_doc else set()
    allowed_task_tags = goal_ids | EXTRA_TASK_TAGS

    papers = doc.get("papers")
    if not isinstance(papers, list) or not papers:
        err("papers must be a non-empty list")
        papers = []

    seen_ids: dict[str, int] = {}
    key_owner: dict[str, str] = {}
    doi_owner: dict[str, str] = {}
    title_owner: dict[str, str] = {}

    for idx, p in enumerate(papers):
        pid = p.get("paper_id") or f"<papers[{idx}]>"
        where = f"paper {pid}"

        # 3. unique paper_id
        if pid in seen_ids:
            err(f"{where}: duplicate paper_id (also papers[{seen_ids[pid]}])")
        seen_ids.setdefault(pid, idx)

        # 16. internal labels are never papers
        title = p.get("title") or ""
        if INTERNAL_LABEL_RE.match(title.strip()):
            err(f"{where}: title {title!r} is an internal experiment label, not a publication")
        author_token = pid.removeprefix("paper_").split("_")[0] if pid.startswith("paper_") else ""
        if INTERNAL_LABEL_RE.match(author_token or ""):
            err(f"{where}: paper_id author token {author_token!r} is an internal experiment label")

        # 7./9. metadata + verification statuses and required fields
        ms = p.get("metadata_status")
        if ms not in METADATA_STATUSES:
            err(f"{where}: invalid metadata_status {ms!r}")
        vs = p.get("verification_status")
        if vs not in VERIFICATION_STATUSES:
            err(f"{where}: invalid verification_status {vs!r}")
        # 14./15. nothing may claim external verification while scope says pending
        if verification_pending and vs == "externally_verified":
            err(f"{where}: verification_status externally_verified while "
                "registry_scope.external_metadata_verification is pending")
        if p.get("doi_verified") or (p.get("identifiers") or {}).get("doi_verified"):
            err(f"{where}: doi_verified flag is not allowed in D4a-1 (no external verification)")
        if not title:
            err(f"{where}: title is required")
        if not p.get("citation_keys"):
            err(f"{where}: citation_keys must be non-empty")
        if ms == "complete_local":
            for field in ("authors", "year", "venue"):
                if not p.get(field):
                    err(f"{where}: metadata_status complete_local requires {field}")
        if ms == "partial_local" and not p.get("notes"):
            err(f"{where}: metadata_status partial_local requires a notes entry naming what is missing")
        if ms == "conflicting_local" and not p.get("metadata_conflicts"):
            err(f"{where}: metadata_status conflicting_local requires metadata_conflicts describing the conflict")

        # 8. year
        year = p.get("year")
        if year is not None and (not isinstance(year, int) or not (YEAR_MIN <= year <= YEAR_MAX)):
            err(f"{where}: invalid year {year!r}")

        # 4./24. citation-key ownership
        for key in p.get("citation_keys") or []:
            if key in key_owner and key_owner[key] != pid:
                err(f"citation key {key!r} owned by both {key_owner[key]} and {pid}")
            key_owner.setdefault(key, pid)

        # 5. duplicate DOI
        doi = (p.get("identifiers") or {}).get("doi")
        if doi:
            d = str(doi).strip().lower()
            if d in doi_owner and doi_owner[d] != pid:
                err(f"duplicate DOI {doi!r} on {doi_owner[d]} and {pid} -- one paper must own it")
            doi_owner.setdefault(d, pid)

        # 6. normalized duplicate titles
        nt = _norm_title(title)
        if nt:
            if nt in title_owner and title_owner[nt] != pid:
                err(f"normalized duplicate title on {title_owner[nt]} and {pid}: {title!r}")
            title_owner.setdefault(nt, pid)

        # 10./11./13./25. source records
        recs = p.get("source_records") or []
        if not recs:
            err(f"{where}: at least one source_records entry is required")
        for r in recs:
            repo = r.get("repository")
            if repo not in allowed_repos:
                err(f"{where}: source repository {repo!r} not in allowed_repositories")
            path = str(r.get("path") or "")
            if not path:
                err(f"{where}: source record missing path")
            elif ABS_PATH_RE.search(path):
                err(f"{where}: source path {path!r} is absolute -- must be repository-relative")
            if r.get("source_type") not in SOURCE_TYPES:
                err(f"{where}: invalid source_type {r.get('source_type')!r}")

        # 12./18-separation. interpretation vs paper claim
        contrib = p.get("paper_contribution_summary") or ""
        rel = p.get("relevance_to_current_results")
        if "paper_contribution_summary" not in p:
            err(f"{where}: paper_contribution_summary field is required")
        if "relevance_to_current_results" not in p:
            err(f"{where}: relevance_to_current_results field is required (may be null)")
        if rel:
            if p.get("interpretation_status") not in INTERPRETATION_STATUSES or \
                    p.get("interpretation_status") == "none":
                err(f"{where}: non-null relevance_to_current_results requires "
                    "interpretation_status local_interpretation")
            if contrib.strip() and contrib.strip() == str(rel).strip():
                err(f"{where}: relevance_to_current_results duplicates paper_contribution_summary "
                    "-- interpretation must stay separate from the paper's claim")
        if "our interpretation" in contrib.lower():
            err(f"{where}: paper_contribution_summary contains interpretation text -- keep it to what the paper reports")

        if p.get("paper_type") not in PAPER_TYPES:
            err(f"{where}: invalid paper_type {p.get('paper_type')!r}")
        if p.get("full_text_status") not in FULL_TEXT_STATUSES:
            err(f"{where}: invalid full_text_status {p.get('full_text_status')!r}")

        # 19. task tags come from the goal registry (plus documented extras)
        for t in p.get("task_tags") or []:
            if allowed_task_tags and t not in allowed_task_tags:
                err(f"{where}: task tag {t!r} is not an approved goal ID or documented extra")
        for t in p.get("method_tags") or []:
            if t not in METHOD_TAGS:
                err(f"{where}: method tag {t!r} not in the documented method-tag vocabulary")

        # 20. dataset tags must not imply unsupported capability
        ds_tags = set(p.get("dataset_tags") or [])
        for t in ds_tags:
            if t not in DATASET_TAGS:
                err(f"{where}: dataset tag {t!r} not in the documented dataset-tag vocabulary")
        if "sensefi_ut_har" in ds_tags:
            bad = ds_tags and (set(p.get("task_tags") or []) & UT_HAR_UNSUPPORTED_TASKS)
            if bad:
                err(f"{where}: dataset tag sensefi_ut_har must not co-occur with unsupported task "
                    f"tags {sorted(bad)} (the dataset registry marks those goals unsupported)")

        # 23. defense-line labels
        for d in p.get("defense_line_tags") or []:
            if d not in DEFENSE_LINES:
                err(f"{where}: invalid defense-line label {d!r}")

        # 17. candidate-direction mappings carry relationship strength
        for c in p.get("candidate_direction_tags") or []:
            if not isinstance(c, dict) or "direction" not in c or "relationship" not in c:
                err(f"{where}: candidate_direction_tags entries must be "
                    "{{direction, relationship}} mappings")
                continue
            if c["direction"] not in CANDIDATE_DIRECTIONS:
                err(f"{where}: unknown candidate direction {c['direction']!r}")
            if c["relationship"] not in RELATIONSHIPS:
                err(f"{where}: invalid relationship strength {c['relationship']!r}")

    # 18. literature gaps
    gaps = doc.get("literature_gaps") or []
    seen_gaps = set()
    for g in gaps:
        gid = g.get("gap_id")
        if not gid:
            err("literature gap missing gap_id")
            continue
        if gid in seen_gaps:
            err(f"duplicate literature gap_id {gid!r}")
        seen_gaps.add(gid)
        for field in ("direction", "current_status", "reason", "required_future_action"):
            if not g.get(field):
                err(f"gap {gid}: missing {field}")
        if g.get("current_status") and g["current_status"] not in GAP_STATUSES:
            err(f"gap {gid}: invalid current_status {g['current_status']!r}")
        if g.get("direction") and g["direction"] not in CANDIDATE_DIRECTIONS:
            err(f"gap {gid}: unknown direction {g['direction']!r}")

    # 21./22./25. whole-document string scans (deterministic order via _walk_strings)
    for path, s in _walk_strings(doc):
        if len(s) > MAX_TEXT_FIELD_CHARS:
            err(f"{path}: text field is {len(s)} chars (> {MAX_TEXT_FIELD_CHARS}) -- "
                "long verbatim extracts must not be stored")
        m = CLINICAL_OVERCLAIM_RE.search(s)
        if m:
            err(f"{path}: assertive clinical/deployment claim {m.group(0)!r} is forbidden")
        if path.endswith(".path") or path.endswith("]"):
            continue  # source paths already checked; skip list-item false positives for abs scan
        if ABS_PATH_RE.search(s) and ("\\" in s or s[:1] == "/"):
            err(f"{path}: absolute local filesystem path is not allowed in the registry")

    return errors


def main(argv):
    kv = dict(a.partition("=")[::2] for a in argv if "=" in a)
    registry_path = Path(kv.get("registry", REPO / "automation" / "literature" / "paper_registry.yaml"))
    goals_path = Path(kv.get("goals", REPO / "automation" / "registry" / "goals.yaml"))

    if not registry_path.exists():
        print(f"[validate] FAIL — registry file not found: {registry_path}")
        return 1
    try:
        doc = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:   # 1. YAML must parse
        print(f"[validate] FAIL — registry YAML is malformed: {e}")
        return 1
    goals_doc = {}
    if goals_path.exists():
        try:
            goals_doc = yaml.safe_load(goals_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            print(f"[validate] FAIL — goals registry YAML is malformed: {goals_path}")
            return 1

    errors = validate(doc, goals_doc)

    papers = doc.get("papers") or [] if isinstance(doc, dict) else []
    n_keys = sum(len(p.get("citation_keys") or []) for p in papers)
    n_conf = sum(1 for p in papers if p.get("metadata_status") in ("conflicting_local", "partial_local"))
    n_gaps = len((doc.get("literature_gaps") or []) if isinstance(doc, dict) else [])
    print(f"[validate] papers={len(papers)} citation_keys={n_keys} "
          f"unresolved_or_conflicting={n_conf} gaps={n_gaps}")
    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
        print(f"[validate] FAIL — {len(errors)} error(s)")
        return 1
    print("[validate] PASS — no errors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
