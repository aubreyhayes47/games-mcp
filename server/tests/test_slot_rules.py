from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from slot_rules import (  # noqa: E402
    initial_slot_state,
    serialize_state,
    spin_slot,
)


def test_initial_slot_state_defaults():
    state = initial_slot_state(stack=1000, bet=10)
    assert state.stack == 1000
    assert state.bet == 10
    assert state.reels == []


def test_spin_updates_stack_and_reels():
    state = initial_slot_state(stack=100, bet=10)
    state_str = serialize_state(state)
    result = spin_slot(state_str)
    assert result["legal"] is True
    assert len(result["reels"]) == 3
    assert result["stack"] >= 90


def test_spin_rejects_invalid_bet():
    state = initial_slot_state(stack=50, bet=10)
    state_str = serialize_state(state)
    result = spin_slot(state_str)
    assert result["legal"] is True

    bad = spin_slot("R:-|BK:0|B:10|P:0|ST:in_progress|LA:-")
    assert bad["legal"] is False


def test_initial_slot_state_invalid_inputs():
    with pytest.raises(ValueError):
        initial_slot_state(stack=0, bet=10)
    with pytest.raises(ValueError):
        initial_slot_state(stack=10, bet=0)
    with pytest.raises(ValueError):
        initial_slot_state(stack=5, bet=10)
