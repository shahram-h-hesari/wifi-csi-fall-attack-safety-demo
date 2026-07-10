#!/usr/bin/env python
"""Result Explorer v1 — read-only lookup over EXISTING committed results (D2c + D2d-2 + D2e-2).

Spec: automation/acceptance/result-explorer.yaml. Contract: run_query(query, sources) -> dict.

Reads ONLY the paths given in `sources` (goals/datasets registries, ledger CSV, manifest CSV,
receipts dir, and — D2d-2 — an optional curated reference-evidence YAML). The manifest is the
evidence-level authority: ledger.source_file joins to manifest.path; evidence levels pass through
verbatim — never derived from filenames, never upgraded. Metrics are copied from source rows only
— never fabricated; a goal metric with no populated column reports as defined-but-not-evaluated via
honest empty states.

D2d-2 curated-first resolution: a named reference_evidence_query is resolved FIRST against
sources['reference_evidence_yaml'] (automation/registry/reference_evidence.yaml in production) —
a hand-curated, user-approved registry of pointers to already-committed evidence. A curated hit
returns EXACTLY ONE row after its provenance paths are cross-checked against the manifest (paths
must exist there and the manifest evidence_level must agree with the curated entry's declared
level); any disagreement, missing path, or ambiguity REFUSES with provenance_mismatch and returns
no metrics — the curated file may point at evidence, it may never overrule what the manifest says
that evidence is. If sources has no curated source configured, or the named key isn't in it, this
falls through unchanged to the pre-existing goals.yaml-driven reference_evidence_queries + ledger-
filter path (D2c), so ordinary and legacy-reference queries are completely unaffected.

D2e-2 identity enrichment: a CURATED reference-evidence row (the two named keys above) may gain a
supplemental `experiment_identity` block from the optional sources['identity_yaml'] registry
(automation/registry/experiment_identity.yaml in production). This runs strictly AFTER the
scientific result has been resolved and provenance-checked -- it only ever ADDS the new
`experiment_identity` key; it never alters any existing scientific field (metrics, evidence_level,
attack, epsilon, split, threshold, provenance). Matching is exact-key only via
`reference_evidence_key`, never fuzzy/alias-based. Three states: `matched` (identity attached),
`unavailable` (no identity source configured, file missing, malformed YAML, or no mapping exists —
scientific result unaffected), `mismatch` (a mapping exists but disagrees with the scientific
result, or is ambiguous — scientific result unaffected, but no canonical identity is attached).
Ordinary (non-reference) ledger rows never receive an experiment_identity block at all.

Safety: pure read-only stdlib+yaml. Never launches other processes, never builds commands with
split flags, never calls training/evaluation/export scripts, never opens a file for writing —
output goes to stdout only. Default exploration is validation-first: filterless queries fill from
the goal registry defaults; already-saved test/frozen summaries are reachable only through an
explicit filter or a named reference evidence query.
"""
import csv
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML required: pip install pyyaml")

DISPLAY_CAP = 25  # output_contract.default_display_cap

WARN_TEXT = {
    "validation-only": "validation-only — selection evidence, not a thesis result",
    "test-post-hoc": "test-post-hoc — descriptive only; not a frozen read",
    "diagnostic-internal": "diagnostic-internal — internal diagnostics; no claim",
    "not_r90f10": "not R90F10 — R90F10 target not met",
    "no_verified_result": "no verified result — row is not backed by verified manifest evidence",
}

NO_FILTER = (None, "", "any", "none")


# ---------------------------------------------------------------------------- loading (read-only)
def _load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------- resolution helpers
def _resolve_goal(goals, wanted):
    if not wanted:
        return None
    w = str(wanted).strip().lower()
    for g in goals:
        if g.get("id", "").lower() == w or w in [str(x).lower() for x in (g.get("aliases") or [])]:
            return g
    return None


def _resolve_dataset(datasets, wanted, family):
    hits = datasets
    if family not in NO_FILTER:
        hits = [d for d in hits if str(d.get("family", "")).lower() == str(family).lower()]
    if wanted not in NO_FILTER:
        w = str(wanted).strip().lower()
        hits = [d for d in hits
                if w in (str(d.get("id", "")).lower(), str(d.get("name", "")).lower(),
                         str(d.get("family", "")).lower())]
    return hits[0] if hits else None


