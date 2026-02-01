from __future__ import annotations

from dataclasses import dataclass


ROWS = 3
COLS = 3

EMPTY = "."
X = "X"
O = "O"

TURN_PLAYER = "player"
TURN_OPPONENT = "opponent"

STATUS_IN_PROGRESS = "in_progress"
STATUS_GAME_OVER = "game_over"


@dataclass(frozen=True)
class TicTacToeMoveResult:
    legal: bool
    state: str
    error: str | None = None
    status: str | None = None
    turn: str | None = None
    last_action: str | None = None
    winner: str | None = None


def initial_tic_tac_toe_state(player_symbol: str = X) -> str:
    player = _normalize_symbol(player_symbol)
    opponent = O if player == X else X
    grid = [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]
    return serialize_state(
        grid=grid,
        turn=TURN_PLAYER,
        status=STATUS_IN_PROGRESS,
        last_action="-",
        winner="-",
        player_symbol=player,
        opponent_symbol=opponent,
    )


def apply_tic_tac_toe_move(state: str, coord: str) -> TicTacToeMoveResult:
    try:
        parsed = parse_state(state)
    except ValueError as exc:
        return TicTacToeMoveResult(False, state, error=str(exc))

    if parsed["status"] != STATUS_IN_PROGRESS:
        return TicTacToeMoveResult(False, state, error="Game is already over.")
    if parsed["turn"] not in {TURN_PLAYER, TURN_OPPONENT}:
        return TicTacToeMoveResult(False, state, error="Invalid turn.")

    try:
        row, col = _coord_to_index(coord)
    except ValueError as exc:
        return TicTacToeMoveResult(False, state, error=str(exc))

    grid = parsed["grid"]
    if grid[row][col] != EMPTY:
        return TicTacToeMoveResult(False, state, error="Square is already occupied.")

    symbol = (
        parsed["player_symbol"]
        if parsed["turn"] == TURN_PLAYER
        else parsed["opponent_symbol"]
    )
    grid[row][col] = symbol

    winner = "-"
    status = STATUS_IN_PROGRESS
    if _check_win(grid, symbol):
        status = STATUS_GAME_OVER
        winner = parsed["turn"]
    elif _is_board_full(grid):
        status = STATUS_GAME_OVER
        winner = "draw"

    next_turn = parsed["turn"]
    if status == STATUS_IN_PROGRESS:
        next_turn = TURN_OPPONENT if parsed["turn"] == TURN_PLAYER else TURN_PLAYER

    last_action = coord.upper()
    new_state = serialize_state(
        grid=grid,
        turn=next_turn,
        status=status,
        last_action=last_action,
        winner=winner,
        player_symbol=parsed["player_symbol"],
        opponent_symbol=parsed["opponent_symbol"],
    )
    return TicTacToeMoveResult(
        True,
        new_state,
        status=status,
        turn=next_turn,
        last_action=last_action,
        winner=None if winner == "-" else winner,
    )


def legal_tic_tac_toe_moves(state: str) -> list[str]:
    try:
        parsed = parse_state(state)
    except ValueError:
        return []
    moves = []
    for row in range(ROWS):
        for col in range(COLS):
            if parsed["grid"][row][col] == EMPTY:
                moves.append(_index_to_coord(row, col))
    return moves


def opponent_move_candidates(state: str, limit: int = 200) -> list[str]:
    moves = legal_tic_tac_toe_moves(state)
    if limit > 0:
        return moves[:limit]
    return moves


def serialize_state(
    *,
    grid: list[list[str]],
    turn: str,
    status: str,
    last_action: str,
    winner: str,
    player_symbol: str,
    opponent_symbol: str,
) -> str:
    return "|".join(
        [
            f"G:{_grid_to_string(grid)}",
            f"T:{turn}",
            f"ST:{status}",
            f"LA:{last_action}",
            f"W:{winner}",
            f"P:{player_symbol}",
            f"O:{opponent_symbol}",
        ]
    )


