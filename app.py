"""
DonutSMP API - Vercel Serverless Handler (Flask/WSGI)
Includes REST, MCP (JSON-RPC 2.0), and SSE endpoints.
"""

import os
import json
import time
import datetime
from typing import Any

import httpx
from flask import Flask, Response, jsonify, request, send_file

API_BASE_URL = "https://api.donutsmp.net/v1"

app = Flask(__name__)


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


@app.get("/")
def http_root():
    return jsonify(
        {
            "name": "DonutSMP API",
            "version": "0.1.0",
            "endpoints": {
                "health": "/health",
                "auction_list": "/auction/list/{page}",
                "auction_transactions": "/auction/transactions/{page}",
                "leaderboards": "/leaderboards/{type}/{page}",
                "lookup": "/lookup/{user}",
                "stats": "/stats/{user}",
                "shield_config": "/shield/{platform}/config/{service}",
                "shield_metrics": "/shield/metrics/{service}",
                "shield_stats": "/shield/stats/{service}",
                "mcp": "/mcp",
                "sse": "/sse",
            },
            "leaderboard_types": [
                "brokenblocks",
                "deaths",
                "kills",
                "mobskilled",
                "money",
                "placedblocks",
                "playtime",
                "sell",
                "shards",
                "shop",
            ],
            "documentation": "https://api.donutsmp.net/index.html",
        }
    )


@app.get("/health")
def http_health():
    return jsonify(
        {
            "status": "ok",
            "server": "donutsmp-api",
            "version": "0.1.0",
            "api_key_configured": bool(get_api_key()),
        }
    )


@app.get("/auction/list/<int:page>")
def http_auction_list(page: int):
    return jsonify(make_request(f"/auction/list/{page}"))


@app.get("/auction/transactions/<int:page>")
def http_auction_transactions(page: int):
    return jsonify(make_request(f"/auction/transactions/{page}"))


@app.get("/leaderboards/<board_type>/<int:page>")
def http_leaderboard(board_type: str, page: int):
    return jsonify(make_request(f"/leaderboards/{board_type}/{page}"))


@app.get("/lookup/<user>")
def http_lookup_player(user: str):
    return jsonify(make_request(f"/lookup/{user}"))


@app.get("/stats/<user>")
def http_player_stats(user: str):
    return jsonify(make_request(f"/stats/{user}"))


@app.get("/shield/<platform>/config/<service>")
def http_shield_config_get(platform: str, service: str):
    return jsonify(make_request(f"/shield/{platform}/config/{service}"))


@app.put("/shield/<platform>/config/<service>")
def http_shield_config_put(platform: str, service: str):
    body = request.get_json(silent=True) or {}
    return jsonify(make_request(f"/shield/{platform}/config/{service}", method="PUT", data=body))


@app.get("/shield/metrics/<service>")
def http_shield_metrics(service: str):
    return jsonify(make_request(f"/shield/metrics/{service}"))


@app.get("/shield/stats/<service>")
def http_shield_stats(service: str):
    return jsonify(make_request(f"/shield/stats/{service}"))


@app.get("/github")
def http_github_page():
    return jsonify(
        {
            "message": "Visit the GitHub repository for documentation and source code.",
            "url": "https://github.com/SzaBee13/DonutSMP-MCP",
        }
    )


@app.get("/favicon.ico")
@app.get("/favicon.png")
def http_favicon():
    icon_path = os.path.join(os.path.dirname(__file__), "favicon.png")
    if os.path.exists(icon_path):
        return send_file(icon_path)
    return ("", 204)


@app.route("/mcp", methods=["GET", "POST"])
def http_mcp_endpoint():
    if request.method != "POST":
        return jsonify(
            {
                "name": "DonutSMP MCP Endpoint",
                "version": "0.1.0",
                "description": "MCP (Model Context Protocol) endpoint for AI integrations",
                "protocol": "JSON-RPC 2.0",
                "usage": "POST JSON-RPC 2.0 requests to this endpoint",
            }
        )

    body = request.get_json(force=True, silent=True)

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
                    "protocolVersion": client_version or "2025-03-26",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "DonutSMP", "version": "0.1.0"},
                },
            )

        if method == "tools/list":
            return mcp_result(req_id, {"tools": get_mcp_tools()})

        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            if not isinstance(arguments, dict):
                arguments = {}

            valid_tools = {
                "auction_list",
                "auction_transactions",
                "leaderboards",
                "lookup_player",
                "player_stats",
                "shield_metrics",
                "shield_stats",
            }
            if tool_name not in valid_tools:
                return mcp_error(req_id, -32601, f"Tool not found: {tool_name}")

            result = execute_mcp_tool(tool_name, arguments)
            return mcp_result(req_id, {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]})

        return mcp_error(req_id, -32601, f"Unknown method: {method}")

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


@app.get("/sse")
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

            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(interval)

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return Response(event_generator(), headers=headers, mimetype="text/event-stream")


def get_mcp_tools():
    return [
        {
            "name": "auction_list",
            "description": "Get all current Auction House entries with pagination",
            "inputSchema": {"type": "object", "properties": {"page": {"type": "number", "default": 1}}},
        },
        {
            "name": "auction_transactions",
            "description": "Get all Auction House transaction data with pagination",
            "inputSchema": {"type": "object", "properties": {"page": {"type": "number", "default": 1}}},
        },
        {
            "name": "leaderboards",
            "description": "Get leaderboard data. Types: brokenblocks, deaths, kills, mobskilled, money, placedblocks, playtime, sell, shards, shop",
            "inputSchema": {
                "type": "object",
                "properties": {"type": {"type": "string", "default": "money"}, "page": {"type": "number", "default": 1}},
                "required": ["type"],
            },
        },
        {
            "name": "lookup_player",
            "description": "Get player info (like /findplayer)",
            "inputSchema": {"type": "object", "properties": {"user": {"type": "string"}}, "required": ["user"]},
        },
        {
            "name": "player_stats",
            "description": "Get player profile statistics (like /stats)",
            "inputSchema": {"type": "object", "properties": {"user": {"type": "string"}}, "required": ["user"]},
        },
        {
            "name": "shield_metrics",
            "description": "Get Shield service metrics",
            "inputSchema": {"type": "object", "properties": {"service": {"type": "string"}}, "required": ["service"]},
        },
        {
            "name": "shield_stats",
            "description": "Get Shield service stats",
            "inputSchema": {"type": "object", "properties": {"service": {"type": "string"}}, "required": ["service"]},
        },
    ]


def execute_mcp_tool(tool_name: str, arguments: dict) -> dict:
    try:
        if tool_name == "auction_list":
            return make_request(f"/auction/list/{arguments.get('page', 1)}")
        if tool_name == "auction_transactions":
            return make_request(f"/auction/transactions/{arguments.get('page', 1)}")
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