def _result(status, state_id, message, rows):
    return {"status": status, "state_id": state_id, "message": message, "rows": rows}


# D2d-2: explicit, minimal allowlist of automation/registry/reference_evidence.yaml `provenance`
# sub-fields that name a real repo-relative artifact path to cross-check against the manifest.
# Deliberately NOT a heuristic (e.g. "starts with results/"): other provenance sub-fields
# (required_manifest_evidence_level, frontier_registry_ref, selector, selector_note,
# threshold_rule) are metadata strings, not manifest-checkable paths, and a heuristic could
# silently mis-cross-check them (e.g. frontier_registry_ref's value looks path-like but isn't one).
# Extend this tuple explicitly if a future curated entry introduces a new path-bearing field name.
CURATED_PROVENANCE_PATH_FIELDS = ("confusion_csv", "result_report", "source_file")


def _normalize_path(p):
    return str(p).replace("\\", "/").strip() if p else p


def _curated_reference_lookup(ref_name, gid, sources):
    """Exact-key curated lookup against sources['reference_evidence_yaml']. Returns
    (row_or_None, refusal_result_or_None); exactly one is non-None, or BOTH are None when no
    curated source is configured or the key isn't curated (caller falls back to the legacy path).
    Never fabricates a row: a manifest disagreement REFUSES with provenance_mismatch rather than
    returning trusted metrics."""
    ref_path = sources.get("reference_evidence_yaml")
    if not ref_path or not Path(ref_path).exists():
        return None, None

    doc = _load_yaml(ref_path) or {}
    entries = doc.get("reference_results") or []
    matches = [e for e in entries if e.get("key") == ref_name]
    if not matches:
        return None, None
    if len(matches) > 1:
        return None, _result(
            "refused", "duplicate_curated_key",
            f"REFUSED — curated key {ref_name!r} appears {len(matches)} times in the "
            f"reference-evidence registry; the registry must be fixed by hand", [])
    entry = matches[0]

    if entry.get("goal") != gid:
        return None, _result(
            "refused", "curated_goal_mismatch",
            f"REFUSED — curated key {ref_name!r} belongs to goal {entry.get('goal')!r}, "
            f"not the requested {gid!r}", [])

    manifest_rows = {_normalize_path(m.get("path")): m for m in _load_csv(sources["manifest_csv"])}
    provenance = entry.get("provenance") or {}
    declared_level = entry.get("evidence_level")
    required_level = provenance.get("required_manifest_evidence_level")

    checked_paths = []
    for field in CURATED_PROVENANCE_PATH_FIELDS:
        raw = provenance.get(field)
        if not raw:
            continue
        norm = _normalize_path(raw)
        man = manifest_rows.get(norm)
        if man is None:
            return None, _result(
                "refused", "provenance_mismatch",
                f"REFUSED — curated key {ref_name!r}: provenance path {raw!r} ({field}) "
                f"not found in the artifact manifest", [])
        man_level = man.get("evidence_level")
        if man_level != declared_level or (required_level and man_level != required_level):
            return None, _result(
                "refused", "provenance_mismatch",
                f"REFUSED — curated key {ref_name!r}: manifest evidence_level {man_level!r} "
                f"for {raw!r} disagrees with the curated entry (declared {declared_level!r}"
                + (f", required {required_level!r}" if required_level else "") + ")", [])
        checked_paths.append((field, raw, man))

    if not checked_paths:
        return None, _result(
            "refused", "provenance_mismatch",
            f"REFUSED — curated key {ref_name!r} has no cross-checkable provenance path "
            f"(expected one of {CURATED_PROVENANCE_PATH_FIELDS})", [])

    primary_field, primary_path, primary_man = checked_paths[0]
    row = {
        "goal": gid,
        "reference_evidence_key": ref_name,
        "dataset": entry.get("dataset"),
        "attack": entry.get("attack"),
        "epsilon": entry.get("epsilon"),
        "defense_or_method_name": entry.get("method"),
        "approach_group": None,
        "split": entry.get("split"),
        "evidence_level": declared_level,          # curated value, cross-checked; never derived/upgraded
        "threshold": entry.get("threshold"),
        "protocol_id": entry.get("protocol_id"),
        "metrics": dict(entry.get("metrics") or {}),   # copied verbatim from the approved entry
        "clean_disclosure_companion": entry.get("clean_disclosure_companion"),
        "source_file": primary_path,
        "provenance": {
            "sha256": primary_man.get("sha256") or None,
            "committed": primary_man.get("committed") or None,
            "curated_key": ref_name,
            "manifest_cross_check": "pass",
            "checked_paths": [{"field": f, "path": p} for f, p, _ in checked_paths],
        },
        "warning_band": list(entry.get("disclosures") or []),
    }
    return row, None


