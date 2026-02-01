"""MCP tool handlers for chess-mcp."""

from __future__ import annotations

import uuid
from typing import Literal

import chess
from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult

try:
    from .chess_rules import apply_uci_move, legal_moves_uci, opponent_move_candidates
    from .blackjack_rules import (
        apply_blackjack_action as apply_blackjack_action_rule,
        initial_blackjack_state,
        legal_dealer_actions,
        legal_player_actions,
        parse_state as parse_blackjack_state,
        serialize_state as serialize_blackjack_state,
    )
    from .rpg_dice_rules import roll_dice
    from .sea_battle_rules import (
        apply_sea_battle_move as apply_sea_battle_move_rule,
        initial_sea_battle_state,
        legal_sea_battle_moves as legal_sea_battle_moves_rule,
        opponent_move_candidates as sea_battle_opponent_moves,
        parse_state as parse_sea_battle_state,
    )
    from .slot_rules import (
        initial_slot_state,
        serialize_state as serialize_slot_state,
        spin_slot as spin_slot_rule,
    )
    from .four_in_a_row_rules import (
        apply_four_in_a_row_move as apply_four_in_a_row_move_rule,
        initial_four_in_a_row_state,
        legal_four_in_a_row_moves as legal_four_in_a_row_moves_rule,
        opponent_move_candidates as four_in_a_row_opponent_moves,
    )
    from .checkers_rules import (
        all_checkers_moves,
        apply_checkers_move as apply_checkers_move_rule,
        initial_checkers_state,
        legal_checkers_moves as legal_checkers_moves_rule,
        opponent_move_candidates as checkers_opponent_move_candidates,
    )
except ImportError:  # pragma: no cover - fallback for script execution
    from chess_rules import apply_uci_move, legal_moves_uci, opponent_move_candidates
    from blackjack_rules import (
        apply_blackjack_action as apply_blackjack_action_rule,
        initial_blackjack_state,
        legal_dealer_actions,
        legal_player_actions,
        parse_state as parse_blackjack_state,
        serialize_state as serialize_blackjack_state,
    )
    from rpg_dice_rules import roll_dice
    from sea_battle_rules import (
        apply_sea_battle_move as apply_sea_battle_move_rule,
        initial_sea_battle_state,
        legal_sea_battle_moves as legal_sea_battle_moves_rule,
        opponent_move_candidates as sea_battle_opponent_moves,
        parse_state as parse_sea_battle_state,
    )
    from slot_rules import (
        initial_slot_state,
        serialize_state as serialize_slot_state,
        spin_slot as spin_slot_rule,
    )
    from four_in_a_row_rules import (
        apply_four_in_a_row_move as apply_four_in_a_row_move_rule,
        initial_four_in_a_row_state,
        legal_four_in_a_row_moves as legal_four_in_a_row_moves_rule,
        opponent_move_candidates as four_in_a_row_opponent_moves,
    )
    from checkers_rules import (
        all_checkers_moves,
        apply_checkers_move as apply_checkers_move_rule,
        initial_checkers_state,
        legal_checkers_moves as legal_checkers_moves_rule,
        opponent_move_candidates as checkers_opponent_move_candidates,
    )

