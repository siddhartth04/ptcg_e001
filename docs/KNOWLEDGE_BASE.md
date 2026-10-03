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
## 2026-10-03 — Official Option Schema Verified

The supplied competition cg/api.py defines the option schema used by CABT.

### Verified OptionType values

- NUMBER = 0: number/count selection.
- YES = 1: select yes.
- NO = 2: select no.
- CARD = 3: card selection; uses area, index, and playerIndex.
- TOOL_CARD = 4: attached Pokémon Tool; uses area, index, playerIndex, toolIndex.
- ENERGY_CARD = 5: attached Energy card; uses area, index, playerIndex, energyIndex.
- ENERGY = 6: energy selection; includes count for energy units.
- PLAY = 7: play a card from hand; uses hand index.
- ATTACH = 8: attach a card to a Pokémon; uses source area/index and target inPlayArea/inPlayIndex.
- EVOLVE = 9: evolution selection; uses evolved-card location and the in-play evolution source.

The generic Option dataclass also supports: type, number, area, index, playerIndex, toolIndex, energyIndex, count, inPlayArea, inPlayIndex, attackId, cardId, serial, specialConditionType.

### Critical action-decoding rule

The integer returned by an agent is only an index into select.option.
The semantic action must be decoded from the current select.type, select.context, and selected select.option[index].

### SelectData schema verified

SelectData contains type, context, minCount, maxCount, remainDamageCounter, remainEnergyCost, option, optional deck, optional contextCard, and optional effect.

### Additional verified SelectContext values

- 38 = DRAW_COUNT
- 39 = DAMAGE_COUNTER_COUNT
- 40 = REMOVE_DAMAGE_COUNTER_COUNT
- 41 = IS_FIRST
- 42 = MULLIGAN
- 43 = ACTIVATE
- 44 = FIRST_EFFECT
- 45 = MORE_DEVOLVE
- 46 = COIN_HEAD
- 47 = AFFECT_SPECIAL_CONDITION
- 48 = RECOVER_SPECIAL_CONDITION

Therefore the observed type=8, context=38 state is definitively a COUNT / DRAW_COUNT decision, with legal count values represented by NUMBER option objects.

### Experiment ledger addition

E001-CABT-08 — Option schema: Read official cg/api.py OptionType, Option, and SelectData definitions. Result: option objects and their fields are source-verified. Decision: never interpret an action from its index alone; use current selection metadata and the option object.

### Current unresolved questions

1. Remaining OptionType definitions after EVOLVE=9.
2. Exact semantics of MAIN, SKILL, ATTACK, and special-condition option variants.
3. Why the high-level CABT wrapper previously returned INVALID while native initialization succeeds.
4. Complete state-transition graph from setup through normal turns.
5. Terminal-state and reward semantics.
6. Search/lookahead interface and deterministic replay behavior.

### Next controlled investigation

Inspect the remainder of the official OptionType enum before taking another native action. Then resume from the real draw-count state and select a valid NUMBER option according to the current observation.

## 2026-10-03 — Complete OptionType Action Ontology Verified

The supplied competition cg/api.py now gives the complete OptionType mapping currently present in the file:

- NUMBER = 0: choose a count.
- YES = 1: choose Yes.
- NO = 2: choose No.
- CARD = 3: choose a card.
- TOOL_CARD = 4: choose an attached Pokémon Tool.
- ENERGY_CARD = 5: choose an attached Energy card.
- ENERGY = 6: choose Energy; the option can include a count of energy units.
- PLAY = 7: play a card from the hand.
- ATTACH = 8: attach a card to a Pokémon.
- EVOLVE = 9: choose an Evolution.
- ABILITY = 10: use an Ability.
- DISCARD = 11: discard a card in play.
- RETREAT = 12: retreat the Active Pokémon.
- ATTACK = 13: choose an Attack by attackId.
- END = 14: end the turn.
- SKILL = 15: select the order of card skills; cardId 0 indicates special-condition handling according to the source comments.
- SPECIAL_CONDITION = 16: select a Special Condition.

