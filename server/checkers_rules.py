from __future__ import annotations

from dataclasses import dataclass

FILES = "abcdefgh"
RANKS = "12345678"

WHITE = "w"
BLACK = "b"


@dataclass(frozen=True)
class CheckersMoveResult:
    legal: bool
    state: str
    error: str | None = None
    status: str | None = None
    turn: str | None = None
    last_move: str | None = None
    winner: str | None = None


def initial_checkers_state() -> str:
    board = [["." for _ in range(8)] for _ in range(8)]
    for row in range(3):
        for col in range(8):
            if is_dark_square(row, col):
                board[row][col] = "b"
    for row in range(5, 8):
        for col in range(8):
            if is_dark_square(row, col):
                board[row][col] = "w"
    return board_to_state(board, WHITE)


def board_to_state(board: list[list[str]], turn: str) -> str:
    rows = ["".join(row) for row in board]
    return "/".join(rows) + f" {turn}"


def parse_state(state: str) -> tuple[list[list[str]], str]:
    if not isinstance(state, str) or " " not in state:
        raise ValueError("Invalid checkers state string.")
    board_part, turn = state.strip().split(" ", 1)
    rows = board_part.split("/")
    if len(rows) != 8:
        raise ValueError("Invalid checkers state rows.")
    board: list[list[str]] = []
    for row in rows:
        if len(row) != 8:
            raise ValueError("Invalid checkers state row length.")
        board_row = []
        for char in row:
            if char not in {"w", "W", "b", "B", "."}:
                raise ValueError("Invalid checkers state piece.")
            board_row.append(char)
        board.append(board_row)
    if turn not in {WHITE, BLACK}:
        raise ValueError("Invalid checkers state turn.")
    return board, turn


def is_dark_square(row: int, col: int) -> bool:
    rank_index = 7 - row
    return (col + rank_index) % 2 == 0


def square_to_coords(square: str) -> tuple[int, int]:
    if len(square) != 2:
        raise ValueError("Invalid square length.")
    file = square[0]
    rank = square[1]
    if file not in FILES or rank not in RANKS:
        raise ValueError("Invalid square coordinates.")
    col = FILES.index(file)
    rank_index = int(rank) - 1
    row = 7 - rank_index
    return row, col


def coords_to_square(row: int, col: int) -> str:
    rank_index = 7 - row
    return f"{FILES[col]}{rank_index + 1}"


def is_king(piece: str) -> bool:
    return piece in {"W", "B"}


def piece_color(piece: str) -> str:
    if piece in {"w", "W"}:
        return WHITE
    if piece in {"b", "B"}:
        return BLACK
    raise ValueError("Unknown piece.")


def opponent(color: str) -> str:
    return BLACK if color == WHITE else WHITE


def move_squares_from_string(move: str) -> list[str]:
    if not move or len(move) % 2 != 0:
        raise ValueError("Invalid move notation.")
    squares = [move[i : i + 2] for i in range(0, len(move), 2)]
    if len(squares) < 2:
        raise ValueError("Move must include at least two squares.")
    return squares


def legal_checkers_moves(state: str) -> list[str]:
    capture_moves, simple_moves = all_checkers_moves(state)
    if capture_moves:
        return capture_moves
    return simple_moves


def all_checkers_moves(state: str) -> tuple[list[str], list[str]]:
    board, turn = parse_state(state)
    capture_moves: set[str] = set()
    simple_moves: set[str] = set()

    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece == ".":
                continue
            if piece_color(piece) != turn:
                continue
            capture_moves.update(generate_capture_sequences(board, row, col, piece))
            simple_moves.update(generate_simple_moves(board, row, col, piece))

    return sorted(capture_moves), sorted(simple_moves)


def generate_simple_moves(
    board: list[list[str]],
    row: int,
    col: int,
    piece: str,
) -> list[str]:
    moves: list[str] = []
    for dr, dc in simple_directions(piece):
        r = row + dr
        c = col + dc
        if not in_bounds(r, c) or not is_dark_square(r, c):
            continue
        if board[r][c] != ".":
            continue
        moves.append(coords_to_square(row, col) + coords_to_square(r, c))
    return moves


