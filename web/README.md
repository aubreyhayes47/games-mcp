# games-mcp widgets

This directory contains the React + Vite widgets for the games MCP library.
Chess, checkers, blackjack, and RPG dice are implemented today; planned additions
include heads-up NL Hold'em (LLM opponent), a slot machine, Four-in-a-Row,
Tic-Tac-Toe, Sea Battle, and Roulette (American).

## Local development

```bash
cd web
npm install
npm run dev
```

To run the checkers widget locally:

```bash
npm run dev:checkers
```

To run the blackjack widget locally:

```bash
npm run dev:blackjack
```

To run the RPG dice widget locally:

```bash
npm run dev:rpg-dice
```

## Build

```bash
npm run build
```

To build the checkers widget bundle:

```bash
npm run build:checkers
```

To build the blackjack widget bundle:

```bash
npm run build:blackjack
```

To build the RPG dice widget bundle:

```bash
npm run build:rpg-dice
```

## Notes

- The chess widget lives at `web/widgets/chess/`.
- The checkers widget lives at `web/widgets/checkers/`.
- The blackjack widget lives at `web/widgets/blackjack/`.
- The RPG dice widget lives at `web/widgets/rpg-dice/`.
- The widget reads from `window.openai.toolOutput`.
- The build output is embedded into the server template.
