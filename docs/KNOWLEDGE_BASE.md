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
## 2026-10-03 — E001-CABT-15: Decoder Namespace Error

Experiment E001-CABT-15 attempted to inspect the semantic MAIN action menu using the official enum classes.

Observed result:
- Setup traversal itself succeeded through `IS_FIRST`, two `SETUP_ACTIVE_POKEMON` decisions, and optional `SETUP_BENCH_POKEMON`.
- The inspection code then raised `AttributeError: type object 'OptionType' has no attribute 'MAIN'`.

Root cause:
- `MAIN` is a member of `SelectType`, not `OptionType`.
- `SelectType.MAIN = 0` identifies the selection mode/context.
- `OptionType` contains the candidate action types such as `PLAY`, `ATTACH`, and `END`.

Decision:
Keep these namespaces strictly separated in the decoder:
`selection.type -> SelectType`; `selection.context -> SelectContext`; `selection.option[i].type -> OptionType`.

This was a code-level namespace mistake in our probe, not an engine failure and not a simulator finding.

Next step: rerun the same semantic-main probe with `SelectType.MAIN` for the selection type and `OptionType.*` only for option types.
## 2026-10-03 — E001-CABT-16: Semantic MAIN Decoder Verified

The corrected semantic decoder successfully reached a real Player 0 MAIN state without error.

Observed state:
- `turn=1`
- `yourIndex=0`
- `handCount=7`
- visible hand contained six copies of Card ID 3 and one Card ID 723.

Observed legal MAIN options:
- options 0-5 were `OptionType.ATTACH` from `area=2`, indices 0-5, targeting `inPlayArea=4`, `inPlayIndex=0`.
- option 6 was `OptionType.END`.

This confirms at runtime that the same integer option index can now be translated into a semantic action using the official `OptionType` schema. It also demonstrates that the legal action set is state-dependent: only actions currently legal are exposed.

Important boundary:
- We have not yet independently mapped numeric `AreaType` values 2 and 4 from the official enum in this ledger.
- We therefore describe them as source/target areas rather than assigning names such as HAND or ACTIVE until the enum is verified.

Decision:
The next implementation layer should formalize a typed `LegalAction` representation while preserving the raw option object for execution. Area mappings must be verified before hard-coded semantic labels are introduced.
## 2026-10-03 — E001-CABT-17: AreaType Mapping Verified

The official competition `cg/api.py` defines the relevant card/field locations:

- `DECK = 1`
- `HAND = 2`
- `DISCARD = 3`
- `ACTIVE = 4`
- `BENCH = 5`
- `PRIZE = 6`
- `STADIUM = 7`
- `ENERGY = 8`
- `TOOL = 9`
- `PRE_EVOLUTION = 10`
- `PLAYER = 11`
- `LOOKING = 12`

This confirms the runtime semantic-main observation from E001-CABT-16:
- `area=2` means HAND.
- `inPlayArea=4` means ACTIVE.

Therefore an observed option such as `{'type': 8, 'area': 2, 'index': 0, 'inPlayArea': 4, 'inPlayIndex': 0}` can now be decoded as an `ATTACH` action from hand index 0 to the Active Pokémon at index 0.

Decision: the semantic decoder can now use official names for these AreaType values instead of leaving them as anonymous numeric areas.

### Architecture checkpoint
We now have source-verified mappings for:
- selection mode (`SelectType`)
- selection context (`SelectContext`)
- candidate action/object type (`OptionType`)
- card/field location (`AreaType`).

This is sufficient to begin implementing the reusable `LegalAction` abstraction while keeping raw CABT dictionaries preserved for exact execution/debugging.
## 2026-10-03 — E001-CABT-18: ATTACH Transition Verified

Experiment E001-CABT-18 executed the first legal ATTACH action from a real MAIN state.

Before ATTACH:
- `turn=1`
- `yourIndex=0`
- Active Pokémon: Card ID 721, HP 150/150.
- Hand contained seven cards.
- MAIN exposed multiple ATTACH actions, PLAY actions, and END.

Selected action:
- MAIN option 0.
- Raw option: `type=8`, `area=2`, `index=1`, `inPlayArea=4`, `inPlayIndex=0`.
- With the verified AreaType enum, this decodes to ATTACH from `HAND[1]` to `ACTIVE[0]`.

After ATTACH:
- `energyAttached=True`.
- The selected hand card disappeared from the hand.
- The Active Pokémon gained one Energy entry and one `energyCards` entry.
- The next MAIN menu contained the remaining PLAY actions plus END; the manual Energy attachment was no longer offered as an ATTACH action.
- Recent logs contained a log entry with the attached card and its target Pokémon.

Directly observed state transition:
`Hand[1] -> Active[0].energyCards`, with the turn-level `energyAttached` flag changing from false to true.

Decision:
The semantic LegalAction representation should retain both source/target locations and the underlying option index. After execution, the environment state should be treated as authoritative rather than inferred from the action.

### Next controlled experiment
Test a PLAY action using one of the currently exposed PLAY options. Choose an Item/basic card only if its option is actually exposed by CABT; do not infer playability from card type alone.
## 2026-10-03 — E001-CABT-19: PLAY Can Create a Follow-Up Deck Selection

Experiment E001-CABT-19 executed a PLAY option from a verified MAIN state.

