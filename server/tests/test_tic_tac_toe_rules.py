from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tic_tac_toe_rules import (  # noqa: E402
    apply_tic_tac_toe_move,
    initial_tic_tac_toe_state,
    legal_tic_tac_toe_moves,
    parse_state,
    serialize_state,
)


def test_initial_state_and_legal_moves():
    state = initial_tic_tac_toe_state()
    moves = legal_tic_tac_toe_moves(state)
    assert len(moves) == 9


def test_apply_move_places_symbol():
    state = initial_tic_tac_toe_state()
    result = apply_tic_tac_toe_move(state, "A1")
    assert result.legal is True
    parsed = parse_state(result.state)
    assert parsed["grid"][0][0] in {"X", "O"}


def test_rejects_occupied_square():
    state = initial_tic_tac_toe_state()
    result = apply_tic_tac_toe_move(state, "B2")
    repeat = apply_tic_tac_toe_move(result.state, "B2")
    assert repeat.legal is False


def test_win_detection_row():
    state = initial_tic_tac_toe_state("X")
    moves = ["A1", "A2", "B1", "B2", "C1"]
    result = None
    for move in moves:
        result = apply_tic_tac_toe_move(state, move)
        state = result.state
    assert result is not None
    assert result.status == "game_over"
    assert result.winner == "player"


def test_draw_detection():
    grid = [
        list("XOO"),
        list("OX."),
        list("XOO"),
    ]
    state = serialize_state(
        grid=grid,
        turn="player",
        status="in_progress",
        last_action="-",
        winner="-",
        player_symbol="X",
        opponent_symbol="O",
    )
    result = apply_tic_tac_toe_move(state, "C2")
    assert result.legal is True
    assert result.status == "game_over"
    assert result.winner == "draw"
