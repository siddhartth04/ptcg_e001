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
            "option": [{"type": 1}, {"type": 2}, {"type": 3}],
            "minCount": 1,
            "maxCount": 2,
        },
        "logs": [],
        "current": None,
    }
    out = agent(obs)
    assert out == [0, 1]
    assert all(0 <= i < 3 for i in out)


def test_zero_selection() -> None:
    obs = {"select": {"option": [], "minCount": 0, "maxCount": 0}}
    assert agent(obs) == []


def test_invalid_selection_cardinality_rejected() -> None:
    with pytest.raises(ContractError):
        agent({"select": {"option": [{"type": 1}], "minCount": 2, "maxCount": 1}})
