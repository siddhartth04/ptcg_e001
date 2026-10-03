"""Native CABT baseline evaluation harness.

The engine's terminal result code is preserved verbatim and, using the
verified CABT contract, decoded into a winner index when applicable.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Mapping

from ptcg_agent.agent import DEFAULT_DECK, agent


# Verified CABT current.result semantics.
# -1 = ongoing
#  0 = player 0 wins
#  1 = player 1 wins
#  2 = draw
RESULT_ONGOING = -1
RESULT_PLAYER_0_WIN = 0
RESULT_PLAYER_1_WIN = 1
RESULT_DRAW = 2


def winner_from_result(result_code: int | None) -> int | None:
    """Return winner player index, or None for draw/non-terminal/unknown."""

    if result_code == RESULT_PLAYER_0_WIN:
        return 0
    if result_code == RESULT_PLAYER_1_WIN:
        return 1
    return None


@dataclass(frozen=True)
class EpisodeRecord:
    episode: int
    steps: int
    terminal: bool
    result_code: int | None
    winner_index: int | None
    invalid_action: bool
    error: str | None


@dataclass(frozen=True)
class EvaluationSummary:
    episodes: int
    completed: int
    incomplete: int
    invalid_actions: int
    result_codes: Mapping[str, int]
    winner_counts: Mapping[str, int]
    records: tuple[EpisodeRecord, ...]


def run_episode(
    episode: int,
    deck0: list[int] | None = None,
    deck1: list[int] | None = None,
    max_steps: int = 1000,
) -> EpisodeRecord:
    from cg import game

    d0 = list(DEFAULT_DECK if deck0 is None else deck0)
    d1 = list(DEFAULT_DECK if deck1 is None else deck1)

    obs, _ = game.battle_start(d0, d1)
    steps = 0
    invalid_action = False
    error: str | None = None
    terminal = False
    result_code: int | None = None

    try:
        while steps < max_steps:
            current = obs.get("current")

            if isinstance(current, Mapping):
                raw_result = current.get("result")
                if isinstance(raw_result, int):
                    result_code = raw_result
                    if raw_result != RESULT_ONGOING:
                        terminal = True
                        break

            select = obs.get("select")
            if select is None:
                break

            try:
                choice = agent(obs)
                obs = game.battle_select(choice)
            except Exception as exc:
                invalid_action = True
                error = f"{type(exc).__name__}: {exc}"
                break

            steps += 1

        if not terminal and steps >= max_steps:
            error = error or f"max_steps_exceeded:{max_steps}"

    finally:
        game.battle_finish()

    return EpisodeRecord(
        episode=episode,
        steps=steps,
        terminal=terminal,
        result_code=result_code,
        winner_index=winner_from_result(result_code) if terminal else None,
        invalid_action=invalid_action,
        error=error,
    )


def evaluate(
    episodes: int = 20,
    max_steps: int = 1000,
) -> EvaluationSummary:
    records = tuple(
        run_episode(
            episode=i + 1,
            max_steps=max_steps,
        )
        for i in range(episodes)
    )

    result_codes = Counter(
        str(record.result_code)
        for record in records
        if record.result_code is not None
    )

    winner_counts = Counter(
        str(record.winner_index)
        for record in records
        if record.winner_index is not None
    )

    completed = sum(record.terminal for record in records)
    invalid_actions = sum(record.invalid_action for record in records)

    return EvaluationSummary(
        episodes=episodes,
        completed=completed,
        incomplete=episodes - completed,
        invalid_actions=invalid_actions,
        result_codes=dict(result_codes),
        winner_counts=dict(winner_counts),
        records=records,
    )
