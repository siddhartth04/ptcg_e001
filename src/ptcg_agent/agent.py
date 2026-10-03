"""CABT competition entry agent."""

from __future__ import annotations

from typing import Any, Mapping

from .contract import ContractError, Selection, Decision, validate_decision
from .policy import LegalFirstPolicy

# Public cabt starter/default deck from the Kaggle environment source.
# 60 cards exactly; card IDs are passed directly to the engine.
DEFAULT_DECK: tuple[int, ...] = (
    721, 721,
    722, 722, 722, 722,
    723, 723, 723, 723,
    1092,
    1121, 1121,
    1145, 1145,
    1163, 1163,
    1219, 1219, 1219, 1219,
    1227, 1227, 1227, 1227,
    1262, 1262,
    *([3] * 33),
)

assert len(DEFAULT_DECK) == 60

_POLICY = LegalFirstPolicy()


def agent(obs: Mapping[str, Any]) -> list[int]:
    """Return a valid CABT action.

    Phase 1: when ``select`` is None, CABT expects a 60-card deck.
    Phase 2+: return indices into the currently supplied legal option list.
    """
    if not isinstance(obs, Mapping):
        raise ContractError("observation must be a mapping")

    selection = Selection.from_observation(obs)
    if selection is None:
        return list(DEFAULT_DECK)

    decision = _POLICY.choose(selection)
    validate_decision(selection, decision)
    return decision.as_list()
