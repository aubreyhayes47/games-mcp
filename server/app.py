"""FastMCP server entrypoint (Task 1: widget resource only)."""

from __future__ import annotations

import os
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.exceptions import ResourceError
from mcp.server.lowlevel.helper_types import ReadResourceContents

try:
    from .tools import register_tools
except ImportError:  # pragma: no cover - fallback for script execution
    from tools import register_tools

CHESS_WIDGET_VERSION = "v1"
CHECKERS_WIDGET_VERSION = "v1"
BLACKJACK_WIDGET_VERSION = "v1"
RPG_DICE_WIDGET_VERSION = "v1"
CHESS_WIDGET_URI = f"ui://widget/chess-board-{CHESS_WIDGET_VERSION}.html"
CHECKERS_WIDGET_URI = f"ui://widget/checkers-board-{CHECKERS_WIDGET_VERSION}.html"
BLACKJACK_WIDGET_URI = f"ui://widget/blackjack-board-{BLACKJACK_WIDGET_VERSION}.html"
RPG_DICE_WIDGET_URI = f"ui://widget/rpg-dice-{RPG_DICE_WIDGET_VERSION}.html"
WIDGET_MIME_TYPE = "text/html+skybridge"
WIDGET_DOMAIN = os.getenv("WIDGET_DOMAIN", "https://chess-mcp.example.com")
MCP_SERVER_ORIGIN = os.getenv("MCP_SERVER_ORIGIN")
ALLOW_LOCALHOST = os.getenv("WIDGET_ALLOW_LOCALHOST", "false").lower() in {
    "1",
    "true",
    "yes",
}
connect_domains = [WIDGET_DOMAIN]
if MCP_SERVER_ORIGIN:
    connect_domains.append(MCP_SERVER_ORIGIN)
if ALLOW_LOCALHOST:
    connect_domains.append("http://localhost:8000")

WIDGET_CSP = {
    "connect_domains": connect_domains,
    "resource_domains": [],
}
WIDGET_BUILD_ROOT = Path(__file__).resolve().parents[1] / "web" / "widgets"
CHESS_WIDGET_BUILD_DIR = WIDGET_BUILD_ROOT / "chess" / "dist"
CHECKERS_WIDGET_BUILD_DIR = WIDGET_BUILD_ROOT / "checkers" / "dist"

CHESS_WIDGET_TEMPLATE_PATH = (
    Path(__file__).resolve().parent
    / "templates"
    / f"chess-board-{CHESS_WIDGET_VERSION}.html"
)
CHECKERS_WIDGET_TEMPLATE_PATH = (
    Path(__file__).resolve().parent
    / "templates"
    / f"checkers-board-{CHECKERS_WIDGET_VERSION}.html"
)
BLACKJACK_WIDGET_TEMPLATE_PATH = (
    Path(__file__).resolve().parent
    / "templates"
    / f"blackjack-board-{BLACKJACK_WIDGET_VERSION}.html"
)
RPG_DICE_WIDGET_TEMPLATE_PATH = (
    Path(__file__).resolve().parent
    / "templates"
    / f"rpg-dice-{RPG_DICE_WIDGET_VERSION}.html"
)

CHESS_WIDGET_JS_PATH = CHESS_WIDGET_BUILD_DIR / "widget.js"
CHESS_WIDGET_CSS_PATH = CHESS_WIDGET_BUILD_DIR / "widget.css"
CHECKERS_WIDGET_JS_PATH = CHECKERS_WIDGET_BUILD_DIR / "widget.js"
CHECKERS_WIDGET_CSS_PATH = CHECKERS_WIDGET_BUILD_DIR / "widget.css"
BLACKJACK_WIDGET_BUILD_DIR = WIDGET_BUILD_ROOT / "blackjack" / "dist"
BLACKJACK_WIDGET_JS_PATH = BLACKJACK_WIDGET_BUILD_DIR / "widget.js"
BLACKJACK_WIDGET_CSS_PATH = BLACKJACK_WIDGET_BUILD_DIR / "widget.css"
RPG_DICE_WIDGET_BUILD_DIR = WIDGET_BUILD_ROOT / "rpg-dice" / "dist"
RPG_DICE_WIDGET_JS_PATH = RPG_DICE_WIDGET_BUILD_DIR / "widget.js"
RPG_DICE_WIDGET_CSS_PATH = RPG_DICE_WIDGET_BUILD_DIR / "widget.css"

