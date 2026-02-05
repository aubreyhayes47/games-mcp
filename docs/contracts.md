# Tool Contracts

This document defines the tool inputs/outputs and state formats for all current games.

## Chess

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

## Checkers

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

## Blackjack

### Blackjack state format

```
S:<shoe>|P:<hand1;hand2>|D:<dealer>|BK:<stack>|B:<bet>|T:<turn>|H:<hand_index>|ST:<status>|LA:<last_action>|R:<results>
```

Hands are encoded as `cards@state@doubled@bet`, for example:

```
P:AS,8D@active@0@10;7C,7H@active@0@10
```

`R` is optional and contains per-hand results when the game is over (`win`, `lose`,
`push`, `bust`, `blackjack`).

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
    "chooseExactlyOne": true,
    "mustNotRevealDealerHoleCardInChat": true,
    "dealerHoleCardVisibility": "hidden_until_dealer_turn_or_game_over"
  }
}
```


## Sea Battle

### Sea Battle state format

```
P:<player_board>|O:<opponent_board>|F:<fog_board>|OF:<opponent_fog>|T:<turn>|ST:<status>|LA:<last_action>|W:<winner>
```

Boards are 10x10 rows using:

- `.` empty
- `S` ship (only on full boards)
- `H` hit
- `M` miss

### Tool: `new_sea_battle_game`

**Output (structuredContent)**

```json
{
  "type": "sea_battle_snapshot",
  "gameType": "sea_battle",
  "gameId": "g_123",
  "state": "<STATE>",
  "status": "in_progress",
  "turn": "player"
}
```

### Tool: `apply_sea_battle_move`

**Input**

* `gameId`
* `state`
* `coord` (string): `A1` through `J10`

**Output (structuredContent)**

```json
{
  "type": "sea_battle_snapshot",
  "gameType": "sea_battle",
  "gameId": "g_123",
  "legal": true,
  "state": "<NEW_STATE>",
  "status": "in_progress",
  "turn": "opponent",
  "lastAction": "B4:hit"
}
```

If illegal:

```json
{
  "type": "sea_battle_snapshot",
  "gameType": "sea_battle",
  "gameId": "g_123",
  "legal": false,
  "state": "<UNCHANGED_STATE>",
  "error": "Illegal move."
}
```

### Tool: `legal_sea_battle_moves` (read-only)

**Input**

* `state`

**Output (structuredContent)**

```json
{
  "type": "legal_moves",
  "gameType": "sea_battle",
  "moves": ["A1", "A2", "B1"]
}
```

### Tool: `choose_sea_battle_opponent_move`

**Input**

* `state`

**Output (structuredContent)**

```json
{
  "type": "opponent_choice",
  "gameType": "sea_battle",
  "moves": ["A1", "A2", "B1"],
  "policy": {
    "mustChooseFromMoves": true,
    "chooseExactlyOne": true
  }
}
```

## Slot Machine

### Slot state format

```
R:<reels>|BK:<stack>|B:<bet>|P:<payout>|ST:<status>|LA:<last_action>
```

### Tool: `new_slot_game`

**Input**

* `stack` (optional, default 1000)
* `bet` (optional, default 10 or `stack` if smaller)

**Output (structuredContent)**

```json
{
  "type": "slot_snapshot",
  "gameType": "slot",
  "state": "<STATE>",
  "stack": 1000,
  "bet": 10,
  "reels": [],
  "payout": 0,
  "status": "in_progress",
  "lastAction": "-"
}
```

### Tool: `spin_slot`

**Input**

* `state`

**Output (structuredContent)**

```json
{
  "type": "slot_snapshot",
  "gameType": "slot",
  "legal": true,
  "state": "<NEW_STATE>",
  "stack": 1010,
  "bet": 10,
  "reels": ["7", "7", "7"],
  "payout": 100,
  "status": "in_progress",
  "lastAction": "spin"
}
```

## Four-in-a-Row

### Four-in-a-Row state format

```
G:<grid>|T:<turn>|ST:<status>|LA:<last_action>|W:<winner>
```

Grid is 6 rows of 7 chars using:

- `.` empty
- `R` player
- `Y` opponent

### Tool: `new_four_in_a_row_game`

**Output (structuredContent)**

```json
{
  "type": "four_in_a_row_snapshot",
  "gameType": "four_in_a_row",
  "gameId": "g_123",
  "state": "<STATE>",
  "status": "in_progress",
  "turn": "player"
}
```

### Tool: `apply_four_in_a_row_move`

**Input**

* `gameId`
* `state`
* `column` (integer): 1 through 7

**Output (structuredContent)**

```json
{
  "type": "four_in_a_row_snapshot",
  "gameType": "four_in_a_row",
  "gameId": "g_123",
  "legal": true,
  "state": "<NEW_STATE>",
  "status": "in_progress",
  "turn": "opponent",
  "lastAction": "4"
}
```

If illegal:

```json
{
  "type": "four_in_a_row_snapshot",
  "gameType": "four_in_a_row",
  "gameId": "g_123",
  "legal": false,
  "state": "<UNCHANGED_STATE>",
  "error": "Illegal move."
}
```

### Tool: `legal_four_in_a_row_moves` (read-only)

**Input**

* `state`

**Output (structuredContent)**

```json
{
  "type": "legal_moves",
  "gameType": "four_in_a_row",
  "moves": [1, 2, 3, 4]
}
```

### Tool: `choose_four_in_a_row_opponent_move`

**Input**

* `state`

**Output (structuredContent)**

```json
{
  "type": "opponent_choice",
  "gameType": "four_in_a_row",
  "moves": [1, 2, 3, 4],
  "policy": {
    "mustChooseFromMoves": true,
    "chooseExactlyOne": true
  }
}
```

## Tic-Tac-Toe

### Tic-Tac-Toe state format

```
G:<grid>|T:<turn>|ST:<status>|LA:<last_action>|W:<winner>|P:<player_symbol>|O:<opponent_symbol>
```

Grid is 3 rows of 3 chars using:

- `.` empty
- `X` player
- `O` opponent

### Tool: `new_tic_tac_toe_game`

**Input**

* `side` (optional): `"X" | "O"`

**Output (structuredContent)**

```json
{
  "type": "tic_tac_toe_snapshot",
  "gameType": "tic_tac_toe",
  "gameId": "g_123",
  "state": "<STATE>",
  "status": "in_progress",
  "turn": "player"
}
```

### Tool: `apply_tic_tac_toe_move`

**Input**

* `gameId`
* `state`
* `coord` (string): `A1` through `C3`

**Output (structuredContent)**

```json
{
  "type": "tic_tac_toe_snapshot",
  "gameType": "tic_tac_toe",
  "gameId": "g_123",
  "legal": true,
  "state": "<NEW_STATE>",
  "status": "in_progress",
  "turn": "opponent",
  "lastAction": "B2"
}
```

If illegal:

```json
{
  "type": "tic_tac_toe_snapshot",
  "gameType": "tic_tac_toe",
  "gameId": "g_123",
  "legal": false,
  "state": "<UNCHANGED_STATE>",
  "error": "Illegal move."
}
```

### Tool: `legal_tic_tac_toe_moves` (read-only)

**Input**

* `state`

**Output (structuredContent)**

```json
{
  "type": "legal_moves",
  "gameType": "tic_tac_toe",
  "moves": ["A1", "B2", "C3"]
}
```

### Tool: `choose_tic_tac_toe_opponent_move`

**Input**

* `state`

**Output (structuredContent)**

```json
{
  "type": "opponent_choice",
  "gameType": "tic_tac_toe",
  "moves": ["A1", "B2", "C3"],
  "policy": {
    "mustChooseFromMoves": true,
    "chooseExactlyOne": true
  }
}
```

## RPG Dice

### Tool: `roll_rpg_dice`

**Input**

* `sides` (required): 4, 6, 8, 10, 12, 20, 100
* `count` (optional, default 1)

**Output (structuredContent)**

```json
{
  "type": "rpg_dice_roll",
  "gameType": "rpg_dice",
  "legal": true,
  "sides": 20,
  "count": 2,
  "rolls": [13, 7],
  "total": 20
}
```

## RPG Dice

### Tool: `roll_rpg_dice`

**Input**

* `sides` (required): 4, 6, 8, 10, 12, 20, 100
* `count` (optional, default 1)

**Output (structuredContent)**

```json
{
  "type": "rpg_dice_roll",
  "gameType": "rpg_dice",
  "legal": true,
  "sides": 20,
  "count": 2,
  "rolls": [13, 7],
  "total": 20
}
```

## Mancala

### Mancala state format

```
P:<p1,p2,p3,p4,p5,p6>|O:<o1,o2,o3,o4,o5,o6>|PS:<player_store>|OS:<opponent_store>|T:<turn>|ST:<status>|LA:<last_action>|W:<winner>
```

`T` is `player` or `opponent`. `ST` is `in_progress` or `game_over`.
`W` is `player`, `opponent`, `draw`, or `-`.

### Tool: `new_mancala_game`

**Output (structuredContent)**

```json
{
  "type": "mancala_snapshot",
  "gameType": "mancala",
  "gameId": "g_123",
  "state": "<STATE>",
  "status": "in_progress",
  "turn": "player"
}
```

### Tool: `apply_mancala_move`

**Input**

* `gameId`
* `state`
* `pit` (integer): `1` through `6`

**Output (structuredContent)**

```json
{
  "type": "mancala_snapshot",
  "gameType": "mancala",
  "gameId": "g_123",
  "legal": true,
  "state": "<NEW_STATE>",
  "status": "in_progress",
  "turn": "opponent",
  "lastAction": "pit3"
}
```

If illegal:

```json
{
  "type": "mancala_snapshot",
  "gameType": "mancala",
  "gameId": "g_123",
  "legal": false,
  "state": "<UNCHANGED_STATE>",
  "error": "Illegal move."
}
```

### Tool: `legal_mancala_moves` (read-only)

**Input**

* `state`

**Output (structuredContent)**

```json
{
  "type": "legal_moves",
  "gameType": "mancala",
  "moves": [1, 2, 3, 4, 5, 6]
}
```

### Tool: `choose_mancala_opponent_move`

**Input**

* `state`

**Output (structuredContent)**

```json
{
  "type": "opponent_choice",
  "gameType": "mancala",
  "moves": [1, 3, 5],
  "policy": {
    "mustChooseFromMoves": true,
    "chooseExactlyOne": true
  }
}
```
