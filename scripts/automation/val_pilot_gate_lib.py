#!/usr/bin/env python
"""Pure logic for the val-pilot gate (read-only scanner core).

Implements the machine-checkable parts of automation/designs/VAL_PILOT_GATE_DESIGN.md v0.2:
  - §2 completed-pilot definition + §3 evidence rules  -> verify_pilot()
  - §4 matching rule (checkpoint path+hash, run_name, seed, epsilon)  -> match_command()
  - §5 STRONG-GO / REVIEW-GO / NO-GO / NEEDS-REVIEW verdict            -> compute_verdict()
  - §3 staleness (recorded hash vs current file hash)                 -> is_stale()

This module is PURE and SAFE by construction:
  - It NEVER runs a --split test/legacy command, never runs training/eval/export, never reads a
    held-out-test artifact, never writes anything, never schedules or authorizes a test read.
  - Its only filesystem interaction is sha256-hashing an already-existing checkpoint path handed
    to it (needed to detect the overwrite/stale hazard). It walks no directory tree; the real
    results/-walking scanner (design §10 step 3) is a SEPARATE, later, separately-approved step.
  - No verdict this module returns authorizes anything. STRONG-GO produces a proposal, never an
    authorization (design §5.2, §9).

Thresholds are read from the caller (the acceptance contract / reference frontier), never typed
inline as scientific constants here.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

# Gate outcome vocabulary (design §5). Integrity NO-GO is terminal and evaluated first.
VERIFIED = "VERIFIED"
NO_GO = "NO-GO"
STRONG_GO = "STRONG-GO"
REVIEW_GO = "REVIEW-GO"
NEEDS_REVIEW = "NEEDS-REVIEW"

# Required metadata fields for a complete pilot (design §2).
REQUIRED_METADATA_FIELDS = ("checkpoint", "run_name", "seed", "split", "epsilon", "model")

# Splits that can never be pilot evidence (design §3, §8-J).
NON_EVIDENCE_SPLITS = {"test", "legacy"}


def sha256_file(path: Path) -> Optional[str]:
    """SHA-256 of a file's bytes, or None if it does not exist. Read-only."""
    p = Path(path)
    if not p.exists() or not p.is_file():
        return None
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class PilotVerification:
    """Result of verifying one candidate pilot against §2/§3."""
    status: str                       # VERIFIED | NO-GO | NEEDS-REVIEW
    integrity_ok: bool
    reasons: list[str] = field(default_factory=list)
    checkpoint_sha256: Optional[str] = None
    fields: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)


def _filename_split_token(csv_name: str) -> Optional[str]:
    name = csv_name.lower()
    for token in ("_val_", "_test_", "_legacy_"):
        if token in name:
            return token.strip("_")
    return None


