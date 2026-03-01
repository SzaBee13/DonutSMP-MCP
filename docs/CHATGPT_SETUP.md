# ChatGPT Custom Connector Setup Guide

## ✅ Updates Applied (Commit e2e3607)

Your DonutSMP MCP server now includes ChatGPT-specific compatibility fixes:

### 1. **Discovery Endpoint** (NEW)
- **`GET /.well-known/mcp.json`** - OpenAI 2026 discovery pattern
  - Returns server capabilities, endpoints, protocol version
  - ChatGPT probes this during connector creation

### 2. **Enhanced CORS**
- Wildcard origin (`*`)
- All headers allowed (`Access-Control-Allow-Headers: *`)
- Exposed headers for client access
- 24h preflight cache (`Access-Control-Max-Age: 86400`)

### 3. **Improved Logging**
- Every request logs: method, path, query, User-Agent, Origin, Content-Type
- Body preview for POST/PUT (first 500 chars)
- Check Vercel logs at: https://vercel.com/szabee13s-projects/donutsmp-mcp/logs

### 4. **Dual-Path Routing** (Already Present)
- All endpoints available at **both**:
  - Root: `/tools`, `/health`, `/auction/list/1`, etc.
  - Prefixed: `/mcp/tools`, `/mcp/health`, `/mcp/auction/list/1`, etc.

---

## 🚀 How to Create ChatGPT Connector

### Option A: Base URL (Recommended)
```
https://donutsmp-mcp.vercel.app
```

### Option B: With /mcp Prefix
```
https://donutsmp-mcp.vercel.app/mcp
```

### Steps:
1. Go to ChatGPT settings → Custom connectors → Create
2. Paste one of the URLs above
3. ChatGPT will:
   - Probe `/.well-known/mcp.json` (discovery)
   - Check `/tools` or `/mcp/tools` (tool list)
   - Test JSON-RPC at `/` or `/mcp` (handshake)
4. If successful, you'll see **7 tools**:
   - `auction_list`, `auction_transactions`, `leaderboards`
   - `lookup_player`, `player_stats`
   - `shield_metrics`, `shield_stats`

---

## 🧪 Production Verification (All Passing ✓)

```powershell
# Discovery endpoint
curl https://donutsmp-mcp.vercel.app/.well-known/mcp.json
# → {"name":"DonutSMP MCP","capabilities":{"tools":true},...}

# Tool list (REST)
curl https://donutsmp-mcp.vercel.app/tools
# → {"tools":[{"name":"auction_list",...}], "server":{...}}

# Tool list (MCP JSON-RPC)
curl -X POST https://donutsmp-mcp.vercel.app/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
# → {"jsonrpc":"2.0","id":1,"result":{"tools":[...]}}

# CORS preflight
curl -X OPTIONS https://donutsmp-mcp.vercel.app/tools -I
# → Access-Control-Allow-Origin: *
```

---

## 🐛 Debugging (If Connector Still Fails)

1. **Check Vercel logs** during connector creation:
   ```
   vercel logs donutsmp-mcp.vercel.app --follow
   ```
   Look for `[REQ]` lines showing ChatGPT's discovery requests.

2. **Common issues:**
   - **"App cannot be found"** → ChatGPT didn't get valid JSON from discovery endpoints
   - **Silent redirect** → CORS preflight failed (now fixed with `*` headers)
   - **Modal despawn** → JSON-RPC handshake error (check logs for exact method called)

3. **Manual verification:**
   ```bash
   # Test discovery
   curl https://donutsmp-mcp.vercel.app/.well-known/mcp.json | jq .
   
   # Test tools endpoint
   curl https://donutsmp-mcp.vercel.app/tools | jq '.tools | length'
   # Should return: 7
   
   # Test MCP handshake
   curl -X POST https://donutsmp-mcp.vercel.app \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26"}}' | jq .
   # Should return: {"jsonrpc":"2.0","id":1,"result":{...}}
   ```

---

## 📝 What Changed in Code

```python
# 1. Added /.well-known/mcp.json (Lines 286-313)
@app.route("/.well-known/mcp.json", methods=["GET"])
def well_known_mcp():
    """OpenAI/ChatGPT MCP discovery endpoint (2026 pattern)."""
    return jsonify({
        "name": "DonutSMP MCP",
        "capabilities": {"tools": True, ...},
        "endpoints": {"root": "/", "tools": "/tools", ...}
    })

# 2. Enhanced CORS (Lines 77-88)
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"  # Was limited before
    response.headers["Access-Control-Expose-Headers"] = "*"  # NEW
    response.headers["Access-Control-Max-Age"] = "86400"     # NEW
    return response

# 3. Improved logging (Lines 62-75)
@app.before_request
def log_requests_and_handle_options():
    ua = request.headers.get('User-Agent', 'n/a')[:80]      # NEW
    origin = request.headers.get('Origin', 'n/a')           # NEW
    ct = request.headers.get('Content-Type', 'n/a')         # NEW
    print(f"[REQ] {request.method} {request.path}")
    print(f"      UA={ua} Origin={origin} CT={ct}")
```

---

## 🎯 Next Steps

1. **Retry connector creation** in ChatGPT with:
   - `https://donutsmp-mcp.vercel.app`
   
2. **If it still fails:**
   - Check Vercel logs during the attempt
   - Share the `[REQ]` log lines here
   - We can add a temporary `/debug/echo` endpoint to capture exact payloads

3. **If it succeeds:**
   - Test a tool (e.g., "Get leaderboard for money")
   - Verify it returns DonutSMP data

---

**Deployment:** Commit `e2e3607` live at https://donutsmp-mcp.vercel.app  
**Repository:** https://github.com/SzaBee13/DonutSMP-MCP
