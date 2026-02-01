from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sea_battle_rules import (  # noqa: E402
    apply_sea_battle_move,
    initial_sea_battle_state,
    legal_sea_battle_moves,
    parse_state,
    serialize_state,
)


def test_initial_state_has_fleet_and_empty_fog():
    state = initial_sea_battle_state()
    parsed = parse_state(state)
    player_board = parsed["player_board"]
    opponent_board = parsed["opponent_board"]
    fog = parsed["fog_board"]
    assert any(cell == "S" for row in player_board for cell in row)
    assert any(cell == "S" for row in opponent_board for cell in row)
    assert all(cell == "." for row in fog for cell in row)


def test_apply_move_marks_hit_or_miss():
    base = initial_sea_battle_state()
    parsed = parse_state(base)
    coord = legal_sea_battle_moves(base)[0]
    result = apply_sea_battle_move(base, coord)
    assert result.legal is True
    next_state = parse_state(result.state)
    row, col = _coord_to_index(coord)
    assert next_state["fog_board"][row][col] in {"H", "M"}


def test_repeat_move_is_allowed_across_turns():
    base = initial_sea_battle_state()
    coord = legal_sea_battle_moves(base)[0]
    result = apply_sea_battle_move(base, coord)
    repeat = apply_sea_battle_move(result.state, coord)
    assert repeat.legal is True


def test_rejects_opponent_repeat_move():
    base = initial_sea_battle_state()
    coord = legal_sea_battle_moves(base)[0]
    result = apply_sea_battle_move(base, coord)
    opponent_coord = legal_sea_battle_moves(result.state)[0]
    result2 = apply_sea_battle_move(result.state, opponent_coord)
    repeat = apply_sea_battle_move(result2.state, opponent_coord)
    assert repeat.legal is False


def test_game_over_when_opponent_sunk():
    parsed = parse_state(initial_sea_battle_state())
    opponent_board = parsed["opponent_board"]
    for r in range(10):
        for c in range(10):
            opponent_board[r][c] = "."
    state = serialize_state(
        player_board=parsed["player_board"],
        opponent_board=opponent_board,
        fog_board=parsed["fog_board"],
        opponent_fog=parsed["opponent_fog"],
        turn="player",
        status="in_progress",
        last_action="-",
        winner="-",
    )
    result = apply_sea_battle_move(state, "A1")
    assert result.status == "game_over"
    assert result.winner == "player"


def _coord_to_index(coord: str) -> tuple[int, int]:
    file = coord[0].upper()
    rank = int(coord[1:])
    return rank - 1, "ABCDEFGHIJ".index(file)
