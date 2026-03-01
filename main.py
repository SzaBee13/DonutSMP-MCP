"""
DonutSMP REST API Server
HTTP-only mode using Starlette and Uvicorn
Includes MCP and SSE endpoints for AI integrations
"""
import os
import sys
import argparse
import json
import asyncio
from typing import Any
import httpx
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse, StreamingResponse
import uvicorn
from dotenv import load_dotenv

# Optional MCP imports
try:
    from mcp.server.models import InitializationOptions
    import mcp.types as types
    from mcp.server import NotificationOptions, Server
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# Load environment variables from .env file
load_dotenv()

# DonutSMP API configuration
API_BASE_URL = "https://api.donutsmp.net/v1"

def get_api_key() -> str:
    """Get API key from environment variable."""
    return os.environ.get("DONUTSMP_API_KEY", "")

def make_request(endpoint: str, method: str = "GET", data: dict | None = None) -> dict[str, Any]:
    """Make a request to the DonutSMP API."""
    api_key = get_api_key()
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    url = f"{API_BASE_URL}{endpoint}"
    print(f"[DonutSMP] {method} {endpoint}", flush=True)
    
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

# HTTP endpoint handlers
async def http_root(request):
    """Root endpoint with API info."""
    return JSONResponse({
        "name": "DonutSMP API",
        "version": "0.1.0",
        "base_url": "https://api.donutsmp.net",
        "endpoints": {
            "health": "/health",
            "auction_list": "/auction/list/{page}",
            "auction_transactions": "/auction/transactions/{page}",
            "leaderboards": "/leaderboards/{type}/{page}",
            "lookup": "/lookup/{user}",
            "stats": "/stats/{user}",
            "shield_config": "/shield/{platform}/config/{service}",
            "shield_metrics": "/shield/metrics/{service}",
            "shield_stats": "/shield/stats/{service}"
        },
        "leaderboard_types": [
            "brokenblocks", "deaths", "kills", "mobskilled", "money",
            "placedblocks", "playtime", "sell", "shards", "shop"
        ],
        "documentation": "https://api.donutsmp.net/index.html"
    })

async def http_health(request):
    """Health check endpoint."""
    api_key = get_api_key()
    return JSONResponse({
        "status": "ok",
        "server": "donutsmp-api",
        "version": "0.1.0",
        "api_key_configured": bool(api_key)
    })

async def http_auction_list(request):
    """GET /auction/list/{page}"""
    page = int(request.path_params.get("page", 1))
    result = make_request(f"/auction/list/{page}")
    return JSONResponse(result)

async def http_auction_transactions(request):
    """GET /auction/transactions/{page}"""
    page = int(request.path_params.get("page", 1))
    result = make_request(f"/auction/transactions/{page}")
    return JSONResponse(result)

async def http_leaderboard(request):
    """GET /leaderboards/{type}/{page}"""
    board_type = request.path_params.get("type")
    page = int(request.path_params.get("page", 1))
    result = make_request(f"/leaderboards/{board_type}/{page}")
    return JSONResponse(result)

async def http_lookup_player(request):
    """GET /lookup/{user}"""
    user = request.path_params.get("user")
    result = make_request(f"/lookup/{user}")
    return JSONResponse(result)

async def http_player_stats(request):
    """GET /stats/{user}"""
    user = request.path_params.get("user")
    result = make_request(f"/stats/{user}")
    return JSONResponse(result)

async def http_shield_config_get(request):
    """GET /shield/{platform}/config/{service}"""
    platform = request.path_params.get("platform")
    service = request.path_params.get("service")
    result = make_request(f"/shield/{platform}/config/{service}")
    return JSONResponse(result)

async def http_shield_config_put(request):
    """PUT /shield/{platform}/config/{service}"""
    platform = request.path_params.get("platform")
    service = request.path_params.get("service")
    body = await request.json()
    result = make_request(f"/shield/{platform}/config/{service}", method="PUT", data=body)
    return JSONResponse(result)

async def http_shield_metrics(request):
    """GET /shield/metrics/{service}"""
    service = request.path_params.get("service")
    result = make_request(f"/shield/metrics/{service}")
    return JSONResponse(result)