# ------------------------------------------------------------ D2e-2: identity enrichment (supplemental)
def _load_identity_registry(sources):
    """Read-only load of the OPTIONAL experiment-identity registry. Returns (doc_or_None,
    reason_or_None). A None doc always carries a specific reason so callers can report an honest
    'unavailable' state rather than silently doing nothing. Never raises on a missing/malformed
    file -- degrades to unavailable, exactly like the D2d-2 curated-lookup precedent."""
    path = sources.get("identity_yaml")
    if not path:
        return None, "no identity source configured"
    p = Path(path)
    if not p.exists():
        return None, f"identity registry file not found: {path}"
    try:
        doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return None, "identity registry YAML is malformed/unparseable"
    return doc, None


def _identity_epsilon_token(epsilon, identity_doc):
    """Reads naming_policy.epsilon_tokens directly from the loaded identity document -- the SAME
    data-driven source scripts/automation/validate_experiment_identity.py uses, so the two can
    never drift without deliberately importing one from the other."""
    tokens = ((identity_doc.get("naming_policy") or {}).get("epsilon_tokens")) or {}
    for k, v in tokens.items():
        try:
            if abs(float(k) - float(epsilon)) < 1e-9:
                return v
        except (TypeError, ValueError):
            continue
    return None


def _find_identity_evaluation(identity_doc, ref_key):
    """Exact match on reference_evidence_key only -- never fuzzy, never alias-based (H15/D8b/A1/H1
    are never treated as standalone lookup keys here)."""
    matches = [e for e in (identity_doc.get("evaluations") or [])
               if e.get("reference_evidence_key") == ref_key]
    if not matches:
        return None, "no evaluation in the identity registry references this reference_evidence_key"
    if len(matches) > 1:
        return None, (f"duplicate identity mapping: {len(matches)} evaluations reference "
                       f"reference_evidence_key {ref_key!r}")
    return matches[0], None


def _find_identity_run(identity_doc, run_id):
    if not run_id:
        return None, "evaluation record has no run_id"
    matches = [r for r in (identity_doc.get("runs") or []) if r.get("run_id") == run_id]
    if not matches:
        return None, f"referenced run_id {run_id!r} does not resolve to any run record"
    if len(matches) > 1:
        return None, f"referenced run_id {run_id!r} resolves to {len(matches)} run records (ambiguous)"
    return matches[0], None


def _identity_cross_check(row_dataset_id, row, evaluation):
    """Exact, deterministic field comparisons (D2e-2 Part 4). Only compares fields BOTH sides
    represent -- a field the scientific row doesn't carry is skipped, never forced to mismatch.
    Epsilon uses a tight tolerance (1e-9), never a loose one that could confuse eps=0.015 with
    eps=0.030. Returns a list of mismatch reasons; empty = no conflict found."""
    reasons = []
    if row.get("goal") != evaluation.get("goal"):
        reasons.append(f"goal disagreement: result={row.get('goal')!r} vs identity={evaluation.get('goal')!r}")
    if row_dataset_id is not None and evaluation.get("dataset") is not None:
        if row_dataset_id != evaluation.get("dataset"):
            reasons.append(f"dataset disagreement: result={row_dataset_id!r} vs identity={evaluation.get('dataset')!r}")
    mv = evaluation.get("method_variant")
    if row.get("defense_or_method_name") and mv:
        if row["defense_or_method_name"] != mv:
            reasons.append(f"method_variant disagreement: result={row['defense_or_method_name']!r} vs identity={mv!r}")
    if row.get("attack") != evaluation.get("attack"):
        reasons.append(f"attack disagreement: result={row.get('attack')!r} vs identity={evaluation.get('attack')!r}")
    r_eps, e_eps = row.get("epsilon"), evaluation.get("epsilon")
    if r_eps is not None and e_eps is not None:
        r_num, e_num = _num(r_eps), _num(e_eps)
        if r_num is None or e_num is None or abs(r_num - e_num) > 1e-9:
            reasons.append(f"epsilon disagreement: result={r_eps!r} vs identity={e_eps!r}")
    if row.get("split") != evaluation.get("split"):
        reasons.append(f"split disagreement: result={row.get('split')!r} vs identity={evaluation.get('split')!r}")
    if row.get("evidence_level") != evaluation.get("evidence_level"):
        reasons.append(
            f"evidence_level disagreement: result={row.get('evidence_level')!r} vs identity={evaluation.get('evidence_level')!r}")
    r_pid, e_pid = row.get("protocol_id"), evaluation.get("protocol_id")
    if r_pid and e_pid and r_pid != e_pid:
        reasons.append(f"protocol_id disagreement: result={r_pid!r} vs identity={e_pid!r}")
    return reasons