The same source also defines LogType values used for event interpretation, including SHUFFLE=0, HAS_BASIC_POKEMON=1, TURN_START=2, TURN_END=3, DRAW=4, DRAW_REVERSE=5, MOVE_CARD=6, MOVE_CARD_REVERSE=7, SWITCH=8, and CHANGE=9.

### Strategic implication
The action space is not a flat global integer action vocabulary. CABT exposes a dynamic legal-action set whose option objects encode the semantics of the currently available actions. This supports a variable-length legal-action policy head and action-conditioned scoring architecture.

### Experiment ledger addition
E001-CABT-09 — Complete OptionType ontology: Read the official cg/api.py OptionType and related LogType definitions. Result: action types 0-16 are source-verified for this competition package. Decision: build the agent around dynamic legal options plus semantic action decoding rather than a guessed fixed action table.

### Current unresolved questions
1. Exact AreaType meanings and all option fields for each action type.
2. How MAIN selection options encode PLAY, ATTACH, EVOLVE, ABILITY, DISCARD, RETREAT, ATTACK, and END.
3. Complete deck/card legality rules exposed by the simulator.
4. Why the high-level kaggle_environments wrapper previously returned INVALID while native initialization succeeds.
5. Complete state-transition graph from setup into normal turns.
6. Terminal-state and reward semantics.
7. Search/lookahead and deterministic replay behavior.

### Next controlled experiment
Resume the exact setup sequence and, when the current selection is COUNT + DRAW_COUNT with NUMBER options, inspect the current options and choose one valid number. Do not hard-code the option index across runs because the legal option set may be state-dependent.
## 2026-10-03 — Controlled Traversal Failure: Hard-Coded Setup Sequence

Experiment E001-CABT-10 attempted to replay the setup phase using a fixed sequence of native selections: `[0]`, `[0]`, `[0]`, `[0]`, `[]`.

Observed result: the sequence raised `IndexError` before the diagnostic print of the target draw-count state.

Interpretation:
- This proves the fixed sequence is not robust across fresh `battle_start()` instances.
- We do **not** yet claim the exact cause from this run alone.
- A plausible cause is randomized setup state, including opening-hand / mulligan branches, but this remains a hypothesis until observed directly.

Decision:
Do not hard-code the number or identity of setup transitions. Build the traversal around the **current observation's `select.context`, `select.type`, option schema, and cardinality** at every step.

Next diagnostic: trace every setup selection before acting, explicitly recognize `IS_FIRST`, `MULLIGAN`, `SETUP_ACTIVE_POKEMON`, `SETUP_BENCH_POKEMON`, and stop when `DRAW_COUNT` is reached. Record the actual branch rather than assuming a fixed setup path.

## 2026-10-03 — State-Driven Traversal Reached MAIN Turn State

Experiment E001-CABT-11 used a state-driven setup tracer instead of hard-coded action counts.

Observed fresh battle branch:
- Step 0: `type=YES_NO`, `context=IS_FIRST`, options YES/NO; the tracer chose YES.
- Step 1: `type=CARD`, `context=SETUP_ACTIVE_POKEMON`, Player 0; one legal option.
- Step 2: `type=CARD`, `context=SETUP_ACTIVE_POKEMON`, Player 1; one legal option.
- Step 3: `type=MAIN`, `context=MAIN`, `minCount=1`, `maxCount=1`.

The step-3 legal options were:
- indices 0-4: `ATTACH` actions from hand to the Active Pokémon.
- index 5: `PLAY` a card from hand (`index=6`).
- index 6: `END` the turn.

Interpretation: the setup phase is complete on this branch and the engine has entered a normal main-action state for the starting player.

Important correction to earlier terminology: this state is not a setup selection. It is the real turn action space. The `MAIN` selector is a higher-level action menu whose options are semantic actions such as ATTACH, PLAY, and END.

Decision: use the verified END option for the next controlled transition. This lets us validate turn handoff without introducing card-effect or attack complexity yet.

## 2026-10-03 — Setup Branch Reaches DRAW_COUNT

Experiment E001-CABT-12 used the state-driven traversal with the official selection mappings.

