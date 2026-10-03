from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from ptcg_agent.actions import decode_legal_actions


def test_decode_main_actions() -> None:
    select = {
        "type": 0,
        "context": 0,
        "option": [
            {"type": 7, "id": 1145, "serial": 77, "playerIndex": 1},
            {"type": 8, "area": 2, "index": 1, "playerIndex": 1},
            {"type": 14},
        ],
        "minCount": 1,
        "maxCount": 1,
    }

    actions = decode_legal_actions(select)

    assert [a.option_index for a in actions] == [0, 1, 2]
    assert [a.option_type_name for a in actions] == ["PLAY", "ATTACH", "END"]
    assert all(a.select_type_name == "MAIN" for a in actions)
    assert all(a.context_name == "MAIN" for a in actions)

    assert actions[0].card_ref is not None
    assert actions[0].card_ref.card_id == 1145
    assert actions[0].card_ref.serial == 77
    assert actions[0].card_ref.player_index == 1


def test_decode_card_followup_context() -> None:
    select = {
        "type": 1,
        "context": 7,
        "option": [
            {"type": 3, "area": 1, "index": 11, "id": 723, "serial": 72, "playerIndex": 1},
            {"type": 3, "area": 1, "index": 18, "id": 723, "serial": 70, "playerIndex": 1},
        ],
        "minCount": 0,
        "maxCount": 1,
    }

    actions = decode_legal_actions(select)

    assert all(a.select_type_name == "CARD" for a in actions)
    assert all(a.context_name == "TO_HAND" for a in actions)
    assert [a.card_ref.card_id for a in actions if a.card_ref] == [723, 723]
    assert [a.card_ref.serial for a in actions if a.card_ref] == [72, 70]


def test_unknown_enum_values_are_preserved() -> None:
    select = {
        "type": 999,
        "context": 998,
        "option": [{"type": 997}],
        "minCount": 0,
        "maxCount": 1,
    }

    action = decode_legal_actions(select)[0]

    assert action.select_type == 999
    assert action.context == 998
    assert action.option_type == 997
    assert action.select_type_name == "UNKNOWN_999"
    assert action.context_name == "UNKNOWN_998"
    assert action.option_type_name == "UNKNOWN_997"
