from __future__ import annotations

from dataclasses import dataclass
import random


ALLOWED_SIDES = {4, 6, 8, 10, 12, 20, 100}
MAX_ROLLS = 100


@dataclass(frozen=True)
class DiceRoll:
    sides: int
    count: int
    rolls: list[int]


def roll_dice(
    *,
    sides: int,
    count: int = 1,
    rng: random.Random | None = None,
) -> DiceRoll:
    if sides not in ALLOWED_SIDES:
        raise ValueError("Unsupported dice sides.")
    if count < 1 or count > MAX_ROLLS:
        raise ValueError("Invalid dice count.")
    rng = rng or random.Random()
    rolls = [rng.randint(1, sides) for _ in range(count)]
    return DiceRoll(sides=sides, count=count, rolls=rolls)
