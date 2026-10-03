"""CABT observation/action contract helpers.

The engine presents legal options and the agent returns indices into that option
list. This module deliberately avoids inventing a global action-id space.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


class ContractError(ValueError):
    """Raised when an observation violates the expected CABT contract."""


def _as_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractError(f"{field} must be an int; got {type(value).__name__}")
    return value


@dataclass(frozen=True)
class Selection:
    """Normalized selection prompt."""

    options: tuple[Mapping[str, Any], ...]
    min_count: int
    max_count: int

    @classmethod
    def from_observation(cls, obs: Mapping[str, Any]) -> "Selection | None":
        select = obs.get("select")
        if select is None:
            return None
        if not isinstance(select, Mapping):
            raise ContractError("obs['select'] must be a mapping or None")

        options = select.get("option", [])
        if not isinstance(options, Sequence) or isinstance(options, (str, bytes)):
            raise ContractError("obs['select']['option'] must be a sequence")

        min_count = _as_int(select.get("minCount", 0), "minCount")
        max_count = _as_int(select.get("maxCount", 0), "maxCount")

        if min_count < 0 or max_count < 0 or min_count > max_count:
            raise ContractError(
                f"invalid selection cardinality: minCount={min_count}, maxCount={max_count}"
            )
        if max_count > len(options):
            raise ContractError(
                f"maxCount={max_count} exceeds option count={len(options)}"
            )

        normalized = []
        for i, option in enumerate(options):
            if not isinstance(option, Mapping):
                raise ContractError(f"option[{i}] must be a mapping")
            normalized.append(option)

        return cls(tuple(normalized), min_count, max_count)


@dataclass(frozen=True)
class Decision:
    """A selected subset of option indices."""

    indices: tuple[int, ...]

    def as_list(self) -> list[int]:
        return list(self.indices)


def validate_decision(selection: Selection, decision: Decision) -> None:
    indices = decision.indices
    if len(indices) < selection.min_count or len(indices) > selection.max_count:
        raise ContractError(
            f"selected {len(indices)} options; expected between "
            f"{selection.min_count} and {selection.max_count}"
        )
    if len(set(indices)) != len(indices):
        raise ContractError("selection contains duplicate option indices")
    if any(i < 0 or i >= len(selection.options) for i in indices):
        raise ContractError("selection contains an out-of-range option index")
