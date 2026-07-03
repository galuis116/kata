from __future__ import annotations

import json
from pathlib import Path

from kata.cli import build_parser, main
from kata.lane_state import (
    LANE_METADATA_SCHEMA_VERSION,
    EvaluatorLaneMetadata,
    write_lane_metadata,
)
from kata.submissions import init_submission


def test_top_level_cli_exposes_agent_competition_commands() -> None:
    parser = build_parser()
    subparser_action = next(
        action
        for action in parser._actions
        if getattr(action, "choices", None)
    )
    commands = set(subparser_action.choices)

    assert {"king", "submission", "lane"} == commands


def test_lane_cli_registers_and_lists_packs(tmp_path: Path, capsys) -> None:
    assert (
        main(
            [
                "lane",
                "init",
                "--lane-id",
                "sn60__bitsec",
                "--evaluator-id",
                "sn60_bitsec",
                "--public-root",
                str(tmp_path),
                "--json",
            ]
        )
        == 0
    )
    init_payload = json.loads(capsys.readouterr().out)
    assert init_payload["lane_id"] == "sn60__bitsec"

    assert (
        main(
            [
                "lane",
                "list",
                "--active-only",
                "--public-root",
                str(tmp_path),
                "--json",
            ]
        )
        == 0
    )
    list_payload = json.loads(capsys.readouterr().out)
    assert [pack["lane_id"] for pack in list_payload["packs"]] == ["sn60__bitsec"]
    assert list_payload["packs"][0]["evaluator_id"] == "sn60_bitsec"
    assert list_payload["packs"][0]["active"] is True

    registry_path = tmp_path / "lanes" / "registry.json"
    assert registry_path.exists()

    # Deactivate and confirm active-only listing excludes the lane.
    assert (
        main(
            [
                "lane",
                "init",
                "--lane-id",
                "sn60__bitsec",
                "--evaluator-id",
                "sn60_bitsec",
                "--inactive",
                "--public-root",
                str(tmp_path),
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert (
        main(
            [
                "lane",
                "list",
                "--active-only",
                "--public-root",
                str(tmp_path),
                "--json",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["packs"] == []


def test_lane_cli_accepts_subnet_pack_alias(tmp_path: Path, capsys) -> None:
    assert (
        main(
            [
                "lane",
                "init",
                "--lane-id",
                "sn60__bitsec",
                "--subnet-pack",
                "sn60__bitsec",
                "--evaluator-id",
                "sn60_bitsec",
                "--public-root",
                str(tmp_path),
                "--json",
            ]
        )
        == 0
    )
    capsys.readouterr()

    assert (
        main(["lane", "list", "--public-root", str(tmp_path), "--json"])
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["packs"][0]["subnet_pack"] == "sn60__bitsec"


def test_lane_cli_sync_registry_rebuilds_from_disk(tmp_path: Path, capsys) -> None:
    assert (
        main(
            [
                "lane",
                "init",
                "--lane-id",
                "sn60__bitsec",
                "--evaluator-id",
                "sn60_bitsec",
                "--public-root",
                str(tmp_path),
            ]
        )
        == 0
    )
    capsys.readouterr()
    (tmp_path / "lanes" / "registry.json").unlink()

    assert main(["lane", "sync-registry", "--public-root", str(tmp_path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["packs"] == ["sn60__bitsec"]


def test_submission_validate_cli_honors_public_root(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    public_root = tmp_path / "kata-root"
    write_lane_metadata(
        EvaluatorLaneMetadata(
            schema_version=LANE_METADATA_SCHEMA_VERSION,
            lane_id="sn60__bitsec",
            repo_pack="sn60__bitsec",
            mode="miner",
            evaluator_id="sn60_bitsec",
            evaluator_policy_version="v1",
            active=True,
            created_at="2026-07-01T00:00:00+00:00",
            updated_at="2026-07-01T00:00:00+00:00",
        ),
        public_root=str(public_root),
    )
    monkeypatch.setenv("KATA_ROOT", str(public_root))

    repo_root = tmp_path / "Kata"
    submission_root = init_submission(
        repo_pack="sn60__bitsec",
        mode="miner",
        submission_id="alice-20260702-01",
        output_root=str(repo_root / "submissions"),
    )
    agent_source = (
        "def agent_main(project_dir=None, inference_api=None):\n"
        "    return {\"vulnerabilities\": []}\n"
    )
    (submission_root / "agent.py").write_text(agent_source, encoding="utf-8")

    decoy_root = tmp_path / "decoy-root"
    decoy_root.mkdir()
    monkeypatch.setenv("KATA_ROOT", str(decoy_root))

    assert (
        main(
            [
                "submission",
                "validate",
                "--path",
                str(submission_root),
                "--repo-root",
                str(repo_root),
                "--public-root",
                str(public_root),
                "--json",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["reasons"] == []
    assert payload["evaluator_id"] == "sn60_bitsec"