Before PLAY:
- `turn=1`, `yourIndex=0`, `handCount=7`.
- MAIN exposed four PLAY options among its legal actions.
- The selected PLAY action was `option[0] -> PLAY hand[0]`, where hand[0] was Card ID 1145.

After PLAY:
- `handCount` became 6.
- The observation returned `select.type=1` (`CARD`).
- The selection context was `7` (`TO_HAND`).
- `minCount=0`, `maxCount=1`.
- The legal options were CARD objects located in `area=1` (`DECK`) at indices 7, 13, and 29.
- The observation included a populated `deck` list and `effect` identifying Card ID 1145 as the effect currently being processed.
- A recent log recorded a skill/effect event for Card ID 1145.

This directly verifies that a MAIN `PLAY` action can create a **multi-stage action sequence**: selecting the card to play is not necessarily the entire effect. CABT can immediately expose a follow-up selection driven by the played card's effect.

Important consequence for architecture:
- A LegalAction abstraction must support the current selection as a transient sub-action within a larger card-effect sequence.
- The environment state, including `select.deck` and `select.effect`, must be preserved.
- A policy cannot assume that every PLAY action returns directly to MAIN.

Unresolved in this experiment:
- We have not yet decoded the exact game-card meaning of Card ID 1145 from the card reference data.
- We have not yet tested whether choosing one of the deck options or choosing the allowed empty selection leads to different follow-up states.

Decision: for the next controlled test, choose the first exposed DECK card option (`select.option[0]`) so that we can observe the successful completion of this multi-stage PLAY effect. Do not infer strategic quality from this choice.
## 2026-10-03 — E001-CABT-20: PLAY Effect Completion Verified

Experiment E001-CABT-20 completed the follow-up selection created by PLAYing Card ID 1145.

Observed sequence:
- MAIN option selected: `PLAY hand[0]`, where hand[0] was Card ID 1145.
- CABT generated `CARD + TO_HAND` with `minCount=0`, `maxCount=1` and four legal cards from the deck.
- The first legal deck card option was selected.

After the effect:
- Card ID 1145 was in the discard pile.
- Player hand count increased from 6 to 7.
- Deck count decreased from 46 to 45.
- The selected deck card, Card ID 723, moved from deck to hand.
- Recent logs explicitly contained a `MOVE_CARD` event for Card ID 723 from `DECK` to `HAND`, followed by the effect completion log.
- CABT returned to a normal `MAIN` action menu.

This verifies that a card PLAY can have a multi-step effect whose final state mutation is entirely observable through the returned state and logs.

### State-machine consequence
A gameplay driver must support a loop of arbitrary selections until the card effect is complete. It must not assume `PLAY -> MAIN`.

### Architecture consequence
The future environment adapter should record, for every transition:
- pre-observation
- decoded selection metadata
- chosen option index
- chosen semantic option
- post-observation
- logs emitted by the transition.

Decision: the simulator adapter is now the next engineering priority. Once this trace layer is implemented and tested, strategic policies can be plugged into the same environment without rewriting the execution logic.
## 2026-10-03 — E001-CABT-21: Native Card Metadata Confirms Mega Signal Effect

Experiment E001-CABT-21 queried CABT's native `all_card_data()` for Card ID 1145.

Native result:
- `cardId = 1145`
- `name = Mega Signal`
- `cardType = 1` (the native CardType enum identifies this as ITEM)
- `skills = [Skill(name='Mega Signal', text='Search your deck for a Mega Evolution Pokémon {ex}, reveal it, and put it into your hand. Then, shuffle your deck.')]`
- `attacks = []`

Interpretation:
The previous observed PLAY -> `CARD + TO_HAND` -> DECK-selection transition now has an exact native-card explanation: Card ID 1145 activates Mega Signal, which searches the deck for a Mega Evolution Pokémon ex, reveals it, puts it into the hand, and then shuffles the deck.

This is stronger evidence than inferring the card effect solely from the observed state transition. The simulator's own card database is now the primary runtime semantic source for supported card metadata.

Decision:
Introduce a card-metadata cache sourced from CABT `all_card_data()` for simulator-facing execution/debugging. Keep the uploaded English card dataset as a separate canonical reference layer; do not silently merge or overwrite one source with the other.

### Architecture consequence
We now have three distinct semantic layers:
1. CABT raw observation/action data.
2. CABT native card metadata and effect definitions.
3. External/reference card catalog used for analysis, feature engineering, and audit.

Any disagreement between layer 2 and layer 3 should be logged as a data-quality discrepancy, not silently reconciled.
## 2026-10-03 — E001-CABT-22: PLAY Identity Binding Error

Experiment E001-CABT-22 attempted to validate Mega Signal candidate semantics by selecting the first PLAY option from a fresh random battle and then assuming the resulting effect was Mega Signal.

Observed result:
- The resulting state was already a `MAIN` selection.
- It contained ATTACH options and END.
- `select.effect` was `None`.
- The follow-up options were `ATTACH`, not `CARD + TO_HAND` deck-search options.

Conclusion:
The experiment did not establish anything about Mega Signal candidates because the code failed to verify that the selected PLAY option actually referenced Card ID 1145. The fresh battle's hand/action set was randomized, so the first PLAY option can represent a different card.

This is an important research correction: semantic labels must be bound to the actual selected card identity before interpreting an effect. A variable or experiment name such as `mega_signal_followup` is not evidence.

Decision:
For card-specific experiments, first enumerate the acting player's hand and all legal PLAY options, resolve each PLAY option's hand index to its actual Card ID, and only execute the option when the target Card ID matches the intended card.

