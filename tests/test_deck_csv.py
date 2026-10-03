from pathlib import Path


def test_deck_csv_has_60_rows_and_integer_ids() -> None:
    p = Path(__file__).parents[1] / "deck.csv"
    values = [int(x.strip()) for x in p.read_text().splitlines() if x.strip()]
    assert len(values) == 60
    assert all(v > 0 for v in values)
