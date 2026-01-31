"""MCP tool handlers for chess-mcp."""

from __future__ import annotations

import uuid
from typing import Literal

import chess
from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult

try:
    from .chess_rules import apply_uci_move, legal_moves_uci, opponent_move_candidates
    from .checkers_rules import (
        all_checkers_moves,
        apply_checkers_move as apply_checkers_move_rule,
        initial_checkers_state,
        legal_checkers_moves as legal_checkers_moves_rule,
        opponent_move_candidates as checkers_opponent_move_candidates,
    )
except ImportError:  # pragma: no cover - fallback for script execution
    from chess_rules import apply_uci_move, legal_moves_uci, opponent_move_candidates
    from checkers_rules import (
        all_checkers_moves,
        apply_checkers_move as apply_checkers_move_rule,
        initial_checkers_state,
        legal_checkers_moves as legal_checkers_moves_rule,
        opponent_move_candidates as checkers_opponent_move_candidates,
    )

CHESS_WIDGET_TEMPLATE_URI = "ui://widget/chess-board-v1.html"
CHECKERS_WIDGET_TEMPLATE_URI = "ui://widget/checkers-board-v1.html"
OPPONENT_MOVE_CAP = 200


def _tool_meta(
    *,
    output_template_uri: str | None = None,
    widget_accessible: bool = False,
) -> dict[str, object]:
    meta: dict[str, object] = {}
    if output_template_uri:
        meta["openai/outputTemplate"] = output_template_uri
    if widget_accessible:
        meta["openai/widgetAccessible"] = True
    return meta


