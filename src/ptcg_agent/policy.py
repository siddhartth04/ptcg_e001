"""Deterministic, legality-first baseline policy."""

from __future__ import annotations

from .contract import Decision
from .decision import DecisionInput


class LegalFirstPolicy:
    """E001 baseline: deterministic legal-action-first policy.

    The policy consumes the canonical DecisionInput boundary. It does not
    infer undocumented action semantics; it selects the first maxCount legal
    action indices supplied by CABT.
    """

    def choose(self, decision_input: DecisionInput) -> Decision:
        if decision_input.max_count == 0:
            return Decision(())

        return Decision(
            tuple(
                action.option_index
                for action in decision_input.actions[: decision_input.max_count]
            )
        )