### Experiment status
E001-CABT-22 is **invalid as a Mega Signal test** and must not be used as evidence for or against the Mega Signal candidate hypothesis.
## 2026-10-03 — E001-CABT-23: Mega Signal Action Identity Verified

Experiment E001-CABT-23 searched fresh native battles until the actual acting-player hand and legal MAIN action were inspected before execution.

Target card:
- Card ID 1145 = Mega Signal.

Observed successful binding:
- `hand[0]` contained Card ID 1145.
- MAIN option `[0]` was `{'type': 7, 'index': 0}`.
- Therefore option 0 was proven to mean `PLAY hand[0]` for this specific state.
- A separate PLAY option targeted Card ID 1262, demonstrating why selecting the first PLAY option without checking identity is unsafe.

Decision:
Card-specific experiments must resolve `option.index` against the current acting player's hand and verify the Card ID before executing or interpreting the action.

E001-CABT-22 remains invalid as a Mega Signal test; E001-CABT-23 is the first clean identity-bound Mega Signal setup.

Next controlled experiment: execute exactly the verified Mega Signal PLAY option and inspect its follow-up selection and candidate card identities without selecting a candidate.
## 2026-10-03 — E001-CABT-24: Target-Locator Traversal Bug

Experiment E001-CABT-24 attempted to execute Card ID 1145 (Mega Signal) after locating a legal PLAY action.

Observed result: the code reached a MAIN state but raised `RuntimeError: Unexpected state while locating Mega Signal` instead of continuing.

Root cause:
- The locator only knew how to process setup contexts.
- Once the battle entered a normal MAIN state where Mega Signal was not currently playable/located, it treated MAIN as an error instead of a valid state requiring a deliberate control action.

This is a driver bug, not evidence about Mega Signal or CABT.

Decision:
Card-specific search drivers must handle MAIN states explicitly. If the target action is not currently exposed, the driver should either continue via a controlled legal MAIN action (for example END) or report that the target is unavailable in the current state. It must never classify a valid MAIN observation as an unexpected setup state.

Next controlled experiment: build a target-aware traversal that handles setup states, recognizes MAIN, resolves PLAY options against the actual hand, executes only Card ID 1145 when exposed, and otherwise ends the turn to continue the search.
## 2026-10-03 — E001-CABT-25: Native Mega Signal Candidate Binding

Experiment E001-CABT-25 used the target-aware traversal and only executed PLAY when the current hand actually contained Card ID 1145.

Observed path:
- The driver reached normal MAIN states and used controlled END actions until the target became legal.
- At turn 11, Player 0 had Card ID 1145 at `hand[11]`.
- MAIN option 11 was `PLAY hand[11]`.
- This was explicitly verified against the actual hand card before execution.

After executing the verified Mega Signal action:
- CABT returned `CARD + TO_HAND` (`type=1`, `context=7`).
- `minCount=0`, `maxCount=1`.
- Exactly one legal CARD option was exposed: `{'type': 3, 'area': 1, 'index': 34, 'playerIndex': 0}`.
- `select.deck` was present and the current effect was explicitly `Card ID 1145`.

This is the first clean run where the observed follow-up is definitely tied to Mega Signal, eliminating the identity-binding problem from E001-CABT-22.

The actual candidate card at `deck[34]` is visible in the returned deck array as Card ID 723. The native semantic predicate for that candidate has not yet been checked in this experiment.

Decision: the next controlled step is to inspect `followup.deck[34]` and compare its native card metadata (`megaEx`, name, card type) without selecting it. This will directly test the Mega Signal legality invariant.
## 2026-10-03 — E001-CABT-26: Mega Signal Candidate Invariant Verified

Experiment E001-CABT-26 executed only after a legal PLAY action for the actual Card ID 1145 was verified.

Observed target:
- Mega Signal was found at `hand[5]` on Player 1's turn (`turn=2`).
- MAIN option 4 was verified as `PLAY hand[5]` for Card ID 1145.

Observed effect resolution:
- Follow-up selection was `CARD + TO_HAND`.
- `minCount=0`, `maxCount=1`.
- Three legal CARD options were exposed.
- The active effect was explicitly Card ID 1145 / Mega Signal.

Candidate verification:
- Option 0 referenced `deck[18]` -> Card ID 723 -> Mega Abomasnow ex -> `megaEx=True`.
- Option 1 referenced `deck[29]` -> Card ID 723 -> Mega Abomasnow ex -> `megaEx=True`.
- Option 2 referenced `deck[36]` -> Card ID 723 -> Mega Abomasnow ex -> `megaEx=True`.

Result:
All three legal Mega Signal candidates observed in this episode satisfied the native `megaEx=True` predicate. This verifies the intended candidate-filter invariant for this episode.

Important scope limitation:
This is an episode-level invariant, not yet a proof across all decks/states/cards. We need additional controlled samples before turning it into a global simulator invariant.

Decision:
Add a semantic constraint to the card-effect layer: when the active effect is Mega Signal, candidate actions should be represented as selecting a deck card whose native metadata satisfies `megaEx=True`. The final legal-option set from CABT remains authoritative.
## 2026-10-03 — E001-CABT-27: Card Identity Probe Incomplete

Experiment E001-CABT-27 verified native metadata for Card ID 723:
- `cardId = 723`
- `name = Mega Abomasnow ex`
- `cardType = 0`
- `stage1 = True`
- `megaEx = True`

