import json
import httpx
import mcp.types as types

URL = "http://127.0.0.1:10000/mcp"
WIDGET_URI = "ui://widget/chess-board-v1.html"
CHECKERS_WIDGET_URI = "ui://widget/checkers-board-v1.html"
BLACKJACK_WIDGET_URI = "ui://widget/blackjack-board-v1.html"


class McpHttpClient:
    def __init__(self, url: str) -> None:
        self.url = url
        self.session_id = None
        self.protocol_version = None
        self.client = httpx.Client(timeout=10)
        self._id = 1

    def _headers(self) -> dict[str, str]:
        headers = {
            "accept": "application/json, text/event-stream",
            "content-type": "application/json",
        }
        if self.session_id:
            headers["mcp-session-id"] = self.session_id
        if self.protocol_version:
            headers["mcp-protocol-version"] = self.protocol_version
        return headers

    @staticmethod
    def _parse_sse_json(text: str) -> dict | None:
        for line in text.splitlines():
            if line.startswith("data: "):
                return json.loads(line[len("data: ") :])
        return None

    def request(
        self, method: str, params: dict | None = None
    ) -> tuple[httpx.Response, dict]:
        req_id = self._id
        self._id += 1
        payload = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            payload["params"] = params
        resp = self.client.post(self.url, headers=self._headers(), json=payload)
        resp.raise_for_status()
        data = self._parse_sse_json(resp.text)
        if data is None:
            raise RuntimeError("No MCP response data found")
        return resp, data

    def notify(self, method: str, params: dict | None = None) -> None:
        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        resp = self.client.post(self.url, headers=self._headers(), json=payload)
        resp.raise_for_status()


def run_chess(client: McpHttpClient) -> None:
    _, widget = client.request("resources/read", {"uri": WIDGET_URI})
    widget_text = widget["result"]["contents"][0].get("text") or widget["result"][
        "contents"
    ][0].get("content")

    _, new_chess_game = client.request(
        "tools/call", {"name": "new_chess_game", "arguments": {"side": "white"}}
    )
    snapshot = new_chess_game["result"]["structuredContent"]
    _, legal_chess_moves = client.request(
        "tools/call",
        {"name": "legal_chess_moves", "arguments": {"fen": snapshot["fen"]}},
    )
    move = legal_chess_moves["result"]["structuredContent"]["movesUci"][0]
    _, applied_chess_move = client.request(
        "tools/call",
        {
            "name": "apply_chess_move",
            "arguments": {
                "gameId": snapshot["gameId"],
                "fen": snapshot["fen"],
                "moveUci": move,
            },
        },
    )
    apply_snapshot = applied_chess_move["result"]["structuredContent"]
    _, choose_chess_opponent_move = client.request(
        "tools/call",
        {
            "name": "choose_chess_opponent_move",
            "arguments": {"fen": apply_snapshot["fen"]},
        },
    )
    print("\n=== Chess ===")
    print("widget_bytes:", len(widget_text) if widget_text else 0)
    print("new_chess_game:", snapshot)
    print(
        "legal_chess_moves_count:",
        len(legal_chess_moves["result"]["structuredContent"]["movesUci"]),
    )
    print("apply_chess_move:", apply_snapshot)
    print(
        "choose_chess_opponent_move_count:",
        len(choose_chess_opponent_move["result"]["structuredContent"]["movesUci"]),
    )


