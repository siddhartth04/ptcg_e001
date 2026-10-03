from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from ptcg_agent.decision import DecisionInput


def _observation() -> dict:
    return {
        "current": {
            "turn": 0,
            "turnActionCount": 2,
            "yourIndex": 1,
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
                    "active": [],
                    "bench": [],
                    "benchMax": 5,
                    "deckCount": 53,
                    "discard": [],
                    "prize": [],
                    "handCount": 7,
                    "hand": None,
                    "poisoned": False,
                    "burned": False,
                    "asleep": False,
                    "paralyzed": False,
                    "confused": False,
                    "win": 0,
                },
                {
                    "active": [],
                    "bench": [],
                    "benchMax": 5,
                    "deckCount": 53,
                    "discard": [],
                    "prize": [],
                    "handCount": 7,
                    "hand": [
                        {"id": 3, "serial": 118, "playerIndex": 1},
                        {"id": 723, "serial": 71, "playerIndex": 1},
                    ],
                    "poisoned": False,
                    "burned": False,
                    "asleep": False,
                    "paralyzed": False,
                    "confused": False,
                    "win": 0,
                },
            ],
        },
        "select": {
            "type": 1,
            "context": 1,
            "minCount": 1,
            "maxCount": 1,
            "option": [
                {"type": 3, "playerIndex": 1},
                {"type": 3, "playerIndex": 1},
            ],
        },
    }


def test_decision_input_bundles_state_and_actions() -> None:
    decision = DecisionInput.from_observation(_observation())

    assert decision.state.your_index == 1
    assert decision.state.first_player == 0
    assert len(decision.actions) == 2
    assert [a.option_index for a in decision.actions] == [0, 1]
    assert all(a.context_name == "SETUP_ACTIVE_POKEMON" for a in decision.actions)


def test_decision_input_does_not_expose_hidden_hand() -> None:
    decision = DecisionInput.from_observation(_observation())

    assert decision.state.players[0].hand is None
    assert decision.state.players[1].hand is not None


def test_decision_input_rejects_missing_current() -> None:
    observation = _observation()
    observation["current"] = None

    try:
        DecisionInput.from_observation(observation)
    except TypeError:
        pass
    else:
        raise AssertionError("missing current should be rejected")