However, the experiment did **not** actually inspect multiple physical instances or their serial numbers. The final printed message only described the intended check; no serial-level evidence was collected.

Decision:
Do not claim that Card ID 723 instances have distinct serials based on E001-CABT-27. The question remains open and requires an observation containing multiple physical card instances with both `id` and `serial` visible.

### Research discipline
A test description or print statement is not a result. Only emitted observations count as evidence.
## 2026-10-03 — E001-CABT-28: Physical Card Identity Verified

Experiment E001-CABT-28 directly inspected all visible instances of Card ID 723 during a verified Mega Signal effect.

Observed instances:
- `deck[11]` -> Card ID 723, serial 72, Player 1.
- `deck[18]` -> Card ID 723, serial 70, Player 1.
- `deck[27]` -> Card ID 723, serial 69, Player 1.

Measured result:
- 3 physical instances of the same Card ID were visible.
- Their serials were `[72, 70, 69]`.
- `len(serials) == len(set(serials))` was `True`.
- Native card identity for Card ID 723 is Mega Abomasnow ex.

Conclusion:
Within this observed battle state, Card ID identifies the card definition while serial identifies the physical card instance. This is directly supported by the observed `(cardId, serial, playerIndex)` tuples.

Scope limitation:
This is an observed-engine invariant for the tested battle state; the implementation should nevertheless preserve both `cardId` and `serial` whenever either is available.

Decision:
The simulator adapter's internal card-instance representation should retain at least `card_id`, `serial`, and `player_index`, with zone/location maintained separately by the observation.

### Architecture milestone
We now have enough verified ontology to begin implementing the semantic simulator adapter and typed LegalAction model. The adapter should be designed around immutable raw observations plus decoded views, not a second hand-written game state that can drift from CABT.

## 2026-10-03 — E001-CABT-29: Semantic Action Decoder Tests

Repository test suite was executed after adding `src/ptcg_agent/actions.py` and `tests/test_actions.py`.

Measured result:
- `pytest -q` => **8 passed**.
- No test failures were observed.

The existing 6 contract tests plus the new semantic action decoder coverage therefore pass together.

Decision:
- Treat the semantic decoder as the current tested foundation for the next policy-layer integration.
- Do not claim runtime-game correctness from unit tests alone; the decoder still needs integration validation against real CABT observations.


## 2026-10-03 — E001-CABT-30: Live CABT Action Decoder Integration

The semantic decoder was run against a real native CABT `select` object returned by `game.battle_start()`.

Observed live selection:
- `SelectType.YES_NO = 9`
- `SelectContext.IS_FIRST = 41`
- `minCount = 1`
- `maxCount = 1`
- 2 legal options.

Decoded options:
- option 0 -> `YES`
- option 1 -> `NO`

Measured result:
- Raw engine observation was successfully accepted by `decode_legal_actions()`.
- Both legal options were decoded with the verified semantic enum names.
- Decoder returned exactly 2 actions, matching the engine's option count.
- Native battle memory was released successfully.

Conclusion:
The decoder is now validated on both unit fixtures and one live native CABT observation. This establishes the first engine-integration checkpoint, but not yet broad coverage across selection types/contexts.

Next controlled integration target:
Advance the same native battle through the verified YES branch and decode the resulting setup selection without interpreting or altering its semantics.


## 2026-10-03 — E001-CABT-31: Live Setup-Active Decoder Integration

A real native CABT battle was advanced through the verified initial `YES` selection and the resulting setup-active selection was decoded.

Observed live selection:
- `SelectType.CARD = 1`
- `SelectContext.SETUP_ACTIVE_POKEMON = 1`
- `minCount = 1`
- `maxCount = 1`
- 2 legal options.

Decoded options:
- option 0 -> `CARD`
- option 1 -> `CARD`

Both options exposed `playerIndex = 0`, while `card_id` and `serial` were absent/decoded as `None`.

Measured result:
- The decoder successfully handled a second live selection type/context.
- It preserved the absence of physical-card identity instead of inventing card IDs or serials.

Conclusion:
Not every CABT legal option exposes card identity fields. The semantic layer must treat `card_id`, `serial`, and `player_index` as optional metadata, while retaining the raw option as authoritative.

Next controlled integration target:
Select one verified setup-active option and decode the resulting state, recording only the next live selection schema.


## 2026-10-03 — E001-CABT-32: Repeated Setup-Active Selection Observed

After selecting the first option from a live `CARD / SETUP_ACTIVE_POKEMON` selection, the native engine returned another live selection with the same schema:

- `SelectType.CARD = 1`
- `SelectContext.SETUP_ACTIVE_POKEMON = 1`
- `minCount = 1`
- `maxCount = 1`
- exactly 1 legal option.
- The option again exposed `playerIndex = 0` and no `card_id` or `serial`.

Measured result:
- The same selection type/context can occur consecutively.
- A repeated selection schema must not be interpreted as a state-transition guarantee by the decoder.
- The decoder correctly preserved the missing physical-card identity fields.

Important limitation:
This observation alone does not establish whether the repeated selection belongs to another setup participant, a remaining setup requirement, or another engine-level setup branch. That interpretation remains unverified.

Next controlled integration target:
Select the sole option and inspect the following native selection/log state, including `current` and `logs`, before assigning semantic meaning.


