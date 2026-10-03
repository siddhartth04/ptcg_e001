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

### Debugging correction: selection-state tracking
The selection with `minCount = 0` and `maxCount = 1` was correctly identified as the setup-bench choice because the official enum later confirms `context = 2` is `SETUP_BENCH_POKEMON`.

Calling `battle_select([])` for that setup-bench state was valid and advanced the game.

The **new** state after that action was:
- `type = 8` = `COUNT`
- `context = 38` = `DRAW_COUNT`
- `minCount = 1`
- `maxCount = 1`
- options of the form `{'type': 0, 'number': 0/1/2}`

We then mistakenly treated this new state as if it were still the previous optional bench selection and called `battle_select([])`.

Observed result: Python raised `IndexError`.

The error was therefore caused by our **state-transition tracking mistake**, not by an invalid optional-bench interpretation.

Correct lesson:
**Every action must be selected from the current observation only. Never carry the previous selection's semantics into the next state.**

### Official selection semantics now verified
The supplied competition `cg/api.py` defines the numeric selection enums.

Relevant `SelectType` values:
- `MAIN = 0`: main-action choices such as play, attach, evolve, ability, discard, retreat, attack, and end.
- `CARD = 1`
- `ATTACHED_CARD = 2`
- `CARD_OR_ATTACHED_CARD = 3`
- `ENERGY = 4`
- `SKILL = 5`
- `ATTACK = 6`
- `EVOLVE = 7`
- `COUNT = 8`
- `YES_NO = 9`
- `SPECIAL_CONDITION = 10`

Relevant `SelectContext` values verified from the source:
- `SETUP_ACTIVE_POKEMON = 1`
- `SETUP_BENCH_POKEMON = 2`
- `SWITCH = 3`
- `TO_ACTIVE = 4`
- `TO_BENCH = 5`
- `TO_FIELD = 6`
- `TO_HAND = 7`
- `DISCARD = 8`
- `TO_DECK = 9`
- `TO_DECK_BOTTOM = 10`
- `TO_PRIZE = 11`
- `DAMAGE_COUNTER = 13`
- `DAMAGE_COUNTER_ANY = 14`
- `DAMAGE = 15`
- `REMOVE_DAMAGE_COUNTER = 16`
- `HEAL = 17`
- `EVOLVES_FROM = 18`
- `EVOLVES_TO = 19`
- `DEVOLVE = 20`
- `ATTACH_FROM = 21`
- `ATTACH_TO = 22`
- `DETACH_FROM = 23`
- `LOOK = 24`
- `EFFECT_TARGET = 25`
- `DISCARD_ENERGY_CARD = 26`
- `DISCARD_TOOL_CARD = 27`
- `SWITCH_ENERGY_CARD = 28`
- `DISCARD_CARD_OR_ATTACHED_CARD = 29`
- `DISCARD_ENERGY = 30`
- `TO_HAND_ENERGY = 31`
- `TO_DECK_ENERGY = 32`
- `SWITCH_ENERGY = 33`
- `SKILL_ORDER = 34`
- `ATTACK = 35`
- `DISABLE_ATTACK = 36`
- `EVOLVE = 37`
- `DRAW_COUNT = 38`
- `DAMAGE_COUNTER_COUNT = 39`
- `REMOVE_DAMAGE_COUNTER_COUNT = 40`
- `IS_FIRST = 41`
- `MULLIGAN = 42`
- `ACTIVATE = 43`

This establishes that the observed `type = 8, context = 38` state is a **draw-count selection**, not a bench-placement selection.

### Current unresolved questions
1. Complete `SelectContext` enum beyond the lines currently inspected.
2. Exact semantics of each option object variant such as `type`, `area`, `index`, `playerIndex`, and `number`.
3. Why the high-level CABT wrapper previously returned `INVALID` while native initialization succeeds.
4. Complete state-transition graph from setup through normal turns.
5. Terminal-state and reward semantics.
6. Search/lookahead interface and deterministic replay behavior.

### Next controlled investigation
Inspect the official `cg/api.py` option definitions and the remaining `SelectContext` values, then resume the state machine from the **draw-count** decision using the current `minCount/maxCount` and option semantics.

Reason: the official package already exposes the intended schema, so using the source is safer than guessing numeric codes from observations.

## Experiment ledger

| ID | Question | Experiment | Result | Status | Decision |
|---|---|---|---|---|---|
| E001-QA | Is the repository baseline internally consistent? | Run `pytest -q` | 8 passed in 0.04s | Verified | Keep as regression gate |
| E001-CABT-01 | Is native CABT unavailable? | Search competition input | `game.py` and `libcg.so` found | Disproved | Use native package |
| E001-CABT-02 | Is the current deck rejected by native CABT? | `battle_start(deck, deck)` | Start succeeded | Disproved | Deck is not blocked at native initialization |
| E001-CABT-03 | Does a legal first setup selection advance? | `battle_select([0])` | Succeeded | Verified | Legal indices drive native state transitions |
| E001-CABT-04 | Does a second setup selection advance? | `battle_select([0])` | Succeeded | Verified | Continue state-machine characterization |
| E001-CABT-05 | Could the setup-bench selection be skipped? | `battle_select([])` while current state had `context=SETUP_BENCH_POKEMON, minCount=0, maxCount=1` | Succeeded; advanced to next state | Verified | Empty selection is valid when current minCount=0 |
| E001-CABT-06 | What are `type=8` and `context=38`? | Read official `cg/api.py` | `COUNT` + `DRAW_COUNT` | Verified | Treat current state as draw-count selection |
| E001-CABT-07 | Why did `battle_select([])` fail after setup? | Replayed state sequence and inspected current selection | Empty selection was sent to a state with `minCount=1` | Verified | The failure was our state-tracking error |

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