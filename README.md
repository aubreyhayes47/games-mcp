# games-mcp

A minimal, **capability-first** ChatGPT App library for turn-based and casino-style
games. It ships with chess and checkers today and is designed to expand cleanly
as new games are added.

## Current and planned games

Implemented today:

* Chess (LLM opponent constrained to legal moves)
* Checkers (algebraic square notation)
* Blackjack (LLM dealer constrained to legal actions)

Planned next:

* Heads-up NL Hold'em (LLM opponent)
* Slot machine

## Design principles

* **Authoritative state:** all game transitions come from tools; no optimistic UI.
* **Idempotent tools:** `(state, move) -> new_state` for safe retries.
* **Small structuredContent:** only what the model needs; UI-only data in `_meta`.
* **Single render tool per game:** only `render_chess_game` and `render_checkers_game` return widgets.

## Architecture

1. **Widget UI (React)**
   * Runs inside ChatGPT as an iframe (`text/html+skybridge`).
   * Renders game state from `window.openai.toolOutput`.
   * Display-only; users input moves via chat.

2. **MCP Server (Python / FastMCP)**
   * Registers the widget resource.
   * Exposes game tools for starting games and applying moves.
   * Enforces authoritative state transitions and idempotency.

3. **Model (ChatGPT)**
   * Orchestrates tool calls.
   * If an LLM opponent is enabled, it must choose from tool-provided legal moves.

## Tool contracts (current: chess + checkers + blackjack)

The chess implementation is the canonical reference for tool behavior and payload
shape. Checkers follows the same principles with a different state format.

### Tool: `render_chess_game`

**Input**

* `snapshot`: object (must include `fen` and `gameId`, plus optional status fields)

**Output (structuredContent)**

```json
{
  "type": "chess_snapshot",
  "gameType": "chess",
  "gameId": "g_123",
  "fen": "<FEN>",
  "status": "in_progress",
  "turn": "w"
}
```

### Tool: `new_chess_game`

**Input**

* `side` (optional): `"white" | "black"`

**Output (structuredContent)**

```json
{
  "type": "chess_snapshot",
  "gameType": "chess",
  "gameId": "g_123",
  "fen": "<FEN>",
  "status": "in_progress",
  "turn": "w"
}
```

### Tool: `apply_chess_move`

**Input**

* `gameId`
* `fen`
* `moveUci` (string): UCI (`e2e4`, `e7e8q`)

**Output (structuredContent)**

```json
{
  "type": "chess_snapshot",
  "gameType": "chess",
  "gameId": "g_123",
  "legal": true,
  "fen": "<NEW_FEN>",
  "status": "in_progress",
  "turn": "b",
  "lastMove": { "uci": "e2e4", "san": "e4" },
  "check": false
}
```

If illegal:

```json
{
  "type": "chess_snapshot",
  "gameType": "chess",
  "gameId": "g_123",
  "legal": false,
  "fen": "<UNCHANGED_FEN>",
  "error": "Illegal move: king would be in check"
}
```

### Tool: `legal_chess_moves` (read-only)

**Input**

* `fen`

**Output (structuredContent)**

```json
{ "type": "legal_moves", "movesUci": ["e2e4", "g1f3"] }
```

### Tool: `choose_chess_opponent_move`

**Input**

* `fen`

**Output (structuredContent)**

```json
{
  "type": "opponent_choice",
  "movesUci": ["g8f6", "d7d5", "e7e5"],
  "policy": {
    "mustChooseFromMovesUci": true,
    "chooseExactlyOne": true
  }
}
```

## Tool contracts (current: checkers)

### Checkers state format

Checkers uses an 8x8 board string plus the side to move:

```
<row8>/<row7>/<row6>/<row5>/<row4>/<row3>/<row2>/<row1> <turn>
```

Rows use `w`/`W` for white man/king, `b`/`B` for black man/king, and `.` for empty.

### Tool: `render_checkers_game`

**Input**

