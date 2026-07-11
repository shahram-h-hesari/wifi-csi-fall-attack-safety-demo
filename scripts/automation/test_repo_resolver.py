#!/usr/bin/env python
"""Synthetic tests for EXTERNAL-REPO-RESOLUTION.

Uses temporary local Git repositories only. No network, no real external checkout, no Research OS
migration, and no writes outside pytest tmp_path.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import repo_resolver as rr  # noqa: E402
import validate_external_repositories as ver  # noqa: E402

REMOTE = "https://github.com/example/synthetic-external.git"


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr or result.stdout
    return result.stdout.strip()


def init_repo(root: Path, *, remote: str = REMOTE) -> Path:
    root.mkdir(parents=True)
    git(root, "init")
    git(root, "config", "user.name", "Synthetic Tester")
    git(root, "config", "user.email", "synthetic@example.invalid")
    git(root, "remote", "add", "origin", remote)
    (root / "results").mkdir()
    (root / "figures").mkdir()
    (root / "scripts" / "analysis").mkdir(parents=True)
    (root / "results" / "evidence.txt").write_text("evidence\n", encoding="utf-8")
    (root / "figures" / "plot.txt").write_text("plot\n", encoding="utf-8")
    (root / "scripts" / "analysis" / "tool.py").write_text("# synthetic\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-m", "initial synthetic evidence")
    return root


def write_yaml(path: Path, doc: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return path


def registry_doc(*repos: dict, default_legacy_repository_id=None) -> dict:
    return {
        "schema_version": 1,
        "default_legacy_repository_id": default_legacy_repository_id,
        "repositories": list(repos),
    }


def repo_entry(
    repository_id="synthetic-repo",
    *,
    remote: str = REMOTE,
    dirty_policy: str = "allowed_read_only",
    required=None,
    roots=None,
) -> dict:
    return {
        "repository_id": repository_id,
        "repository_role": "experiment-and-evidence",
        "expected_remote_url": remote,
        "canonical_branch_or_ref_policy": "any branch, full commit recorded per claim",
        "provenance_commit_policy": "full 40-char SHA required",
        "required_repository_relative_paths": required or ["results/", "figures/", "scripts/analysis/"],
        "allowed_evidence_roots": roots or ["results/", "figures/"],
        "read_only_to_research_os": True,
        "git_identity_verification_required": True,
        "dirty_worktree_policy": dirty_policy,
        "claim_boundaries": [
            "registry presence does not authorize experiments",
            "registry presence does not authorize held-out-test reads",
        ],
    }


def write_registry(tmp_path: Path, doc: dict) -> Path:
    return write_yaml(tmp_path / "automation" / "registry" / "external_repositories.yaml", doc)


def write_override(tmp_path: Path, mapping: dict[str, Path | str]) -> Path:
    local_paths = {k: str(v) for k, v in mapping.items()}
    return write_yaml(
        tmp_path / "automation" / "local" / "external_repository_paths.yaml",
        {"schema_version": 1, "local_paths": local_paths},
    )


def empty_registry(tmp_path: Path) -> Path:
    return write_registry(tmp_path, registry_doc())


def tree_snapshot(root: Path) -> dict[str, str]:
    out = {}
    for path in sorted(root.rglob("*")):
        if path.is_dir() or ".git" in path.parts:
            continue
        out[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


@pytest.fixture()
def external_setup(tmp_path: Path):
    repo = init_repo(tmp_path / "external")
    registry = write_registry(tmp_path, registry_doc(repo_entry()))
    override = write_override(tmp_path, {"synthetic-repo": repo})
    return repo, registry, override


def expect_code(code: str, fn, *args, **kwargs):
    with pytest.raises(rr.RepositoryResolutionError) as exc:
        fn(*args, **kwargs)
    assert exc.value.code == code
    return str(exc.value)


def test_01_valid_same_repository_backward_compatible_resolution(tmp_path):
    repo = init_repo(tmp_path / "governance")
    registry = empty_registry(tmp_path)
    resolved = rr.resolve_legacy_evidence_path(
        "results/evidence.txt", registry_path=registry, base=repo, compute_sha256=True
    )
    assert resolved.repository.repository_id == rr.GOVERNANCE_REPOSITORY_ID
    assert resolved.repository_relative_path == "results/evidence.txt"
    assert resolved.sha256 == hashlib.sha256((repo / "results" / "evidence.txt").read_bytes()).hexdigest()


def test_02_valid_explicit_external_repository_resolution(external_setup):
    repo, registry, override = external_setup
    resolved = rr.resolve_external_evidence_path(
        "synthetic-repo", "results/evidence.txt", registry_path=registry, local_paths_path=override
    )
    assert resolved.absolute_path == repo / "results" / "evidence.txt"
    assert resolved.repository.expected_remote_url == REMOTE
    assert resolved.repository.resolved_remote_url == REMOTE
    assert resolved.repository.worktree_clean is True


def test_03_missing_tracked_registry_fails(tmp_path):
    missing = tmp_path / "missing.yaml"
    expect_code("registry_missing", rr.resolve_external_repository, "synthetic-repo", registry_path=missing)


def test_04_missing_local_override_fails_without_sibling_inference(tmp_path):
    repo = init_repo(tmp_path / "synthetic-repo")
    registry = write_registry(tmp_path, registry_doc(repo_entry()))
    missing_override = tmp_path / "automation" / "local" / "external_repository_paths.yaml"
    message = expect_code(
        "local_override_missing",
        rr.resolve_external_repository,
        "synthetic-repo",
        registry_path=registry,
        local_paths_path=missing_override,
    )
    assert "external_repository_paths.example.yaml" in message
    assert repo.exists()


def test_05_unknown_repository_id_fails(tmp_path):
    registry = write_registry(tmp_path, registry_doc(repo_entry(repository_id="known-repo")))
    expect_code("unknown_repository_id", rr.resolve_external_repository, "unknown-repo", registry_path=registry)


def test_06_missing_override_entry_fails(tmp_path):
    repo = init_repo(tmp_path / "external")
    registry = write_registry(tmp_path, registry_doc(repo_entry()))
    override = write_override(tmp_path, {"other-repo": repo})
    expect_code(
        "local_override_missing_entry",
        rr.resolve_external_repository,
        "synthetic-repo",
        registry_path=registry,
        local_paths_path=override,
    )


def test_07_invalid_local_path_fails(tmp_path):
    registry = write_registry(tmp_path, registry_doc(repo_entry()))
    override = write_override(tmp_path, {"synthetic-repo": tmp_path / "does-not-exist"})
    expect_code(
        "invalid_local_path",
        rr.resolve_external_repository,
        "synthetic-repo",
        registry_path=registry,
        local_paths_path=override,
    )


def test_08_non_git_directory_fails(tmp_path):
    not_git = tmp_path / "not-git"
    not_git.mkdir()
    registry = write_registry(tmp_path, registry_doc(repo_entry()))
    override = write_override(tmp_path, {"synthetic-repo": not_git})
    expect_code(
        "not_git_worktree",
        rr.resolve_external_repository,
        "synthetic-repo",
        registry_path=registry,
        local_paths_path=override,
    )


def test_09_remote_url_mismatch_fails(tmp_path):
    repo = init_repo(tmp_path / "external", remote="https://github.com/example/other.git")
    registry = write_registry(tmp_path, registry_doc(repo_entry(remote=REMOTE)))
    override = write_override(tmp_path, {"synthetic-repo": repo})
    expect_code(
        "remote_url_mismatch",
        rr.resolve_external_repository,
        "synthetic-repo",
        registry_path=registry,
        local_paths_path=override,
    )


def test_10_missing_required_repository_relative_path_fails(tmp_path):
    repo = init_repo(tmp_path / "external")
    registry = write_registry(tmp_path, registry_doc(repo_entry(required=["results/", "missing-required/"])))
    override = write_override(tmp_path, {"synthetic-repo": repo})
    expect_code(
        "required_path_missing",
        rr.resolve_external_repository,
        "synthetic-repo",
        registry_path=registry,
        local_paths_path=override,
    )


def test_11_full_40_character_sha_is_captured(external_setup):
    _, registry, override = external_setup
    resolved = rr.resolve_external_repository("synthetic-repo", registry_path=registry, local_paths_path=override)
    assert len(resolved.full_commit_sha) == 40
    assert rr.FULL_SHA_RE.match(resolved.full_commit_sha)


def test_12_dirty_worktree_allowed_read_only(external_setup):
    repo, registry, override = external_setup
    (repo / "results" / "evidence.txt").write_text("changed\n", encoding="utf-8")
    resolved = rr.resolve_external_repository("synthetic-repo", registry_path=registry, local_paths_path=override)
    assert resolved.worktree_clean is False
    assert "results/evidence.txt" in resolved.dirty_paths


def test_13_dirty_worktree_rejected(tmp_path):
    repo = init_repo(tmp_path / "external")
    (repo / "results" / "evidence.txt").write_text("changed\n", encoding="utf-8")
    registry = write_registry(tmp_path, registry_doc(repo_entry(dirty_policy="rejected")))
    override = write_override(tmp_path, {"synthetic-repo": repo})
    expect_code(
        "dirty_worktree_rejected",
        rr.resolve_external_repository,
        "synthetic-repo",
        registry_path=registry,
        local_paths_path=override,
    )


def test_14_dirty_worktree_allowed_with_recorded_dirty_state(tmp_path):
    repo = init_repo(tmp_path / "external")
    (repo / "results" / "evidence.txt").write_text("changed\n", encoding="utf-8")
    registry = write_registry(tmp_path, registry_doc(repo_entry(dirty_policy="allowed_with_recorded_dirty_state")))
    override = write_override(tmp_path, {"synthetic-repo": repo})
    resolved = rr.resolve_external_repository("synthetic-repo", registry_path=registry, local_paths_path=override)
    assert resolved.worktree_clean is False
    assert resolved.dirty_paths == ("results/evidence.txt",)


def test_15_absolute_evidence_path_rejected(external_setup):
    repo, registry, override = external_setup
    expect_code(
        "absolute_path_rejected",
        rr.resolve_external_evidence_path,
        "synthetic-repo",
        str(repo / "results" / "evidence.txt"),
        registry_path=registry,
        local_paths_path=override,
    )


def test_16_traversal_evidence_path_rejected(external_setup):
    _, registry, override = external_setup
    expect_code(
        "path_traversal_rejected",
        rr.resolve_external_evidence_path,
        "synthetic-repo",
        "results/../figures/plot.txt",
        registry_path=registry,
        local_paths_path=override,
    )


def test_17_symlink_escape_rejected_where_supported(external_setup, tmp_path):
    repo, registry, override = external_setup
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    link = repo / "results" / "escape.txt"
    rel = "results/escape.txt"
    try:
        os.symlink(outside, link)
    except (OSError, NotImplementedError) as exc:
        if os.name != "nt":
            pytest.skip(f"symlink unavailable: {exc}")
        outside_dir = tmp_path / "outside_dir"
        outside_dir.mkdir()
        (outside_dir / "evidence.txt").write_text("outside\n", encoding="utf-8")
        junction = repo / "results" / "escape_dir"
        made = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(junction), str(outside_dir)],
            capture_output=True,
            text=True,
            check=False,
        )
        if made.returncode != 0:
            pytest.skip(f"symlink and junction unavailable: {exc}; {made.stderr or made.stdout}")
        rel = "results/escape_dir/evidence.txt"
    expect_code(
        "symlink_escape_rejected",
        rr.resolve_external_evidence_path,
        "synthetic-repo",
        rel,
        registry_path=registry,
        local_paths_path=override,
    )


def test_18_path_outside_allowed_evidence_roots_rejected(external_setup):
    _, registry, override = external_setup
    expect_code(
        "outside_allowed_evidence_roots",
        rr.resolve_external_evidence_path,
        "synthetic-repo",
        "scripts/analysis/tool.py",
        registry_path=registry,
        local_paths_path=override,
    )


def test_19_no_sibling_folder_inference(tmp_path):
    init_repo(tmp_path / "synthetic-repo")
    registry = write_registry(tmp_path, registry_doc(repo_entry()))
    expect_code(
        "local_override_missing",
        rr.resolve_external_repository,
        "synthetic-repo",
        registry_path=registry,
        local_paths_path=tmp_path / "automation" / "local" / "external_repository_paths.yaml",
    )


def test_20_resolver_uses_no_network_or_mutating_git_commands(external_setup, monkeypatch):
    _, registry, override = external_setup
    real_run = rr.subprocess.run
    seen = []

    def recording_run(args, **kwargs):
        seen.append(tuple(args))
        return real_run(args, **kwargs)

    monkeypatch.setattr(rr.subprocess, "run", recording_run)
    rr.resolve_external_repository("synthetic-repo", registry_path=registry, local_paths_path=override)
    git_commands = [cmd[1] for cmd in seen if cmd and cmd[0] == "git"]
    assert git_commands
    assert set(git_commands) <= {"rev-parse", "remote", "status"}
    assert not (set(git_commands) & rr.MUTATING_GIT_COMMANDS)


def test_21_external_repository_worktree_bytes_unchanged_after_resolution(external_setup):
    repo, registry, override = external_setup
    before = tree_snapshot(repo)
    rr.resolve_external_evidence_path(
        "synthetic-repo", "results/evidence.txt", registry_path=registry, local_paths_path=override
    )
    assert tree_snapshot(repo) == before


def test_22_resolver_source_has_no_external_write_api():
    source = Path(rr.__file__).read_text(encoding="utf-8")
    assert ".write_text(" not in source
    assert ".write_bytes(" not in source
    assert "open(\"w\"" not in source
    assert "open('w'" not in source


def test_23_deterministic_registry_error_ordering():
    bad = {
        "schema_version": 99,
        "repositories": [
            {
                "repository_id": "bad repo",
                "repository_role": "wrong",
                "expected_remote_url": "ssh://token@example.invalid/repo.git",
                "canonical_branch_or_ref_policy": "any",
                "provenance_commit_policy": "full",
                "required_repository_relative_paths": ["/absolute"],
                "allowed_evidence_roots": ["../escape"],
                "read_only_to_research_os": False,
                "git_identity_verification_required": False,
                "dirty_worktree_policy": "whatever",
                "claim_boundaries": [],
            }
        ],
    }
    first = rr.validate_registry_doc(bad)
    second = rr.validate_registry_doc(bad)
    assert first == second
    assert first == sorted(first)


def test_24_deterministic_public_metadata_output(external_setup):
    _, registry, override = external_setup
    resolved = rr.resolve_external_repository("synthetic-repo", registry_path=registry, local_paths_path=override)
    assert rr.dump_public_metadata(resolved) == rr.dump_public_metadata(resolved)


def test_25_legacy_path_compatibility_with_exactly_one_repository(tmp_path):
    repo = init_repo(tmp_path / "external")
    registry = write_registry(tmp_path, registry_doc(repo_entry(), default_legacy_repository_id="synthetic-repo"))
    override = write_override(tmp_path, {"synthetic-repo": repo})
    resolved = rr.resolve_legacy_evidence_path(
        "results/evidence.txt", registry_path=registry, local_paths_path=override
    )
    assert resolved.repository.repository_id == "synthetic-repo"


def test_26_legacy_path_ambiguity_fails_with_multiple_repositories(tmp_path):
    registry = write_registry(
        tmp_path,
        registry_doc(repo_entry(repository_id="repo-a"), repo_entry(repository_id="repo-b")),
    )
    expect_code(
        "legacy_path_ambiguous",
        rr.resolve_legacy_evidence_path,
        "results/evidence.txt",
        registry_path=registry,
        local_paths_path=tmp_path / "unused.yaml",
    )


def test_27_registry_validator_accepts_production_zero_config():
    errors = ver.validate_paths()
    assert errors == []


def test_28_local_override_example_is_safe_and_gitignored():
    template = rr.LOCAL_PATHS_TEMPLATE_PATH.read_text(encoding="utf-8")
    assert "C:\\Users\\Hesar" not in template
    assert "<repository_id>" in template
    gitignore = (rr.DEFAULT_GOVERNANCE_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "automation/local/external_repository_paths.yaml" in gitignore


def test_29_governance_and_external_resolution_are_distinct(external_setup):
    repo, registry, override = external_setup
    governance = rr.resolve_governance_repository()
    external = rr.resolve_external_repository("synthetic-repo", registry_path=registry, local_paths_path=override)
    assert governance.repository_id == rr.GOVERNANCE_REPOSITORY_ID
    assert external.repository_id == "synthetic-repo"
    assert external.root_path == repo.resolve()
    assert governance.root_path != external.root_path


def test_30_explicit_evidence_path_missing_reports_repository_id(external_setup):
    _, registry, override = external_setup
    message = expect_code(
        "evidence_path_missing",
        rr.resolve_external_evidence_path,
        "synthetic-repo",
        "results/missing.txt",
        registry_path=registry,
        local_paths_path=override,
    )
    assert "synthetic-repo:results/missing.txt" in message


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
