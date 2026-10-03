"""Deterministic, legality-first baseline policy."""

from __future__ import annotations

from typing import Mapping, Sequence

from .contract import Decision, Selection


class LegalFirstPolicy:
    """E001 baseline: deterministic legal-action-first policy.

    The baseline does not infer undocumented action semantics. It simply returns
    the first maxCount options supplied by CABT, guaranteeing that the returned
    indices refer to the current legal option list.
    """

    def choose(self, selection: Selection) -> Decision:
        if selection.max_count == 0:
            return Decision(())
        return Decision(tuple(range(selection.max_count)))
