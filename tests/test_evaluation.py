from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from ptcg_agent.evaluation import EpisodeRecord, EvaluationSummary


def test_episode_record_is_immutable() -> None:
    record = EpisodeRecord(
        episode=1,
        steps=20,
        terminal=False,
        result_code=-1,
        invalid_action=False,
        error=None,
    )

    assert record.episode == 1
    assert record.steps == 20
    assert record.result_code == -1


def test_summary_counts_are_explicit() -> None:
    records = (
        EpisodeRecord(1, 10, True, 1, False, None),
        EpisodeRecord(2, 12, False, -1, False, "max_steps_exceeded:12"),
        EpisodeRecord(3, 4, False, -1, True, "ValueError: invalid action"),
    )

    summary = EvaluationSummary(
        episodes=3,
        completed=1,
        incomplete=2,
        invalid_actions=1,
        result_codes={"1": 1, "-1": 2},
        records=records,
    )

    assert summary.episodes == 3
    assert summary.completed == 1
    assert summary.incomplete == 2
    assert summary.invalid_actions == 1
    assert summary.result_codes["1"] == 1
