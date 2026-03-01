"""
DonutSMP API - Vercel Serverless Handler
Includes REST, MCP (JSON-RPC 2.0), and SSE endpoints.
"""
import os
import json
import asyncio
import datetime
from typing import Any
import httpx
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse, StreamingResponse

API_BASE_URL = "https://api.donutsmp.net/v1"

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

# ── REST endpoints ────────────────────────────────────────────
async def http_root(request):
    return JSONResponse({
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
            "sse": "/sse"
        },
        "leaderboard_types": [
            "brokenblocks", "deaths", "kills", "mobskilled", "money",
            "placedblocks", "playtime", "sell", "shards", "shop"
        ],
        "documentation": "https://api.donutsmp.net/index.html"
    })

async def http_health(request):
    return JSONResponse({
        "status": "ok",
        "server": "donutsmp-api",
        "version": "0.1.0",
        "api_key_configured": bool(get_api_key())
    })

async def http_auction_list(request):
    page = int(request.path_params.get("page", 1))
    return JSONResponse(make_request(f"/auction/list/{page}"))

async def http_auction_transactions(request):
    page = int(request.path_params.get("page", 1))
    return JSONResponse(make_request(f"/auction/transactions/{page}"))

async def http_leaderboard(request):
    board_type = request.path_params.get("type")
    page = int(request.path_params.get("page", 1))
    return JSONResponse(make_request(f"/leaderboards/{board_type}/{page}"))

async def http_lookup_player(request):
    user = request.path_params.get("user")
    return JSONResponse(make_request(f"/lookup/{user}"))

async def http_player_stats(request):
    user = request.path_params.get("user")
    return JSONResponse(make_request(f"/stats/{user}"))

async def http_shield_config_get(request):
    platform = request.path_params.get("platform")
    service = request.path_params.get("service")
    return JSONResponse(make_request(f"/shield/{platform}/config/{service}"))

async def http_shield_config_put(request):
    platform = request.path_params.get("platform")
    service = request.path_params.get("service")
    body = await request.json()
    return JSONResponse(make_request(f"/shield/{platform}/config/{service}", method="PUT", data=body))

async def http_shield_metrics(request):
    service = request.path_params.get("service")
    return JSONResponse(make_request(f"/shield/metrics/{service}"))

async def http_shield_stats(request):
    service = request.path_params.get("service")
    return JSONResponse(make_request(f"/shield/stats/{service}"))

async def http_github_page(request):
    return JSONResponse({
        "message": "Visit the GitHub repository for documentation and source code.",
        "url": "https://github.com/SzaBee13/DonutSMP-MCP"
    })

# ── MCP endpoint (JSON-RPC 2.0) ───────────────────────────────
async def http_mcp_endpoint(request):
    if request.method != "POST":
        return JSONResponse({
            "name": "DonutSMP MCP Endpoint",
            "version": "0.1.0",
            "description": "MCP (Model Context Protocol) endpoint for AI integrations",
            "protocol": "JSON-RPC 2.0",
            "usage": "POST JSON-RPC 2.0 requests to this endpoint"
        })
    try:
        body = await request.json()
        if "method" not in body:
            return JSONResponse({"error": "Invalid MCP request"}, status_code=400)

        method = body.get("method")
        params = body.get("params", {})
        req_id = body.get("id")

        if method == "initialize":
            return JSONResponse({
                "jsonrpc": "2.0", "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"resources": {}, "tools": {"listChanged": True}},
                    "serverInfo": {"name": "DonutSMP", "version": "0.1.0"}
                }
            })
        elif method == "tools/list":
            return JSONResponse({
                "jsonrpc": "2.0", "id": req_id,
                "result": {"tools": get_mcp_tools()}
            })
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            valid_tools = ["auction_list", "auction_transactions", "leaderboards",
                           "lookup_player", "player_stats", "shield_metrics", "shield_stats"]
            if tool_name not in valid_tools:
                return JSONResponse({
                    "jsonrpc": "2.0", "id": req_id,
                    "error": {"code": -32601, "message": f"Tool not found: {tool_name}"}
                })
            result = execute_mcp_tool(tool_name, arguments)
            return JSONResponse({
                "jsonrpc": "2.0", "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
            })
        else:
            return JSONResponse({
                "jsonrpc": "2.0", "id": req_id,
                "error": {"code": -32601, "message": f"Unknown method: {method}"}
            })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