def register_tools(app: FastMCP) -> None:
    """Register MCP tools on the provided FastMCP app instance."""

    @app.tool(
        name="render_chess_game",
        description="Render the chess widget for the provided snapshot.",
        meta=_tool_meta(output_template_uri=CHESS_WIDGET_TEMPLATE_URI),
    )
    def render_chess_game(snapshot: dict) -> ToolResult:
        if not isinstance(snapshot, dict):
            payload = {
                "type": "chess_snapshot",
                "gameType": "chess",
                "gameId": "unknown",
                "fen": "",
                "status": "in_progress",
                "turn": "w",
                "legal": False,
                "error": "Invalid snapshot payload.",
            }
            return ToolResult(content=[], structured_content=payload)
        snapshot_payload = {**snapshot}
        snapshot_payload.setdefault("type", "chess_snapshot")
        snapshot_payload.setdefault("gameType", "chess")
        return ToolResult(content=[], structured_content=snapshot_payload)

    @app.tool(
        name="new_chess_game",
        description="Start a new chess game for chat-driven play.",
        meta=_tool_meta(),
    )
    def new_chess_game(side: Literal["white", "black"] | None = None) -> ToolResult:
        board = chess.Board()
        if side == "black":
            board.turn = chess.BLACK
        game_id = f"g_{uuid.uuid4().hex}"
        payload = {
            "type": "chess_snapshot",
            "gameType": "chess",
            "gameId": game_id,
            "fen": board.fen(),
            "status": "in_progress",
            "turn": "w" if board.turn == chess.WHITE else "b",
        }
        return ToolResult(content=[], structured_content=payload)

    @app.tool(
        name="apply_chess_move",
        description=(
            "Validate and apply a UCI move to the provided FEN. Intended for the "
            "model to call after the user types a move in chat."
        ),
        meta=_tool_meta(),
        annotations={
            "readOnlyHint": False,
            "openWorldHint": False,
            "destructiveHint": False,
        },
    )
    def apply_chess_move(gameId: str, fen: str, moveUci: str) -> ToolResult:  # noqa: N803
        result = apply_uci_move(fen, moveUci)
        if not result["legal"]:
            payload = {
                "type": "chess_snapshot",
                "gameType": "chess",
                "gameId": gameId,
                "legal": False,
                "fen": result["fen"],
                "error": result["error"],
            }
            return ToolResult(content=[], structured_content=payload)

        payload = {
            "type": "chess_snapshot",
            "gameType": "chess",
            "gameId": gameId,
            "legal": True,
            "fen": result["fen"],
            "status": result["status"],
            "turn": result["turn"],
            "lastMove": {"uci": result["uci"], "san": result["san"]},
            "check": result["check"],
        }
        return ToolResult(content=[], structured_content=payload)

    @app.tool(
        name="legal_chess_moves",
        description=(
            "List legal moves for a given FEN so the model can interpret chat input."
        ),
        meta=_tool_meta(),
        annotations={"readOnlyHint": True},
    )
    def legal_chess_moves(fen: str) -> ToolResult:
        payload = {
            "type": "legal_moves",
            "movesUci": legal_moves_uci(fen),
        }
        return ToolResult(content=[], structured_content=payload)

    @app.tool(
        name="choose_chess_opponent_move",
        description=(
            "Return legal moves and opponent selection policy for the "
            "model-driven opponent turn loop."
        ),
        meta=_tool_meta(),
    )
    def choose_chess_opponent_move(fen: str) -> ToolResult:
        moves = opponent_move_candidates(fen, limit=OPPONENT_MOVE_CAP)
        content = []
        if not moves:
            content = [
                {
                    "type": "text",
                    "text": "No legal moves available; the game is over.",
                }
            ]
        payload = {
            "type": "opponent_choice",
            "movesUci": moves,
            "policy": {
                "mustChooseFromMovesUci": True,
                "chooseExactlyOne": True,
            },
        }
        return ToolResult(content=content, structured_content=payload)

    @app.tool(
        name="render_checkers_game",
        description="Render the checkers widget for the provided snapshot.",
        meta=_tool_meta(output_template_uri=CHECKERS_WIDGET_TEMPLATE_URI),
    )
    def render_checkers_game(snapshot: dict) -> ToolResult:
        if not isinstance(snapshot, dict):
            payload = {
                "type": "checkers_snapshot",
                "gameType": "checkers",
                "gameId": "unknown",
                "state": "",
                "status": "in_progress",
                "turn": "w",
                "legal": False,
                "error": "Invalid snapshot payload.",
            }
            return ToolResult(content=[], structured_content=payload)
        snapshot_payload = {**snapshot}
        snapshot_payload.setdefault("type", "checkers_snapshot")
        snapshot_payload.setdefault("gameType", "checkers")
        return ToolResult(content=[], structured_content=snapshot_payload)

    @app.tool(
        name="new_checkers_game",
        description="Start a new checkers game for chat-driven play.",
        meta=_tool_meta(),
    )
    def new_checkers_game() -> ToolResult:
        game_id = f"g_{uuid.uuid4().hex}"
        payload = {
            "type": "checkers_snapshot",
            "gameType": "checkers",
            "gameId": game_id,
            "state": initial_checkers_state(),
            "status": "in_progress",
            "turn": "w",
        }
        return ToolResult(content=[], structured_content=payload)

    @app.tool(
        name="apply_checkers_move",
        description=(
            "Validate and apply a checkers move to the provided state. Intended for the "
            "model to call after the user types a move in chat."
        ),
        meta=_tool_meta(),
        annotations={
            "readOnlyHint": False,
            "openWorldHint": False,
            "destructiveHint": False,
        },
    )
    def apply_checkers_move(gameId: str, state: str, move: str) -> ToolResult:  # noqa: N803
        result = apply_checkers_move_rule(state, move)
        if not result.legal:
            payload = {
                "type": "checkers_snapshot",
                "gameType": "checkers",
                "gameId": gameId,
                "legal": False,
                "state": result.state,
                "error": result.error or "Illegal move.",
            }
            return ToolResult(content=[], structured_content=payload)

        payload = {
            "type": "checkers_snapshot",
            "gameType": "checkers",
            "gameId": gameId,
            "legal": True,
            "state": result.state,
            "status": result.status,
            "turn": result.turn,
            "lastMove": {"notation": result.last_move},
        }
        if result.winner:
            payload["winner"] = result.winner
        return ToolResult(content=[], structured_content=payload)

    @app.tool(
        name="legal_checkers_moves",
        description=(
            "List legal checkers moves for a given state so the model can interpret chat "
            "input."
        ),
        meta=_tool_meta(),
        annotations={"readOnlyHint": True},
    )
    def legal_checkers_moves(state: str) -> ToolResult:
        capture_moves, simple_moves = all_checkers_moves(state)
        must_capture = bool(capture_moves)
        all_moves = capture_moves + [
            move for move in simple_moves if move not in capture_moves
        ]
        payload = {
            "type": "legal_moves",
            "gameType": "checkers",
            "moves": all_moves,
            "forcedCaptures": capture_moves,
            "mustCapture": must_capture,
        }
        return ToolResult(content=[], structured_content=payload)

    @app.tool(
        name="choose_checkers_opponent_move",
        description=(
            "Return legal moves and opponent selection policy for the model-driven "
            "checkers opponent turn loop."
        ),
        meta=_tool_meta(),
    )
    def choose_checkers_opponent_move(state: str) -> ToolResult:
        moves = checkers_opponent_move_candidates(state, limit=OPPONENT_MOVE_CAP)
        content = []
        if not moves:
            content = [
                {
                    "type": "text",
                    "text": "No legal moves available; the game is over.",
                }
            ]
        payload = {
            "type": "opponent_choice",
            "gameType": "checkers",
            "moves": moves,
            "policy": {
                "mustChooseFromMoves": True,
                "chooseExactlyOne": True,
            },
        }
        return ToolResult(content=content, structured_content=payload)
