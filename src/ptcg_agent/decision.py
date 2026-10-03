"""Decision input boundary between CABT and policy logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Any

from .actions import LegalAction
from .state import GameState


@dataclass(frozen=True)
class DecisionInput:
    """All information a policy receives for one CABT decision.

    The simulator remains authoritative. The policy receives only the
    normalized state and the currently legal decoded actions.
    """

    state: GameState
    actions: tuple[LegalAction, ...]

    @classmethod
    def from_observation(
        cls,
        observation: Mapping[str, Any],
    ) -> "DecisionInput":
        if not isinstance(observation, Mapping):
            raise TypeError("observation must be a mapping")

        current = observation.get("current")
        if not isinstance(current, Mapping):
            raise TypeError("observation['current'] must be a mapping")

        select = observation.get("select")
        if not isinstance(select, Mapping):
            raise TypeError("observation['select'] must be a mapping")

        from .actions import decode_legal_actions

        return cls(
            state=GameState.from_current(current),
            actions=decode_legal_actions(select),
        )
