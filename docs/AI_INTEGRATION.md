# AI Integration Guide

This guide explains how to use the DonutSMP API with AI tools like Claude through the `/mcp` and `/sse` endpoints.

## Endpoints for AI

### 1. MCP Endpoint (JSON-RPC 2.0)

**URL:** `POST https://yourserver.vercel.app/mcp`

The `/mcp` endpoint implements the Model Context Protocol using JSON-RPC 2.0. This allows AI tools to query DonutSMP data.

#### Methods Available

**Initialize Connection**
```bash
POST /mcp
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "clientInfo": {
      "name": "Claude",
      "version": "3.5"
    }
  }
}
```

**List Available Tools**
```bash
POST /mcp
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list"
}
```

**Call a Tool**
```bash
POST /mcp
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "player_stats",
    "arguments": {
      "user": "Notch"
    }
  }
}
```

#### Available MCP Tools

- `auction_list` - Get auction house listings
- `auction_transactions` - Get auction transactions
- `leaderboards` - Get leaderboard data (money, kills, deaths, etc.)
- `lookup_player` - Look up player information
- `player_stats` - Get player statistics
- `shield_metrics` - Get shield service metrics
- `shield_stats` - Get shield service stats

### 2. SSE Endpoint (Server-Sent Events)

**URL:** `GET https://yourserver.vercel.app/sse`

The `/sse` endpoint provides real-time streaming updates using Server-Sent Events.

#### Query Parameters

- `type` - Type of updates to stream (default: "health")
  - `health` - Server health status
  - `leaderboards` - Leaderboard updates
  - `stats` - Player stats updates
- `interval` - Update interval in seconds (default: 30)
- `board` - For leaderboards: which board (money, kills, deaths, etc.)
- `page` - Page number for leaderboard
- `user` - Username for stats

#### Examples

**Stream health status every 10 seconds:**
```bash
curl "http://127.0.0.1:8000/sse?type=health&interval=10"
```

**Stream money leaderboard updates every 60 seconds:**
```bash
curl "http://127.0.0.1:8000/sse?type=leaderboards&board=money&page=1&interval=60"
```

**Stream player stats for Notch every 30 seconds:**
```bash
curl "http://127.0.0.1:8000/sse?type=stats&user=Notch&interval=30"
```

#### SSE Event Format

```
data: {"status": "ok", "timestamp": "2026-03-01T12:00:00", "api_key_configured": true}

data: {"name": "Player1", "money": 5000, ...}

```

## Using with Claude Desktop

To use the `/mcp` endpoint with Claude Desktop, configure it to connect via HTTP:

```json
{
  "mcpServers": {
    "donutsmp": {
      "command": "curl",
      "args": ["-X", "POST", "-d", "@-", "http://localhost:8000/mcp"],
      "env": {}
    }
  }
}
```

Or if deployed on Vercel:

```json
{
  "mcpServers": {
    "donutsmp": {
      "command": "curl",
      "args": ["-X", "POST", "-d", "@-", "https://yourproject.vercel.app/mcp"],
      "env": {}
    }
  }
}
```

## Using with Custom AI Tools

### Python Example

```python
import httpx
import json

BASE_URL = "http://127.0.0.1:8000"

# Get player stats
response = httpx.post(
    f"{BASE_URL}/mcp",
    json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "player_stats",
            "arguments": {"user": "Notch"}
        }
    }
)

print(json.dumps(response.json(), indent=2))
```

### JavaScript Example

```javascript
const BASE_URL = "http://127.0.0.1:8000";

async function getPlayerStats(user) {
  const response = await fetch(`${BASE_URL}/mcp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method: "tools/call",
      params: {
        name: "player_stats",
        arguments: { user }
      }
    })
  });

  return response.json();
}

getPlayerStats("Notch").then(console.log);
```

## Benefits

✅ **JSON-RPC Standard** - MCP endpoint uses standard JSON-RPC 2.0 protocol
✅ **Real-time Streaming** - SSE endpoint for live data updates
✅ **AI-Ready** - Works with Claude, GPT-4, and other AI tools
✅ **Scalable** - Deploy to Vercel and scale automatically
✅ **No Authentication Overhead** - API key is configured server-side

## Error Handling

### MCP Error Response

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Method not found"
  }
}
```

### SSE Error Response

```
data: {"error": "Invalid query parameter: board=invalid"}
```

## Rate Limits

- DonutSMP API: 250 requests/minute per API key
- SSE: Each stream counts as ongoing requests
- MCP: Standard JSON-RPC rate limits apply

## Troubleshooting

**MCP: Method not found**
- Check method name is correct: `initialize`, `tools/list`, `tools/call`
- Verify JSON-RPC format is valid

**SSE: No data received**
- Ensure query parameters are valid
- Check network connection (SSE requires persistent connection)
- Verify `interval` parameter is reasonable (default 30s)

**No API key configured warning**
- Set `DONUTSMP_API_KEY` environment variable
- Some endpoints may return limited data without API key

## Documentation

- Full API docs: https://api.donutsmp.net/index.html
- GitHub: https://github.com/SzaBee13/DonutSMP-MCP
