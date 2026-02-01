from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from four_in_a_row_rules import (  # noqa: E402
    apply_four_in_a_row_move,
    initial_four_in_a_row_state,
    legal_four_in_a_row_moves,
    parse_state,
    serialize_state,
)


def test_drop_in_column():
    state = initial_four_in_a_row_state()
    result = apply_four_in_a_row_move(state, 4)
    assert result.legal is True
    parsed = parse_state(result.state)
    assert parsed["grid"][5][3] in {"R", "Y"}


def test_column_full_rejected():
    state = initial_four_in_a_row_state()
    for _ in range(6):
        result = apply_four_in_a_row_move(state, 1)
        state = result.state
    repeat = apply_four_in_a_row_move(state, 1)
    assert repeat.legal is False


def test_horizontal_win():
    state = initial_four_in_a_row_state()
    for col in [1, 1, 2, 2, 3, 3, 4]:
        result = apply_four_in_a_row_move(state, col)
        state = result.state
    assert result.status == "game_over"
    assert result.winner == "player"


def test_draw_detection():
    grid = [
        list("RRYYRRY"),
        list("YYRRYYR"),
        list("RRYYRRY"),
        list("YYRRYYR"),
        list("RRYYRRY"),
        list("YYRRYYR"),
    ]
    grid[0][6] = "."
    state = serialize_state(
        grid=grid,
        turn="player",
        status="in_progress",
        last_action="-",
        winner="-",
    )
    result = apply_four_in_a_row_move(state, 7)
    assert result.legal is True
    assert result.status == "game_over"
    assert result.winner is None


def test_legal_moves_count():
    state = initial_four_in_a_row_state()
    moves = legal_four_in_a_row_moves(state)
    assert moves == [1, 2, 3, 4, 5, 6, 7]
