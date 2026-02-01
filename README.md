# games-mcp

🎮 **Chat-driven games for ChatGPT Apps**

games-mcp is a playful, developer-centric library for chat-controlled games with
display-only widgets. The model runs the tools; the widget renders the authoritative
state. You type moves in chat and watch the board or table update instantly.

## ✅ What you can do

* Start a game with a single tool call (`new_*`).
* Type moves/actions in chat (no UI input).
* Watch auto-rendered widgets update from tool output.

## 🧩 Implemented games

* Chess (LLM opponent constrained to legal moves)
* Checkers (algebraic square notation)
* Blackjack (LLM dealer constrained to legal actions, with betting)
* RPG dice (d4, d6, d8, d10, d12, d20, d100)
* Sea Battle (Battleship-style, LLM opponent)
* Slot machine (classic table with weighted symbols)
* Four-in-a-Row (classic Connect 4)

## 🧭 Roadmap (planned additions)

* Tic-Tac-Toe

## ⚡ Quickstart (Local)

```bash
cd server
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

```bash
cd web
npm install
npm run build
```

```bash
python server/run_http.py
```

```bash
./.venv/bin/python scripts/mcp_smoke_test.py
```

## 🔁 How it works (the short version)

1. User asks to start a game.
2. Model calls `new_*` → widget auto-renders from tool output.
3. User types a move/action in chat.
4. Model calls `legal_*` as needed to disambiguate.
5. Model calls `apply_*` → widget auto-renders from tool output.
6. Opponent/dealer loop runs via `choose_*` tools when applicable.

## 🛠️ For developers first

* 🛠️ **Minimal surface area:** few tools, consistent patterns across games.
* 🔒 **Server-verified transitions:** no state changes from chat prose.
* 🎛️ **Explicit opponent policy:** legal actions are always enumerated.
* ⚡ **Fast to extend:** new games plug into the same loop + widget model.

## 📚 Tool contracts

Full tool contracts and state formats live in `docs/contracts.md`.

## 🧪 Testing

```bash
cd server
pytest
```

```bash
./.venv/bin/python scripts/mcp_smoke_test.py
```
