# PTCG AI Battle — Living Knowledge Base

> North star: use a top-tier game-AI / ML engineering standard: empirical, reproducible, hypothesis-driven, compute-aware, and honest about uncertainty.

## Operating rules

1. Facts before theories. Never convert an inference into a fact.
2. Record provenance for important claims.
3. Label assumptions explicitly and test them.
4. Keep failed experiments. They prevent repeated mistakes.
5. Never fabricate win rates, scores, runtime, memory, or other metrics.
6. Preserve known-good baselines and use controlled changes during debugging.
7. Legality and simulator integration come before strategy optimization.
8. Evaluate before optimizing.
9. Record seeds, decks, environment, commit, and configuration for meaningful experiments.
10. Treat hidden information and dynamic legal actions as first-class parts of the problem.

## 2026-10-03 — Native CABT Bring-Up

### Goal
Establish native CABT connectivity, verify the baseline deck, and characterize the real observation/action contract from the engine.

### Verified repository QA
- Public repository: `siddhartth04/ptcg_e001`.
- Kaggle offline test result supplied by the user: **8 tests passed in 0.04s**.
- The baseline deck contains exactly 60 card IDs.
- The agent returns option indices during battle.

### Native CABT package
Found in the competition input:

`/kaggle/input/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/sample_submission/sample_submission/sample_submission/cg/`

Verified files:
- `cg/game.py`
- `cg/libcg.so`

`cg` and `cg.game` import successfully after adding the competition package root to `sys.path`.

### Native API verified from competition source
- `battle_start(deck0: list[int], deck1: list[int], reverse_player=False) -> tuple[dict, cg.sim.StartData]`
- `battle_select(select_list: list[int]) -> dict`
- `battle_finish()`

From the supplied `cg/game.py` implementation:
- `battle_start` requires each deck list to have length 60.
- `battle_select` requires `list[int]`.
- Native error code 4 corresponds to selection cardinality failure.
- Native error code 5 corresponds to an out-of-range option index.
- Native error code 6 corresponds to duplicate option indices.

From the supplied competition `main.py` contract:
- Every returned index must satisfy `0 <= index < len(obs.select.option)`.
- Selection length must satisfy `minCount <= len(selection) <= maxCount`.
- Duplicate option indices are not allowed.

### Native deck result
The exact current 60-card baseline deck was passed directly to `cg.game.battle_start(deck, deck, reverse_player=False)`.

Measured result: **`battle_start()` succeeded**.

Initial native state included `select`, `logs`, `current`, and `search_begin_input`. Both players initially showed `deckCount = 60`.

Therefore the hypothesis that the current 60-card deck is intrinsically rejected by the native CABT engine is **disproved**.

Important unresolved distinction:
- The high-level `kaggle_environments.make('cabt')` run previously returned `INVALID`.
- The same deck is accepted by direct native `cg.game.battle_start()`.
- The exact reason for the wrapper-level `INVALID` result is still unresolved.
- We must not blame the deck, wrapper, or engine without a controlled test.

### Hidden information confirmed
The acting player can receive card objects in `hand`, while the opponent hand is represented as `None`.

This confirms that the observation is partially observable and that a future agent must not assume access to the opponent hand.

### Setup transitions confirmed
Native CABT automatically handled opening hands, Basic Pokemon checks, setup card movement, and prize placement during the tested sequence.

### Debugging correction: optional-selection assumption
We previously saw a selection with `minCount = 0` and `maxCount = 1` and interpreted the next step as an optional bench-placement action.

The next actual state had:
- `type = 8`
- `context = 38`
- `minCount = 1`
- `maxCount = 1`
- three options.

We then called `battle_select([])`.

Observed result: Python raised `IndexError` because the native selection was invalid for the current `minCount = 1` contract.

Correct lesson:
**Never infer that an action is optional from a previous state. Inspect the current `minCount` and `maxCount` immediately before acting.**

### Current unresolved questions
1. Exact enum mapping for `SelectType`.
2. Exact enum mapping for `SelectContext`.
3. Semantics of each option object variant such as `type`, `area`, `index`, `playerIndex`, and `number`.
4. Meaning of setup `type = 8`, `context = 38`.
5. Why the high-level CABT wrapper previously returned `INVALID` while native initialization succeeds.
6. Complete state-transition graph from setup through normal turns.
7. Terminal-state and reward semantics.
8. Search/lookahead interface and deterministic replay behavior.

### Next controlled investigation
Read the official competition `cg/api.py` definitions for `SelectType`, `SelectContext`, and the option dataclasses before making another state transition.

Reason: the official package already exposes the intended schema, so using the source is safer than guessing numeric codes from observations.

## Experiment ledger

| ID | Question | Experiment | Result | Status | Decision |
|---|---|---|---|---|---|
| E001-QA | Is the repository baseline internally consistent? | Run `pytest -q` | 8 passed in 0.04s | Verified | Keep as regression gate |
| E001-CABT-01 | Is native CABT unavailable? | Search competition input | `game.py` and `libcg.so` found | Disproved | Use native package |
| E001-CABT-02 | Is the current deck rejected by native CABT? | `battle_start(deck, deck)` | Start succeeded | Disproved | Deck is not blocked at native initialization |
| E001-CABT-03 | Does a legal first setup selection advance? | `battle_select([0])` | Succeeded | Verified | Legal indices drive native state transitions |
| E001-CABT-04 | Does a second setup selection advance? | `battle_select([0])` | Succeeded | Verified | Continue state-machine characterization |
| E001-CABT-05 | Was the later setup choice optional? | `battle_select([])` | Native error mapped to `IndexError` | Disproved | Respect current cardinality exactly |
| E001-CABT-06 | Can numeric type/context semantics be safely inferred from one observation? | Not accepted as evidence | Unproven | Open | Read official enum definitions first |

## Architecture direction

Target pipeline:

`Observation -> structured state encoder -> hidden-state belief -> legal-action encoder -> policy/value heads -> optional search -> legal action`

Important design dimensions:
- public state
- hidden-hand belief
- dynamic legal-action set
- tactical terminal search
- uncertainty
- compute budget

## Evaluation standard

No claim about strategic strength until it is measured over many games.

Required metrics:
- win rate over a fixed evaluation protocol
- matchup or deck-pair matrix
- variance or confidence intervals
- invalid-action rate
- game length
- decision latency
- memory usage
- terminal result distribution

## Research discipline

For every meaningful change:
1. Establish a baseline.
2. Change one major component.
3. Evaluate on fixed seeds or a documented sampling protocol.
4. Compare distributions rather than one anecdotal game.
5. Store reproducible artifacts.
6. Keep rejected ideas in this ledger.

## Current status

**Phase:** native simulator bring-up and environment characterization.

**Known good:** repository QA, native package discovery, native deck initialization, native selection API, basic state retrieval.

**Not yet measured:** gameplay win rate, strategic strength, policy quality, search benefit, self-play improvement.

**Current blocker:** map CABT selection enums and contexts from the supplied `api.py`, then build a reliable state-transition driver.