# ── SSE endpoint ──────────────────────────────────────────────
async def http_sse_endpoint(request):
    query_params = request.query_params
    update_type = query_params.get("type", "health")
    interval = int(query_params.get("interval", "30"))

    async def event_generator():
        try:
            while True:
                if update_type == "health":
                    data = {
                        "status": "ok",
                        "timestamp": datetime.datetime.now().isoformat(),
                        "api_key_configured": bool(get_api_key())
                    }
                elif update_type == "leaderboards":
                    board = query_params.get("board", "money")
                    page = query_params.get("page", "1")
                    data = make_request(f"/leaderboards/{board}/{page}")
                elif update_type == "stats":
                    user = query_params.get("user", "")
                    data = {"error": "Provide ?user=USERNAME"} if not user else make_request(f"/stats/{user}")
                else:
                    data = {"error": f"Unknown type '{update_type}'. Use: health, leaderboards, stats"}
                yield f"data: {json.dumps(data)}\n\n"
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

# ── MCP helpers ───────────────────────────────────────────────
def get_mcp_tools():
    return [
        {
            "name": "auction_list",
            "description": "Get all current Auction House entries with pagination",
            "inputSchema": {"type": "object", "properties": {"page": {"type": "number", "default": 1}}}
        },
        {
            "name": "auction_transactions",
            "description": "Get all Auction House transaction data with pagination",
            "inputSchema": {"type": "object", "properties": {"page": {"type": "number", "default": 1}}}
        },
        {
            "name": "leaderboards",
            "description": "Get leaderboard data. Types: brokenblocks, deaths, kills, mobskilled, money, placedblocks, playtime, sell, shards, shop",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "default": "money"},
                    "page": {"type": "number", "default": 1}
                },
                "required": ["type"]
            }
        },
        {
            "name": "lookup_player",
            "description": "Get player info (like /findplayer)",
            "inputSchema": {"type": "object", "properties": {"user": {"type": "string"}}, "required": ["user"]}
        },
        {
            "name": "player_stats",
            "description": "Get player profile statistics (like /stats)",
            "inputSchema": {"type": "object", "properties": {"user": {"type": "string"}}, "required": ["user"]}
        },
        {
            "name": "shield_metrics",
            "description": "Get Shield service metrics",
            "inputSchema": {"type": "object", "properties": {"service": {"type": "string"}}, "required": ["service"]}
        },
        {
            "name": "shield_stats",
            "description": "Get Shield service stats",
            "inputSchema": {"type": "object", "properties": {"service": {"type": "string"}}, "required": ["service"]}
        }
    ]

def execute_mcp_tool(tool_name: str, arguments: dict) -> dict:
    try:
        if tool_name == "auction_list":
            return make_request(f"/auction/list/{arguments.get('page', 1)}")
        elif tool_name == "auction_transactions":
            return make_request(f"/auction/transactions/{arguments.get('page', 1)}")
        elif tool_name == "leaderboards":
            return make_request(f"/leaderboards/{arguments.get('type', 'money')}/{arguments.get('page', 1)}")
        elif tool_name == "lookup_player":
            user = arguments.get("user")
            return {"error": "user required"} if not user else make_request(f"/lookup/{user}")
        elif tool_name == "player_stats":
            user = arguments.get("user")
            return {"error": "user required"} if not user else make_request(f"/stats/{user}")
        elif tool_name == "shield_metrics":
            service = arguments.get("service")
            return {"error": "service required"} if not service else make_request(f"/shield/metrics/{service}")
        elif tool_name == "shield_stats":
            service = arguments.get("service")
            return {"error": "service required"} if not service else make_request(f"/shield/stats/{service}")
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        return {"error": str(e)}

# ── App ───────────────────────────────────────────────────────
app = Starlette(
    debug=False,
    routes=[
        Route("/", http_root),
        Route("/health", http_health),
        Route("/auction/list/{page:int}", http_auction_list),
        Route("/auction/transactions/{page:int}", http_auction_transactions),
        Route("/leaderboards/{type}/{page:int}", http_leaderboard),
        Route("/lookup/{user}", http_lookup_player),
        Route("/stats/{user}", http_player_stats),
        Route("/shield/{platform}/config/{service}", http_shield_config_get, methods=["GET"]),
        Route("/shield/{platform}/config/{service}", http_shield_config_put, methods=["PUT"]),
        Route("/shield/metrics/{service}", http_shield_metrics),
        Route("/shield/stats/{service}", http_shield_stats),
        Route("/github", http_github_page),
        Route("/mcp", http_mcp_endpoint, methods=["GET", "POST"]),
        Route("/sse", http_sse_endpoint, methods=["GET"]),
    ],
)

handler = app
