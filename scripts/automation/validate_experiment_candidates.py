#!/usr/bin/env python
"""Read-only validator for the experiment-candidate registry (REG-CANDIDATES).

Registry: automation/registry/experiment_candidates.yaml. Implementation contract:
automation/acceptance/experiment-candidates.yaml (hash-bound, never edited by this script).

Usage:
    python scripts/automation/validate_experiment_candidates.py \
        [candidates=automation/registry/experiment_candidates.yaml] \
        [papers=automation/literature/paper_registry.yaml] \
        [goals=automation/registry/goals.yaml] \
        [datasets=automation/registry/datasets.yaml] \
        [frontier=automation/frontier.yaml] \
        [reference-evidence=automation/registry/reference_evidence.yaml] \
        [experiment-identity=automation/registry/experiment_identity.yaml]

Pure read-only stdlib+yaml: never writes, never opens a network connection, never requires a PDF
or checkpoint to exist, never runs a subprocess, never requires the thesis/experiment repositories
to be present. Exit 0 = PASS, 1 = FAIL. Output is deterministic for identical inputs.
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

# Goal registry `status` -> the ONLY dataset_readiness value a candidate targeting that goal may
# declare. Mirrors scripts/automation/dashboard_research_summary.py's STATUS_LABELS mapping (same
# four-value goal-status enum), applied here as a readiness-agreement gate instead of prose.
GOAL_STATUS_TO_READINESS = {
    "ACTIVE_THESIS_PRIMARY": "available",
    "DATA_AVAILABLE_NOT_EVALUATED": "available_not_evaluated",
    "NO_DATA": "unavailable",
    "NO_DATA_ASPIRATIONAL": "aspirational_only",
}

REQUIRED_CANDIDATE_FIELDS = {
    "candidate_id", "title", "hypothesis", "target_gap", "direction_tags", "literature_support",
    "literature_gap_ids", "current_evidence_refs", "current_evidence_summary",
    "prior_negative_evidence_refs", "our_rationale", "required_dataset_ids", "target_goal_ids",
    "dataset_readiness", "allowed_split", "frozen_protocol_requirement", "test_read_risk",
    "other_risks", "evidence_strength", "status", "claim_boundaries", "supersedes",
    "superseded_by", "notes",
}
# no unexpected extra field (e.g. a queue_entry_id or a manual verdict field) may be present
ALLOWED_CANDIDATE_FIELDS = REQUIRED_CANDIDATE_FIELDS

RELATIONSHIP_STRENGTH = {"not_established": 0, "background": 1, "indirect": 2, "direct": 3}

# direction -> substring(s) that MUST appear (case-insensitive) in at least one
# prior_negative_evidence_refs[].identity for a candidate tagging that direction (rule 23).
DIRECTION_REQUIRES_NEGATIVE_EVIDENCE = {
    "ensemble_or_gating": ("d13",),
    "low_far_partial_auc_objective": ("d14",),
}

CLINICAL_OVERCLAIM_RE = re.compile(
    r"(?<!not )(?<!never )(?<!no )(clinically (proven|validated|certified)"
    r"|proves? clinical|establishes clinical (efficacy|validity)"
    r"|deployment[- ]ready|ready for (clinical )?deployment|certified for clinical)", re.I)
ABS_PATH_RE = re.compile(r"^[A-Za-z]:[\\/]|^\\\\|^/(Users|home|mnt|var|etc)\b")
COMMAND_LIKE_RE = re.compile(
    r"--split\b|\.venv[\\/ ]?Scripts[\\/]?python|^\s*python\s|train_\w+\.py|scripts/train_", re.I)
MARKDOWN_TABLE_ROW_RE = re.compile(r"(\|.*){5,}")  # >=5 pipes on one line looks like a copied table row
MAX_TEXT_FIELD_CHARS = 900


def _walk_strings(node, path=""):
    if isinstance(node, dict):
        for k, v in sorted(node.items(), key=lambda kv: str(kv[0])):
            yield from _walk_strings(v, f"{path}.{k}" if path else str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk_strings(v, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


def _load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def validate(candidates_doc, papers_doc, goals_doc, datasets_doc, frontier_doc,
             ref_evidence_doc, identity_doc, sources=None) -> list[str]:
    """Return a deterministic (stable-order) list of error strings; empty == PASS. `sources` is
    an optional dict of {name: path} used only for repository-relative file-existence checks on
    research_os current_evidence_refs / prior_negative_evidence_refs entries."""
    errors: list[str] = []
    err = errors.append
    sources = sources or {}

    if not isinstance(candidates_doc, dict):
        return ["registry root is not a mapping"]

    if candidates_doc.get("schema_version") not in SUPPORTED_SCHEMA:
        err(f"unsupported schema_version {candidates_doc.get('schema_version')!r}")

    scope = candidates_doc.get("registry_scope") or {}
    if scope.get("clinical_claims_allowed") is not False:
        err("registry_scope.clinical_claims_allowed must be false")
    if scope.get("source_policy") != "local_cited_sources_only":
        err("registry_scope.source_policy must be local_cited_sources_only")

    vocab = candidates_doc.get("controlled_vocabularies") or {}
    v_direction = set(vocab.get("direction_tags") or [])
    v_lit_rel = set(vocab.get("literature_relationship") or [])
    v_readiness = set(vocab.get("dataset_readiness") or [])
    v_split = set(vocab.get("allowed_split") or [])
    v_test_risk = set(vocab.get("test_read_risk") or [])
    v_strength = set(vocab.get("evidence_strength") or [])
    v_status = set(vocab.get("candidate_status") or [])

    papers_by_id = {p.get("paper_id"): p for p in (papers_doc.get("papers") or [])}
    gap_ids = {g.get("gap_id") for g in (papers_doc.get("literature_gaps") or [])}
    goals_by_id = {g.get("id"): g for g in (goals_doc.get("goals") or [])}
    dataset_ids = {d.get("id") for d in (datasets_doc.get("datasets") or [])}
    frozen_protocol_ids = {fp.get("protocol_id") for fp in (frontier_doc.get("frozen_protocol_registry") or [])}
    ref_evidence_keys = {e.get("key") for e in (ref_evidence_doc.get("reference_results") or [])}
    ref_evidence_by_key = {e.get("key"): e for e in (ref_evidence_doc.get("reference_results") or [])}
    evaluation_ids = {e.get("evaluation_id") for e in (identity_doc.get("evaluations") or [])}

    candidates = candidates_doc.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return ["candidates must be a non-empty list"]

    seen_ids: dict[str, int] = {}

    for idx, c in enumerate(candidates):
        cid = c.get("candidate_id") or f"<candidates[{idx}]>"
        where = f"candidate {cid}"

        # 4. required fields present
        missing = REQUIRED_CANDIDATE_FIELDS - set(c.keys())
        if missing:
            err(f"{where}: missing required field(s) {sorted(missing)}")
        # no unexpected field (blocks a smuggled-in verdict/queue-link field) -- rules 17/18
        extra = set(c.keys()) - ALLOWED_CANDIDATE_FIELDS
        if extra:
            err(f"{where}: unexpected field(s) {sorted(extra)} -- not part of the approved schema (this is how a manual verdict or queue-link field is blocked)")
        # 17. explicit belt-and-braces: no key literally named/containing 'verdict'
        if any("verdict" in str(k).lower() for k in c.keys()):
            err(f"{where}: contains a verdict-named field -- verdicts are never manually stored")

        # 3. unique candidate_id
        if cid in seen_ids:
            err(f"{where}: duplicate candidate_id (also candidates[{seen_ids[cid]}])")
        seen_ids.setdefault(cid, idx)

        # 5./6. controlled vocabulary + reference checks
        for d in c.get("direction_tags") or []:
            if d not in v_direction:
                err(f"{where}: unknown direction_tag {d!r}")
        for gid in c.get("literature_gap_ids") or []:
            if gid not in gap_ids:  # 9. every literature_gap_id exists
                err(f"{where}: literature_gap_id {gid!r} not found in paper_registry.yaml literature_gaps")
            if gid not in v_status:  # placeholder no-op to keep linters quiet; real gap check above
                pass
        for did in c.get("required_dataset_ids") or []:
            if did not in dataset_ids:  # 10. every dataset ID exists
                err(f"{where}: required_dataset_ids entry {did!r} not found in datasets.yaml")
        for gid in c.get("target_goal_ids") or []:
            if gid not in goals_by_id:  # 11. every goal ID exists
                err(f"{where}: target_goal_ids entry {gid!r} not found in goals.yaml")

        readiness = c.get("dataset_readiness")
        if readiness not in v_readiness:
            err(f"{where}: invalid dataset_readiness {readiness!r}")
        else:
            # 12./13. dataset readiness must agree with the goal registry's own status
            for gid in c.get("target_goal_ids") or []:
                goal = goals_by_id.get(gid)
                if not goal:
                    continue
                expected = GOAL_STATUS_TO_READINESS.get(goal.get("status"))
                if expected and readiness != expected:
                    err(f"{where}: dataset_readiness {readiness!r} disagrees with goal {gid!r}'s "
                        f"registry status {goal.get('status')!r} (expected {expected!r})")
                # 13. unsupported future-fall-risk data cannot be marked available
                if gid == "future_fall_risk_prediction" and readiness in ("available", "available_not_evaluated"):
                    err(f"{where}: future_fall_risk_prediction cannot be marked {readiness!r} -- goals.yaml marks it NO_DATA_ASPIRATIONAL")

        split = c.get("allowed_split")
        if split not in v_split:
            err(f"{where}: invalid allowed_split {split!r}")
        risk = c.get("test_read_risk")
        if risk not in v_test_risk:
            err(f"{where}: invalid test_read_risk {risk!r}")
        strength = c.get("evidence_strength")
        if strength not in v_strength:
            err(f"{where}: invalid evidence_strength {strength!r}")
        status = c.get("status")
        if status not in v_status:
            err(f"{where}: invalid status {status!r}")

        # 19./20./21. split/test-read-risk/frozen-protocol coherence -- structurally prevents any
        # candidate from authorizing or quietly implying a test read.
        fpr = c.get("frozen_protocol_requirement")
        if split in ("validation_only", "training_and_validation", "no_experiment_allowed"):
            if fpr is not None:
                err(f"{where}: allowed_split {split!r} must have frozen_protocol_requirement null")
            if risk != "none":
                err(f"{where}: allowed_split {split!r} must have test_read_risk 'none' (no test involvement)")
        elif split == "requires_new_frozen_protocol":
            if fpr != "new_protocol_required":
                err(f"{where}: allowed_split requires_new_frozen_protocol must set "
                    "frozen_protocol_requirement to the literal 'new_protocol_required'")
            if risk not in ("requires_review", "blocked_without_protocol"):
                err(f"{where}: a new-frozen-protocol requirement can never be low-risk or "
                    f"auto-approved -- test_read_risk was {risk!r}")  # rule 20
        elif split == "existing_frozen_protocol_only":
            if fpr not in frozen_protocol_ids:
                err(f"{where}: existing_frozen_protocol_only must set frozen_protocol_requirement "
                    f"to a real protocol_id from automation/frontier.yaml (got {fpr!r})")  # rule 25
            if risk not in ("low", "requires_review"):
                err(f"{where}: existing_frozen_protocol_only should not claim test_read_risk 'none' "
                    f"(got {risk!r})")

        # 22. dataset-blocked candidates use no_experiment_allowed
        if strength == "dataset_blocked" and split != "no_experiment_allowed":
            err(f"{where}: evidence_strength dataset_blocked must use allowed_split no_experiment_allowed")

        # 23. D13/D14 negative evidence not omitted from directly related candidates
        neg_identities = " ".join(
            str((n or {}).get("identity", "")).lower()
            for n in (c.get("prior_negative_evidence_refs") or []))
        for d in c.get("direction_tags") or []:
            required_substrings = DIRECTION_REQUIRES_NEGATIVE_EVIDENCE.get(d)
            if required_substrings and not any(s in neg_identities for s in required_substrings):
                err(f"{where}: direction {d!r} requires prior_negative_evidence_refs mentioning "
                    f"{required_substrings} (D13/D14 must not be omitted from directly related candidates)")

        # 7./8. literature_support: paper exists, relationship does not exceed the accepted one
        for ls in c.get("literature_support") or []:
            pid = ls.get("paper_id")
            rel = ls.get("relationship")
            if rel not in v_lit_rel:
                err(f"{where}: invalid literature relationship {rel!r} for paper {pid!r}")
            paper = papers_by_id.get(pid)
            if paper is None:
                err(f"{where}: paper_id {pid!r} not found in paper_registry.yaml")
                continue
            tags = paper.get("candidate_direction_tags") or []
            matching = [t for t in tags if t.get("direction") in (c.get("direction_tags") or [])]
            if not matching:
                err(f"{where}: paper {pid!r} has no candidate_direction_tags entry for any of this "
                    f"candidate's direction_tags in paper_registry.yaml -- cannot cite it as support here")
                continue
            max_accepted = max((RELATIONSHIP_STRENGTH.get(t.get("relationship"), -1) for t in matching), default=-1)
            if RELATIONSHIP_STRENGTH.get(rel, 99) > max_accepted:
                err(f"{where}: relationship {rel!r} for paper {pid!r} exceeds the accepted "
                    f"relationship recorded in paper_registry.yaml for this direction")

        # 14./24./25. current-evidence + prior-negative references resolve to a real identity
        all_refs = list(c.get("current_evidence_refs") or []) + list(c.get("prior_negative_evidence_refs") or [])
        for ref in all_refs:
            src = ref.get("source")
            ident = ref.get("identity")
            rel = ref.get("relationship")
            if rel is not None and rel not in v_lit_rel:
                err(f"{where}: evidence ref {ident!r} has invalid relationship {rel!r}")
            if src not in ("research_os", "thesis_overleaf"):
                err(f"{where}: evidence ref {ident!r} has unknown source {src!r}")
                continue
            resolved = (ident in ref_evidence_keys or ident in evaluation_ids
                        or ident in frozen_protocol_ids or ident in dataset_ids)
            if not resolved and src == "research_os":
                # treat as a repository-relative path reference; must exist (never required for
                # thesis_overleaf, which this validator does not assume is checked out)
                p = REPO / str(ident)
                if ABS_PATH_RE.search(str(ident)):
                    err(f"{where}: evidence ref path {ident!r} is absolute -- must be repository-relative")
                elif not p.exists():
                    err(f"{where}: evidence ref {ident!r} does not resolve to a known identity "
                        "(reference_evidence_key/evaluation_id/protocol_id/dataset id) or an "
                        "existing repository-relative path")
            # 24. AFAC post-hoc evidence never presented as frozen
            if ident == "AFAC_eps0030_F20_posthoc":
                entry = ref_evidence_by_key.get(ident) or {}
                if entry.get("evidence_level") == "frozen-test":
                    err(f"{where}: AFAC_eps0030_F20_posthoc is test-post-hoc in reference_evidence.yaml "
                        "but would be presented as frozen -- registry data disagreement")
                note = str(ref.get("note") or "")
                for m in re.finditer(r"frozen", note, re.I):
                    preceding = note[max(0, m.start() - 20):m.start()].lower()
                    if "not" not in preceding and "never" not in preceding:
                        err(f"{where}: note for AFAC_eps0030_F20_posthoc must not describe it as frozen evidence")
                        break

        # 15./16. structural separation: no ref identity duplicated across support vs negative,
        # and our_rationale must not be byte-identical to current_evidence_summary
        cur_idents = {(r.get("source"), r.get("identity")) for r in (c.get("current_evidence_refs") or [])}
        neg_idents = {(r.get("source"), r.get("identity")) for r in (c.get("prior_negative_evidence_refs") or [])}
        overlap = cur_idents & neg_idents
        if overlap:
            err(f"{where}: the same evidence identity appears in both current_evidence_refs and "
                f"prior_negative_evidence_refs: {sorted(overlap)}")
        summary = (c.get("current_evidence_summary") or "").strip()
        rationale = (c.get("our_rationale") or "").strip()
        if summary and rationale and summary == rationale:
            err(f"{where}: our_rationale must stay separate from current_evidence_summary (identical text found)")
        if rationale and "OUR INTERPRETATION" not in rationale.upper():
            err(f"{where}: our_rationale should be explicitly prefixed as interpretation (missing 'OUR INTERPRETATION')")

        # 26./27./29./30. whole-record string scans
        for path, s in _walk_strings(c):
            if len(s) > MAX_TEXT_FIELD_CHARS:
                err(f"{where}.{path}: text field is {len(s)} chars (> {MAX_TEXT_FIELD_CHARS}) -- "
                    "must not duplicate a full paper summary or metric table")
            if MARKDOWN_TABLE_ROW_RE.search(s):
                err(f"{where}.{path}: looks like an embedded markdown table row -- do not copy full metric tables here")
            m = CLINICAL_OVERCLAIM_RE.search(s)
            if m:
                err(f"{where}.{path}: assertive clinical/deployment claim {m.group(0)!r} is forbidden")
            if COMMAND_LIKE_RE.search(s):
                err(f"{where}.{path}: contains an embedded experiment command or configuration -- forbidden")
            if path.endswith(".identity") or path.endswith(".source"):
                continue
            if ABS_PATH_RE.search(s):
                err(f"{where}.{path}: absolute local filesystem path is not allowed")

    return errors


def main(argv):
    kv = dict(a.partition("=")[::2] for a in argv if "=" in a)
    paths = {
        "candidates": Path(kv.get("candidates", REPO / "automation" / "registry" / "experiment_candidates.yaml")),
        "papers": Path(kv.get("papers", REPO / "automation" / "literature" / "paper_registry.yaml")),
        "goals": Path(kv.get("goals", REPO / "automation" / "registry" / "goals.yaml")),
        "datasets": Path(kv.get("datasets", REPO / "automation" / "registry" / "datasets.yaml")),
        "frontier": Path(kv.get("frontier", REPO / "automation" / "frontier.yaml")),
        "reference-evidence": Path(kv.get("reference-evidence", REPO / "automation" / "registry" / "reference_evidence.yaml")),
        "experiment-identity": Path(kv.get("experiment-identity", REPO / "automation" / "registry" / "experiment_identity.yaml")),
    }
    if not paths["candidates"].exists():
        print(f"[validate] FAIL — registry file not found: {paths['candidates']}")
        return 1
    try:
        candidates_doc = yaml.safe_load(paths["candidates"].read_text(encoding="utf-8"))
    except yaml.YAMLError as e:  # 1. YAML must parse
        print(f"[validate] FAIL — registry YAML is malformed: {e}")
        return 1

    docs = {}
    for name in ("papers", "goals", "datasets", "frontier", "reference-evidence", "experiment-identity"):
        p = paths[name]
        docs[name] = (yaml.safe_load(p.read_text(encoding="utf-8")) or {}) if p.exists() else {}

    errors = validate(candidates_doc, docs["papers"], docs["goals"], docs["datasets"],
                       docs["frontier"], docs["reference-evidence"], docs["experiment-identity"])

    cands = candidates_doc.get("candidates") or [] if isinstance(candidates_doc, dict) else []
    n_lit = sum(len(c.get("literature_support") or []) for c in cands)
    n_gaps_cited = sum(len(c.get("literature_gap_ids") or []) for c in cands)
    n_neg = sum(1 for c in cands if c.get("prior_negative_evidence_refs"))
    n_blocked = sum(1 for c in cands if c.get("evidence_strength") == "dataset_blocked")
    print(f"[validate] candidates={len(cands)} literature_support_entries={n_lit} "
          f"literature_gap_refs={n_gaps_cited} prior_negative_evidence_candidates={n_neg} "
          f"dataset_blocked={n_blocked}")
    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
        print(f"[validate] FAIL — {len(errors)} error(s)")
        return 1
    print("[validate] PASS — no errors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
