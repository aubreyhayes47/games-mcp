# games-mcp widgets

This directory contains the React + Vite widgets for the games MCP library.
Chess and checkers are implemented today; planned additions include heads-up NL
Hold'em (LLM opponent), blackjack (LLM dealer), and a slot machine.

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

## Build

```bash
npm run build
```

To build the checkers widget bundle:

```bash
npm run build:checkers
```

## Notes

- The chess widget lives at `web/widgets/chess/`.
- The checkers widget lives at `web/widgets/checkers/`.
- The widget reads from `window.openai.toolOutput`.
- The build output is embedded into the server template.