## 2026-10-03 — E001-CABT-33: Setup Completion Reaches Draw-Count Selection

After the second observed setup-active selection was resolved, the native engine exposed a new live selection:

- `SelectType.COUNT = 8`
- `SelectContext.DRAW_COUNT = 38`
- `minCount = 1`
- `maxCount = 1`
- 3 legal options.
- Each decoded option had `OptionType.NUMBER = 0`.

The accompanying live `current` snapshot showed:
- `turn = 0`
- `yourIndex = 1`
- `firstPlayer = 0`
- player 0 had `handCount = 6`, `active = [None]`, `deckCount = 47`.
- player 1 had `handCount = 6`, `active = [None]`, `deckCount = 47`.

The live logs also showed a setup branch in which player 0 initially had `hasBasicPokemon = False`, cards were moved from hand back to deck, a new hand was drawn, then `hasBasicPokemon = True`, followed by active/prize setup. These observations are recorded as raw engine evidence only; the exact rule interpretation of the draw-count branch is not yet finalized.

Measured result:
- The decoder successfully crossed into COUNT/DRAW_COUNT.
- Three legal choices were preserved as NUMBER options.
- The semantic decoder alone does not yet expose the numeric value of each NUMBER option; the raw option must be inspected.

Next controlled integration target:
Inspect the three raw NUMBER options and record their `number` values without selecting one yet.


## 2026-10-03 — E001-CABT-34: Setup-Bench Branch Prevented Clean DRAW_COUNT Capture

A controlled traversal intended to stop at `SelectType.COUNT / SelectContext.DRAW_COUNT` did not reach that state.

Observed path:
- Step 0: `YES_NO / IS_FIRST`
- Step 1: `CARD / SETUP_ACTIVE_POKEMON`
- Step 2: `CARD / SETUP_ACTIVE_POKEMON`
- Step 3: `CARD / SETUP_BENCH_POKEMON`
- Step 4: `CARD / SETUP_BENCH_POKEMON`
- Step 5: `MAIN / MAIN`

At both setup-bench states, the traversal selected option `[0]` rather than taking the optional zero-selection branch when permitted.

Measured result:
- The expected DRAW_COUNT state was not reached.
- The resulting MAIN selection contained 5 legal options: PLAY, ATTACH, PLAY, ATTACH, END.
- This run provides evidence that setup traversal is branch-sensitive, but does not by itself establish the exact causal rule because the episode also depends on engine state/randomization.

Correction:
- The intended DRAW_COUNT probe must preserve the verified optional-bench no-op path by selecting `[]` whenever `SETUP_BENCH_POKEMON` has `minCount = 0`.
- No DRAW_COUNT numeric semantics should be inferred from this run.

Next controlled integration target:
Repeat the traversal while taking the zero-selection branch at optional setup-bench prompts and stop immediately when DRAW_COUNT appears.


## 2026-10-03 — E001-CABT-35: DRAW_COUNT Is a Conditional Setup Branch

A second controlled traversal using the optional-bench no-op policy again did not reach `DRAW_COUNT`.

Observed path:
- Step 0: `YES_NO / IS_FIRST`
- Step 1: `CARD / SETUP_ACTIVE_POKEMON`
- Step 2: `CARD / SETUP_ACTIVE_POKEMON`
- Step 3: `MAIN / MAIN`

The resulting MAIN selection contained:
- ATTACH at hand index 2
- ATTACH at hand index 4
- ATTACH at hand index 6
- END

Measured result:
- The path reached normal MAIN directly after active setup.
- Therefore `DRAW_COUNT` is not a mandatory successor of setup-active selection.
- The earlier observed `DRAW_COUNT` state is best treated as a conditional branch until a controlled trigger is isolated.
- We should not keep forcing a traversal path toward DRAW_COUNT by assuming fixed setup transition sequences.

Methodological decision:
Switch from path-forcing to branch discovery. Sample fresh native battles and record the first selection type/context after setup completion. Continue until a genuine DRAW_COUNT occurrence is observed, then inspect its raw NUMBER options without selecting one.

No numeric interpretation of DRAW_COUNT has been established yet.


## 2026-10-03 — E001-CABT-36: DRAW_COUNT Raw Number Choices Captured

A 20-episode native-battle branch-discovery probe was run using the current verified setup traversal.

Measured result:
- DRAW_COUNT occurred in 14 of 20 episodes under this exact probe procedure.
- 6 episodes reached MAIN before DRAW_COUNT.
- This 14/20 figure is an observation of this probe, not a general probability estimate.

Every observed DRAW_COUNT selection had:
- `SelectType.COUNT = 8`
- `SelectContext.DRAW_COUNT = 38`
- `minCount = 1`
- `maxCount = 1`
- `OptionType.NUMBER = 0` for every option.

Observed raw numeric choices included:
- `[0, 1]`
- `[0, 1, 2]`
- `[0, 1, 2, 3]`
- `[0, 1, 2, 3, 4]`
- `[0, 1, 2, 3, 4, 5]`

Thus the option's `number` field is demonstrably part of the executable choice payload for DRAW_COUNT.

What remains unverified:
- The exact semantic meaning of the selected number has not yet been established.
- The varying maximum number has not yet been causally tied to a specific game-state quantity.
- No strategic conclusion should be drawn from the observed 14/20 frequency.

Next controlled integration target:
Select a known DRAW_COUNT numeric option in a fresh episode and compare the immediate before/after `current`, `logs`, hand count, and deck count to identify the engine-level effect of the chosen number.