def run_checkers(client: McpHttpClient) -> None:
    _, widget = client.request("resources/read", {"uri": CHECKERS_WIDGET_URI})
    widget_text = widget["result"]["contents"][0].get("text") or widget["result"][
        "contents"
    ][0].get("content")

    _, new_checkers_game = client.request(
        "tools/call", {"name": "new_checkers_game", "arguments": {}}
    )
    snapshot = new_checkers_game["result"]["structuredContent"]
    _, legal_checkers_moves = client.request(
        "tools/call",
        {"name": "legal_checkers_moves", "arguments": {"state": snapshot["state"]}},
    )
    legal_payload = legal_checkers_moves["result"]["structuredContent"]
    forced_moves = legal_payload.get("forcedCaptures") or []
    move = forced_moves[0] if forced_moves else legal_payload["moves"][0]
    _, applied_checkers_move = client.request(
        "tools/call",
        {
            "name": "apply_checkers_move",
            "arguments": {
                "gameId": snapshot["gameId"],
                "state": snapshot["state"],
                "move": move,
            },
        },
    )
    apply_snapshot = applied_checkers_move["result"]["structuredContent"]
    _, choose_checkers_opponent_move = client.request(
        "tools/call",
        {
            "name": "choose_checkers_opponent_move",
            "arguments": {"state": apply_snapshot["state"]},
        },
    )
    print("\n=== Checkers ===")
    print("widget_bytes:", len(widget_text) if widget_text else 0)
    print("new_checkers_game:", snapshot)
    print(
        "legal_checkers_moves_count:",
        len(legal_checkers_moves["result"]["structuredContent"]["moves"]),
    )
    print(
        "legal_checkers_forced_count:",
        len(
            legal_checkers_moves["result"]["structuredContent"].get(
                "forcedCaptures", []
            )
        ),
    )
    print("apply_checkers_move:", apply_snapshot)
    print(
        "choose_checkers_opponent_move_count:",
        len(choose_checkers_opponent_move["result"]["structuredContent"]["moves"]),
    )


def run_blackjack(client: McpHttpClient) -> None:
    _, widget = client.request("resources/read", {"uri": BLACKJACK_WIDGET_URI})
    widget_text = widget["result"]["contents"][0].get("text") or widget["result"][
        "contents"
    ][0].get("content")

    _, new_blackjack_game = client.request(
        "tools/call", {"name": "new_blackjack_game", "arguments": {}}
    )
    snapshot = new_blackjack_game["result"]["structuredContent"]
    _, legal_blackjack_actions = client.request(
        "tools/call",
        {"name": "legal_blackjack_actions", "arguments": {"state": snapshot["state"]}},
    )
    actions = legal_blackjack_actions["result"]["structuredContent"]["actions"]
    action = "stand" if "stand" in actions else actions[0] if actions else "stand"
    _, applied_blackjack_action = client.request(
        "tools/call",
        {
            "name": "apply_blackjack_action",
            "arguments": {
                "gameId": snapshot["gameId"],
                "state": snapshot["state"],
                "action": action,
            },
        },
    )
    apply_snapshot = applied_blackjack_action["result"]["structuredContent"]
    _, choose_blackjack_dealer_action = client.request(
        "tools/call",
        {
            "name": "choose_blackjack_dealer_action",
            "arguments": {"state": apply_snapshot["state"]},
        },
    )
    print("\n=== Blackjack ===")
    print("widget_bytes:", len(widget_text) if widget_text else 0)
    print("new_blackjack_game:", snapshot)
    print("legal_blackjack_actions:", actions)
    print("apply_blackjack_action:", apply_snapshot)
    print(
        "choose_blackjack_dealer_action:",
        choose_blackjack_dealer_action["result"]["structuredContent"],
    )


def main() -> None:
    client = McpHttpClient(URL)

    init_resp, init = client.request(
        "initialize",
        {
            "protocolVersion": types.LATEST_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "smoke-test", "version": "0.0.0"},
        },
    )
    client.session_id = init_resp.headers.get("mcp-session-id")
    client.protocol_version = init["result"]["protocolVersion"]
    client.notify("notifications/initialized")

    _, tools = client.request("tools/list")
    _, resources = client.request("resources/list")
    _, templates = client.request("resources/templates/list")
    _, prompts = client.request("prompts/list")

    print(
        "initialize:", init["result"]["protocolVersion"], init["result"]["serverInfo"]
    )
    print("tools:", [tool["name"] for tool in tools["result"]["tools"]])
    print("resources:", [res["uri"] for res in resources["result"]["resources"]])
    print(
        "resource_templates:",
        [tpl["uriTemplate"] for tpl in templates["result"]["resourceTemplates"]],
    )
    print("prompts:", [prompt["name"] for prompt in prompts["result"]["prompts"]])

    run_chess(client)
    run_checkers(client)
    run_blackjack(client)


if __name__ == "__main__":
    main()