def generate_capture_sequences(
    board: list[list[str]],
    row: int,
    col: int,
    piece: str,
) -> list[str]:
    sequences: list[str] = []
    start_square = coords_to_square(row, col)

    for dr, dc in capture_directions(piece):
        mid_row = row + dr // 2
        mid_col = col + dc // 2
        end_row = row + dr
        end_col = col + dc
        if not in_bounds(end_row, end_col) or not is_dark_square(end_row, end_col):
            continue
        if board[end_row][end_col] != ".":
            continue
        middle_piece = board[mid_row][mid_col]
        if middle_piece == "." or piece_color(middle_piece) == piece_color(piece):
            continue

        new_board = clone_board(board)
        new_board[row][col] = "."
        new_board[mid_row][mid_col] = "."
        new_piece = maybe_king(piece, end_row)
        new_board[end_row][end_col] = new_piece

        landing_square = coords_to_square(end_row, end_col)

        if new_piece != piece and not is_king(piece):
            sequences.append(start_square + landing_square)
            continue

        continuation = generate_capture_sequences(
            new_board, end_row, end_col, new_piece
        )
        if continuation:
            for cont in continuation:
                sequences.append(start_square + cont)
        else:
            sequences.append(start_square + landing_square)

    return sequences


def apply_checkers_move(state: str, move: str) -> CheckersMoveResult:
    try:
        board, turn = parse_state(state)
    except ValueError as exc:
        return CheckersMoveResult(False, state, error=str(exc))

    legal_moves = legal_checkers_moves(state)
    if move not in legal_moves:
        return CheckersMoveResult(False, state, error="Illegal move.")

    squares = move_squares_from_string(move)
    start_row, start_col = square_to_coords(squares[0])
    piece = board[start_row][start_col]
    board[start_row][start_col] = "."

    for idx in range(1, len(squares)):
        end_row, end_col = square_to_coords(squares[idx])
        dr = end_row - start_row
        dc = end_col - start_col
        if abs(dr) == 2 and abs(dc) == 2:
            mid_row = start_row + dr // 2
            mid_col = start_col + dc // 2
            board[mid_row][mid_col] = "."
        start_row, start_col = end_row, end_col

    piece = maybe_king(piece, start_row)
    board[start_row][start_col] = piece

    next_turn = opponent(turn)
    new_state = board_to_state(board, next_turn)

    status = "in_progress"
    winner = None
    if not has_pieces(board, next_turn) or not legal_checkers_moves(new_state):
        status = "game_over"
        winner = turn

    return CheckersMoveResult(
        True,
        new_state,
        status=status,
        turn=next_turn,
        last_move=move,
        winner=winner,
    )


def has_pieces(board: list[list[str]], color: str) -> bool:
    for row in board:
        for piece in row:
            if piece == ".":
                continue
            if piece_color(piece) == color:
                return True
    return False


def maybe_king(piece: str, row: int) -> str:
    if is_king(piece):
        return piece
    if piece == "w" and row == 0:
        return "W"
    if piece == "b" and row == 7:
        return "B"
    return piece


def simple_directions(piece: str) -> list[tuple[int, int]]:
    if is_king(piece):
        return [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    if piece == "w":
        return [(-1, -1), (-1, 1)]
    return [(1, -1), (1, 1)]


def capture_directions(piece: str) -> list[tuple[int, int]]:
    if is_king(piece):
        return [(-2, -2), (-2, 2), (2, -2), (2, 2)]
    if piece == "w":
        return [(-2, -2), (-2, 2)]
    return [(2, -2), (2, 2)]


def in_bounds(row: int, col: int) -> bool:
    return 0 <= row < 8 and 0 <= col < 8


def clone_board(board: list[list[str]]) -> list[list[str]]:
    return [list(row) for row in board]


def opponent_move_candidates(state: str, limit: int = 200) -> list[str]:
    moves = legal_checkers_moves(state)
    return moves[:limit]