def parse_state(state: str) -> dict[str, object]:
    if not isinstance(state, str) or not state.strip():
        raise ValueError("Invalid tic-tac-toe state string.")
    parts: dict[str, str] = {}
    for chunk in state.split("|"):
        if ":" not in chunk:
            raise ValueError("Invalid tic-tac-toe state segment.")
        key, value = chunk.split(":", 1)
        parts[key] = value

    grid = _grid_from_string(parts.get("G"))
    turn = parts.get("T") or TURN_PLAYER
    status = parts.get("ST") or STATUS_IN_PROGRESS
    last_action = parts.get("LA") or "-"
    winner = parts.get("W") or "-"
    player_symbol = _normalize_symbol(parts.get("P") or X)
    opponent_symbol = _normalize_symbol(
        parts.get("O") or (O if player_symbol == X else X)
    )

    if turn not in {TURN_PLAYER, TURN_OPPONENT}:
        raise ValueError("Invalid tic-tac-toe turn.")
    if status not in {STATUS_IN_PROGRESS, STATUS_GAME_OVER}:
        raise ValueError("Invalid tic-tac-toe status.")

    return {
        "grid": grid,
        "turn": turn,
        "status": status,
        "last_action": last_action,
        "winner": winner,
        "player_symbol": player_symbol,
        "opponent_symbol": opponent_symbol,
    }


def _normalize_symbol(symbol: str) -> str:
    if not symbol:
        return X
    upper = symbol.upper()
    if upper not in {X, O}:
        raise ValueError("Invalid player symbol.")
    return upper


def _grid_to_string(grid: list[list[str]]) -> str:
    if len(grid) != ROWS or any(len(row) != COLS for row in grid):
        raise ValueError("Invalid grid size.")
    rows = []
    for row in grid:
        for cell in row:
            if cell not in {EMPTY, X, O}:
                raise ValueError("Invalid grid cell.")
        rows.append("".join(row))
    return "/".join(rows)


def _grid_from_string(raw: str | None) -> list[list[str]]:
    if not raw:
        raise ValueError("Invalid grid string.")
    rows = raw.split("/")
    if len(rows) != ROWS:
        raise ValueError("Invalid grid rows.")
    grid: list[list[str]] = []
    for row in rows:
        if len(row) != COLS:
            raise ValueError("Invalid grid row length.")
        cells = list(row)
        for cell in cells:
            if cell not in {EMPTY, X, O}:
                raise ValueError("Invalid grid cell.")
        grid.append(cells)
    return grid


def _coord_to_index(coord: str) -> tuple[int, int]:
    if not isinstance(coord, str):
        raise ValueError("Invalid coordinate format.")
    cleaned = coord.strip().upper()
    if len(cleaned) != 2:
        raise ValueError("Invalid coordinate format.")
    file = cleaned[0]
    rank = cleaned[1]
    if file not in {"A", "B", "C"}:
        raise ValueError("Invalid coordinate file.")
    if rank not in {"1", "2", "3"}:
        raise ValueError("Invalid coordinate rank.")
    col = {"A": 0, "B": 1, "C": 2}[file]
    row = int(rank) - 1
    return row, col


def _index_to_coord(row: int, col: int) -> str:
    file = {0: "A", 1: "B", 2: "C"}[col]
    return f"{file}{row + 1}"


def _check_win(grid: list[list[str]], symbol: str) -> bool:
    for row in range(ROWS):
        if all(grid[row][col] == symbol for col in range(COLS)):
            return True
    for col in range(COLS):
        if all(grid[row][col] == symbol for row in range(ROWS)):
            return True
    if all(grid[i][i] == symbol for i in range(ROWS)):
        return True
    if all(grid[i][COLS - 1 - i] == symbol for i in range(ROWS)):
        return True
    return False


def _is_board_full(grid: list[list[str]]) -> bool:
    return all(cell != EMPTY for row in grid for cell in row)
