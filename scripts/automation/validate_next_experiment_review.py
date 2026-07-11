#!/usr/bin/env python
"""Read-only validator for the generated Next Experiment Brainstorm review (NEXT-EXP-REVIEW).

Review: automation/reviews/next_experiment_review.yaml. Generator + design contract:
scripts/automation/next_experiment_brainstorm_checker.py, automation/acceptance/next-experiment-review.yaml.

Strategy: the strongest verification of "the derived verdict / ranking / material-difference /
summary / fingerprint / idempotency are all correct" is to RE-BUILD the review from the current
authoritative sources using the checker's own pure build function (seeded with the on-disk
review_id/generated_at) and assert byte-identical output. Everything the checker computes is then
verified in one shot (rules 3, 8, 9, 10, 11, 12, 28, 29). This validator then adds independent
structural/safety scans (rules 14-27, 30) that do NOT trust the checker.

Pure read-only stdlib+yaml: never writes, no network, deterministic. Exit 0 = PASS, 1 = FAIL.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML required: pip install pyyaml")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import next_experiment_brainstorm_checker as chk  # noqa: E402

REPO = chk.REPO
REVIEW_PATH = chk.REVIEW_PATH
CHECKER_SRC = Path(chk.__file__)

MAX_TEXT_FIELD_CHARS = 900
ABS_PATH_RE = re.compile(r"[A-Za-z]:[\\/]|^\\\\|(?:^|[\s\"'])/(?:Users|home|mnt|var|etc)\b")
MARKDOWN_TABLE_ROW_RE = re.compile(r"(\|[^|\n]*){5,}\|")
COMMAND_LIKE_RE = re.compile(
    r"--split\b|\.venv[\\/ ]?Scripts[\\/]?python|(?:^|\s)python\s|train_\w+\.py|scripts/train_|\bnvidia-smi\b", re.I)
CLINICAL_OVERCLAIM_RE = re.compile(
    r"(?<!not )(?<!never )(?<!no )(clinically (proven|validated|certified)"
    r"|proves? clinical|establishes clinical (efficacy|validity)"
    r"|deployment[- ]ready|ready for (clinical )?deployment|certified for clinical)", re.I)
QUEUE_LINKAGE_RE = re.compile(r"queue_entry|entry_id\s*[:=]|\bEQ-\d{4}-", re.I)


def _walk_strings(node, path=""):
    if isinstance(node, dict):
        for k, v in sorted(node.items(), key=lambda kv: str(kv[0])):
            yield from _walk_strings(v, f"{path}.{k}" if path else str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk_strings(v, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


def validate(base=REPO):
    errors = []
    err = errors.append

    if not REVIEW_PATH.exists():
        return ["review file not found: automation/reviews/next_experiment_review.yaml"]

    text = REVIEW_PATH.read_text(encoding="utf-8")
    try:
        doc = yaml.safe_load(text)  # 1. YAML parses
    except yaml.YAMLError as e:
        return [f"review YAML is malformed: {e}"]
    if not isinstance(doc, dict):
        return ["review root is not a mapping"]

    # 2. schema version
    if doc.get("schema_version") not in {chk.SCHEMA_VERSION}:
        err(f"unsupported schema_version {doc.get('schema_version')!r}")

    # ---- rebuild from current sources, seeded with on-disk id/timestamp, assert byte-identical.
    sources = chk.load_sources(base)
    rebuilt = chk.build_review(sources, existing=doc)
    rebuilt_text = chk.dump_yaml(rebuilt)
    if rebuilt_text != text:
        err("on-disk review is NOT byte-identical to a fresh rebuild from current sources "
            "(verdict/ranking/material-difference/summary/fingerprint drift, or the sources changed "
            "without regeneration)")
    # 3. source_fingerprint correct
    if doc.get("source_fingerprint") != chk.compute_fingerprint(sources):
        err("recorded source_fingerprint does not match the current authoritative inputs")
    # 29. identical fingerprint preserves review_id/generated_at
    if rebuilt.get("review_id") != doc.get("review_id") or rebuilt.get("generated_at") != doc.get("generated_at"):
        err("rebuild with unchanged fingerprint did not preserve review_id/generated_at")
    # 28. determinism: two rebuilds identical
    if chk.dump_yaml(chk.build_review(sources, existing=doc)) != rebuilt_text:
        err("two rebuilds are not byte-identical (non-deterministic output)")

    idx = chk._index(sources)
    registry_candidate_ids = [c.get("candidate_id") for c in idx["candidates"]]
    entries = doc.get("entries") or []

    # 4. candidate_count matches registry
    if doc.get("candidate_count") != len(registry_candidate_ids):
        err(f"candidate_count {doc.get('candidate_count')} != registry candidate count {len(registry_candidate_ids)}")
    if len(entries) != len(registry_candidate_ids):
        err(f"entries length {len(entries)} != registry candidate count {len(registry_candidate_ids)}")

    # 5./6. every registry candidate appears exactly once and resolves
    seen = {}
    for e in entries:
        cid = e.get("candidate_id")
        seen[cid] = seen.get(cid, 0) + 1
        if cid not in registry_candidate_ids:  # 6
            err(f"entry candidate_id {cid!r} does not resolve in experiment_candidates.yaml")
    for cid in registry_candidate_ids:
        if seen.get(cid, 0) != 1:
            err(f"registry candidate {cid!r} appears {seen.get(cid, 0)} times in the review (expected exactly 1)")

    # 10. ranks unique and contiguous 1..N
    ranks = sorted(e.get("rank") for e in entries)
    if ranks != list(range(1, len(entries) + 1)):
        err(f"ranks are not unique-and-contiguous 1..{len(entries)}: {ranks}")

    # 11. summary counts match entries
    s = doc.get("summary") or {}
    if s.get("go_count") != sum(1 for e in entries if e.get("derived_verdict") == "GO"):
        err("summary.go_count does not match entries")
    if s.get("review_count") != sum(1 for e in entries if e.get("derived_verdict") == "REVIEW"):
        err("summary.review_count does not match entries")
    if s.get("no_go_count") != sum(1 for e in entries if e.get("derived_verdict") == "NO-GO"):
        err("summary.no_go_count does not match entries")

    cand_by_id = {c.get("candidate_id"): c for c in idx["candidates"]}
    for e in entries:
        cid = e.get("candidate_id")
        c = cand_by_id.get(cid)
        if not c:
            continue
        verdict = e.get("derived_verdict")
        # 7./18. every reference resolves; unresolved -> must be NO-GO
        unresolved = chk.resolve_references(c, idx, base)
        if unresolved and verdict != "NO-GO":
            err(f"{cid}: has unresolved references but verdict is {verdict} (must be NO-GO)")
        # 12. material-difference status correctly derived
        md = chk.derive_material_difference(c)
        if (e.get("material_difference_requirement") or {}).get("status") != md["status"]:
            err(f"{cid}: material_difference status mismatch vs re-derivation")
        # 13. prior-negative evidence not omitted
        if (c.get("prior_negative_evidence_refs") or []) and \
                e.get("prior_negative_evidence_summary") in (None, "", "no prior negative evidence"):
            err(f"{cid}: prior negative evidence exists but the review omits it")
        # 14. dataset-blocked candidates are NO-GO
        if c.get("evidence_strength") == "dataset_blocked" and verdict != "NO-GO":
            err(f"{cid}: evidence_strength dataset_blocked must be NO-GO (got {verdict})")
        # 15. available_not_evaluated cannot bypass the REVIEW cap -> never GO
        if c.get("dataset_readiness") == "available_not_evaluated" and verdict == "GO":
            err(f"{cid}: available_not_evaluated must not receive GO")
        # 16. new frozen-protocol candidates cannot receive GO
        if c.get("allowed_split") == "requires_new_frozen_protocol" and verdict == "GO":
            err(f"{cid}: requires_new_frozen_protocol must not receive GO")
        # 17. test-risk candidates cannot receive GO
        if c.get("test_read_risk") in ("requires_review", "blocked_without_protocol") and verdict == "GO":
            err(f"{cid}: test_read_risk {c.get('test_read_risk')} must not receive GO")
        # 19. GO wording states human planning review only
        if verdict == "GO":
            joined = " ".join(e.get("required_human_actions") or [])
            if "human planning review only" not in joined.lower():
                err(f"{cid}: GO entry must state 'Suitable for human planning review only.'")

    # 19b. the global notice states the GO meaning + non-authorization
    notice = str(doc.get("notice") or "").lower()
    if "human planning review only" not in notice or "authorizes" not in notice:
        err("review notice must state that GO means human-planning-review-only and authorizes nothing")

    # 20./21./22./23./24./25. structural safety scans over every string in the document
    for path, txt in _walk_strings(doc):
        if len(txt) > MAX_TEXT_FIELD_CHARS:
            err(f"{path}: text field is {len(txt)} chars (> {MAX_TEXT_FIELD_CHARS}) -- possible copied summary/table")
        if MARKDOWN_TABLE_ROW_RE.search(txt):
            err(f"{path}: embedded markdown table row -- copied metric table forbidden")
        if COMMAND_LIKE_RE.search(txt):
            err(f"{path}: runnable-command-like content forbidden")
        if QUEUE_LINKAGE_RE.search(txt):
            err(f"{path}: queue-linkage content forbidden")
        if CLINICAL_OVERCLAIM_RE.search(txt):
            err(f"{path}: clinical/deployment claim forbidden")
        if ABS_PATH_RE.search(txt):
            err(f"{path}: absolute filesystem path forbidden")
        if chk._affirmative_hit(txt, chk.EXECUTION_AUTH_TRIGGERS):
            err(f"{path}: execution/test-read authorization content forbidden")
    # 21b. no entry may carry a queue-linkage field key
    for e in entries:
        for k in e.keys():
            if "queue" in str(k).lower() or "entry_id" == str(k).lower():
                err(f"entry {e.get('candidate_id')}: forbidden queue-linkage field {k!r}")

    # 26. candidate registry unchanged: the review's recorded hash for it must match the live file
    recorded = {a.get("path"): a.get("sha256") for a in (doc.get("authoritative_sources") or [])}
    import hashlib
    for rel in ("automation/registry/experiment_candidates.yaml",):
        live = hashlib.sha256((base / rel).read_bytes()).hexdigest()
        if recorded.get(rel) != live:
            err(f"candidate registry hash in the review does not match the live file ({rel})")
    # 27. experiment queue unchanged: still parses with an empty entries list (checker never wrote to it)
    q = yaml.safe_load((base / "automation" / "experiment_queue.yaml").read_text(encoding="utf-8")) or {}
    if (q.get("entries") or []) != []:
        err("experiment_queue.yaml entries is non-empty -- the checker must never populate the queue")

    # 30. only the designated review file is a checker write target; no shell/network in the source.
    # Match actual imports/call-sites (not documentation mentions in the docstring/comments).
    src = CHECKER_SRC.read_text(encoding="utf-8")
    forbidden_import_re = re.compile(
        r"^\s*(?:import|from)\s+(subprocess|socket|urllib|requests|http\.client|httplib|pty|ctypes|asyncio)\b",
        re.M)
    for m in forbidden_import_re.finditer(src):
        err(f"checker source imports forbidden module {m.group(1)!r}")
    for call in ("os.system(", "os.popen(", "os.exec", "subprocess.", "eval(", "exec("):
        if call in src:
            err(f"checker source uses forbidden call {call!r}")
    write_text_calls = src.count(".write_text(")
    # exactly one write_text target, and it is the review path variable
    if write_text_calls != 1 or "review_path.write_text(" not in src:
        err("checker must write via exactly one review_path.write_text(...) call and nowhere else")
    if re.search(r"open\([^)]*['\"][wax]", src):
        err("checker source opens a file for writing via open() -- only review_path.write_text is permitted")

    return errors


def main(argv):
    base = REPO
    for a in argv:
        if a.startswith("base="):
            base = Path(a.split("=", 1)[1])
    errors = validate(base)
    doc = {}
    if REVIEW_PATH.exists():
        try:
            doc = yaml.safe_load(REVIEW_PATH.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            doc = {}
    s = doc.get("summary") or {}
    print(f"[validate] candidates={doc.get('candidate_count')} GO={s.get('go_count')} "
          f"REVIEW={s.get('review_count')} NO-GO={s.get('no_go_count')} "
          f"unresolved_refs={s.get('unresolved_reference_count')} "
          f"fingerprint={str(doc.get('source_fingerprint'))[:16]}...")
    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
        print(f"[validate] FAIL — {len(errors)} error(s)")
        return 1
    print("[validate] PASS — no errors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
