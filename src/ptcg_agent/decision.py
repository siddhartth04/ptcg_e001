"""Decision input boundary between CABT and policy logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .actions import LegalAction
from .state import GameState


@dataclass(frozen=True)
class DecisionInput:
    """All information a policy receives for one CABT decision.

    The simulator remains authoritative. The policy receives only the
    normalized state, current legal actions, and selection cardinality.
    """

    state: GameState
    actions: tuple[LegalAction, ...]
    min_count: int
    max_count: int

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

        min_count = select.get("minCount")
        max_count = select.get("maxCount")

        if (
            isinstance(min_count, bool)
            or not isinstance(min_count, int)
            or isinstance(max_count, bool)
            or not isinstance(max_count, int)
        ):
            raise TypeError("select cardinality must contain integer minCount/maxCount")

        if min_count < 0 or max_count < 0 or min_count > max_count:
            raise ValueError(
                f"invalid selection cardinality: minCount={min_count}, "
                f"maxCount={max_count}"
            )

        from .actions import decode_legal_actions

        actions = decode_legal_actions(select)

        if max_count > len(actions):
            raise ValueError(
                f"maxCount={max_count} exceeds action count={len(actions)}"
            )

        return cls(
            state=GameState.from_current(current),
            actions=actions,
            min_count=min_count,
            max_count=max_count,
        )

    def to_selection(self):
        """Build the legacy contract Selection view for final validation."""
        from .contract import Selection

        return Selection(
            options=tuple(action.raw_option for action in self.actions),
            min_count=self.min_count,
            max_count=self.max_count,
        )
