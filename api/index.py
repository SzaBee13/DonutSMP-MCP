"""
Vercel serverless function for DonutSMP API.
This provides HTTP REST API access to DonutSMP data.
"""
import os
from typing import Any
import httpx
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse

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

# HTTP endpoints
async def http_auction_list(request):
    """HTTP endpoint for auction list."""
    page = int(request.path_params.get("page", 1))
    result = make_request(f"/auction/list/{page}")
    return JSONResponse(result)

async def http_auction_transactions(request):
    """HTTP endpoint for auction transactions."""
    page = int(request.path_params.get("page", 1))
    result = make_request(f"/auction/transactions/{page}")
    return JSONResponse(result)

async def http_leaderboard(request):
    """HTTP endpoint for leaderboards."""
    board_type = request.path_params.get("type")
    page = int(request.path_params.get("page", 1))
    result = make_request(f"/leaderboards/{board_type}/{page}")
    return JSONResponse(result)

async def http_lookup_player(request):
    """HTTP endpoint for player lookup."""
    user = request.path_params.get("user")
    result = make_request(f"/lookup/{user}")
    return JSONResponse(result)

async def http_player_stats(request):
    """HTTP endpoint for player stats."""
    user = request.path_params.get("user")
    result = make_request(f"/stats/{user}")
    return JSONResponse(result)

async def http_shield_config_get(request):
    """HTTP endpoint for shield config get."""
    platform = request.path_params.get("platform")
    service = request.path_params.get("service")
    result = make_request(f"/shield/{platform}/config/{service}")
    return JSONResponse(result)

async def http_shield_metrics(request):
    """HTTP endpoint for shield metrics."""
    service = request.path_params.get("service")
    result = make_request(f"/shield/metrics/{service}")
    return JSONResponse(result)

async def http_shield_stats(request):
    """HTTP endpoint for shield stats."""
    service = request.path_params.get("service")
    result = make_request(f"/shield/stats/{service}")
    return JSONResponse(result)

async def http_health(request):
    """Health check endpoint."""
    return JSONResponse({
        "status": "ok",
        "server": "donutsmp-vercel",
        "version": "0.1.0",
        "environment": "vercel"
    })

async def http_root(request):
    """Root endpoint with API info."""
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
            "shield_stats": "/shield/stats/{service}"
        },
        "leaderboard_types": [
            "brokenblocks", "deaths", "kills", "mobskilled", "money",
            "placedblocks", "playtime", "sell", "shards", "shop"
        ],
        "documentation": "https://api.donutsmp.net/index.html"
    })

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
        Route("/shield/{platform}/config/{service}", http_shield_config_get),
        Route("/shield/metrics/{service}", http_shield_metrics),
        Route("/shield/stats/{service}", http_shield_stats),
    ],
)

# Vercel handler
handler = app