## 2026-10-03 — E001-CABT-37: DRAW_COUNT Number 0 Transition Measured

A fresh native battle reached `COUNT / DRAW_COUNT` with options `[0, 1, 2]`. The probe selected the raw `number = 0` option.

Before selection:
- `turn = 0`
- acting player `yourIndex = 0`
- player 0: `handCount = 6`, `deckCount = 47`, `active = [None]`
- player 1: `handCount = 6`, `deckCount = 47`, `active = [None]`

After selecting number 0:
- `turn = 1`
- acting player remains `yourIndex = 0`
- player 0 active became Card ID 721, serial 4, HP 150/150
- player 1 active became Card ID 722, serial 65, HP 90/90
- player 0 `handCount = 7`
- player 0 `deckCount = 46`
- player 0 received Card ID 1121, serial 15 in hand
- opponent hand remained hidden.

Measured change:
- Player 0 hand increased by exactly 1 and deck decreased by exactly 1.
- The battle advanced from setup (`turn = 0`) to `turn = 1`.
- No new logs were emitted by the returned `logs` slice used in this probe.

Interpretation status:
- Directly measured: selecting number 0 is followed by one card entering the active player's hand and a transition to turn 1.
- Plausible but not yet isolated: number 0 may mean zero additional compensation/mulligan cards, with the observed one-card increase being the normal turn draw.
- The experiment does NOT establish that the number field itself caused the one-card draw.

