from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from ptcg_agent.evaluation import (
    EpisodeRecord,
    EvaluationSummary,
    winner_from_result,
)


def test_episode_record_is_immutable() -> None:
    record = EpisodeRecord(
        episode=1,
        steps=20,
        terminal=False,
        result_code=-1,
        winner_index=None,
        invalid_action=False,
        error=None,
    )

    assert record.episode == 1
    assert record.steps == 20
    assert record.result_code == -1
    assert record.winner_index is None


def test_result_code_winner_mapping() -> None:
    assert winner_from_result(0) == 0
    assert winner_from_result(1) == 1
    assert winner_from_result(2) is None
    assert winner_from_result(-1) is None
    assert winner_from_result(None) is None


def test_summary_counts_are_explicit() -> None:
    records = (
        EpisodeRecord(1, 10, True, 1, 1, False, None),
        EpisodeRecord(2, 12, False, -1, None, False, "max_steps_exceeded:12"),
        EpisodeRecord(3, 4, False, -1, None, True, "ValueError: invalid action"),
    )

    summary = EvaluationSummary(
        episodes=3,
        completed=1,
        incomplete=2,
        invalid_actions=1,
        result_codes={"1": 1, "-1": 2},
        winner_counts={"1": 1},
        records=records,
    )

    assert summary.episodes == 3
    assert summary.completed == 1
    assert summary.incomplete == 2
    assert summary.invalid_actions == 1
    assert summary.result_codes["1"] == 1
    assert summary.winner_counts["1"] == 1
