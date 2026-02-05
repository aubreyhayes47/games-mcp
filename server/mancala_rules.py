from __future__ import annotations

from dataclasses import dataclass


PITS_PER_SIDE = 6
STARTING_SEEDS_PER_PIT = 4

TURN_PLAYER = "player"
TURN_OPPONENT = "opponent"

STATUS_IN_PROGRESS = "in_progress"
STATUS_GAME_OVER = "game_over"


@dataclass(frozen=True)
class MancalaMoveResult:
    legal: bool
    state: str
    error: str | None = None
    status: str | None = None
    turn: str | None = None
    last_action: str | None = None
    winner: str | None = None


def initial_mancala_state() -> str:
    return serialize_state(
        player_pits=[STARTING_SEEDS_PER_PIT] * PITS_PER_SIDE,
        opponent_pits=[STARTING_SEEDS_PER_PIT] * PITS_PER_SIDE,
        player_store=0,
        opponent_store=0,
        turn=TURN_PLAYER,
        status=STATUS_IN_PROGRESS,
        last_action="-",
        winner="-",
    )


def apply_mancala_move(state: str, pit: int) -> MancalaMoveResult:
    try:
        parsed = parse_state(state)
    except ValueError as exc:
        return MancalaMoveResult(False, state, error=str(exc))

    if parsed["status"] != STATUS_IN_PROGRESS:
        return MancalaMoveResult(False, state, error="Game is already over.")

    turn = parsed["turn"]
    if turn not in {TURN_PLAYER, TURN_OPPONENT}:
        return MancalaMoveResult(False, state, error="Invalid turn.")

    if not isinstance(pit, int):
        return MancalaMoveResult(False, state, error="Invalid pit.")
    if pit < 1 or pit > PITS_PER_SIDE:
        return MancalaMoveResult(False, state, error="Invalid pit.")

    player_pits = list(parsed["player_pits"])
    opponent_pits = list(parsed["opponent_pits"])
    player_store = int(parsed["player_store"])
    opponent_store = int(parsed["opponent_store"])

    active_pits = player_pits if turn == TURN_PLAYER else opponent_pits
    pit_index = pit - 1
    seeds = active_pits[pit_index]
    if seeds <= 0:
        return MancalaMoveResult(False, state, error="Chosen pit is empty.")

    active_pits[pit_index] = 0

    ring_positions = _build_sowing_ring(turn)
    cursor = ring_positions.index(("pit", pit_index))

    while seeds > 0:
        cursor = (cursor + 1) % len(ring_positions)
        kind, idx = ring_positions[cursor]
        if kind == "store":
            if turn == TURN_PLAYER:
                player_store += 1
            else:
                opponent_store += 1
        else:
            if turn == TURN_PLAYER:
                if idx < PITS_PER_SIDE:
                    player_pits[idx] += 1
                else:
                    opponent_pits[idx - PITS_PER_SIDE] += 1
            else:
                if idx < PITS_PER_SIDE:
                    opponent_pits[idx] += 1
                else:
                    player_pits[idx - PITS_PER_SIDE] += 1
        seeds -= 1

    last_kind, last_idx = ring_positions[cursor]
    action_parts = [f"pit{pit}"]

    if last_kind == "pit":
        own_side_landing = last_idx < PITS_PER_SIDE
        if own_side_landing:
            own_pits = player_pits if turn == TURN_PLAYER else opponent_pits
            opp_pits = opponent_pits if turn == TURN_PLAYER else player_pits
            own_index = last_idx
            opposite_index = PITS_PER_SIDE - 1 - own_index
            if own_pits[own_index] == 1 and opp_pits[opposite_index] > 0:
                captured = opp_pits[opposite_index] + 1
                own_pits[own_index] = 0
                opp_pits[opposite_index] = 0
                if turn == TURN_PLAYER:
                    player_store += captured
                else:
                    opponent_store += captured
                action_parts.append(f"capture{captured}")

    extra_turn = last_kind == "store"
    if extra_turn:
        action_parts.append("extra_turn")

    game_over = all(v == 0 for v in player_pits) or all(v == 0 for v in opponent_pits)
    status = STATUS_IN_PROGRESS
    winner = "-"
    next_turn = turn if extra_turn else _other_turn(turn)

    if game_over:
        player_store += sum(player_pits)
        opponent_store += sum(opponent_pits)
        player_pits = [0] * PITS_PER_SIDE
        opponent_pits = [0] * PITS_PER_SIDE
        status = STATUS_GAME_OVER
        action_parts.append("sweep")
        if player_store > opponent_store:
            winner = TURN_PLAYER
        elif opponent_store > player_store:
            winner = TURN_OPPONENT
        else:
            winner = "draw"
        next_turn = turn

    last_action = ",".join(action_parts)
    new_state = serialize_state(
        player_pits=player_pits,
        opponent_pits=opponent_pits,
        player_store=player_store,
        opponent_store=opponent_store,
        turn=next_turn,
        status=status,
        last_action=last_action,
        winner=winner,
    )

    return MancalaMoveResult(
        True,
        new_state,
        status=status,
        turn=next_turn,
        last_action=last_action,
        winner=None if winner == "-" else winner,
    )