Observed branch:
- Step 0: `IS_FIRST` (`type=9`, `context=41`).
- Step 1: Player 1 `SETUP_ACTIVE_POKEMON`.
- Step 2: Player 0 `SETUP_ACTIVE_POKEMON`.
- Step 3: `DRAW_COUNT` (`type=8`, `context=38`) with `minCount=1`, `maxCount=1`.
- Legal NUMBER options were `0` and `1`.

This differs from the earlier branch that entered a `MAIN` action menu after setup. Therefore setup is **branch-dependent** and the earlier path to MAIN was not sufficient to characterize all setup transitions.

Current interpretation status:
- `DRAW_COUNT` semantics are source-verified.
- The exact reason this count decision appears on this branch is not yet established.
- Do not label it a mulligan decision merely from its presence; `MULLIGAN` has a separate context value of 42.

Decision: add `DRAW_COUNT` as an explicit state in the traversal driver. Before selecting a number, log the current state and recent logs so the causal setup event can be identified empirically.

## Traversal policy update

Setup traversal must be event/state driven, not sequence-count driven. Every transition is selected from the current observation. For each nonterminal state, first decode `(select.type, select.context, option[])`, then choose a test action consistent with `minCount/maxCount`.

## 2026-10-03 — Mulligan Compensation Draw State and Normal Main Menu

Experiment E001-CABT-13 reached `DRAW_COUNT` and selected `NUMBER 0`.

Observed causal evidence in the logs immediately before the draw-count state:
- `HAS_BASIC_POKEMON` for Player 0 was false.
- Cards were moved from Player 0's hand back into the deck.
- A shuffle event occurred.
- A second basic-Pokémon check became true.
- Face-down card movement events followed.

This strongly suggests the draw-count state is associated with the no-Basic-Pokémon / mulligan setup flow. However, the exact game rule meaning of the selected count has not yet been formally proven from source comments, so it remains an evidence-backed hypothesis rather than a final semantic claim.

Selecting `NUMBER 0` was accepted. The next state was:
- `SETUP_BENCH_POKEMON`, `minCount=0`, `maxCount=1`.

Selecting the empty bench choice was accepted and advanced to:
- `turn=1`
- `yourIndex=0`
- `firstPlayer=0`
- `result=-1`
- `MAIN` selection with 8 legal options.

That main menu contained:
- options 0-2: `PLAY` from hand indices 0-2.
- options 3-6: `ATTACH` actions from hand to the Active Pokémon.
- option 7: `END`.

Decision: the setup-to-normal-turn transition is now reliably traversed using current-state decoding. The next controlled test should select the verified `END` option and observe the turn handoff.

### Research discipline note
Do not encode the hypothesized mulligan/draw relationship into the agent yet. First collect multiple controlled episodes and correlate `MULLIGAN`, `DRAW_COUNT`, logs, and resulting hand/deck changes.
## 2026-10-03 — Verified END Turn Handoff

Experiment E001-CABT-14 reached a normal MAIN action state and selected the explicit END option.

Observed result:
- The starting player selected END from the MAIN menu.
- After END, `turn=2`, `yourIndex=1`, `firstPlayer=0`, `result=-1`.
- The next selection was another `MAIN` menu for Player 1.
- Recent logs included Player 0 `TURN_START`, Player 0 draw-reverse / turn-end events, then Player 1 `TURN_START` and a draw event.

The source API defines `TURN_START` and `TURN_END` as log events and `DRAW_REVERSE` / `DRAW` as draw events, supporting the interpretation that END caused the turn to hand off to the second player and that the second player's turn began with a draw. This source-backed log interpretation is recorded separately from the directly observed state values.

Decision: the normal turn-cycle transition is now verified enough to begin building a reusable environment driver. The driver should preserve the raw observation, decoded selection, chosen option, next observation, and logs at every transition.

### Architecture consequence
We now have enough evidence to introduce a semantic action decoder with a structure such as:

`Selection(type, context, minCount, maxCount, options) -> LegalAction[]`

and an executor:

`LegalAction -> option index -> cg.battle_select([index])`

Search, policy learning, and strategic scoring should operate on `LegalAction` representations rather than raw integer indices.