app = FastMCP("games-mcp")
register_tools(app)


def load_widget_template(template_path: Path, js_path: Path, css_path: Path) -> str:
    if not template_path.exists():
        raise ResourceError(
            f"Widget template not found at {template_path}. "
            "Ensure the template exists and the URI version matches."
        )
    if not js_path.exists() or not css_path.exists():
        raise ResourceError(
            "Widget build artifacts are missing. "
            "Run `npm install && npm run build` in the web/ directory "
            "to generate web/widgets/<game>/dist/widget.js and widget.css."
        )

    template = template_path.read_text(encoding="utf-8")
    css = css_path.read_text(encoding="utf-8")
    js = js_path.read_text(encoding="utf-8")

    if "/* INLINE_CSS */" not in template or "/* INLINE_JS */" not in template:
        raise ResourceError(
            "Widget template placeholders are missing. "
            "Expected /* INLINE_CSS */ and /* INLINE_JS */ markers."
        )

    return template.replace("/* INLINE_CSS */", css).replace("/* INLINE_JS */", js)


@app.resource(CHESS_WIDGET_URI, mime_type=WIDGET_MIME_TYPE)
def chess_widget_template() -> str:
    return load_widget_template(
        CHESS_WIDGET_TEMPLATE_PATH, CHESS_WIDGET_JS_PATH, CHESS_WIDGET_CSS_PATH
    )


@app.resource(CHECKERS_WIDGET_URI, mime_type=WIDGET_MIME_TYPE)
def checkers_widget_template() -> str:
    return load_widget_template(
        CHECKERS_WIDGET_TEMPLATE_PATH,
        CHECKERS_WIDGET_JS_PATH,
        CHECKERS_WIDGET_CSS_PATH,
    )


@app.resource(BLACKJACK_WIDGET_URI, mime_type=WIDGET_MIME_TYPE)
def blackjack_widget_template() -> str:
    return load_widget_template(
        BLACKJACK_WIDGET_TEMPLATE_PATH,
        BLACKJACK_WIDGET_JS_PATH,
        BLACKJACK_WIDGET_CSS_PATH,
    )


@app.resource(RPG_DICE_WIDGET_URI, mime_type=WIDGET_MIME_TYPE)
def rpg_dice_widget_template() -> str:
    return load_widget_template(
        RPG_DICE_WIDGET_TEMPLATE_PATH,
        RPG_DICE_WIDGET_JS_PATH,
        RPG_DICE_WIDGET_CSS_PATH,
    )


@app._mcp_server.read_resource()
async def read_resource(uri: str):
    resource = await app._resource_manager.get_resource(uri)
    if not resource:
        raise ResourceError(f"Unknown resource: {uri}")

    content = await resource.read()
    meta = None
    if str(uri) in {
        CHESS_WIDGET_URI,
        CHECKERS_WIDGET_URI,
        BLACKJACK_WIDGET_URI,
        RPG_DICE_WIDGET_URI,
    }:
        meta = {
            "openai/widgetDomain": WIDGET_DOMAIN,
            "openai/widgetCSP": WIDGET_CSP,
        }

    return [
        ReadResourceContents(
            content=content,
            mime_type=resource.mime_type,
            meta=meta,
        )
    ]


if __name__ == "__main__":
    # TODO: Replace with proper ASGI server invocation for production.
    app.run()
