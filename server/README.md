# games-mcp server

This directory contains the FastMCP server and game MCP tools.

## Local development

```bash
cd server
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
python app.py
```

## Widget build & serving

The widget bundle is built from `web/` and inlined into the skybridge template.

```bash
cd web
npm install
npm run build
npm run build:checkers
npm run build:blackjack
npm run build:rpg-dice
npm run build:sea-battle
npm run build:slot
npm run build:four-in-a-row
npm run build:tic-tac-toe
npm run build:mancala
```

The server reads `web/widgets/<game>/dist/widget.js` and
`web/widgets/<game>/dist/widget.css` at runtime and replaces the
`/* INLINE_CSS */` and `/* INLINE_JS */` placeholders in the matching template.

To cache-bust the widget, bump `WIDGET_VERSION` in `server/app.py` and rename the
template file (for example `chess-board-v2.html`).

### CSP for local development

By default, the widget CSP only allows the configured `WIDGET_DOMAIN` for
`connect_domains`. To allow local development against
`http://localhost:8000`, set:

```bash
export WIDGET_ALLOW_LOCALHOST=true
```

## Example tool calls

Use MCP Inspector (or any MCP client) to call the tools with these sample inputs.
In production, the model calls these tools in response to user chat input and
auto-renders widget output from `new_*` and `apply_*` tool responses.

```json
// new_chess_game
{
  "side": "white"
}
```

```json
// legal_chess_moves
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
}
```

```json
// apply_chess_move
{
  "gameId": "g_example",
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "moveUci": "e2e4"
}
```

```json
// choose_chess_opponent_move
{
  "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
}
```

```json
// new_checkers_game
{}
```

```json
// legal_checkers_moves
{
  "state": ".b.b.b.b/b.b.b.b./.b.b.b.b/......../......../w.w.w.w./.w.w.w.w/w.w.w.w. w"
}
```

```json
// apply_checkers_move
{
  "gameId": "g_example",
  "state": ".b.b.b.b/b.b.b.b./.b.b.b.b/......../......../w.w.w.w./.w.w.w.w/w.w.w.w. w",
  "move": "b6a5"
}
```

```json
// choose_checkers_opponent_move
{
  "state": ".b.b.b.b/b.b.b.b./.b.b.b.b/......../......../w.w.w.w./.w.w.w.w/w.w.w.w. w"
}
```

```json
// new_blackjack_game
{
  "stack": 1000,
  "bet": 10
}
```

```json
// legal_blackjack_actions
{
  "state": "S:<shoe>|P:AS,8D@active@0@10|D:7C,2H|BK:1000|B:10|T:player|H:0|ST:in_progress|LA:deal|R:-"
}
```

```json
// apply_blackjack_action
{
  "gameId": "g_example",
  "state": "S:<shoe>|P:AS,8D@active@0@10|D:7C,2H|BK:1000|B:10|T:player|H:0|ST:in_progress|LA:deal|R:-",
  "action": "hit"
}
```

```json
// choose_blackjack_dealer_action
{
  "state": "S:<shoe>|P:AS,8D@stood@0@10|D:7C,2H|BK:1000|B:10|T:dealer|H:0|ST:in_progress|LA:stand|R:-"
}
```

```json
// roll_rpg_dice
{
  "sides": 20,
  "count": 2
}
```

```json
// new_sea_battle_game
{}
```

```json
// legal_sea_battle_moves
{
  "state": "P:<board>|O:<board>|F:<fog>|OF:<fog>|T:player|ST:in_progress|LA:-|W:-"
}
```

```json
// apply_sea_battle_move
{
  "gameId": "g_example",
  "state": "P:<board>|O:<board>|F:<fog>|OF:<fog>|T:player|ST:in_progress|LA:-|W:-",
  "coord": "A1"
}
```

```json
// choose_sea_battle_opponent_move
{
  "state": "P:<board>|O:<board>|F:<fog>|OF:<fog>|T:opponent|ST:in_progress|LA:A1:hit|W:-"
}
```

```json
// new_slot_game
{
  "stack": 1000,
  "bet": 10
}
```

```json
// spin_slot
{
  "state": "R:-|BK:1000|B:10|P:0|ST:in_progress|LA:-"
}
```

```json
// new_four_in_a_row_game
{}
```

```json
// legal_four_in_a_row_moves
{
  "state": "G:......./......./......./......./......./.......|T:player|ST:in_progress|LA:-|W:-"
}
```

