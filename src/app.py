"""
DonutSMP API bridge with MCP-compatible dual-path support.

This server intentionally exposes MCP at both:
- /        (root)
- /mcp     (prefixed)

And it mirrors REST/tool routes under both path spaces, e.g.:
- /tools and /mcp/tools
- /health and /mcp/health

This makes ChatGPT custom connector setup resilient regardless of whether
users paste the base URL or base/mcp.
"""

import os
import json
import time
import datetime
from typing import Any

import httpx
from flask import Blueprint, Flask, Response, jsonify, request, send_file

API_BASE_URL = "https://api.donutsmp.net/v1"
MCP_PROTOCOL_VERSION = "2025-03-26"

app = Flask(__name__)
app.url_map.strict_slashes = False


def get_api_key() -> str:
    return os.environ.get("DONUTSMP_API_KEY", "")


def make_request(endpoint: str, method: str = "GET", data: dict | None = None) -> dict[str, Any]:
    api_key = get_api_key()
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = httpx.get(url, headers=headers, timeout=30.0)
        elif method == "PUT":
            response = httpx.put(url, headers=headers, json=data, timeout=30.0)
        else:
            return {"error": f"Unsupported method: {method}"}

        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"error": str(e)}


@app.before_request
def log_requests_and_handle_options():
    """Verbose request logging for connector discovery/debugging.

    This intentionally logs request method/path/remote address and all headers
    so Vercel logs show exactly what ChatGPT probes during "Create".
    """
    print(
        f"[{datetime.datetime.now().isoformat()}] "
        f"{request.method} {request.path} from {request.remote_addr} "
        f"headers: {dict(request.headers)}"
    )

    if request.method in {"POST", "PUT", "PATCH"}:
        raw = request.get_data(cache=True, as_text=True) or ""
        if raw:
            print(f"[{datetime.datetime.now().isoformat()}] body: {raw[:1000]}")

    # Ensure preflight requests always return 204 for connector compatibility,
    # even when Flask auto-generates OPTIONS for specific routes.
    if request.method == "OPTIONS":
        return ("", 204)

    return None


@app.after_request
def add_cors_headers(response):
    """Full CORS support for ChatGPT connector (browser-based clients).
    
    ChatGPT's custom connector UI makes cross-origin requests to discover tools.
    Without these headers, browser preflight (OPTIONS) requests will fail silently.
    """
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept, X-Requested-With"
    response.headers["Access-Control-Max-Age"] = "86400"  # Cache preflight for 24h
    return response


# Explicit OPTIONS handlers are required for some browser-based MCP clients.
# This ensures every preflight request receives a clean 204 response.
@app.route("/", methods=["OPTIONS"])
@app.route("/<path:path>", methods=["OPTIONS"])
def options_handler(path: str = ""):
    return ("", 204)


# ── Tool definitions ───────────────────────────────────────────────────────────
def get_mcp_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": "auction_list",
            "description": "Get all current Auction House entries with pagination",
            "inputSchema": {
                "type": "object",
                "properties": {"page": {"type": "number", "default": 1}},
            },
        },
        {
            "name": "auction_transactions",
            "description": "Get all Auction House transaction data with pagination",
            "inputSchema": {
                "type": "object",
                "properties": {"page": {"type": "number", "default": 1}},
            },
        },
        {
            "name": "auction_search",
            "description": "Search Auction House by item name (e.g., 'Diamond', 'Netherite'). Searches up to 20 pages by default for comprehensive results.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Item name to search for (e.g., 'netherite', 'diamond_sword')"},
                    "page": {"type": "number", "default": 1, "description": "Starting page (usually 1)"},
                    "max_pages": {"type": "number", "default": 20, "description": "Number of pages to search (increase for more results)"},
                },
                "required": ["query"],
            },
        },
        {
            "name": "leaderboards",
            "description": "Get leaderboard data. Types: brokenblocks, deaths, kills, mobskilled, money, placedblocks, playtime, sell, shards, shop",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "default": "money"},
                    "page": {"type": "number", "default": 1},
                },
                "required": ["type"],
            },
        },
        {
            "name": "lookup_player",
            "description": "Get player info (like /findplayer)",
            "inputSchema": {
                "type": "object",
                "properties": {"user": {"type": "string"}},
                "required": ["user"],
            },
        },
        {
            "name": "player_stats",
            "description": "Get player profile statistics (like /stats)",
            "inputSchema": {
                "type": "object",
                "properties": {"user": {"type": "string"}},
                "required": ["user"],
            },
        },
        {
            "name": "shield_metrics",
            "description": "Get Shield service metrics",
            "inputSchema": {
                "type": "object",
                "properties": {"service": {"type": "string"}},
                "required": ["service"],
            },
        },
        {
            "name": "shield_stats",
            "description": "Get Shield service stats",
            "inputSchema": {
                "type": "object",
                "properties": {"service": {"type": "string"}},
                "required": ["service"],
            },
        },
    ]


