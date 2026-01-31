from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from checkers_rules import (  # noqa: E402
    all_checkers_moves,
    apply_checkers_move,
    initial_checkers_state,
    legal_checkers_moves,
)


def test_initial_state_has_moves():
    state = initial_checkers_state()
    moves = legal_checkers_moves(state)
    assert moves


def test_apply_checkers_move_changes_turn():
    state = initial_checkers_state()
    move = legal_checkers_moves(state)[0]
    result = apply_checkers_move(state, move)
    assert result.legal is True
    assert result.turn == "b"


def test_forced_capture_blocks_simple_move():
    state = "......../......../......../......../...b..../..w...../......../........ w"
    legal = legal_checkers_moves(state)
    capture_moves, simple_moves = all_checkers_moves(state)
    assert "c3b4" in simple_moves
    assert "c3e5" in capture_moves
    assert "c3b4" not in legal
    assert "c3e5" in legal
