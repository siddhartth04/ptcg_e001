# PTCG AI Agent — E001 Baseline

This repository is the first reproducible agent baseline for the Pokémon TCG AI Battle `cabt` environment.

## Objective

Establish a correct, deterministic, legality-first agent contract before adding ML.

## Verified contract

According to the official `cabt` documentation, the agent receives an `Observation` containing `logs`, `current`, and `select`. The available actions are represented by option indices from the current `select.option` list; the engine supplies legal options. The official game API also requires 60-card decks and advances a game through `battle_select`.

## E001 policy

The E001 policy intentionally does **not** attempt to be strategically strong.

It establishes:

1. a fixed valid 60-card deck;
2. deterministic handling of the deck-selection phase;
3. deterministic selection of the first `maxCount` legal options;
4. strict validation of selection cardinality and index bounds.

This gives us a regression control group before introducing heuristic scoring, behavioral cloning, Transformers or RL.

## Run offline contract tests

```bash
pytest -q
python scripts/smoke_test.py
```

## Run against CABT

The official environment is provided through `kaggle-environments` / the `cabt` environment. Run the actual game only in an environment where the native CABT engine is available.

```python
from kaggle_environments import make
from main import agent

env = make("cabt")
steps = env.run([agent, agent])
print("steps:", len(steps))
```

Do not interpret a successful offline smoke test as a successful CABT game. The native simulator must be executed separately.

## E001 acceptance criteria

- [x] Agent returns exactly 60 card IDs during deck selection.
- [x] Agent returns indices into the current legal option list.
- [x] Selection cardinality is validated.
- [x] No global action-ID vocabulary is assumed.
- [ ] Native CABT game execution verified.
- [ ] Baseline win rate measured.
- [ ] Baseline completion/invalid-action rate measured.

Until the last three items are executed on CABT, E001 remains **implementation-complete but experimentally unvalidated**.