def verify_pilot(
    *,
    probabilities_csv: Optional[Path],
    metadata: Optional[dict[str, Any]],
    checkpoint_path: Optional[Path],
    metrics: Optional[dict[str, Any]],
) -> PilotVerification:
    """Verify §2 completeness + §3 evidence consistency for ONE pilot.

    metadata is the already-parsed export metadata dict (None if the JSON is missing).
    checkpoint_path is the .pt path recorded by metadata (may or may not exist on disk).
    metrics is the already-parsed analysis-artifact metric dict (None if absent).

    Returns a PilotVerification. Integrity failures (§5.1) are terminal NO-GO. Metric-coverage
    gaps in otherwise-consistent evidence are NEEDS-REVIEW (§2, §5.4-1). Never silently upgraded.
    """
    reasons: list[str] = []

    # §2 / §8-H: metadata JSON is mandatory. Its absence is an integrity NO-GO, never a match.
    if metadata is None:
        return PilotVerification(status=NO_GO, integrity_ok=False,
                                 reasons=["metadata_json_missing"])

    # §2: all required metadata fields present.
    missing = [f for f in REQUIRED_METADATA_FIELDS if f not in metadata or metadata[f] in (None, "")]
    if missing:
        return PilotVerification(status=NO_GO, integrity_ok=False,
                                 reasons=[f"metadata_field_missing:{','.join(missing)}"])

    split = str(metadata.get("split", "")).lower()

    # §3 / §8-J: test/legacy-derived artifacts can NEVER be pilot evidence. Terminal.
    if split in NON_EVIDENCE_SPLITS:
        return PilotVerification(status=NO_GO, integrity_ok=False,
                                 reasons=[f"non_evidence_split:{split}"])

    # §3 / §8-I: filename split token must not contradict metadata. Metadata is authoritative;
    # a disagreement is quarantined as NEEDS-REVIEW, never treated as evidence.
    if probabilities_csv is not None:
        ftoken = _filename_split_token(Path(probabilities_csv).name)
        if ftoken is not None and ftoken != split:
            return PilotVerification(
                status=NEEDS_REVIEW, integrity_ok=False,
                reasons=[f"filename_metadata_split_disagreement:file={ftoken},meta={split}"],
                fields={"split": split})

    # Only validation split is in-scope pilot evidence (design §2 "Required split: validation only").
    if split != "val":
        return PilotVerification(status=NEEDS_REVIEW, integrity_ok=False,
                                 reasons=[f"split_not_val:{split}"], fields={"split": split})

    # §2: checkpoint must exist locally so a future test read can evaluate the SAME weights.
    ckpt_hash = sha256_file(checkpoint_path) if checkpoint_path is not None else None
    if ckpt_hash is None:
        return PilotVerification(status=NO_GO, integrity_ok=False,
                                 reasons=["checkpoint_file_absent"],
                                 fields={"split": split})

    resolved = {
        "checkpoint": str(metadata["checkpoint"]),
        "run_name": str(metadata["run_name"]),
        "seed": metadata["seed"],
        "epsilon": metadata["epsilon"],
        "model": str(metadata["model"]),
        "split": split,
    }

    # §2: metric coverage. recall/far/auroc/rfall_at_far_020 are the minimum; rfall_at_far_010 is
    # required only for a candidate claiming R90F10 progress (§2), so its absence -> NEEDS-REVIEW,
    # not NO-GO.
    metrics = metrics or {}
    core = ("recall", "far", "auroc", "rfall_at_far_020")
    metric_gap = [m for m in core if metrics.get(m) is None]
    if metric_gap:
        reasons.append(f"metric_coverage_gap:{','.join(metric_gap)}")
        return PilotVerification(status=NEEDS_REVIEW, integrity_ok=True, reasons=reasons,
                                 checkpoint_sha256=ckpt_hash, fields=resolved, metrics=metrics)

    return PilotVerification(status=VERIFIED, integrity_ok=True, reasons=["complete"],
                             checkpoint_sha256=ckpt_hash, fields=resolved, metrics=metrics)


def is_stale(*, recorded_sha256: str, checkpoint_path: Path) -> bool:
    """§3 staleness: a pilot is auto-invalid if the checkpoint's current content hash differs from
    the hash recorded when the pilot was verified (retrain-in-place hazard). Missing file = stale."""
    current = sha256_file(checkpoint_path)
    return current != recorded_sha256


@dataclass
class MatchResult:
    matched: bool
    reason: Optional[str] = None   # the specific mismatching field on a non-match (§4)


def match_command(
    *,
    command: dict[str, Any],
    pilot: dict[str, Any],
    pilot_checkpoint_sha256: str,
    current_checkpoint_sha256: Optional[str],
) -> MatchResult:
    """§4 matching: a prospective test-split command matches a verified pilot iff ALL of
    checkpoint(path+hash), run_name, seed, epsilon agree. Any partial match is a NON-match, named
    by the first failing field — never a fuzzy "close enough". This function AUTHORIZES NOTHING; it
    only reports whether a match exists so a warning can carry accurate information (design §6).

    command / pilot dicts carry: checkpoint, run_name, seed, epsilon.
    """
    # §3 staleness dominates: a pilot bound to an overwritten checkpoint is invalid before matching.
    if current_checkpoint_sha256 is None:
        return MatchResult(False, "stale_checkpoint")
    if current_checkpoint_sha256 != pilot_checkpoint_sha256:
        return MatchResult(False, "stale_checkpoint")

    if str(command.get("checkpoint")) != str(pilot.get("checkpoint")):
        return MatchResult(False, "checkpoint_path")
    if str(command.get("checkpoint_sha256")) != str(pilot_checkpoint_sha256):
        return MatchResult(False, "checkpoint_hash")
    if str(command.get("run_name")) != str(pilot.get("run_name")):
        return MatchResult(False, "run_name")
    if command.get("seed") != pilot.get("seed"):
        return MatchResult(False, "seed")
    # epsilon is a first-class identity field (§4): 0.03 != 0.015.
    if not _num_eq(command.get("epsilon"), pilot.get("epsilon")):
        return MatchResult(False, "epsilon")
    return MatchResult(True, None)


def _num_eq(a: Any, b: Any, tol: float = 1e-9) -> bool:
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return a == b


