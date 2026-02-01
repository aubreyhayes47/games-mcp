from __future__ import annotations

from dataclasses import dataclass


ROWS = 6
COLS = 7

EMPTY = "."
PLAYER = "R"
OPPONENT = "Y"

TURN_PLAYER = "player"
TURN_OPPONENT = "opponent"

STATUS_IN_PROGRESS = "in_progress"
STATUS_GAME_OVER = "game_over"


@dataclass(frozen=True)
class FourInARowMoveResult:
    legal: bool
    state: str
    error: str | None = None
    status: str | None = None
    turn: str | None = None
    last_action: str | None = None
    winner: str | None = None


def initial_four_in_a_row_state() -> str:
    grid = [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]
    return serialize_state(
        grid=grid,
        turn=TURN_PLAYER,
        status=STATUS_IN_PROGRESS,
        last_action="-",
        winner="-",
    )


def apply_four_in_a_row_move(state: str, column: int) -> FourInARowMoveResult:
    try:
        parsed = parse_state(state)
    except ValueError as exc:
        return FourInARowMoveResult(False, state, error=str(exc))

    if parsed["status"] != STATUS_IN_PROGRESS:
        return FourInARowMoveResult(False, state, error="Game is already over.")
    if parsed["turn"] not in {TURN_PLAYER, TURN_OPPONENT}:
        return FourInARowMoveResult(False, state, error="Invalid turn.")

    if column < 1 or column > COLS:
        return FourInARowMoveResult(False, state, error="Invalid column.")
    col_index = column - 1

    grid = parsed["grid"]
    row_index = _find_drop_row(grid, col_index)
    if row_index is None:
        return FourInARowMoveResult(False, state, error="Column is full.")

    token = PLAYER if parsed["turn"] == TURN_PLAYER else OPPONENT
    grid[row_index][col_index] = token

    winner = "-"
    status = STATUS_IN_PROGRESS
    if _check_win(grid, row_index, col_index, token):
        status = STATUS_GAME_OVER
        winner = parsed["turn"]
    elif _is_board_full(grid):
        status = STATUS_GAME_OVER

    next_turn = parsed["turn"]
    if status == STATUS_IN_PROGRESS:
        next_turn = TURN_OPPONENT if parsed["turn"] == TURN_PLAYER else TURN_PLAYER

    last_action = str(column)
    new_state = serialize_state(
        grid=grid,
        turn=next_turn,
        status=status,
        last_action=last_action,
        winner=winner,
    )
    return FourInARowMoveResult(
        True,
        new_state,
        status=status,
        turn=next_turn,
        last_action=last_action,
        winner=None if winner == "-" else winner,
    )


def legal_four_in_a_row_moves(state: str) -> list[int]:
    try:
        parsed = parse_state(state)
    except ValueError:
        return []
    grid = parsed["grid"]
    moves = []
    for col in range(COLS):
        if _find_drop_row(grid, col) is not None:
            moves.append(col + 1)
    return moves


def opponent_move_candidates(state: str, limit: int = 200) -> list[int]:
    moves = legal_four_in_a_row_moves(state)
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
) -> str:
    return "|".join(
        [
            f"G:{_grid_to_string(grid)}",
            f"T:{turn}",
            f"ST:{status}",
            f"LA:{last_action}",
            f"W:{winner}",
        ]
    )


def parse_state(state: str) -> dict[str, object]:
    if not isinstance(state, str) or not state.strip():
        raise ValueError("Invalid four-in-a-row state string.")
    parts: dict[str, str] = {}
    for chunk in state.split("|"):
        if ":" not in chunk:
            raise ValueError("Invalid four-in-a-row state segment.")
        key, value = chunk.split(":", 1)
        parts[key] = value

    grid = _grid_from_string(parts.get("G"))
    turn = parts.get("T") or TURN_PLAYER
    status = parts.get("ST") or STATUS_IN_PROGRESS
    last_action = parts.get("LA") or "-"
    winner = parts.get("W") or "-"

    if turn not in {TURN_PLAYER, TURN_OPPONENT}:
        raise ValueError("Invalid four-in-a-row turn.")
    if status not in {STATUS_IN_PROGRESS, STATUS_GAME_OVER}:
        raise ValueError("Invalid four-in-a-row status.")

    return {
        "grid": grid,
        "turn": turn,
        "status": status,
        "last_action": last_action,
        "winner": winner,
    }


def _grid_to_string(grid: list[list[str]]) -> str:
    if len(grid) != ROWS or any(len(row) != COLS for row in grid):
        raise ValueError("Invalid grid size.")
    rows = []
    for row in grid:
        for cell in row:
            if cell not in {EMPTY, PLAYER, OPPONENT}:
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
            if cell not in {EMPTY, PLAYER, OPPONENT}:
                raise ValueError("Invalid grid cell.")
        grid.append(cells)
    return grid


def _find_drop_row(grid: list[list[str]], col: int) -> int | None:
    for row in range(ROWS - 1, -1, -1):
        if grid[row][col] == EMPTY:
            return row
    return None


def _check_win(grid: list[list[str]], row: int, col: int, token: str) -> bool:
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    for dr, dc in directions:
        count = 1
        count += _count_direction(grid, row, col, dr, dc, token)
        count += _count_direction(grid, row, col, -dr, -dc, token)
        if count >= 4:
            return True
    return False


def _count_direction(
    grid: list[list[str]],
    row: int,
    col: int,
    dr: int,
    dc: int,
    token: str,
) -> int:
    count = 0
    r = row + dr
    c = col + dc
    while 0 <= r < ROWS and 0 <= c < COLS and grid[r][c] == token:
        count += 1
        r += dr
        c += dc
    return count


def _is_board_full(grid: list[list[str]]) -> bool:
    return all(cell != EMPTY for row in grid for cell in row)