def _enrich_with_identity(row, row_dataset_id, sources):
    """Attach a SUPPLEMENTAL experiment_identity block to an already scientifically-resolved
    curated row. Called strictly after manifest cross-checking has passed. Only ever ADDS the
    experiment_identity key -- every existing scientific field is left untouched. Never fabricates
    a mapping; never resolves via alias (H15/D8b/A1/H1 are never used as lookup keys here)."""
    ref_key = row.get("reference_evidence_key")
    identity_doc, load_reason = _load_identity_registry(sources)
    if identity_doc is None:
        row["experiment_identity"] = {"state": "unavailable", "reason": load_reason}
        return row

    evaluation, eval_reason = _find_identity_evaluation(identity_doc, ref_key)
    if evaluation is None:
        state = "mismatch" if eval_reason and eval_reason.startswith("duplicate") else "unavailable"
        row["experiment_identity"] = {"state": state, "reason": eval_reason}
        return row

    mismatches = _identity_cross_check(row_dataset_id, row, evaluation)
    if mismatches:
        row["experiment_identity"] = {"state": "mismatch", "reason": "; ".join(mismatches)}
        return row

    eps_tok = _identity_epsilon_token(evaluation.get("epsilon"), identity_doc)
    eval_id = evaluation.get("evaluation_id") or ""
    if eps_tok and eps_tok not in eval_id:
        row["experiment_identity"] = {
            "state": "mismatch",
            "reason": f"epsilon token {eps_tok!r} not found in evaluation_id {eval_id!r}"}
        return row

    if not evaluation.get("display_name"):
        row["experiment_identity"] = {"state": "mismatch", "reason": "identity evaluation has no display_name"}
        return row

    run, run_reason = _find_identity_run(identity_doc, evaluation.get("run_id"))
    if run is None:
        row["experiment_identity"] = {"state": "mismatch", "reason": run_reason}
        return row

    row["experiment_identity"] = {
        "state": "matched",
        "evaluation_id": evaluation.get("evaluation_id"),
        "display_name": evaluation.get("display_name"),
        "run_id": run.get("run_id"),
        "run_display_name": run.get("display_name"),
        "run_link_status": evaluation.get("run_link_status"),
        "reference_evidence_key": ref_key,
        "identity_status": evaluation.get("identity_status"),
        "method_family": evaluation.get("method_family"),
        "method_variant": evaluation.get("method_variant"),
        "legacy_aliases": evaluation.get("legacy_aliases") or [],
        "protocol_id": evaluation.get("protocol_id"),
    }
    return row


def _receipt_id_for(source_file, receipts_dir):
    """Provenance enrichment only: surface a receipt id when one mentions the source file."""
    try:
        for p in sorted(Path(receipts_dir).glob("*.json")):
            text = p.read_text(encoding="utf-8")
            if source_file and source_file in text:
                try:
                    return json.loads(text).get("receipt_id")
                except json.JSONDecodeError:
                    continue
    except (OSError, TypeError):
        pass
    return None