CHESS_WIDGET_TEMPLATE_URI = "ui://widget/chess-board-v1.html"
CHECKERS_WIDGET_TEMPLATE_URI = "ui://widget/checkers-board-v1.html"
BLACKJACK_WIDGET_TEMPLATE_URI = "ui://widget/blackjack-board-v1.html"
RPG_DICE_WIDGET_TEMPLATE_URI = "ui://widget/rpg-dice-v1.html"
SEA_BATTLE_WIDGET_TEMPLATE_URI = "ui://widget/sea-battle-v1.html"
SLOT_WIDGET_TEMPLATE_URI = "ui://widget/slot-v1.html"
FOUR_IN_A_ROW_WIDGET_TEMPLATE_URI = "ui://widget/four-in-a-row-v1.html"
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
        name="new_chess_game",
        description="Start a new chess game for chat-driven play.",
        meta=_tool_meta(output_template_uri=CHESS_WIDGET_TEMPLATE_URI),
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
        meta=_tool_meta(output_template_uri=CHESS_WIDGET_TEMPLATE_URI),
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
        name="new_checkers_game",
        description="Start a new checkers game for chat-driven play.",
        meta=_tool_meta(output_template_uri=CHECKERS_WIDGET_TEMPLATE_URI),
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
        meta=_tool_meta(output_template_uri=CHECKERS_WIDGET_TEMPLATE_URI),
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

    @app.tool(
        name="new_blackjack_game",
        description="Start a new blackjack game for chat-driven play.",
        meta=_tool_meta(output_template_uri=BLACKJACK_WIDGET_TEMPLATE_URI),
    )
    def new_blackjack_game(
        stack: int | float | None = None,
        bet: int | float | None = None,
    ) -> ToolResult:
        resolved_stack = 1000.0 if stack is None else float(stack)
        if resolved_stack <= 0:
            payload = {
                "type": "blackjack_snapshot",
                "gameType": "blackjack",
                "gameId": "unknown",
                "state": "",
                "status": "in_progress",
                "turn": "player",
                "legal": False,
                "error": "Stack must be positive.",
            }
            return ToolResult(content=[], structured_content=payload)

        resolved_bet = float(bet) if bet is not None else min(10.0, resolved_stack)
        if resolved_bet <= 0:
            payload = {
                "type": "blackjack_snapshot",
                "gameType": "blackjack",
                "gameId": "unknown",
                "state": "",
                "status": "in_progress",
                "turn": "player",
                "legal": False,
                "error": "Bet must be positive.",
            }
            return ToolResult(content=[], structured_content=payload)
        if resolved_bet > resolved_stack:
            payload = {
                "type": "blackjack_snapshot",
                "gameType": "blackjack",
                "gameId": "unknown",
                "state": "",
                "status": "in_progress",
                "turn": "player",
                "legal": False,
                "error": "Bet cannot exceed stack.",
            }
            return ToolResult(content=[], structured_content=payload)

        game_id = f"g_{uuid.uuid4().hex}"
        state = initial_blackjack_state(stack=resolved_stack, bet=resolved_bet)
        payload = {
            "type": "blackjack_snapshot",
            "gameType": "blackjack",
            "gameId": game_id,
            "state": serialize_blackjack_state(state),
            "status": state.status,
            "turn": state.turn,
            "lastAction": state.last_action,
        }
        if state.results:
            payload["results"] = state.results
        return ToolResult(content=[], structured_content=payload)

    @app.tool(
        name="apply_blackjack_action",
        description=(
            "Validate and apply a blackjack action to the provided state. Intended for "
            "the model to call after the user types an action in chat."
        ),
        meta=_tool_meta(output_template_uri=BLACKJACK_WIDGET_TEMPLATE_URI),
        annotations={
            "readOnlyHint": False,
            "openWorldHint": False,
            "destructiveHint": False,
        },
    )
    def apply_blackjack_action(gameId: str, state: str, action: str) -> ToolResult:  # noqa: N803
        result = apply_blackjack_action_rule(state, action)
        if not result["legal"]:
            payload = {
                "type": "blackjack_snapshot",
                "gameType": "blackjack",
                "gameId": gameId,
                "legal": False,
                "state": result["state"],
                "error": result.get("error") or "Illegal action.",
            }
            return ToolResult(content=[], structured_content=payload)

        payload = {
            "type": "blackjack_snapshot",
            "gameType": "blackjack",
            "gameId": gameId,
            "legal": True,
            "state": result["state"],
            "status": result["status"],
            "turn": result["turn"],
            "lastAction": result.get("lastAction"),
            "handIndex": result.get("handIndex"),
        }
        if result.get("results"):
            payload["results"] = result["results"]
        return ToolResult(content=[], structured_content=payload)

    @app.tool(
        name="legal_blackjack_actions",
        description=(
            "List legal blackjack actions for the current state so the model can "
            "interpret chat input."
        ),
        meta=_tool_meta(),
        annotations={"readOnlyHint": True},
    )
    def legal_blackjack_actions(state: str) -> ToolResult:
        actions: list[str] = []
        turn = "player"
        hand_index = 0
        try:
            parsed = parse_blackjack_state(state)
            actions = legal_player_actions(parsed)
            turn = parsed.turn
            hand_index = parsed.hand_index
        except ValueError:
            actions = []
        payload = {
            "type": "legal_actions",
            "gameType": "blackjack",
            "actions": actions,
            "turn": turn,
            "handIndex": hand_index,
        }
        return ToolResult(content=[], structured_content=payload)

    @app.tool(
        name="choose_blackjack_dealer_action",
        description=(
            "Return legal dealer actions and opponent selection policy for the "
            "model-driven dealer turn loop."
        ),
        meta=_tool_meta(),
    )
    def choose_blackjack_dealer_action(state: str) -> ToolResult:
        actions: list[str] = []
        content = []
        try:
            parsed = parse_blackjack_state(state)
            actions = legal_dealer_actions(parsed)
        except ValueError:
            actions = []
        if not actions:
            content = [
                {
                    "type": "text",
                    "text": "No legal dealer actions available; the game is over.",
                }
            ]
        payload = {
            "type": "opponent_choice",
            "gameType": "blackjack",
            "actions": actions,
            "policy": {
                "mustChooseFromActions": True,
                "chooseExactlyOne": True,
            },
        }
        return ToolResult(content=content, structured_content=payload)

    @app.tool(
        name="roll_rpg_dice",
        description="Roll one or more RPG dice (d4, d6, d8, d10, d12, d20, d100).",
        meta=_tool_meta(output_template_uri=RPG_DICE_WIDGET_TEMPLATE_URI),
        annotations={
            "readOnlyHint": False,
            "openWorldHint": False,
            "destructiveHint": False,
        },
    )
    def roll_rpg_dice(sides: int, count: int = 1) -> ToolResult:
        try:
            result = roll_dice(sides=sides, count=count)
        except ValueError as exc:
            payload = {
                "type": "rpg_dice_roll",
                "gameType": "rpg_dice",
                "legal": False,
                "sides": sides,
                "count": count,
                "rolls": [],
                "total": 0,
                "error": str(exc),
            }
            return ToolResult(content=[], structured_content=payload)

        payload = {
            "type": "rpg_dice_roll",
            "gameType": "rpg_dice",
            "legal": True,
            "sides": result.sides,
            "count": result.count,
            "rolls": result.rolls,
            "total": sum(result.rolls),
        }
        return ToolResult(content=[], structured_content=payload)

    @app.tool(
        name="new_sea_battle_game",
        description="Start a new Sea Battle game for chat-driven play.",
        meta=_tool_meta(output_template_uri=SEA_BATTLE_WIDGET_TEMPLATE_URI),
    )
    def new_sea_battle_game() -> ToolResult:
        game_id = f"g_{uuid.uuid4().hex}"
        state = initial_sea_battle_state()
        payload = {
            "type": "sea_battle_snapshot",
            "gameType": "sea_battle",
            "gameId": game_id,
            "state": state,
            "status": "in_progress",
            "turn": "player",
        }
        return ToolResult(content=[], structured_content=payload)

    @app.tool(
        name="apply_sea_battle_move",
        description=(
            "Validate and apply a Sea Battle move to the provided state. Intended for "
            "the model to call after the user types a coordinate in chat."
        ),
        meta=_tool_meta(output_template_uri=SEA_BATTLE_WIDGET_TEMPLATE_URI),
        annotations={
            "readOnlyHint": False,
            "openWorldHint": False,
            "destructiveHint": False,
        },
    )
    def apply_sea_battle_move(gameId: str, state: str, coord: str) -> ToolResult:  # noqa: N803
        result = apply_sea_battle_move_rule(state, coord)
        if not result.legal:
            payload = {
                "type": "sea_battle_snapshot",
                "gameType": "sea_battle",
                "gameId": gameId,
                "legal": False,
                "state": result.state,
                "error": result.error or "Illegal move.",
            }
            return ToolResult(content=[], structured_content=payload)

        payload = {
            "type": "sea_battle_snapshot",
            "gameType": "sea_battle",
            "gameId": gameId,
            "legal": True,
            "state": result.state,
            "status": result.status,
            "turn": result.turn,
            "lastAction": result.last_action,
        }
        if result.winner:
            payload["winner"] = result.winner
        return ToolResult(content=[], structured_content=payload)

    @app.tool(
        name="legal_sea_battle_moves",
        description=(
            "List legal Sea Battle moves for a given state so the model can interpret "
            "chat input."
        ),
        meta=_tool_meta(),
        annotations={"readOnlyHint": True},
    )
    def legal_sea_battle_moves(state: str) -> ToolResult:
        payload = {
            "type": "legal_moves",
            "gameType": "sea_battle",
            "moves": legal_sea_battle_moves_rule(state),
        }
        return ToolResult(content=[], structured_content=payload)

    @app.tool(
        name="choose_sea_battle_opponent_move",
        description=(
            "Return legal moves and opponent selection policy for the model-driven "
            "Sea Battle opponent turn loop."
        ),
        meta=_tool_meta(),
    )
    def choose_sea_battle_opponent_move(state: str) -> ToolResult:
        moves = sea_battle_opponent_moves(state, limit=OPPONENT_MOVE_CAP)
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
            "gameType": "sea_battle",
            "moves": moves,
            "policy": {
                "mustChooseFromMoves": True,
                "chooseExactlyOne": True,
            },
        }
        return ToolResult(content=content, structured_content=payload)

    @app.tool(
        name="new_slot_game",
        description="Start a new slot machine session with an optional stack and bet.",
        meta=_tool_meta(output_template_uri=SLOT_WIDGET_TEMPLATE_URI),
    )
    def new_slot_game(
        stack: int | float | None = None,
        bet: int | float | None = None,
    ) -> ToolResult:
        resolved_stack = 1000.0 if stack is None else float(stack)
        resolved_bet = float(bet) if bet is not None else min(10.0, resolved_stack)
        try:
            state = initial_slot_state(stack=resolved_stack, bet=resolved_bet)
        except ValueError as exc:
            payload = {
                "type": "slot_snapshot",
                "gameType": "slot",
                "legal": False,
                "state": "",
                "error": str(exc),
            }
            return ToolResult(content=[], structured_content=payload)

        payload = {
            "type": "slot_snapshot",
            "gameType": "slot",
            "state": serialize_slot_state(state),
            "stack": state.stack,
            "bet": state.bet,
            "reels": state.reels,
            "payout": state.payout,
            "status": state.status,
            "lastAction": state.last_action,
        }
        return ToolResult(content=[], structured_content=payload)

    @app.tool(
        name="spin_slot",
        description="Spin the slot reels for the given state.",
        meta=_tool_meta(output_template_uri=SLOT_WIDGET_TEMPLATE_URI),
        annotations={
            "readOnlyHint": False,
            "openWorldHint": False,
            "destructiveHint": False,
        },
    )
    def spin_slot(state: str) -> ToolResult:
        result = spin_slot_rule(state)
        if not result["legal"]:
            payload = {
                "type": "slot_snapshot",
                "gameType": "slot",
                "legal": False,
                "state": result["state"],
                "error": result.get("error") or "Illegal spin.",
            }
            return ToolResult(content=[], structured_content=payload)

        payload = {
            "type": "slot_snapshot",
            "gameType": "slot",
            "legal": True,
            "state": result["state"],
            "stack": result["stack"],
            "bet": result["bet"],
            "reels": result["reels"],
            "payout": result["payout"],
            "status": result["status"],
            "lastAction": result["lastAction"],
        }
        return ToolResult(content=[], structured_content=payload)

    @app.tool(
        name="new_four_in_a_row_game",
        description="Start a new Four-in-a-Row game for chat-driven play.",
        meta=_tool_meta(output_template_uri=FOUR_IN_A_ROW_WIDGET_TEMPLATE_URI),
    )
    def new_four_in_a_row_game() -> ToolResult:
        game_id = f"g_{uuid.uuid4().hex}"
        state = initial_four_in_a_row_state()
        payload = {
            "type": "four_in_a_row_snapshot",
            "gameType": "four_in_a_row",
            "gameId": game_id,
            "state": state,
            "status": "in_progress",
            "turn": "player",
        }
        return ToolResult(content=[], structured_content=payload)

    @app.tool(
        name="apply_four_in_a_row_move",
        description=(
            "Validate and apply a Four-in-a-Row move to the provided state. Intended for "
            "the model to call after the user types a column number in chat."
        ),
        meta=_tool_meta(output_template_uri=FOUR_IN_A_ROW_WIDGET_TEMPLATE_URI),
        annotations={
            "readOnlyHint": False,
            "openWorldHint": False,
            "destructiveHint": False,
        },
    )
    def apply_four_in_a_row_move(
        gameId: str,
        state: str,
        column: int,
    ) -> ToolResult:  # noqa: N803
        result = apply_four_in_a_row_move_rule(state, column)
        if not result.legal:
            payload = {
                "type": "four_in_a_row_snapshot",
                "gameType": "four_in_a_row",
                "gameId": gameId,
                "legal": False,
                "state": result.state,
                "error": result.error or "Illegal move.",
            }
            return ToolResult(content=[], structured_content=payload)

        payload = {
            "type": "four_in_a_row_snapshot",
            "gameType": "four_in_a_row",
            "gameId": gameId,
            "legal": True,
            "state": result.state,
            "status": result.status,
            "turn": result.turn,
            "lastAction": result.last_action,
        }
        if result.winner:
            payload["winner"] = result.winner
        return ToolResult(content=[], structured_content=payload)

    @app.tool(
        name="legal_four_in_a_row_moves",
        description=(
            "List legal Four-in-a-Row moves for a given state so the model can interpret "
            "chat input."
        ),
        meta=_tool_meta(),
        annotations={"readOnlyHint": True},
    )
    def legal_four_in_a_row_moves(state: str) -> ToolResult:
        payload = {
            "type": "legal_moves",
            "gameType": "four_in_a_row",
            "moves": legal_four_in_a_row_moves_rule(state),
        }
        return ToolResult(content=[], structured_content=payload)

    @app.tool(
        name="choose_four_in_a_row_opponent_move",
        description=(
            "Return legal moves and opponent selection policy for the model-driven "
            "Four-in-a-Row opponent turn loop."
        ),
        meta=_tool_meta(),
    )
    def choose_four_in_a_row_opponent_move(state: str) -> ToolResult:
        moves = four_in_a_row_opponent_moves(state, limit=OPPONENT_MOVE_CAP)
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
            "gameType": "four_in_a_row",
            "moves": moves,
            "policy": {
                "mustChooseFromMoves": True,
                "chooseExactlyOne": True,
            },
        }
        return ToolResult(content=content, structured_content=payload)