Next controlled experiment:
Repeat on a genuine DRAW_COUNT branch, select `number = 1), and compare hand/deck changes against the number-0 baseline. This isolates whether the numeric choice changes the draw amount.


## 2026-10-03 — E001-CABT-38: DRAW_COUNT Number 1 Matches Number 0 Immediate Delta

A fresh native battle reached `COUNT / DRAW_COUNT` with options `[0, 1]`. The probe selected raw `number = 1`.

Measured before/after state for the acting player:
- Hand: `6 -> 7`, delta `+1`.
- Deck: `47 -> 46`, delta `-1`.
- Turn: `0 -> 1`.

The resulting active player received Card ID 722, serial 7 in the active zone, and Card ID 722, serial 8 entered the hand. The opponent also transitioned into an active Pokémon and drew one card.

Comparison against E001-CABT-37:
- Number 0: hand delta `+1`, deck delta `-1`, turn `0 -> 1`.
- Number 1: hand delta `+1`, deck delta `-1`, turn `0 -> 1`.

Measured conclusion:
- The immediate state delta after choosing DRAW_COUNT number 0 and number 1 is identical in these two observations.
- Therefore the available evidence does NOT support interpreting the numeric field as a simple "number of cards drawn" value.

Additional note:
- The probe raised `SystemExit` deliberately after printing the result; the IPython warning is a notebook control-flow artifact, not a CABT engine failure.

Next controlled experiment:
Capture the full `select` object, `current`, and logs immediately BEFORE selecting a DRAW_COUNT value, then compare those pre-selection observations for episodes exposing different option ranges. This should identify what game-state quantity the numeric choices are representing before we assign semantics.


## 2026-10-03 — E001-CABT-39: DRAW_COUNT Context Includes Opponent Mulligan Evidence

A clean DRAW_COUNT context capture showed the following pre-selection facts:

- `SelectType.COUNT = 8`
- `SelectContext.DRAW_COUNT = 38`
- options were `number = [0, 1, 2]`.
- acting player was `yourIndex = 0`.
- both players had `handCount = 6` and `deckCount = 47` before the selection.
- the logs immediately before DRAW_COUNT contained a setup branch for player 1 with:
  - `hasBasicPokemon = False`
  - seven cards then moved from hand back to deck.
  - a second hand was drawn.
  - `hasBasicPokemon = True`.
  - player 1 was then assigned an active Pokémon and six prize cards.

Measured observation:
- At least one mulligan-related `hasBasicPokemon = False` event occurred for player 1 immediately before a DRAW_COUNT selection presented to player 0.

Hypothesis to test (not yet established):
- The DRAW_COUNT numeric options may encode the number of mulligans/compensation cards associated with the opponent's setup branch.

Why this remains unverified:
- Prior E001-CABT-37 and E001-CABT-38 showed identical immediate hand/deck deltas after selecting numbers 0 and 1.
- Therefore the numeric choice cannot currently be interpreted as a simple standalone draw amount from those transitions.

Next controlled experiment:
Across fresh episodes, count `hasBasicPokemon = False` setup events per opponent before DRAW_COUNT and compare that count with the maximum available `number` option. Do not select a DRAW_COUNT option.


## 2026-10-03 — E001-CABT-40: DRAW_COUNT Option Range Matches Opponent Mulligans + 1

The 30-episode correlation probe produced 17 usable DRAW_COUNT samples. The earlier summary comparison used the wrong equality (`mulligans == max_number`) and therefore reported `0/17`. The informative invariant is instead:

`max_number == mulligans + 1`

Observed samples:
- 0 mulligans -> maximum option 1
- 1 mulligan -> maximum option 2
- 2 mulligans -> maximum option 3
- 4 mulligans -> maximum option 5

Across all 17 observed DRAW_COUNT samples:
- `max_number == mulligans + 1` matched **17/17**.
- The available raw options were contiguous from 0 through the maximum, e.g. `[0,1]`, `[0,1,2]`, `[0,1,2,3]`, and `[0,1,2,3,4,5]`.

Measured conclusion:
- The DRAW_COUNT option range is strongly and directly correlated in this probe with the opponent's number of `hasBasicPokemon = False` events, with one additional option beyond that count.
- This is much stronger evidence than the prior hypothesis that the numeric value itself was the number of cards to draw.

Still unverified:
- The exact semantic meaning of the selected numeric value (especially why the domain is 0..mulligans+1) has not yet been established.
- We should not infer the effect from the option domain alone.

Next controlled experiment:
Find a DRAW_COUNT state with exactly one recorded opponent mulligan (options 0,1,2), select the maximum value 2, and measure the complete immediate state/log delta. Compare it with the same branch selecting 0.


## 2026-10-03 — E001-CABT-41: DRAW_COUNT Number 2 Directly Changes Hand by +2

A controlled one-mulligan DRAW_COUNT episode exposed options `[0,1,2]`. The probe selected raw `number = 2`.

Pre-selection:
- acting player hand count = 6
- acting player deck count = 47
- turn = 0
- opponent had exactly 1 `hasBasicPokemon = False` event.

Immediately after selection:
- acting player hand count = 8, delta `+2`
- acting player deck count = 45, delta `-2`
- opponent hand count remained 6
- opponent deck count remained 47
- turn remained 0

Measured conclusion:
- In this controlled state, selecting DRAW_COUNT number 2 caused exactly two cards to move from the acting player's deck into the acting player's hand.
- This is direct evidence that the NUMBER payload controls a card-draw quantity in this state.
- Unlike E001-CABT-37/38, this observation did not advance the turn immediately.

Important remaining ambiguity:
- The relationship between DRAW_COUNT, the opponent's mulligan count, and the subsequent turn-start draw has not yet been fully modeled.
- We should inspect the next `select`, `current`, and logs after selecting number 2 before finalizing the semantic label.

Next controlled experiment:
Repeat the one-mulligan case, select number 2, and print the complete post-selection `select`, `current`, and newly emitted logs. Do not make a further selection.


## 2026-10-03 — E001-CABT-42: Post-DRAW_COUNT State Returns to Optional Bench Setup

Following the controlled one-mulligan case, selecting DRAW_COUNT `number = 2` produced:

- player 0 hand count: 6 -> 8
- player 0 deck count: 47 -> 45
- turn remained 0
- player 0 active remained unset at this snapshot
- opponent state remained unchanged.

The immediate next selection was:
- `SelectType.CARD = 1`
- `SelectContext.SETUP_BENCH_POKEMON = 2`
- `minCount = 0`
- `maxCount = 1`
- one legal option targeting hand index 7.

Measured conclusion:
- DRAW_COUNT is an intermediate setup-stage draw decision, not a turn-start transition.
- After the draw decision, CABT can return to optional bench selection while remaining on `turn = 0`.
- The newly drawn cards remain in hand and can therefore participate in subsequent setup decisions.

Semantic status:
- The numeric choice is directly demonstrated to control the number of cards added to the acting player's hand in this branch.
- The exact rule-level relationship between the option domain, opponent mulligans, and the player's permitted choice remains to be modeled cautiously.

Next controlled experiment:
Use the same one-mulligan condition but select DRAW_COUNT `number = 0`, then inspect the immediate hand/deck delta and next selection. This gives a direct within-branch contrast against the `number = 2` result.


## 2026-10-03 — E001-CABT-43: DRAW_COUNT Number 0 Causes No Draw and Ends Setup

A controlled one-mulligan `DRAW_COUNT` state exposed options `[0, 1, 2]`. The probe selected raw `number = 0`.

Measured transition:
- Acting player's hand: `6 -> 6`, delta `0`.
- Acting player's deck: `47 -> 47`, delta `0`.
- Turn: `0 -> 1`.
- Immediate next selection: `MAIN / MAIN`.

Comparison with E001-CABT-41:
- Number 2: hand `+2`, deck `-2`, turn remained `0`, followed by `SETUP_BENCH_POKEMON`.
- Number 0: hand/deck unchanged, turn advanced to `1`, followed by `MAIN`.

Measured conclusion:
- `number = 0` means zero cards are drawn in this state.
- The numeric choice also affects the subsequent setup flow: choosing 0 ended the setup stage immediately in this observation, while choosing 2 kept the engine in setup.
- The raw evidence still does not by itself establish the complete game-rule semantics of why these choices are available.

Next controlled experiment:
Use a one-mulligan DRAW_COUNT state, select `number = 1), and inspect the immediate hand/deck delta plus the next selection. This completes the 0/1/2 behavioral comparison.


## 2026-10-03 — E001-CABT-44: DRAW_COUNT Number 1 Completes the 0/1/2 Contrast

A controlled one-mulligan DRAW_COUNT state exposed options `[0, 1, 2]`. The probe selected raw `number = 1`.

Measured transition:
- Acting player's hand: `6 -> 7`, delta `+1`.
- Acting player's deck: `47 -> 46`, delta `-1`.
- Turn remained `0`.
- The immediate next selection was `CARD / SETUP_BENCH_POKEMON`.
- The next selection had `minCount = 0`, `maxCount = 2`, and two legal options, both with `playerIndex = 1`.

