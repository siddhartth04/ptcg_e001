"""Offline contract smoke test.

This validates our agent contract without requiring the native cabt engine.
Run in any Python environment with the repository on disk.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ptcg_agent.agent import DEFAULT_DECK, agent  # noqa: E402


cases = [
    {"select": None},
    {
        "select": {
            "option": [{"type": 1}, {"type": 2}, {"type": 3}, {"type": 4}],
            "minCount": 1,
            "maxCount": 2,
        }
    },
    {"select": {"option": [], "minCount": 0, "maxCount": 0}},
]

for case in cases:
    result = agent(case)
    print(result)

assert len(agent({"select": None})) == 60
assert len(DEFAULT_DECK) == 60
print("E001 offline contract smoke test: PASS")
