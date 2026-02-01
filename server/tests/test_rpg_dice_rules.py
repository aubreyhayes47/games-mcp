from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from rpg_dice_rules import roll_dice  # noqa: E402


def test_roll_dice_valid():
    result = roll_dice(sides=20, count=3)
    assert result.sides == 20
    assert result.count == 3
    assert len(result.rolls) == 3
    assert all(1 <= value <= 20 for value in result.rolls)


def test_roll_dice_invalid_sides():
    with pytest.raises(ValueError):
        roll_dice(sides=7, count=1)


def test_roll_dice_invalid_count():
    with pytest.raises(ValueError):
        roll_dice(sides=6, count=0)
