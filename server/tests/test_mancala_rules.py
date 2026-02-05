from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from mancala_rules import (  # noqa: E402
    apply_mancala_move,
    initial_mancala_state,
    legal_mancala_moves,
    parse_state,
    serialize_state,
)


def test_initial_state_and_legal_moves():
    state = initial_mancala_state()
    parsed = parse_state(state)
    assert parsed["player_pits"] == [4, 4, 4, 4, 4, 4]
    assert parsed["opponent_pits"] == [4, 4, 4, 4, 4, 4]
    assert parsed["player_store"] == 0
    assert parsed["opponent_store"] == 0
    assert legal_mancala_moves(state) == [1, 2, 3, 4, 5, 6]


def test_rejects_invalid_pit_number():
    state = initial_mancala_state()
    result = apply_mancala_move(state, 0)
    assert result.legal is False


def test_rejects_empty_pit_move():
    state = serialize_state(
        player_pits=[0, 4, 4, 4, 4, 4],
        opponent_pits=[4, 4, 4, 4, 4, 4],
        player_store=0,
        opponent_store=0,
        turn="player",
        status="in_progress",
        last_action="-",
        winner="-",
    )
    result = apply_mancala_move(state, 1)
    assert result.legal is False


def test_extra_turn_when_landing_in_store():
    state = serialize_state(
        player_pits=[1, 0, 0, 0, 0, 1],
        opponent_pits=[4, 4, 4, 4, 4, 4],
        player_store=0,
        opponent_store=0,
        turn="player",
        status="in_progress",
        last_action="-",
        winner="-",
    )
    result = apply_mancala_move(state, 6)
    assert result.legal is True
    assert result.turn == "player"
    assert result.last_action is not None
    assert "extra_turn" in result.last_action


def test_capture_when_landing_in_empty_own_pit():
    state = serialize_state(
        player_pits=[0, 1, 0, 0, 0, 0],
        opponent_pits=[0, 0, 0, 5, 0, 0],
        player_store=0,
        opponent_store=0,
        turn="player",
        status="in_progress",
        last_action="-",
        winner="-",
    )
    result = apply_mancala_move(state, 2)
    assert result.legal is True
    parsed = parse_state(result.state)
    assert parsed["player_store"] == 6
    assert parsed["player_pits"][2] == 0
    assert parsed["opponent_pits"][3] == 0


def test_no_capture_when_opposite_empty():
    state = serialize_state(
        player_pits=[0, 1, 0, 0, 0, 0],
        opponent_pits=[1, 0, 0, 0, 0, 0],
        player_store=0,
        opponent_store=0,
        turn="player",
        status="in_progress",
        last_action="-",
        winner="-",
    )
    result = apply_mancala_move(state, 2)
    assert result.legal is True
    parsed = parse_state(result.state)
    assert parsed["player_store"] == 0


def test_endgame_sweep_and_winner():
    state = serialize_state(
        player_pits=[0, 0, 0, 0, 0, 1],
        opponent_pits=[1, 1, 1, 1, 1, 1],
        player_store=20,
        opponent_store=10,
        turn="player",
        status="in_progress",
        last_action="-",
        winner="-",
    )
    result = apply_mancala_move(state, 6)
    assert result.legal is True
    assert result.status == "game_over"
    assert result.winner == "player"
    parsed = parse_state(result.state)
    assert parsed["player_pits"] == [0, 0, 0, 0, 0, 0]
    assert parsed["opponent_pits"] == [0, 0, 0, 0, 0, 0]


def test_endgame_draw():
    state = serialize_state(
        player_pits=[0, 0, 0, 0, 0, 1],
        opponent_pits=[0, 0, 0, 0, 0, 0],
        player_store=24,
        opponent_store=25,
        turn="player",
        status="in_progress",
        last_action="-",
        winner="-",
    )
    result = apply_mancala_move(state, 6)
    assert result.legal is True
    assert result.status == "game_over"
    assert result.winner == "draw"


def test_serialize_parse_roundtrip():
    original = serialize_state(
        player_pits=[1, 2, 3, 4, 5, 6],
        opponent_pits=[6, 5, 4, 3, 2, 1],
        player_store=7,
        opponent_store=8,
        turn="opponent",
        status="in_progress",
        last_action="pit3",
        winner="-",
    )
    parsed = parse_state(original)
    rebuilt = serialize_state(
        player_pits=parsed["player_pits"],
        opponent_pits=parsed["opponent_pits"],
        player_store=parsed["player_store"],
        opponent_store=parsed["opponent_store"],
        turn=parsed["turn"],
        status=parsed["status"],
        last_action=parsed["last_action"],
        winner=parsed["winner"],
    )
    assert rebuilt == original


def test_illegal_on_malformed_state():
    result = apply_mancala_move("bad", 1)
    assert result.legal is False
    assert result.error is not None