* `snapshot`: object (must include `state` and `gameId`, plus optional status fields)

**Output (structuredContent)**

```json
{
  "type": "checkers_snapshot",
  "gameType": "checkers",
  "gameId": "g_123",
  "state": "<STATE>",
  "status": "in_progress",
  "turn": "w"
}
```

### Tool: `new_checkers_game`

**Output (structuredContent)**

```json
{
  "type": "checkers_snapshot",
  "gameType": "checkers",
  "gameId": "g_123",
  "state": "<STATE>",
  "status": "in_progress",
  "turn": "w"
}
```

### Tool: `apply_checkers_move`

**Input**

* `gameId`
* `state`
* `move` (string): algebraic squares (e.g., `b6a5`, `b6d4f2`)

**Output (structuredContent)**

```json
{
  "type": "checkers_snapshot",
  "gameType": "checkers",
  "gameId": "g_123",
  "legal": true,
  "state": "<NEW_STATE>",
  "status": "in_progress",
  "turn": "b",
  "lastMove": { "notation": "b6a5" }
}
```

If illegal:

```json
{
  "type": "checkers_snapshot",
  "gameType": "checkers",
  "gameId": "g_123",
  "legal": false,
  "state": "<UNCHANGED_STATE>",
  "error": "Illegal move."
}
```

### Tool: `legal_checkers_moves` (read-only)

**Input**

* `state`

**Output (structuredContent)**

```json
{
  "type": "legal_moves",
  "gameType": "checkers",
  "moves": ["b6a5", "b6d4f2"],
  "forcedCaptures": ["b6d4f2"],
  "mustCapture": true
}
```

### Tool: `choose_checkers_opponent_move`

**Input**

* `state`

**Output (structuredContent)**

```json
{
  "type": "opponent_choice",
  "gameType": "checkers",
  "moves": ["b6a5", "b6d4f2"],
  "policy": {
    "mustChooseFromMoves": true,
    "chooseExactlyOne": true
  }
}
```

## Tool contracts (current: blackjack)

### Blackjack state format

```
S:<shoe>|P:<hand1;hand2>|D:<dealer>|T:<turn>|H:<hand_index>|ST:<status>|LA:<last_action>|R:<results>
```

Hands are encoded as `cards@state@doubled`, for example:

```
P:AS,8D@active@0;7C,7H@active@0
```

`R` is optional and contains per-hand results when the game is over (`win`,
`lose`, `push`, `bust`, `blackjack`).

### Tool: `render_blackjack_game`

**Input**

* `snapshot`: object (must include `state` and `gameId`, plus optional status fields)

**Output (structuredContent)**

```json
{
  "type": "blackjack_snapshot",
  "gameType": "blackjack",
  "gameId": "g_123",
  "state": "<STATE>",
  "status": "in_progress",
  "turn": "player"
}
```

### Tool: `new_blackjack_game`

**Output (structuredContent)**

```json
{
  "type": "blackjack_snapshot",
  "gameType": "blackjack",
  "gameId": "g_123",
  "state": "<STATE>",
  "status": "in_progress",
  "turn": "player",
  "lastAction": "deal"
}
```

### Tool: `apply_blackjack_action`

**Input**

* `gameId`
* `state`
* `action` (string): `hit`, `stand`, `double`, `split`

**Output (structuredContent)**

```json
{
  "type": "blackjack_snapshot",
  "gameType": "blackjack",
  "gameId": "g_123",
  "legal": true,
  "state": "<NEW_STATE>",
  "status": "in_progress",
  "turn": "dealer",
  "lastAction": "hit",
  "handIndex": 0
}
```

If illegal:

```json
{
  "type": "blackjack_snapshot",
  "gameType": "blackjack",
  "gameId": "g_123",
  "legal": false,
  "state": "<UNCHANGED_STATE>",
  "error": "Illegal action."
}
```

### Tool: `legal_blackjack_actions` (read-only)

**Input**

* `state`

**Output (structuredContent)**

