"""Semantic CABT action decoding.

The engine remains authoritative: execution uses the option index supplied by
CABT. This module adds a typed semantic view without inventing a second action
ID space.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


# Verified CABT SelectType values.
SELECT_TYPE_NAMES: dict[int, str] = {
    0: "MAIN",
    1: "CARD",
    2: "ATTACHED_CARD",
    3: "CARD_OR_ATTACHED_CARD",
    4: "ENERGY",
    5: "SKILL",
    6: "ATTACK",
    7: "EVOLVE",
    8: "COUNT",
    9: "YES_NO",
    10: "SPECIAL_CONDITION",
}

# Verified CABT SelectContext values.
SELECT_CONTEXT_NAMES: dict[int, str] = {
    0: "MAIN",
    1: "SETUP_ACTIVE_POKEMON",
    2: "SETUP_BENCH_POKEMON",
    3: "SWITCH",
    4: "TO_ACTIVE",
    5: "TO_BENCH",
    6: "TO_FIELD",
    7: "TO_HAND",
    8: "DISCARD",
    9: "TO_DECK",
    10: "TO_DECK_BOTTOM",
    11: "TO_PRIZE",
    12: "NOT_MOVE",
    13: "DAMAGE_COUNTER",
    14: "DAMAGE_COUNTER_ANY",
    15: "DAMAGE",
    16: "REMOVE_DAMAGE_COUNTER",
    17: "HEAL",
    18: "EVOLVES_FROM",
    19: "EVOLVES_TO",
    20: "DEVOLVE",
    21: "ATTACH_FROM",
    22: "ATTACH_TO",
    23: "DETACH_FROM",
    24: "LOOK",
    25: "EFFECT_TARGET",
    26: "DISCARD_ENERGY_CARD",
    27: "DISCARD_TOOL_CARD",
    28: "SWITCH_ENERGY_CARD",
    29: "DISCARD_CARD_OR_ATTACHED_CARD",
    30: "DISCARD_ENERGY",
    31: "TO_HAND_ENERGY",
    32: "TO_DECK_ENERGY",
    33: "SWITCH_ENERGY",
    34: "SKILL_ORDER",
    35: "ATTACK",
    36: "DISABLE_ATTACK",
    37: "EVOLVE",
    38: "DRAW_COUNT",
    39: "DAMAGE_COUNTER_COUNT",
    40: "REMOVE_DAMAGE_COUNTER_COUNT",
    41: "IS_FIRST",
    42: "MULLIGAN",
    43: "ACTIVATE",
    44: "FIRST_EFFECT",
    45: "MORE_DEVOLVE",
    46: "COIN_HEAD",
    47: "AFFECT_SPECIAL_CONDITION",
    48: "RECOVER_SPECIAL_CONDITION",
}

# Verified CABT OptionType values.
OPTION_TYPE_NAMES: dict[int, str] = {
    0: "NUMBER",
    1: "YES",
    2: "NO",
    3: "CARD",
    4: "TOOL_CARD",
    5: "ENERGY_CARD",
    6: "ENERGY",
    7: "PLAY",
    8: "ATTACH",
    9: "EVOLVE",
    10: "ABILITY",
    11: "DISCARD",
    12: "RETREAT",
    13: "ATTACK",
    14: "END",
    15: "SKILL",
    16: "SPECIAL_CONDITION",
}


@dataclass(frozen=True)
class CardRef:
    """Physical-card identity when CABT exposes the corresponding fields."""

    card_id: int | None
    serial: int | None
    player_index: int | None


@dataclass(frozen=True)
class LegalAction:
    """Semantic view of one currently legal CABT option.

    option_index is the only execution handle. raw_option is retained so
    higher-level policies never lose engine-specific information.
    """

    option_index: int
    select_type: int
    select_type_name: str
    context: int
    context_name: str
    option_type: int
    option_type_name: str
    raw_option: Mapping[str, Any]
    card_ref: CardRef | None = None


def _optional_int(option: Mapping[str, Any], key: str) -> int | None:
    value = option.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"option[{key!r}] must be int or None")
    return value


def decode_legal_actions(
    select: Mapping[str, Any],
) -> tuple[LegalAction, ...]:
    """Decode a CABT select object into semantic actions.

    Unknown numeric enum values are preserved numerically and named as
    UNKNOWN_<value> rather than guessed.
    """
    if not isinstance(select, Mapping):
        raise TypeError("select must be a mapping")

    try:
        select_type = int(select["type"])
        context = int(select["context"])
    except (KeyError, TypeError, ValueError) as exc:
        raise TypeError("select must contain integer type and context") from exc

    options = select.get("option", [])
    if not isinstance(options, (list, tuple)):
        raise TypeError("select[option] must be a list or tuple")

    decoded: list[LegalAction] = []
    for index, option in enumerate(options):
        if not isinstance(option, Mapping):
            raise TypeError(f"option[{index}] must be a mapping")

        option_type_raw = option.get("type")
        if isinstance(option_type_raw, bool) or not isinstance(option_type_raw, int):
            raise TypeError(f"option[{index}][type] must be int")

        identity_keys = ("id", "serial", "playerIndex")
        has_identity = any(key in option for key in identity_keys)
        card_ref = (
            CardRef(
                card_id=_optional_int(option, "id"),
                serial=_optional_int(option, "serial"),
                player_index=_optional_int(option, "playerIndex"),
            )
            if has_identity
            else None
        )

        decoded.append(
            LegalAction(
                option_index=index,
                select_type=select_type,
                select_type_name=SELECT_TYPE_NAMES.get(
                    select_type, f"UNKNOWN_{select_type}"
                ),
                context=context,
                context_name=SELECT_CONTEXT_NAMES.get(
                    context, f"UNKNOWN_{context}"
                ),
                option_type=option_type_raw,
                option_type_name=OPTION_TYPE_NAMES.get(
                    option_type_raw, f"UNKNOWN_{option_type_raw}"
                ),
                raw_option=option,
                card_ref=card_ref,
            )
        )

    return tuple(decoded)