def get_chatgpt_tools_payload() -> dict[str, Any]:
    tools = []
    for tool in get_mcp_tools():
        schema = tool.get("inputSchema", {"type": "object", "properties": {}})
        tools.append(
            {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": schema,
                "inputSchema": schema,
            }
        )
    return {"tools": tools}


def execute_mcp_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        if tool_name == "auction_list":
            return make_request(f"/auction/list/{arguments.get('page', 1)}")
        if tool_name == "auction_transactions":
            return make_request(f"/auction/transactions/{arguments.get('page', 1)}")
        if tool_name == "auction_search":
            query = arguments.get("query", "").strip()
            if not query:
                return {"error": "query parameter required"}
            start_page = arguments.get("page", 1)
            max_pages = arguments.get("max_pages", 20)  # Search up to 20 pages by default for comprehensive results
            
            # Search for items matching the query across multiple pages
            query_lower = query.lower()
            # Create variants of the query to match different naming conventions
            # "item frame" -> ["item frame", "item_frame"]
            query_variants = [
                query_lower,
                query_lower.replace(" ", "_"),  # Handle spaces vs underscores
                query_lower.replace("_", " "),  # Handle underscores vs spaces
            ]
            
            all_filtered = []
            
            for page_num in range(start_page, start_page + max_pages):
                page_resp = make_request(f"/auction/list/{page_num}")
                if "error" in page_resp:
                    break  # Stop if we hit an error (invalid page, etc.)
                
                # Handle different response formats from DonutSMP API
                if "result" in page_resp:
                    auctions = page_resp.get("result", [])
                elif isinstance(page_resp, dict) and "auctions" in page_resp:
                    auctions = page_resp.get("auctions", [])
                elif isinstance(page_resp, list):
                    auctions = page_resp
                else:
                    auctions = []
                
                # Filter auctions on this page
                for auction in auctions:
                    if isinstance(auction, dict):
                        item = auction.get("item", {})
                        if isinstance(item, dict):
                            # Check item ID (e.g., "minecraft:diamond", "minecraft:item_frame")
                            item_id = (item.get("id") or "").lower()
                            # Check custom display name
                            display_name = (item.get("display_name") or "").lower()
                            # Check lore text
                            lore = (item.get("lore") or "").lower()
                            
                            # Match against any query variant
                            matches = any(
                                variant in item_id or 
                                variant in display_name or 
                                variant in lore
                                for variant in query_variants
                            )
                            
                            if matches:
                                all_filtered.append(auction)
                        elif isinstance(item, str) and any(variant in item.lower() for variant in query_variants):
                            all_filtered.append(auction)
                
                # Stop if this page had no results (empty page = no more pages)
                if not auctions:
                    break
            
            return {
                "query": query,
                "start_page": start_page,
                "pages_searched": min(max_pages, (start_page - 1) + len([p for p in range(start_page, start_page + max_pages)])),
                "total_found": len(all_filtered),
                "auctions": all_filtered[:30],  # Return top 30 matches across all pages
            }
        if tool_name == "leaderboards":
            return make_request(f"/leaderboards/{arguments.get('type', 'money')}/{arguments.get('page', 1)}")
        if tool_name == "lookup_player":
            user = arguments.get("user")
            return {"error": "user required"} if not user else make_request(f"/lookup/{user}")
        if tool_name == "player_stats":
            user = arguments.get("user")
            return {"error": "user required"} if not user else make_request(f"/stats/{user}")
        if tool_name == "shield_metrics":
            service = arguments.get("service")
            return {"error": "service required"} if not service else make_request(f"/shield/metrics/{service}")
        if tool_name == "shield_stats":
            service = arguments.get("service")
            return {"error": "service required"} if not service else make_request(f"/shield/stats/{service}")
        return {"error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        return {"error": str(e)}


# ── MCP helpers ────────────────────────────────────────────────────────────────
def mcp_result(req_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def mcp_error(req_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def handle_mcp_message(message: Any) -> dict[str, Any] | None:
    if not isinstance(message, dict):
        return mcp_error(None, -32600, "Invalid Request")

    req_id = message.get("id")
    method = message.get("method")

    if message.get("jsonrpc") != "2.0" or not isinstance(method, str):
        return mcp_error(req_id, -32600, "Invalid Request")

    params = message.get("params", {})
    if not isinstance(params, dict):
        params = {}

    if method.startswith("notifications/"):
        return None

    if method == "ping":
        return mcp_result(req_id, {})

    if method == "initialize":
        client_version = params.get("protocolVersion")
        return mcp_result(
            req_id,
            {
                "protocolVersion": client_version or MCP_PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "DonutSMP", "version": "0.1.0"},
            },
        )

    if method == "tools/list":
        return mcp_result(req_id, get_chatgpt_tools_payload())

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        if not isinstance(arguments, dict):
            arguments = {}
        result = execute_mcp_tool(str(tool_name), arguments)
        return mcp_result(req_id, {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]})

    return mcp_error(req_id, -32601, f"Unknown method: {method}")


def handle_mcp_request() -> Response | tuple[str, int]:
    body = request.get_json(force=True, silent=True)

    if isinstance(body, list):
        if not body:
            return jsonify(mcp_error(None, -32600, "Invalid Request"))
        responses = [item for item in (handle_mcp_message(message) for message in body) if item is not None]
        if not responses:
            return ("", 204)
        return jsonify(responses)

    response = handle_mcp_message(body)
    if response is None:
        return ("", 204)
    return jsonify(response)


def get_server_metadata(base_path: str) -> dict[str, Any]:
    prefix = base_path.rstrip("/")
    if prefix == "":
        prefix = ""

    def p(path: str) -> str:
        return f"{prefix}{path}" if prefix else path

    return {
        "name": "DonutSMP MCP Bridge",
        "version": "0.1.0",
        "description": "Read-only bridge for DonutSMP API with MCP-compatible endpoints.",
        "protocolVersion": MCP_PROTOCOL_VERSION,
        "mcp": {
            "jsonrpc": p("/"),
            "tools": p("/tools"),
            "health": p("/health"),
        },
        "api_key_configured": bool(get_api_key()),
    }


# ── Root + /mcp handshake endpoints ───────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def mcp_root_base():
    """Root endpoint: GET returns metadata, POST handles JSON-RPC MCP requests.
    
    ChatGPT may probe this endpoint directly or use /mcp prefix.
    Dual-path support ensures compatibility with different client discovery patterns.
    """
    if request.method == "POST":
        return handle_mcp_request()

    payload = get_server_metadata("")
    payload.update(
        {
            "message": "DonutSMP MCP Server - use /mcp for discovery or /tools for direct tool list",
            "discovery_url": "/mcp",
            "tools_url": "/tools",
        }
    )
    return jsonify(payload)


@app.route("/mcp", methods=["GET", "POST"])
def mcp_root_prefixed():
    """Prefixed MCP endpoint for clients that expect /mcp base path.
    
    Some MCP clients (including ChatGPT) may expect /mcp as the base path.
    This mirrors the root endpoint behavior under the /mcp prefix.
    """
    if request.method == "POST":
        return handle_mcp_request()
    return jsonify(get_server_metadata("/mcp"))


@app.route("/.well-known/mcp.json", methods=["GET"])
def well_known_mcp():
    """OpenAI/ChatGPT MCP discovery endpoint (2026 pattern).
    
    ChatGPT custom connectors may probe /.well-known/mcp.json for discovery.
    This returns minimal valid JSON describing the MCP server capabilities.
    Even for no-auth servers, this helps ChatGPT discover available tools.
    """
    return jsonify({
        "name": "DonutSMP MCP",
        "description": "DonutSMP API bridge with MCP protocol support",
        "version": "1.0",
        "protocolVersion": MCP_PROTOCOL_VERSION,
        "transport": {"type": "http"},
        "capabilities": {
            "tools": True,
            "resources": False,
            "prompts": False
        },
        "endpoints": {
            "root": "/",
            "mcp": "/mcp",
            "tools": "/tools",
            "health": "/health"
        }
    })


# ── Shared API routes exposed under BOTH root and /mcp ───────────────────────
bridge = Blueprint("bridge", __name__)


@bridge.get("/health")
def http_health():
    return jsonify(
        {
            "status": "ok",
            "server": "donutsmp-api",
            "version": "0.1.0",
            "api_key_configured": bool(get_api_key()),
        }
    )


@bridge.get("/tools")
def http_tools():
    """Return OpenAI-compatible tool list for ChatGPT connector discovery.
    
    ChatGPT probes /tools (or /mcp/tools) to discover available tools.
    Each tool includes name, description, and parameters as JSON schema.
    This format is compatible with both MCP clients and OpenAI's tool calling.
    """
    payload = get_chatgpt_tools_payload()
    payload["server"] = {"name": "DonutSMP MCP Bridge", "version": "0.1.0"}
    return jsonify(payload)


@bridge.get("/auction/list/<int:page>")
def http_auction_list(page: int):
    return jsonify(make_request(f"/auction/list/{page}"))


@bridge.get("/auction/search/<query>")
@bridge.get("/auction/search/<query>/<int:page>")
def http_auction_search(query: str, page: int = 1):
    """Search auctions by item name."""
    result = execute_mcp_tool("auction_search", {"query": query, "page": page})
    return jsonify(result)


@bridge.get("/auction/transactions/<int:page>")
def http_auction_transactions(page: int):
    return jsonify(make_request(f"/auction/transactions/{page}"))


@bridge.get("/leaderboards/<board_type>/<int:page>")
def http_leaderboard(board_type: str, page: int):
    return jsonify(make_request(f"/leaderboards/{board_type}/{page}"))


@bridge.get("/lookup/<user>")
def http_lookup_player(user: str):
    return jsonify(make_request(f"/lookup/{user}"))


@bridge.get("/stats/<user>")
def http_player_stats(user: str):
    return jsonify(make_request(f"/stats/{user}"))


@bridge.get("/shield/<platform>/config/<service>")
def http_shield_config_get(platform: str, service: str):
    return jsonify(make_request(f"/shield/{platform}/config/{service}"))


@bridge.put("/shield/<platform>/config/<service>")
def http_shield_config_put(platform: str, service: str):
    body = request.get_json(silent=True) or {}
    return jsonify(make_request(f"/shield/{platform}/config/{service}", method="PUT", data=body))


@bridge.get("/shield/metrics/<service>")
def http_shield_metrics(service: str):
    return jsonify(make_request(f"/shield/metrics/{service}"))


@bridge.get("/shield/stats/<service>")
def http_shield_stats(service: str):
    return jsonify(make_request(f"/shield/stats/{service}"))


@bridge.get("/github")
def http_github_page():
    return jsonify(
        {
            "message": "Visit the GitHub repository for documentation and source code.",
            "url": "https://github.com/SzaBee13/DonutSMP-MCP",
        }
    )


@bridge.get("/favicon.ico")
@bridge.get("/favicon.png")
def http_favicon():
    icon_path = os.path.join(os.path.dirname(__file__), "/static/favicon.png")
    if os.path.exists(icon_path):
        return send_file(icon_path)
    return ("", 204)


@bridge.get("/sse")
def http_sse_endpoint():
    update_type = request.args.get("type", "health")
    interval = int(request.args.get("interval", "30"))

    def event_generator():
        while True:
            if update_type == "health":
                data = {
                    "status": "ok",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "api_key_configured": bool(get_api_key()),
                }
            elif update_type == "leaderboards":
                board = request.args.get("board", "money")
                page = request.args.get("page", "1")
                data = make_request(f"/leaderboards/{board}/{page}")
            elif update_type == "stats":
                user = request.args.get("user", "")
                data = {"error": "Provide ?user=USERNAME"} if not user else make_request(f"/stats/{user}")
            else:
                data = {"error": f"Unknown type '{update_type}'. Use: health, leaderboards, stats"}

            yield f"data: {json.dumps(data)}\\n\\n"
            time.sleep(interval)

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return Response(event_generator(), headers=headers, mimetype="text/event-stream")


# Register shared routes under both path spaces.
app.register_blueprint(bridge, url_prefix="")
app.register_blueprint(bridge, url_prefix="/mcp", name="bridge_prefixed")