```json
{
  "type": "legal_actions",
  "gameType": "blackjack",
  "actions": ["hit", "stand", "double"],
  "turn": "player",
  "handIndex": 0
}
```

### Tool: `choose_blackjack_dealer_action`

**Input**

* `state`

**Output (structuredContent)**

```json
{
  "type": "opponent_choice",
  "gameType": "blackjack",
  "actions": ["hit", "stand"],
  "policy": {
    "mustChooseFromActions": true,
    "chooseExactlyOne": true
  }
}
```

## Repo layout

```
games-mcp/
  server/
    app.py                 # MCP server (FastMCP/FastAPI)
    chess_rules.py         # move parsing + legality + FEN transitions
    checkers_rules.py      # move parsing + legality + state transitions
    storage.py             # optional: gameId -> state/history persistence
    templates/
      chess-board-v1.html  # text/html+skybridge wrapper
      checkers-board-v1.html
  web/
    widgets/
      chess/
        src/
          App.jsx          # React widget
          hooks/
            useOpenAiGlobal.js
        dist/
          widget.js        # bundled JS (inlined into template)
          widget.css       # bundled CSS (inlined into template)
      checkers/
        src/
          App.jsx
          hooks/
            useOpenAiGlobal.js
        dist/
          widget.js
          widget.css
  README.md
```

## Build the widget

```bash
cd web
npm install
npm run build
```

To build the checkers widget:

```bash
npm run build:checkers
```

Build output lives in `web/widgets/chess/dist/`:

* `web/widgets/chess/dist/widget.js`
* `web/widgets/chess/dist/widget.css`

Checkers output lives in `web/widgets/checkers/dist/`:

* `web/widgets/checkers/dist/widget.js`
* `web/widgets/checkers/dist/widget.css`

## How the server loads the widget

* `server/app.py` reads bundles from `web/widgets/<game>/dist/`.
* `server/templates/chess-board-v1.html` and `server/templates/checkers-board-v1.html` contain placeholders for inline CSS/JS:
  * `/* INLINE_CSS */`
  * `/* INLINE_JS */`
* The server replaces those markers at runtime and returns a single
  `text/html+skybridge` document.

## Local run (HTTP)

```bash
python server/run_http.py
```

## MCP smoke test (HTTP)

With the server running locally, run:

```bash
./.venv/bin/python scripts/mcp_smoke_test.py
```

This exercises chess, checkers, and blackjack tool flows over HTTP.

## Testing (current: chess + checkers + blackjack)

At minimum, tests should cover:

* normal moves (e2e4)
* illegal move (moving pinned piece exposing king)
* castling
* en passant
* promotion
* check/checkmate detection
* forced captures
* multi-jump captures
* kinging
* legal blackjack actions (hit/stand/double/split)
* split hand sequencing and handIndex updates
* double action transitions
* dealer action policy (stands on soft 17)
* blackjack game over results

Manual test checklist:

* Build the widget: `cd web && npm install && npm run build`
* Build checkers: `cd web && npm run build:checkers`
* Build blackjack: `cd web && npm run build:blackjack`
* Start a new game via chat (model calls `new_chess_game`).
* Type a legal move and confirm `render_chess_game` updates the board.
* Type an illegal move and confirm the error with no board change.
* Confirm the opponent loop runs after a legal move.
* Reach checkmate/stalemate and confirm status renders.
* Start a checkers game via chat (model calls `new_checkers_game`).
* Type a legal move and confirm `render_checkers_game` updates the board.
* Type an illegal move and confirm the error with no board change.
* Confirm the opponent loop runs after a legal checkers move.
* Confirm forced captures are enforced.
* Start a blackjack game via chat (model calls `new_blackjack_game`).
* Type `hit`, `stand`, `double`, and `split` as legal and confirm `render_blackjack_game` updates the table.
* Type an illegal action and confirm the error with no table change.
* Confirm the dealer loop runs after player actions and respects the tool action list.
* Reach game over and confirm results render per hand.
