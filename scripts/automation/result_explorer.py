#!/usr/bin/env python
"""Result Explorer v1 — read-only lookup over EXISTING committed results (D2c + D2d-2).

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
            ds_c = _resolve_dataset(datasets, curated_row.get("dataset"), None)
            if ds_c:
                curated_row["dataset"] = ds_c.get("name") or curated_row["dataset"]
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
goal=<id> [attack=..] [epsilon=..] [split=..] [defense=..] [evidence_level=..] \
[reference_evidence_query=..]  (key=value only; prints JSON)"""
    kv = dict(a.partition("=")[::2] for a in argv if "=" in a)
    src_keys = {"goals": "goals_yaml", "datasets": "datasets_yaml",
                "ledger": "ledger_csv", "manifest": "manifest_csv", "receipts": "receipts_dir",
                "reference-evidence": "reference_evidence_yaml"}
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
