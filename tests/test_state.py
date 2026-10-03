from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from ptcg_agent.state import GameState


def test_game_state_preserves_hidden_opponent_hand() -> None:
    current = {
        "turn": 1,
        "turnActionCount": 1,
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
        "players": [
            {
                "active": [{"id": 721, "serial": 4, "playerIndex": 0}],
                "bench": [],
                "benchMax": 5,
                "deckCount": 46,
                "discard": [],
                "prize": [None] * 6,
                "handCount": 7,
                "hand": [
                    {"id": 3, "serial": 54, "playerIndex": 0},
                ],
                "poisoned": False,
                "burned": False,
                "asleep": False,
                "paralyzed": False,
                "confused": False,
                "win": 0,
            },
            {
                "active": [{"id": 722, "serial": 65, "playerIndex": 1}],
                "bench": [],
                "benchMax": 5,
                "deckCount": 47,
                "discard": [],
                "prize": [None] * 6,
                "handCount": 6,
                "hand": None,
                "poisoned": False,
                "burned": False,
                "asleep": False,
                "paralyzed": False,
                "confused": False,
                "win": 0,
            },
        ],
    }

    state = GameState.from_current(current)

    assert state.your_index == 0
    assert state.players[0].hand is not None
    assert state.players[0].hand[0].card_id == 3
    assert state.players[0].hand[0].serial == 54

    assert state.players[1].hand is None
    assert state.players[1].hand_count == 6


def test_card_identity_and_zone_are_preserved() -> None:
    current = {
        "turn": 1,
        "turnActionCount": 1,
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
        "players": [
            {
                "active": [{"id": 721, "serial": 4, "playerIndex": 0}],
                "bench": [],
                "benchMax": 5,
                "deckCount": 46,
                "discard": [],
                "prize": [None] * 6,
                "handCount": 0,
                "hand": [],
                "poisoned": False,
                "burned": False,
                "asleep": False,
                "paralyzed": False,
                "confused": False,
                "win": 0,
            }
        ],
    }

    state = GameState.from_current(current)
    card = state.players[0].active[0]

    assert card is not None
    assert card.card_id == 721
    assert card.serial == 4
    assert card.player_index == 0
    assert card.zone == "active"


def test_state_rejects_invalid_scalar_types() -> None:
    current = {
        "turn": "1",
    }

    try:
        GameState.from_current(current)
    except TypeError:
        pass
    else:
        raise AssertionError("invalid turn type should be rejected")