def legal_mancala_moves(state: str) -> list[int]:
    try:
        parsed = parse_state(state)
    except ValueError:
        return []

    if parsed["status"] != STATUS_IN_PROGRESS:
        return []

    pits = parsed["player_pits"] if parsed["turn"] == TURN_PLAYER else parsed["opponent_pits"]
    return [index + 1 for index, count in enumerate(pits) if count > 0]


def opponent_move_candidates(state: str, limit: int = 200) -> list[int]:
    moves = legal_mancala_moves(state)
    if limit > 0:
        return moves[:limit]
    return moves


def serialize_state(
    *,
    player_pits: list[int],
    opponent_pits: list[int],
    player_store: int,
    opponent_store: int,
    turn: str,
    status: str,
    last_action: str,
    winner: str,
) -> str:
    _validate_pits(player_pits)
    _validate_pits(opponent_pits)
    if turn not in {TURN_PLAYER, TURN_OPPONENT}:
        raise ValueError("Invalid mancala turn.")
    if status not in {STATUS_IN_PROGRESS, STATUS_GAME_OVER}:
        raise ValueError("Invalid mancala status.")
    if winner not in {"-", TURN_PLAYER, TURN_OPPONENT, "draw"}:
        raise ValueError("Invalid mancala winner.")

    return "|".join(
        [
            f"P:{_pits_to_string(player_pits)}",
            f"O:{_pits_to_string(opponent_pits)}",
            f"PS:{player_store}",
            f"OS:{opponent_store}",
            f"T:{turn}",
            f"ST:{status}",
            f"LA:{last_action}",
            f"W:{winner}",
        ]
    )


def parse_state(state: str) -> dict[str, object]:
    if not isinstance(state, str) or not state.strip():
        raise ValueError("Invalid mancala state string.")

    parts: dict[str, str] = {}
    for chunk in state.split("|"):
        if ":" not in chunk:
            raise ValueError("Invalid mancala state segment.")
        key, value = chunk.split(":", 1)
        parts[key] = value

    player_pits = _pits_from_string(parts.get("P"))
    opponent_pits = _pits_from_string(parts.get("O"))
    player_store = _parse_non_negative_int(parts.get("PS"), "Invalid player store.")
    opponent_store = _parse_non_negative_int(parts.get("OS"), "Invalid opponent store.")
    turn = parts.get("T") or TURN_PLAYER
    status = parts.get("ST") or STATUS_IN_PROGRESS
    last_action = parts.get("LA") or "-"
    winner = parts.get("W") or "-"

    if turn not in {TURN_PLAYER, TURN_OPPONENT}:
        raise ValueError("Invalid mancala turn.")
    if status not in {STATUS_IN_PROGRESS, STATUS_GAME_OVER}:
        raise ValueError("Invalid mancala status.")
    if winner not in {"-", TURN_PLAYER, TURN_OPPONENT, "draw"}:
        raise ValueError("Invalid mancala winner.")

    return {
        "player_pits": player_pits,
        "opponent_pits": opponent_pits,
        "player_store": player_store,
        "opponent_store": opponent_store,
        "turn": turn,
        "status": status,
        "last_action": last_action,
        "winner": winner,
    }


def _parse_non_negative_int(raw: str | None, error: str) -> int:
    if raw is None:
        raise ValueError(error)
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(error) from exc
    if value < 0:
        raise ValueError(error)
    return value


def _pits_to_string(pits: list[int]) -> str:
    _validate_pits(pits)
    return ",".join(str(value) for value in pits)


def _pits_from_string(raw: str | None) -> list[int]:
    if raw is None:
        raise ValueError("Invalid pit string.")
    values = raw.split(",")
    if len(values) != PITS_PER_SIDE:
        raise ValueError("Invalid pit count.")
    pits: list[int] = []
    for value in values:
        try:
            parsed = int(value)
        except ValueError as exc:
            raise ValueError("Invalid pit value.") from exc
        if parsed < 0:
            raise ValueError("Invalid pit value.")
        pits.append(parsed)
    return pits


def _validate_pits(pits: list[int]) -> None:
    if len(pits) != PITS_PER_SIDE:
        raise ValueError("Invalid pit count.")
    for value in pits:
        if not isinstance(value, int) or value < 0:
            raise ValueError("Invalid pit value.")


def _other_turn(turn: str) -> str:
    return TURN_OPPONENT if turn == TURN_PLAYER else TURN_PLAYER


def _build_sowing_ring(turn: str) -> list[tuple[str, int]]:
    # Ring for current side perspective: own pits (0..5), own store, opponent pits (5..0)
    positions: list[tuple[str, int]] = []
    for idx in range(PITS_PER_SIDE):
        positions.append(("pit", idx))
    positions.append(("store", -1))
    for idx in range(PITS_PER_SIDE - 1, -1, -1):
        positions.append(("pit", PITS_PER_SIDE + idx))
    if turn == TURN_PLAYER:
        return positions
    # Same relative ring works for opponent because pit arrays are swapped by turn handling.
    return positions