# ---------------------------------------------------------------------------- core query
def run_query(query, sources):
    goals = (_load_yaml(sources["goals_yaml"]) or {}).get("goals", [])
    datasets = (_load_yaml(sources["datasets_yaml"]) or {}).get("datasets", [])

    goal = _resolve_goal(goals, query.get("goal"))
    if goal is None:
        known = ", ".join(g.get("id", "?") for g in goals)
        return _result("refused", "unknown_goal",
                       f"REFUSED — unknown goal {query.get('goal')!r}; registered goals: {known}", [])
    gid = goal["id"]

    # named reference evidence query: explicit, user-invoked window onto saved test/frozen evidence
    filters = dict(query)
    ref_name = filters.pop("reference_evidence_query", None)
    if ref_name:
        # D2d-2: curated registry resolved FIRST, exact-key only, never a filtered pool.
        curated_row, curated_refusal = _curated_reference_lookup(ref_name, gid, sources)
        if curated_refusal is not None:
            return curated_refusal
        if curated_row is not None:
            # capture the raw dataset ID BEFORE the display-name rename below -- identity
            # cross-checking must compare against the identity registry's dataset ID field
            raw_dataset_id = curated_row.get("dataset")
            ds_c = _resolve_dataset(datasets, curated_row.get("dataset"), None)
            if ds_c:
                curated_row["dataset"] = ds_c.get("name") or curated_row["dataset"]
            # D2e-2: scientific result is fully resolved and provenance-checked above; identity
            # enrichment happens ONLY now, as supplemental metadata that never alters it.
            curated_row = _enrich_with_identity(curated_row, raw_dataset_id, sources)
            return _result("ok", None, "1 curated result row", [curated_row])
        # no curated entry for this key -> fall back to the pre-existing (D2c) path, unchanged
        ref = (goal.get("reference_evidence_queries") or {}).get(ref_name)
        if ref is None:
            have = ", ".join((goal.get("reference_evidence_queries") or {}).keys()) or "(none)"
            return _result("refused", "unknown_reference_query",
                           f"REFUSED — no reference query {ref_name!r} for {gid}; available: {have}", [])
        for key in ("split", "evidence_level", "attack", "epsilon"):
            if key in ref:
                filters[key] = ref[key]

    # dataset resolution + integrity gate
    ds = _resolve_dataset(datasets, filters.get("dataset"), filters.get("dataset_family"))
    if filters.get("dataset") not in NO_FILTER:
        if ds is None:
            return _result("refused", "unknown_dataset",
                           f"REFUSED — unknown dataset {filters.get('dataset')!r}", [])
        if gid in (ds.get("unsupported_goals") or []) or gid not in (ds.get("supported_goals") or []):
            return _result("refused", "unsupported_pair",
                           f"REFUSED — {ds.get('name')} cannot support {gid} "
                           f"(see registry unsupported_goals)", [])

    # evidence-level filter validated against the goal registry (only when a filter is present)
    allowed = goal.get("allowed_evidence_levels") or []
    ev_filter = filters.get("evidence_level")
    if ev_filter not in NO_FILTER and ev_filter not in allowed:
        return _result("refused", "disallowed_evidence",
                       f"REFUSED — evidence level {ev_filter!r} not in {gid} "
                       f"allowed_evidence_levels {allowed}", [])

    # goals with no supporting dataset: data needed is a first-class answer, not a failure
    if not (goal.get("datasets_available") or []):
        needs = ", ".join(goal.get("data_needs") or []) or "unspecified"
        return _result("empty", "data_needed", f"NO RESULTS — data needed: {needs}", [])

    # fill omitted filters from the goal registry defaults (validation-first by registry rule)
    defaults = goal.get("default_query_fields") or {}
    for key in ("attack", "epsilon", "split", "defense"):
        if filters.get(key) in NO_FILTER and key not in ("epsilon",):
            filters[key] = defaults.get(key)
        elif key == "epsilon" and filters.get(key) is None:
            filters[key] = defaults.get(key)

    ledger = _load_csv(sources["ledger_csv"])
    manifest = {m.get("path"): m for m in _load_csv(sources["manifest_csv"])}

    # a ledger row belongs to this goal iff its defining metric (first primary key) is populated
    keys = goal.get("primary_metric_keys") or []
    defining = keys[0] if keys else None
    goal_rows = [r for r in ledger if defining and str(r.get(defining, "")).strip()]
    if not goal_rows:
        name = ds.get("name") if ds else (goal.get("datasets_available") or ["?"])[0]
        return _result("empty", "supported_not_evaluated",
                       f"NO RESULTS — goal supported by {name} but not yet evaluated "
                       f"(defining metric {defining!r} has no populated result column)", [])

    # filter rows
    hits = []
    for r in goal_rows:
        if filters.get("attack") not in NO_FILTER and r.get("attack") != filters["attack"]:
            continue
        eps = filters.get("epsilon")
        if eps is not None and eps != "" and _num(r.get("epsilon")) is not None:
            if _num(eps) is None or abs(_num(r.get("epsilon")) - _num(eps)) > 1e-9:
                continue
        if filters.get("split") not in NO_FILTER and r.get("split") != filters["split"]:
            continue
        if filters.get("defense") not in NO_FILTER and \
                filters["defense"] not in (r.get("approach_group"), r.get("method_internal_name"),
                                           r.get("method_thesis_name")):
            continue
        man = manifest.get(r.get("source_file"))
        level = (man or {}).get("evidence_level") or None   # manifest is authoritative; never derived
        if ev_filter not in NO_FILTER and level != ev_filter:
            continue
        hits.append((r, man, level))

    if not hits:
        return _result("empty", "no_matching_artifact",
                       "NO MATCH — valid query, zero rows under these filters", [])
    if len(hits) > DISPLAY_CAP:
        return _result("empty", "query_too_broad",
                       f"QUERY TOO BROAD — {len(hits)} rows exceeds cap {DISPLAY_CAP}; "
                       f"add filters (attack/epsilon/defense/split)", [])

    # R90F10 banner applies to every row of a goal whose R90F10 target is not truly met
    targets = goal.get("success_targets") or {}
    r90 = targets.get("R90F10") or {}
    needs_r90_warning = bool(r90) and str(r90.get("status", "")).lower() not in ("met", "pass")

    rows = []
    for r, man, level in hits:
        metrics, missing = {}, []
        for k in keys:
            raw = str(r.get(k, "")).strip() if k in r else ""
            if raw:
                metrics[k] = _num(raw) if _num(raw) is not None else raw
            else:
                missing.append(k)
        warning = []
        if level in ("validation-only", "test-post-hoc", "diagnostic-internal"):
            warning.append(WARN_TEXT[level])
        if level is None:
            warning.append(WARN_TEXT["no_verified_result"])
        if needs_r90_warning:
            warning.append(WARN_TEXT["not_r90f10"])
        if missing:
            warning.append(f"metrics defined but not evaluated in this row: {', '.join(missing)}")
        provenance = {}
        if man:
            provenance["sha256"] = man.get("sha256") or None
            provenance["committed"] = man.get("committed") or None
        rid = _receipt_id_for(r.get("source_file"), sources.get("receipts_dir"))
        if rid:
            provenance["receipt_id"] = rid
        rows.append({
            "goal": gid,
            "dataset": (ds or {}).get("name") or (goal.get("datasets_available") or [""])[0],
            "attack": r.get("attack"),
            "epsilon": _num(r.get("epsilon")) if _num(r.get("epsilon")) is not None else r.get("epsilon"),
            "defense_or_method_name": r.get("method_internal_name") or r.get("method_thesis_name"),
            "approach_group": r.get("approach_group"),
            "split": r.get("split"),
            "evidence_level": level,
            "metrics": metrics,
            "source_file": r.get("source_file"),
            "provenance": provenance,
            "warning_band": warning,
        })
    return _result("ok", None, f"{len(rows)} result row(s)", rows)