def _dominates(cand: dict[str, Any], other: dict[str, Any]) -> bool:
    """§5.4-2 dominance: `other` (a VERIFIED pilot at same ε/split) is >= cand on rfall_at_far_010
    and auroc and <= cand on clean_recall_degradation_pp, with >= 1 strict improvement.
    Returns True iff cand is dominated by other."""
    c_r = cand.get("rfall_at_far_010")
    c_a = cand.get("auroc")
    c_d = cand.get("clean_recall_degradation_pp")
    o_r = other.get("rfall_at_far_010")
    o_a = other.get("auroc")
    o_d = other.get("clean_recall_degradation_pp")
    if None in (c_r, c_a, c_d, o_r, o_a, o_d):
        return False
    ge_all = (o_r >= c_r) and (o_a >= c_a) and (o_d <= c_d)
    strict_one = (o_r > c_r) or (o_a > c_a) or (o_d < c_d)
    return ge_all and strict_one


def compute_verdict(
    *,
    metrics: dict[str, Any],
    thresholds: dict[str, float],
    reference_frontier: dict[str, float],
    prior_verified_pilots: Optional[list[dict[str, Any]]] = None,
    integrity_ok: bool = True,
) -> tuple[str, list[str]]:
    """§5 verdict. Precedence: NO-GO (integrity) -> NO-GO (perf) -> STRONG-GO -> REVIEW-GO ->
    NEEDS-REVIEW (default). Returns (verdict, reasons). NEVER authorizes a test read.

    thresholds keys (read from the acceptance contract, not inlined here):
      auroc_nogo_below, strong_rfall010_min, strong_auroc_min, strong_clean_degrade_max_pp,
      review_rfall010_lo, review_rfall010_hi, review_auroc_lo, review_auroc_hi
    reference_frontier keys: val_recall_at_far_le_10 (the existing frontier's low-FAR recall).
    """
    reasons: list[str] = []
    prior = prior_verified_pilots or []

    # §5.1 integrity NO-GO is terminal.
    if not integrity_ok:
        return NO_GO, ["integrity_failure"]

    rfall010 = metrics.get("rfall_at_far_010")
    auroc = metrics.get("auroc")
    clean_degrade = metrics.get("clean_recall_degradation_pp")
    frontier_recall = reference_frontier.get("val_recall_at_far_le_10")

    # §5.1 performance NO-GO: AUROC clearly below the NO-GO line AND low-FAR recall not improved
    # over the existing frontier.
    if auroc is not None and auroc < thresholds["auroc_nogo_below"]:
        improved = (rfall010 is not None and frontier_recall is not None
                    and rfall010 > frontier_recall)
        if not improved:
            return NO_GO, [f"auroc_below_{thresholds['auroc_nogo_below']}_and_no_lowfar_gain"]

    # §5.1 / §5.4-2 dominated NO-GO.
    for other in prior:
        if _dominates(metrics, other):
            return NO_GO, [f"dominated_by:{other.get('run_name', 'prior_pilot')}"]

    # §5.2 STRONG-GO (all required). Missing any input -> falls through to default (§5.4-1).
    if None not in (rfall010, auroc, clean_degrade):
        if (rfall010 >= thresholds["strong_rfall010_min"]
                and auroc >= thresholds["strong_auroc_min"]
                and clean_degrade <= thresholds["strong_clean_degrade_max_pp"]):
            return STRONG_GO, ["meets_strong_go_all_criteria_human_approval_still_required"]

    # §5.3 REVIEW-GO: rfall010 in [lo, hi) OR auroc in [auroc_lo, auroc_hi), AND (novel OR improves
    # low-FAR). Novelty is a human field; here we accept the improves-low-FAR operational test.
    band_rfall = (rfall010 is not None
                  and thresholds["review_rfall010_lo"] <= rfall010 < thresholds["review_rfall010_hi"])
    band_auroc = (auroc is not None
                  and thresholds["review_auroc_lo"] <= auroc < thresholds["review_auroc_hi"])
    improves_lowfar = (rfall010 is not None and frontier_recall is not None
                       and rfall010 > frontier_recall)
    if (band_rfall or band_auroc) and improves_lowfar:
        return REVIEW_GO, ["review_band_and_improves_lowfar_needs_additional_seed"]

    # §5.4-1 default bucket: anything matching no category is NEEDS-REVIEW (never guessed upward).
    reasons.append("no_category_matched_default_needs_review")
    return NEEDS_REVIEW, reasons
