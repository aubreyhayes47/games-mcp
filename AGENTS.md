# AGENTS.md

This file is the **single source of truth** for how coding agents should work on this repo.

Repo: **games-mcp**
Stack preference: **Python (FastMCP)** for the MCP server, React widget for UI.

## 0) One-paragraph goal

Build a minimal ChatGPT Apps SDK **games library** that exposes authoritative game tools and a
display-only widget UI. Chess, checkers, blackjack, RPG dice, and Sea Battle are implemented
today; planned additions include heads-up NL Hold'em (LLM opponent), a slot machine,
Four-in-a-Row, Tic-Tac-Toe, and Roulette (American).

## 1) Definition of Done (current implementations: chess + checkers + blackjack)

A change is “done” when all of the following are true:

1. **Widget renders a board/table** from `window.openai.toolOutput` inside the ChatGPT iframe.
2. User **types moves in chat** (no board interaction).
3. The model calls `apply_chess_move`, `apply_checkers_move`, or `apply_blackjack_action` based on chat input.
4. The model receives widget output directly from `new_*` and `apply_*` tool responses (auto-render).
   * If `legal: false`, the model reports the error and does not change the board.
5. After a legal player move, the model runs the **opponent/dealer turn loop**:
   * Chess/Checkers: call `choose_chess_opponent_move(fen)` or `choose_checkers_opponent_move(state)`
     and select exactly one move from the list, apply it via the matching apply tool,
     then the updated snapshot auto-renders from the apply tool response.
   * Blackjack: call `choose_blackjack_dealer_action(state)` and select exactly one
     action from the list, apply it via `apply_blackjack_action`, then auto-render
     from the tool response.
6. Game over states are rendered correctly.
7. Works locally and in production behind HTTPS (e.g., Render).

## 2) Non-negotiable invariants

These are hard rules. If your implementation violates them, it is wrong.

### 2.1 Canonical truth

* **Canonical state is the server-confirmed game snapshot** returned by tools.
* The widget must never “optimistically commit” a move.

### 2.2 LLM opponent constraints

* The LLM opponent/dealer **must choose from** a tool-provided list of legal moves/actions.
* The server must **re-validate** the chosen move/action via the game-specific apply tool before committing.

### 2.3 No game logic in prose

* No game state transitions are inferred from chat text.
* Every state transition is derived from a tool response.

### 2.4 Payload discipline

* `structuredContent` is **small** and stable.
* Put bulky or UI-only information in `_meta` (or omit for v1).

## 3) Current tool contracts (chess + checkers + blackjack)

The chess tool contracts are the reference for future games. Checkers follows the same
constraints and payload discipline with a different state format.

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

## Checkers tool contracts

### Checkers state format

```
<row8>/<row7>/<row6>/<row5>/<row4>/<row3>/<row2>/<row1> <turn>
```

Rows use `w`/`W` for white man/king, `b`/`B` for black man/king, and `.` for empty.

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

## Blackjack tool contracts

### Blackjack state format

```
S:<shoe>|P:<hand1;hand2>|D:<dealer>|BK:<stack>|B:<bet>|T:<turn>|H:<hand_index>|ST:<status>|LA:<last_action>|R:<results>
```

Hands are encoded as `cards@state@doubled@bet`, for example:

```
P:AS,8D@active@0@10;7C,7H@active@0@10
```

### Tool: `new_blackjack_game`

**Input**

* `stack` (optional, default 1000)
* `bet` (optional, default 10 or `stack` if smaller)

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

## 4) Repo layout (current)

```
games-mcp/
  server/
    app.py                 # MCP server (FastMCP/FastAPI)
    chess_rules.py         # move parsing + legality + FEN transitions
    checkers_rules.py      # move parsing + legality + state transitions
    blackjack_rules.py     # action parsing + legality + state transitions
    storage.py             # optional: gameId -> state/history persistence
    templates/
      chess-board-v1.html  # text/html+skybridge wrapper
      checkers-board-v1.html
      blackjack-board-v1.html
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
      blackjack/
        src/
          App.jsx
          hooks/
            useOpenAiGlobal.js
        dist/
          widget.js
          widget.css
  README.md
```