# ---------------------------------------------------------------------------- tiny stdout-only CLI
def main(argv):
    """Usage: result_explorer.py goals=<goals.yaml> datasets=<datasets.yaml> ledger=<ledger.csv> \
manifest=<manifest.csv> [receipts=<dir>] [reference-evidence=<reference_evidence.yaml>] \
[identity=<experiment_identity.yaml>] goal=<id> [attack=..] [epsilon=..] [split=..] \
[defense=..] [evidence_level=..] [reference_evidence_query=..]  (key=value only; prints JSON)"""
    kv = dict(a.partition("=")[::2] for a in argv if "=" in a)
    src_keys = {"goals": "goals_yaml", "datasets": "datasets_yaml",
                "ledger": "ledger_csv", "manifest": "manifest_csv", "receipts": "receipts_dir",
                "reference-evidence": "reference_evidence_yaml", "identity": "identity_yaml"}
    sources = {dest: kv.pop(k) for k, dest in src_keys.items() if k in kv}
    missing = [k for k in ("goals_yaml", "datasets_yaml", "ledger_csv", "manifest_csv")
               if k not in sources]
    if missing or "goal" not in kv:
        print(main.__doc__)
        return 2
    if "epsilon" in kv and _num(kv["epsilon"]) is not None:
        kv["epsilon"] = _num(kv["epsilon"])
    print(json.dumps(run_query(kv, sources), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
