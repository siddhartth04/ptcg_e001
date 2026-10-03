"""Normalized CABT game-state representation.

The native CABT observation remains authoritative. This layer converts only
fields already exposed by the engine and preserves raw card dictionaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class CardInstance:
    """One observed physical card or in-play card object."""

    card_id: int | None
    serial: int | None
    player_index: int | None
    zone: str
    raw: Mapping[str, Any]

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any],
        *,
        zone: str,
    ) -> "CardInstance":
        return cls(
            card_id=value.get("id"),
            serial=value.get("serial"),
            player_index=value.get("playerIndex"),
            zone=zone,
            raw=value,
        )


@dataclass(frozen=True)
class PlayerState:
    """Normalized view of one player's currently exposed state."""

    index: int
    active: tuple[CardInstance | None, ...]
    bench: tuple[CardInstance | None, ...]
    bench_max: int
    deck_count: int
    discard: tuple[CardInstance | None, ...]
    prize: tuple[CardInstance | None, ...]
    hand_count: int
    hand: tuple[CardInstance, ...] | None
    poisoned: bool
    burned: bool
    asleep: bool
    paralyzed: bool
    confused: bool
    win: int
    raw: Mapping[str, Any]


@dataclass(frozen=True)
class GameState:
    """Normalized snapshot of CABT current state."""

    turn: int
    turn_action_count: int
    your_index: int
    first_player: int
    supporter_played: bool
    stadium_played: bool
    energy_attached: bool
    retreated: bool
    result: int
    draw: int
    round: int
    stadium: tuple[CardInstance | None, ...]
    looking: Any
    players: tuple[PlayerState, ...]
    raw: Mapping[str, Any]

    @classmethod
    def from_current(cls, current: Mapping[str, Any]) -> "GameState":
        if not isinstance(current, Mapping):
            raise TypeError("current must be a mapping")

        players_raw = current.get("players", [])
        if not isinstance(players_raw, (list, tuple)):
            raise TypeError("current['players'] must be a list or tuple")

        players = tuple(
            _parse_player(index, value)
            for index, value in enumerate(players_raw)
        )

        stadium = tuple(
            _parse_card(value, zone="stadium")
            for value in current.get("stadium", [])
        )

        return cls(
            turn=_required_int(current, "turn"),
            turn_action_count=_required_int(current, "turnActionCount"),
            your_index=_required_int(current, "yourIndex"),
            first_player=_required_int(current, "firstPlayer"),
            supporter_played=_required_bool(current, "supporterPlayed"),
            stadium_played=_required_bool(current, "stadiumPlayed"),
            energy_attached=_required_bool(current, "energyAttached"),
            retreated=_required_bool(current, "retreated"),
            result=_required_int(current, "result"),
            draw=_required_int(current, "draw"),
            round=_required_int(current, "round"),
            stadium=stadium,
            looking=current.get("looking"),
            players=players,
            raw=current,
        )


def _required_int(mapping: Mapping[str, Any], key: str) -> int:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{key!r} must be int")
    return value


def _required_bool(mapping: Mapping[str, Any], key: str) -> bool:
    value = mapping.get(key)
    if not isinstance(value, bool):
        raise TypeError(f"{key!r} must be bool")
    return value


def _parse_card(
    value: Any,
    *,
    zone: str,
) -> CardInstance | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise TypeError(f"{zone} card must be a mapping or None")
    return CardInstance.from_mapping(value, zone=zone)


def _parse_player(index: int, value: Any) -> PlayerState:
    if not isinstance(value, Mapping):
        raise TypeError(f"players[{index}] must be a mapping")

    active = tuple(
        _parse_card(card, zone="active")
        for card in value.get("active", [])
    )
    bench = tuple(
        _parse_card(card, zone="bench")
        for card in value.get("bench", [])
    )
    discard = tuple(
        _parse_card(card, zone="discard")
        for card in value.get("discard", [])
    )
    prize = tuple(
        _parse_card(card, zone="prize")
        for card in value.get("prize", [])
    )

    hand_raw = value.get("hand")
    if hand_raw is None:
        hand = None
    else:
        if not isinstance(hand_raw, (list, tuple)):
            raise TypeError(f"players[{index}]['hand'] must be list/tuple/None")
        hand = tuple(
            _parse_card(card, zone="hand")
            for card in hand_raw
        )
        if any(card is None for card in hand):
            raise TypeError("hand entries must be card mappings, not None")

    return PlayerState(
        index=index,
        active=active,
        bench=bench,
        bench_max=_required_int(value, "benchMax"),
        deck_count=_required_int(value, "deckCount"),
        discard=discard,
        prize=prize,
        hand_count=_required_int(value, "handCount"),
        hand=hand,
        poisoned=bool(value.get("poisoned", False)),
        burned=bool(value.get("burned", False)),
        asleep=bool(value.get("asleep", False)),
        paralyzed=bool(value.get("paralyzed", False)),
        confused=bool(value.get("confused", False)),
        win=_required_int(value, "win"),
        raw=value,
    )
