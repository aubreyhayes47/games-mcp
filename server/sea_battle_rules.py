from __future__ import annotations

from dataclasses import dataclass
import random


BOARD_SIZE = 10
FLEET_SIZES = [5, 4, 3, 3, 2]

STATUS_IN_PROGRESS = "in_progress"
STATUS_GAME_OVER = "game_over"

TURN_PLAYER = "player"
TURN_OPPONENT = "opponent"

EMPTY = "."
SHIP = "S"
HIT = "H"
MISS = "M"

FILES = "ABCDEFGHIJ"
RANKS = list(range(1, 11))


@dataclass(frozen=True)
class SeaBattleMoveResult:
    legal: bool
    state: str
    error: str | None = None
    status: str | None = None
    turn: str | None = None
    last_action: str | None = None
    winner: str | None = None


def initial_sea_battle_state(rng: random.Random | None = None) -> str:
    rng = rng or random.Random()
    player_board = _empty_board()
    opponent_board = _empty_board()
    _place_fleet_random(player_board, rng)
    _place_fleet_random(opponent_board, rng)
    fog_board = _empty_board()
    return serialize_state(
        player_board=player_board,
        opponent_board=opponent_board,
        fog_board=fog_board,
        turn=TURN_PLAYER,
        status=STATUS_IN_PROGRESS,
        last_action="-",
        winner="-",
    )


def apply_sea_battle_move(state: str, coord: str) -> SeaBattleMoveResult:
    try:
        parsed = parse_state(state)
    except ValueError as exc:
        return SeaBattleMoveResult(False, state, error=str(exc))

    if parsed["status"] != STATUS_IN_PROGRESS:
        return SeaBattleMoveResult(False, state, error="Game is already over.")
    if parsed["turn"] != TURN_PLAYER and parsed["turn"] != TURN_OPPONENT:
        return SeaBattleMoveResult(False, state, error="Invalid turn.")

    try:
        row, col = _coord_to_index(coord)
    except ValueError as exc:
        return SeaBattleMoveResult(False, state, error=str(exc))

    if parsed["turn"] == TURN_PLAYER:
        target_board = parsed["opponent_board"]
        fog_board = parsed["fog_board"]
    else:
        target_board = parsed["player_board"]
        fog_board = parsed["opponent_fog"]

    if fog_board[row][col] in {HIT, MISS}:
        return SeaBattleMoveResult(False, state, error="Coordinate already targeted.")

    hit = target_board[row][col] == SHIP
    if hit:
        target_board[row][col] = HIT
        fog_board[row][col] = HIT
    else:
        fog_board[row][col] = MISS

    sunk_size = _sunk_ship_size(target_board, row, col) if hit else None
    last_action = _format_last_action(coord, hit, sunk_size)

    winner = "-"
    status = STATUS_IN_PROGRESS
    if _all_ships_sunk(target_board):
        status = STATUS_GAME_OVER
        winner = parsed["turn"]

    next_turn = parsed["turn"]
    if status == STATUS_IN_PROGRESS:
        next_turn = TURN_OPPONENT if parsed["turn"] == TURN_PLAYER else TURN_PLAYER

    if parsed["turn"] == TURN_PLAYER:
        player_board = parsed["player_board"]
        opponent_board = target_board
        player_fog = fog_board
        opponent_fog = parsed["opponent_fog"]
    else:
        player_board = target_board
        opponent_board = parsed["opponent_board"]
        player_fog = parsed["fog_board"]
        opponent_fog = fog_board

    new_state = serialize_state(
        player_board=player_board,
        opponent_board=opponent_board,
        fog_board=player_fog,
        turn=next_turn,
        status=status,
        last_action=last_action,
        winner=winner,
        opponent_fog=opponent_fog,
    )
    return SeaBattleMoveResult(
        True,
        new_state,
        status=status,
        turn=next_turn,
        last_action=last_action,
        winner=None if winner == "-" else winner,
    )


def legal_sea_battle_moves(state: str) -> list[str]:
    try:
        parsed = parse_state(state)
    except ValueError:
        return []
    fog = (
        parsed["fog_board"] if parsed["turn"] == TURN_PLAYER else parsed["opponent_fog"]
    )
    moves = []
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if fog[row][col] == EMPTY:
                moves.append(_index_to_coord(row, col))
    return moves


def opponent_move_candidates(state: str, limit: int = 200) -> list[str]:
    moves = legal_sea_battle_moves(state)
    if limit > 0:
        return moves[:limit]
    return moves


def serialize_state(
    *,
    player_board: list[list[str]],
    opponent_board: list[list[str]],
    fog_board: list[list[str]],
    turn: str,
    status: str,
    last_action: str,
    winner: str,
    opponent_fog: list[list[str]] | None = None,
) -> str:
    opponent_fog = opponent_fog or _empty_board()
    return "|".join(
        [
            f"P:{_board_to_string(player_board)}",
            f"O:{_board_to_string(opponent_board)}",
            f"F:{_board_to_string(fog_board)}",
            f"OF:{_board_to_string(opponent_fog)}",
            f"T:{turn}",
            f"ST:{status}",
            f"LA:{last_action}",
            f"W:{winner}",
        ]
    )