Controlled comparison for a one-mulligan DRAW_COUNT state:
- Number 0: hand/deck delta `0/0`; turn advanced to `1`; next selection was `MAIN / MAIN` in the observed episode.
- Number 1: hand/deck delta `+1/-1`; turn stayed `0`; next selection was `SETUP_BENCH_POKEMON`.
- Number 2: hand/deck delta `+2/-2`; turn stayed `0`; next selection was `SETUP_BENCH_POKEMON`.

Measured conclusion:
- The NUMBER payload directly controls how many cards are drawn in the DRAW_COUNT state.
- For this one-mulligan condition, choosing a positive number keeps the battle in setup, while choosing zero advanced to the normal turn in the observed zero case.
- The exact game-rule rationale for the permissible range `0..2` is still not promoted beyond the observed correlation with the opponent's one mulligan.

Pattern/condition discipline:
- Pattern: the available maximum was mulligans + 1 in all 17 sampled DRAW_COUNT states in E001-CABT-40.
- Condition-specific evidence: the complete 0/1/2 behavioral contrast above was obtained for a one-mulligan state.
- Causal evidence: selecting 0, 1, and 2 demonstrably changed the number of cards drawn in their respective controlled states.
- Not yet established: whether the same exact post-selection transitions hold for every mulligan count or every branch.

Next step:
Stop expanding DRAW_COUNT probes for now. Promote the verified numeric behavior into the semantic action model, while keeping the mulligan interpretation explicitly conditional. Then move back to the main architecture: normalized state + legal-action decoding.


## 2026-10-03 — E001-CABT-45: Normalized State Layer Unit Tests Passing

A fresh checkout of the repository was tested after adding the normalized state layer.

Measured result:
- `pytest -q /kaggle/working/ptcg_e001_latest/tests` -> **14 passed**.
- The earlier baseline suite had 8 tests; the new normalized-state tests therefore increased the total to 14.
- No test failures were observed.

Validated state-layer behaviors include:
- hidden opponent hand remains represented as `None`
- observed physical card identity preserves `card_id`, `serial`, `player_index`, and zone
- invalid scalar types are rejected.

Decision:
The normalized state layer is unit-tested and ready for live native-CABT integration testing. Unit tests alone do not establish full simulator correctness.


## 2026-10-03 — E001-CABT-46: Live Normalized State Integration at Battle Start

The normalized `GameState.from_current()` parser was run against the actual native CABT `current` object returned immediately from `battle_start()`.

Measured live state:
- `turn = 0`
- `your_index = 0`
- `first_player = -1`
- `round = 1`
- 2 players were exposed.
- Player 0: `hand_count = 0`, hand visible, `deck_count = 60`, no active card, no bench cards.
- Player 1: `hand_count = 0`, hand hidden (`None`), `deck_count = 60`, no active card, no bench cards.

Measured conclusion:
- The normalized state layer successfully parsed a real pre-setup native observation.
- The engine can expose a pre-selection state with `first_player = -1`; therefore the state representation must preserve this sentinel rather than assuming first-player assignment is immediately available.
- Hidden-information handling was preserved: player 1 hand remained unavailable while its hand count was exposed.

Important scope note:
- This is a battle-start snapshot before the setup decisions are resolved. It should not be conflated with the later setup state where `first_player`, hands, active Pokémon, and prizes have been populated.

Next controlled integration target:
Advance only through the verified initial YES/NO selection and parse the resulting live `current` into `GameState`, comparing the normalized fields with the raw observation.


## 2026-10-03 — E001-CABT-47: Live State Parsing After Initial YES

After the initial `YES` selection, the native CABT observation was parsed successfully by `GameState.from_current()`.

Raw live state:
- `turn = 0`
- `yourIndex = 1`
- `firstPlayer = 0`
- `round = 1`
- both players had `handCount = 7`
- both players had `deckCount = 53`
- player 0 hand remained hidden
- player 1 hand was visible with seven physical card instances
- no active/bench cards or prize cards had yet been populated in this snapshot.

Measured conclusion:
- The normalized state layer correctly tracks the change from the battle-start sentinel `firstPlayer = -1` to the resolved `firstPlayer = 0`.
- The acting/observable player can be player 1 even though player 0 is the first player; therefore `your_index` and `first_player` must remain separate state fields.
- Hidden-information handling remains correct after setup begins.

Next controlled integration target:
Decode the live setup-active selection from this state and verify that the selected option index is kept separate from the normalized state representation.


## 2026-10-03 — E001-CABT-48: Live State + LegalAction Integration

A live native CABT observation was simultaneously normalized into `GameState` and decoded into semantic `LegalAction` objects.

Observed state:
- `turn = 0`
- `your_index = 1`
- `first_player = 0`

Observed legal actions:
- option 0 -> `CARD / SETUP_ACTIVE_POKEMON -> CARD`
- option 1 -> `CARD / SETUP_ACTIVE_POKEMON -> CARD`

Execution invariant:
- the decoded action indices were exactly `[0, 1]`, matching the native option list positions.

Measured conclusion:
- The state abstraction and legal-action abstraction can coexist on the same live CABT observation without changing the engine-facing option index.
- This establishes the first combined state/action integration checkpoint.

Architecture decision:
- A policy should consume `GameState` plus decoded `LegalAction[]`.
- The final execution layer should return only the selected `option_index` values required by CABT.
- No global action-ID remapping should be introduced.

Next step:
Implement a thin decision-input object that bundles normalized `GameState` and `LegalAction[]`, then unit-test that bundle before connecting any strategic policy.