```json
// apply_four_in_a_row_move
{
  "gameId": "g_example",
  "state": "G:......./......./......./......./......./.......|T:player|ST:in_progress|LA:-|W:-",
  "column": 4
}
```

```json
// choose_four_in_a_row_opponent_move
{
  "state": "G:......./......./......./......./......./...R...|T:opponent|ST:in_progress|LA:4|W:-"
}
```

```json
// new_tic_tac_toe_game
{
  "side": "X"
}
```

```json
// legal_tic_tac_toe_moves
{
  "state": "G:.../.../...|T:player|ST:in_progress|LA:-|W:-|P:X|O:O"
}
```

```json
// apply_tic_tac_toe_move
{
  "gameId": "g_example",
  "state": "G:.../.../...|T:player|ST:in_progress|LA:-|W:-|P:X|O:O",
  "coord": "B2"
}
```

```json
// choose_tic_tac_toe_opponent_move
{
  "state": "G:.../.X./...|T:opponent|ST:in_progress|LA:B2|W:-|P:X|O:O"
}
```

```json
// new_mancala_game
{}
```

```json
// legal_mancala_moves
{
  "state": "P:4,4,4,4,4,4|O:4,4,4,4,4,4|PS:0|OS:0|T:player|ST:in_progress|LA:-|W:-"
}
```

```json
// apply_mancala_move
{
  "gameId": "g_example",
  "state": "P:4,4,4,4,4,4|O:4,4,4,4,4,4|PS:0|OS:0|T:player|ST:in_progress|LA:-|W:-",
  "pit": 3
}
```

```json
// choose_mancala_opponent_move
{
  "state": "P:4,4,0,5,5,5|O:4,4,4,4,4,4|PS:1|OS:0|T:opponent|ST:in_progress|LA:pit3|W:-"
}
```

## Running tests

```bash
cd server
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
pytest
```

## Opponent move constraints & revalidation

The `choose_chess_opponent_move` tool always returns a list of legal UCI moves derived
from the current FEN. By default the server returns all legal moves and caps the
list at 200 entries (rarely exceeded). The tool also provides a strict policy
object that requires the model to choose exactly one UCI move from that list.

When a model-selected move is applied, the server **must** revalidate it using
the same rules engine as `apply_chess_move`. Use
`revalidate_opponent_choice(fen, move_uci, allowed_moves)` to enforce:

- The move is legal for the provided FEN.
- The move is present in the allowed list that was given to the model.

If the selected move is not in the allowed list, the helper returns
`legal: false` with `error: "Opponent move not in allowed list"`, and the UI or
orchestrator should call `choose_chess_opponent_move` again to request a valid move.

## Manual test checklist

- Start the server and open MCP Inspector.
- Call `new_chess_game` (the model would do this when a user asks to start).
- Call `legal_chess_moves` with the returned `fen` to mirror how the model disambiguates chat input.
- Call `apply_chess_move` with a legal move (e.g., `e2e4` from the starting position).
- Call `apply_chess_move` with an illegal move (e.g., `e2e5` from the starting position).
- Call `choose_chess_opponent_move` with the current `fen` and confirm it returns moves + policy.
- Confirm the widget auto-renders from `new_chess_game` and `apply_chess_move` outputs.
- Call `new_checkers_game` and keep the returned `state`.
- Call `legal_checkers_moves` to confirm the legal/forced capture list.
- Call `apply_checkers_move` with a legal move (e.g., `b6a5` from the starting position).
- Call `apply_checkers_move` with an illegal move to confirm `legal: false`.
- Call `choose_checkers_opponent_move` with the current `state` and confirm it returns moves + policy.
- Confirm the widget auto-renders from `new_checkers_game` and `apply_checkers_move` outputs.

## Notes

- Tool handlers live in `tools.py`.
- Chess rules and legality checks live in `chess_rules.py`.
- Checkers rules and legality checks live in `checkers_rules.py`.
- The widget HTML templates are in `templates/chess-board-v1.html` and
  `templates/checkers-board-v1.html`, and `templates/blackjack-board-v1.html`.
- Widget resources are registered in `app.py` with the URIs
  `ui://widget/chess-board-v1.html` and
  `ui://widget/checkers-board-v1.html`, and
  `ui://widget/blackjack-board-v1.html`, served with
  `mimeType: text/html+skybridge`.
- To cache-bust future template changes, version the URI and template name
  (for example `ui://widget/chess-board-v2.html` plus a new
  `templates/chess-board-v2.html`) and update `app.py` accordingly.
