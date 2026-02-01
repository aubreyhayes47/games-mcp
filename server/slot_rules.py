from __future__ import annotations

from dataclasses import dataclass
import random


SYMBOLS = ["7", "BAR", "BELL", "CHERRY", "LEMON", "ORANGE"]
SYMBOL_WEIGHTS = {
    "7": 1,
    "BAR": 2,
    "BELL": 3,
    "CHERRY": 4,
    "LEMON": 5,
    "ORANGE": 5,
}
PAYOUT_MULTIPLIERS = {
    "7": 10,
    "BAR": 8,
    "BELL": 6,
    "CHERRY": 4,
    "LEMON": 3,
    "ORANGE": 2,
}

STATUS_IN_PROGRESS = "in_progress"


@dataclass(frozen=True)
class SlotState:
    reels: list[str]
    stack: float
    bet: float
    payout: float
    status: str
    last_action: str


def initial_slot_state(
    *,
    stack: float,
    bet: float,
) -> SlotState:
    _validate_stack_bet(stack, bet)
    return SlotState(
        reels=[],
        stack=stack,
        bet=bet,
        payout=0.0,
        status=STATUS_IN_PROGRESS,
        last_action="-",
    )


def spin_slot(state_str: str, rng: random.Random | None = None) -> dict[str, object]:
    try:
        state = parse_state(state_str)
    except ValueError as exc:
        return {
            "legal": False,
            "state": state_str,
            "error": str(exc),
        }

    if state.stack <= 0:
        return _illegal(state, "Stack must be positive.")
    if state.bet <= 0:
        return _illegal(state, "Bet must be positive.")
    if state.bet > state.stack:
        return _illegal(state, "Bet cannot exceed stack.")

    rng = rng or random.Random()
    weights = [SYMBOL_WEIGHTS[symbol] for symbol in SYMBOLS]
    reels = rng.choices(SYMBOLS, weights=weights, k=3)
    payout = _calculate_payout(reels, state.bet)
    new_stack = state.stack - state.bet + payout
    next_state = SlotState(
        reels=reels,
        stack=new_stack,
        bet=state.bet,
        payout=payout,
        status=STATUS_IN_PROGRESS,
        last_action="spin",
    )
    return {
        "legal": True,
        "state": serialize_state(next_state),
        "reels": reels,
        "stack": new_stack,
        "bet": state.bet,
        "payout": payout,
        "status": next_state.status,
        "lastAction": next_state.last_action,
    }


def serialize_state(state: SlotState) -> str:
    reels = ",".join(state.reels) if state.reels else "-"
    return "|".join(
        [
            f"R:{reels}",
            f"BK:{_format_amount(state.stack)}",
            f"B:{_format_amount(state.bet)}",
            f"P:{_format_amount(state.payout)}",
            f"ST:{state.status}",
            f"LA:{state.last_action}",
        ]
    )


def parse_state(state_str: str) -> SlotState:
    if not isinstance(state_str, str) or not state_str.strip():
        raise ValueError("Invalid slot state string.")
    parts: dict[str, str] = {}
    for chunk in state_str.split("|"):
        if ":" not in chunk:
            raise ValueError("Invalid slot state segment.")
        key, value = chunk.split(":", 1)
        parts[key] = value

    reels_raw = parts.get("R") or "-"
    reels = [] if reels_raw in {"-", ""} else reels_raw.split(",")
    stack = _parse_amount(parts.get("BK"), default=0.0)
    bet = _parse_amount(parts.get("B"), default=0.0)
    payout = _parse_amount(parts.get("P"), default=0.0)
    status = parts.get("ST") or STATUS_IN_PROGRESS
    last_action = parts.get("LA") or "-"

    return SlotState(
        reels=reels,
        stack=stack,
        bet=bet,
        payout=payout,
        status=status,
        last_action=last_action,
    )


def _calculate_payout(reels: list[str], bet: float) -> float:
    if len(reels) != 3:
        return 0.0
    if reels[0] == reels[1] == reels[2]:
        multiplier = PAYOUT_MULTIPLIERS.get(reels[0], 0)
        return bet * multiplier
    return 0.0


def _validate_stack_bet(stack: float, bet: float) -> None:
    if stack <= 0:
        raise ValueError("Stack must be positive.")
    if bet <= 0:
        raise ValueError("Bet must be positive.")
    if bet > stack:
        raise ValueError("Bet cannot exceed stack.")


def _parse_amount(raw: str | None, *, default: float) -> float:
    if raw is None or raw == "-" or raw == "":
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError("Invalid slot amount.") from exc
    if value < 0:
        raise ValueError("Invalid slot amount.")
    return value


def _format_amount(value: float) -> str:
    if isinstance(value, int):
        return str(value)
    if value.is_integer():
        return str(int(value))
    return str(value)


def _illegal(state: SlotState, message: str) -> dict[str, object]:
    return {
        "legal": False,
        "state": serialize_state(state),
        "error": message,
    }
