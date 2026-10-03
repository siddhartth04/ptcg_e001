from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

import pytest

from ptcg_agent.agent import DEFAULT_DECK, agent
from ptcg_agent.contract import ContractError


REPO_ROOT = Path(__file__).parents[1]
DECK_PATH = REPO_ROOT / "deck.csv"


def _read_deck_csv() -> list[int]:
    return [
        int(line.strip())
        for line in DECK_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _current_for_agent_test() -> dict:
    base = {
        "turn": 0,
        "turnActionCount": 2,
        "yourIndex": 0,
        "firstPlayer": 0,
        "supporterPlayed": False,
        "stadiumPlayed": False,
        "energyAttached": False,
        "retreated": False,
        "result": -1,
        "draw": 0,
        "round": 1,
        "stadium": [],
        "looking": None,
    }

    player = {
        "active": [],
        "bench": [],
        "benchMax": 5,
        "deckCount": 53,
        "discard": [],
        "prize": [],
        "handCount": 7,
        "hand": [],
        "poisoned": False,
        "burned": False,
        "asleep": False,
        "paralyzed": False,
        "confused": False,
        "win": 0,
    }

    return {**base, "players": [player, player]}


def test_default_deck_is_60_cards() -> None:
    assert len(DEFAULT_DECK) == 60


def test_deck_csv_is_60_cards() -> None:
    card_ids = _read_deck_csv()
    assert len(card_ids) == 60
    assert all(card_id > 0 for card_id in card_ids)


def test_default_deck_matches_deck_csv() -> None:
    assert _read_deck_csv() == list(DEFAULT_DECK)


def test_deck_phase_returns_60_card_ids() -> None:
    out = agent({"select": None})
    assert out == list(DEFAULT_DECK)
    assert len(out) == 60


def test_battle_phase_returns_indices_into_legal_options() -> None:
    obs = {
        "select": {
            "type": 0,
            "context": 0,
            "option": [{"type": 14}, {"type": 14}, {"type": 14}],
            "minCount": 1,
            "maxCount": 2,
        },
        "logs": [],
        "current": _current_for_agent_test(),
    }

    out = agent(obs)

    assert out == [0, 1]
    assert all(0 <= i < 3 for i in out)


def test_zero_selection() -> None:
    obs = {
        "select": {
            "type": 0,
            "context": 0,
            "option": [],
            "minCount": 0,
            "maxCount": 0,
        },
        "current": _current_for_agent_test(),
    }
    assert agent(obs) == []


def test_invalid_selection_cardinality_rejected() -> None:
    obs = {
        "select": {
            "type": 0,
            "context": 0,
            "option": [{"type": 14}],
            "minCount": 2,
            "maxCount": 1,
        },
        "current": _current_for_agent_test(),
    }

    with pytest.raises((ContractError, ValueError)):
        agent(obs)


def test_missing_current_rejected_during_battle() -> None:
    obs = {
        "select": {
            "type": 0,
            "context": 0,
            "option": [{"type": 14}],
            "minCount": 1,
            "maxCount": 1,
        },
        "current": None,
    }

    with pytest.raises(TypeError):
        agent(obs)