async def http_shield_stats(request):
    """GET /shield/stats/{service}"""
    service = request.path_params.get("service")
    result = make_request(f"/shield/stats/{service}")
    return JSONResponse(result)

async def http_github_page(request):
    """Redirect to GitHub repository."""
    return JSONResponse({
        "message": "Visit the GitHub repository for documentation and source code.",
        "url": "https://github.com/SzaBee13/DonutSMP-MCP"
    })

# MCP and SSE Endpoints for AI

async def http_mcp_endpoint(request):
    """MCP protocol endpoint for AI integrations.
    
    This endpoint allows Claude and other AI tools to use this as an MCP server
    via HTTP POST requests with JSON-RPC format.
    
    Example request:
    POST /mcp
    {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {...}}
    """
    if request.method == "POST":
        try:
            body = await request.json()
            
            # Handle JSON-RPC MCP requests
            if "method" in body:
                method = body.get("method")
                params = body.get("params", {})
                
                # MCP Initialize request
                if method == "initialize":
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "resources": {},
                                "tools": {
                                    "listChanged": True
                                }
                            },
                            "serverInfo": {
                                "name": "DonutSMP",
                                "version": "0.1.0"
                            }
                        }
                    })
                
                # MCP Tools/Resources list request
                elif method == "tools/list":
                    tools = get_mcp_tools()
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "result": {
                            "tools": tools
                        }
                    })
                
                # MCP Tool call request
                elif method == "tools/call":
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    
                    # Execute tool
                    if tool_name in ["auction_list", "auction_transactions", "leaderboards", 
                                    "lookup_player", "player_stats", "shield_metrics", "shield_stats"]:
                        result = execute_mcp_tool(tool_name, arguments)
                        return JSONResponse({
                            "jsonrpc": "2.0",
                            "id": body.get("id"),
                            "result": {
                                "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                            }
                        })
                    else:
                        return JSONResponse({
                            "jsonrpc": "2.0",
                            "id": body.get("id"),
                            "error": {"code": -32601, "message": f"Method not found: {tool_name}"}
                        })
                
                else:
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "error": {"code": -32601, "message": f"Unknown method: {method}"}
                    })
            else:
                return JSONResponse({"error": "Invalid MCP request"}, status_code=400)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=400)
    else:
        return JSONResponse({
            "name": "DonutSMP MCP Endpoint",
            "version": "0.1.0",
            "description": "MCP (Model Context Protocol) endpoint for AI integrations",
            "protocol": "JSON-RPC 2.0",
            "usage": "POST JSON-RPC 2.0 requests to this endpoint"
        })

async def http_sse_endpoint(request):
    """Server-Sent Events (SSE) endpoint for real-time AI streaming.
    
    This endpoint allows clients to establish a streaming connection
    to receive real-time updates from the DonutSMP API.
    
    Example:
    GET /sse?type=leaderboards&board=money&interval=30
    """
    query_params = request.query_params
    update_type = query_params.get("type", "health")
    interval = int(query_params.get("interval", "30"))
    
    async def event_generator():
        """Generate SSE events."""
        try:
            while True:
                if update_type == "health":
                    api_key = get_api_key()
                    data = {
                        "status": "ok",
                        "timestamp": __import__("datetime").datetime.now().isoformat(),
                        "api_key_configured": bool(api_key)
                    }
                
                elif update_type == "leaderboards":
                    board = query_params.get("board", "money")
                    page = query_params.get("page", "1")
                    data = make_request(f"/leaderboards/{board}/{page}")
                
                elif update_type == "stats":
                    user = query_params.get("user", "Notch")
                    data = make_request(f"/stats/{user}")
                
                else:
                    data = {"error": f"Unknown type: {update_type}"}
                
                # Format as SSE
                yield f"data: {json.dumps(data)}\n\n"
                
                # Wait before next update
                await asyncio.sleep(interval)
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )

def get_mcp_tools():
    """Get list of tools in MCP format."""
    return [
        {
            "name": "auction_list",
            "description": "Get all current Auction House entries with pagination",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "page": {
                        "type": "number",
                        "description": "Page number to retrieve",
                        "default": 1
                    }
                }
            }
        },
        {
            "name": "auction_transactions",
            "description": "Get all Auction House transaction data with pagination",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "page": {
                        "type": "number",
                        "description": "Page number to retrieve",
                        "default": 1
                    }
                }
            }
        },
        {
            "name": "leaderboards",
            "description": "Get leaderboard data",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "description": "Leaderboard type (brokenblocks, deaths, kills, mobskilled, money, placedblocks, playtime, sell, shards, shop)",
                        "default": "money"
                    },
                    "page": {
                        "type": "number",
                        "description": "Page number",
                        "default": 1
                    }
                },
                "required": ["type"]
            }
        },
        {
            "name": "lookup_player",
            "description": "Get player information",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "user": {
                        "type": "string",
                        "description": "Username or UUID of the player"
                    }
                },
                "required": ["user"]
            }
        },
        {
            "name": "player_stats",
            "description": "Get player profile statistics",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "user": {
                        "type": "string",
                        "description": "Username or UUID of the player"
                    }
                },
                "required": ["user"]
            }
        },
        {
            "name": "shield_metrics",
            "description": "Get service metrics for Shield",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Service name"
                    }
                },
                "required": ["service"]
            }
        },
        {
            "name": "shield_stats",
            "description": "Get service stats for Shield",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Service name"
                    }
                },
                "required": ["service"]
            }
        }
    ]

def execute_mcp_tool(tool_name: str, arguments: dict) -> dict:
    """Execute an MCP tool and return result."""
    try:
        if tool_name == "auction_list":
            page = arguments.get("page", 1)
            return make_request(f"/auction/list/{page}")
        
        elif tool_name == "auction_transactions":
            page = arguments.get("page", 1)
            return make_request(f"/auction/transactions/{page}")
        
        elif tool_name == "leaderboards":
            board_type = arguments.get("type", "money")
            page = arguments.get("page", 1)
            return make_request(f"/leaderboards/{board_type}/{page}")
        
        elif tool_name == "lookup_player":
            user = arguments.get("user")
            if not user:
                return {"error": "User parameter required"}
            return make_request(f"/lookup/{user}")
        
        elif tool_name == "player_stats":
            user = arguments.get("user")
            if not user:
                return {"error": "User parameter required"}
            return make_request(f"/stats/{user}")
        
        elif tool_name == "shield_metrics":
            service = arguments.get("service")
            if not service:
                return {"error": "Service parameter required"}
            return make_request(f"/shield/metrics/{service}")
        
        elif tool_name == "shield_stats":
            service = arguments.get("service")
            if not service:
                return {"error": "Service parameter required"}
            return make_request(f"/shield/stats/{service}")
        
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    except Exception as e:
        return {"error": str(e)}

def serve_favicon():
    """Serve a simple favicon."""
    from starlette.responses import FileResponse
    return FileResponse("favicon.png", media_type="image/png")

# Create Starlette app
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
        # AI Integration endpoints
        Route("/mcp", http_mcp_endpoint, methods=["GET", "POST"]),
        Route("/sse", http_sse_endpoint, methods=["GET"]),
        Route("/favicon.ico", serve_favicon),
        Route("/favicon.png", serve_favicon)
    ],
)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="DonutSMP REST API Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to run server on (default: 8000)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    args = parser.parse_args()
    
    print("="*60, flush=True)
    print("DonutSMP REST API Server", flush=True)
    print("https://api.donutsmp.net", flush=True)
    print("="*60, flush=True)
    print(f"[DonutSMP] API Base URL: {API_BASE_URL}", flush=True)
    
    api_key = get_api_key()
    if api_key:
        print(f"[DonutSMP] API Key loaded: {api_key[:10]}...", flush=True)
    else:
        print("[DonutSMP] WARNING: No API key found in DONUTSMP_API_KEY environment variable", flush=True)
    
    print(f"[DonutSMP] Starting HTTP server on http://{args.host}:{args.port}", flush=True)
    print(f"[DonutSMP] Endpoints: http://{args.host}:{args.port}/", flush=True)
    print("[DonutSMP] Press Ctrl+C to stop", flush=True)
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info"
    )

if __name__ == "__main__":
    main()