def parse_state(state: str) -> dict[str, object]:
    if not isinstance(state, str) or not state.strip():
        raise ValueError("Invalid sea battle state string.")
    parts: dict[str, str] = {}
    for chunk in state.split("|"):
        if ":" not in chunk:
            raise ValueError("Invalid sea battle state segment.")
        key, value = chunk.split(":", 1)
        parts[key] = value

    player_board = _board_from_string(parts.get("P"))
    opponent_board = _board_from_string(parts.get("O"))
    fog_board = _board_from_string(parts.get("F"))
    opponent_fog = _board_from_string(parts.get("OF"))
    turn = parts.get("T") or TURN_PLAYER
    status = parts.get("ST") or STATUS_IN_PROGRESS
    last_action = parts.get("LA") or "-"
    winner = parts.get("W") or "-"

    if turn not in {TURN_PLAYER, TURN_OPPONENT}:
        raise ValueError("Invalid sea battle turn.")
    if status not in {STATUS_IN_PROGRESS, STATUS_GAME_OVER}:
        raise ValueError("Invalid sea battle status.")

    return {
        "player_board": player_board,
        "opponent_board": opponent_board,
        "fog_board": fog_board,
        "opponent_fog": opponent_fog,
        "turn": turn,
        "status": status,
        "last_action": last_action,
        "winner": winner,
    }


def _empty_board() -> list[list[str]]:
    return [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def _place_fleet_random(board: list[list[str]], rng: random.Random) -> None:
    for size in FLEET_SIZES:
        placed = False
        while not placed:
            horizontal = rng.choice([True, False])
            if horizontal:
                row = rng.randrange(BOARD_SIZE)
                col = rng.randrange(BOARD_SIZE - size + 1)
                coords = [(row, col + offset) for offset in range(size)]
            else:
                row = rng.randrange(BOARD_SIZE - size + 1)
                col = rng.randrange(BOARD_SIZE)
                coords = [(row + offset, col) for offset in range(size)]

            if any(board[r][c] == SHIP for r, c in coords):
                continue
            for r, c in coords:
                board[r][c] = SHIP
            placed = True


def _board_to_string(board: list[list[str]]) -> str:
    if len(board) != BOARD_SIZE or any(len(row) != BOARD_SIZE for row in board):
        raise ValueError("Invalid board size.")
    rows = []
    for row in board:
        for cell in row:
            if cell not in {EMPTY, SHIP, HIT, MISS}:
                raise ValueError("Invalid board cell.")
        rows.append("".join(row))
    return "/".join(rows)


def _board_from_string(raw: str | None) -> list[list[str]]:
    if not raw:
        raise ValueError("Invalid board string.")
    rows = raw.split("/")
    if len(rows) != BOARD_SIZE:
        raise ValueError("Invalid board rows.")
    board: list[list[str]] = []
    for row in rows:
        if len(row) != BOARD_SIZE:
            raise ValueError("Invalid board row length.")
        cells = list(row)
        for cell in cells:
            if cell not in {EMPTY, SHIP, HIT, MISS}:
                raise ValueError("Invalid board cell.")
        board.append(cells)
    return board


def _coord_to_index(coord: str) -> tuple[int, int]:
    if not isinstance(coord, str):
        raise ValueError("Invalid coordinate format.")
    cleaned = coord.strip().upper()
    if len(cleaned) < 2 or len(cleaned) > 3:
        raise ValueError("Invalid coordinate format.")
    file = cleaned[0]
    if file not in FILES:
        raise ValueError("Invalid coordinate file.")
    try:
        rank = int(cleaned[1:])
    except ValueError as exc:
        raise ValueError("Invalid coordinate rank.") from exc
    if rank not in RANKS:
        raise ValueError("Invalid coordinate rank.")
    row = rank - 1
    col = FILES.index(file)
    return row, col


def _index_to_coord(row: int, col: int) -> str:
    return f"{FILES[col]}{row + 1}"


def _all_ships_sunk(board: list[list[str]]) -> bool:
    return all(cell != SHIP for row in board for cell in row)


def _sunk_ship_size(board: list[list[str]], row: int, col: int) -> int | None:
    if board[row][col] != HIT:
        return None
    visited = set()
    stack = [(row, col)]
    hits = []
    while stack:
        r, c = stack.pop()
        if (r, c) in visited:
            continue
        visited.add((r, c))
        if board[r][c] == HIT:
            hits.append((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    if board[nr][nc] in {HIT, SHIP}:
                        stack.append((nr, nc))

    for r, c in hits:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                if board[nr][nc] == SHIP:
                    return None
    return len(hits) if hits else None


def _format_last_action(coord: str, hit: bool, sunk_size: int | None) -> str:
    result = "hit" if hit else "miss"
    if sunk_size:
        result = f"sunk({sunk_size})"
    return f"{coord.upper()}:{result}"
