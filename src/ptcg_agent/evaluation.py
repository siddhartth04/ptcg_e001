"""Native CABT baseline evaluation harness.

Run this script only in an environment that provides the native `cg` package.
The harness records raw terminal result codes; it does not assume the meaning
of those codes until verified from the engine contract.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Mapping

from cg import game

from ptcg_agent.agent import DEFAULT_DECK, agent


@dataclass(frozen=True)
class EpisodeRecord:
    episode: int
    steps: int
    terminal: bool
    result_code: int | None
    invalid_action: bool
    error: str | None


@dataclass(frozen=True)
class EvaluationSummary:
    episodes: int
    completed: int
    incomplete: int
    invalid_actions: int
    result_codes: Mapping[str, int]
    records: tuple[EpisodeRecord, ...]


def run_episode(
    episode: int,
    deck0: list[int] | None = None,
    deck1: list[int] | None = None,
    max_steps: int = 1000,
) -> EpisodeRecord:
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
                    if raw_result != -1:
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

    completed = sum(record.terminal for record in records)
    invalid_actions = sum(record.invalid_action for record in records)

    return EvaluationSummary(
        episodes=episodes,
        completed=completed,
        incomplete=episodes - completed,
        invalid_actions=invalid_actions,
        result_codes=dict(result_codes),
        records=records,
    )
