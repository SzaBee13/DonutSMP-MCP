# Claude Desktop Integration

## ✅ Configuration Added

The DonutSMP MCP server is now configured in your Claude Desktop at:
```
c:\Users\szabo\AppData\Roaming\Claude\claude_desktop_config.json
```

## 🔧 How It Works

- **`stdio_server.py`** - Stdio wrapper for Claude Desktop communication
  - Reads JSON-RPC from stdin (Claude Desktop)
  - Executes MCP protocol methods directly
  - Writes responses to stdout
  
- **`app.py`** - HTTP server for Vercel/ChatGPT
  - REST API endpoints
  - Flask-based for Vercel deployment
  - Both use the same core MCP logic

## 🚀 Usage

1. **Restart Claude Desktop** to load the new configuration

2. **Available in Claude Desktop as:** `donutsmp` MCP server

3. **7 Tools Available:**
   - `auction_list` - Get Auction House entries
   - `auction_transactions` - Get transaction history
   - `leaderboards` - Get leaderboards (money, kills, playtime, etc.)
   - `lookup_player` - Find player info
   - `player_stats` - Get player statistics
   - `shield_metrics` - Get Shield service metrics  
   - `shield_stats` - Get Shield service stats

## 🧪 Testing

Verified stdio communication:
```powershell
# Test initialize
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26"}}' | python stdio_server.py
# ✓ Returns: protocol version, capabilities, serverInfo

# Test tools/list
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python stdio_server.py
# ✓ Returns: 7 tools with descriptions and JSON schemas
```

## 🔑 API Key (Optional)

The server works without an API key, but if you have a DonutSMP API key:

1. Open: `c:\Users\szabo\AppData\Roaming\Claude\claude_desktop_config.json`
2. Update the `DONUTSMP_API_KEY` value:
   ```json
   "env": {
     "DONUTSMP_API_KEY": "your-key-here"
   }
   ```
3. Restart Claude Desktop

## 🐛 Debugging

Check Claude Desktop logs for MCP server output:
- Startup message: "DonutSMP MCP stdio server starting"
- Request logs: "[STDIO] Request: {method} (id={id})"
- Any errors will appear in Claude Desktop's MCP server logs

## 📊 Architecture

```
Claude Desktop (stdio) ──→ stdio_server.py ──→ app.py (core logic) ──→ DonutSMP API
                                                                          (api.donutsmp.net)

ChatGPT (HTTP) ────────→ app.py (Flask/Vercel) ──→ app.py (core logic) ──→ DonutSMP API
```

Both interfaces use the same MCP protocol implementation (`handle_mcp_message` in app.py).

---

**Next:** Restart Claude Desktop and try asking: *"List the top players on the DonutSMP money leaderboard"*
