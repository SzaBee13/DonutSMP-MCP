"""Quick test script for verifying all endpoints after ChatGPT compatibility updates."""
import json
from app import app

def test_all_endpoints():
    with app.test_client() as client:
        tests = [
            # Discovery endpoints
            ("GET", "/.well-known/mcp.json", None),
            ("GET", "/", None),
            ("GET", "/mcp", None),
            
            # Tool endpoints (dual-path)
            ("GET", "/tools", None),
            ("GET", "/mcp/tools", None),
            
            # Health endpoints (dual-path)
            ("GET", "/health", None),
            ("GET", "/mcp/health", None),
            
            # JSON-RPC MCP requests (dual-path)
            ("POST", "/", {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}}),
            ("POST", "/mcp", {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
            
            # OPTIONS preflight (CORS)
            ("OPTIONS", "/tools", None),
            ("OPTIONS", "/.well-known/mcp.json", None),
        ]
        
        print("Testing all endpoints:\n")
        for method, path, body in tests:
            if method == "GET":
                resp = client.get(path)
            elif method == "POST":
                resp = client.post(path, json=body, content_type="application/json")
            elif method == "OPTIONS":
                resp = client.options(path)
            
            status_ok = "✓" if resp.status_code in [200, 204] else "✗"
            print(f"{status_ok} {method:7} {path:30} → {resp.status_code}")
            
            # Show response preview for key endpoints
            if path in ["/.well-known/mcp.json", "/tools"] and resp.status_code == 200:
                data = resp.get_json()
                if path == "/.well-known/mcp.json":
                    print(f"    → name: {data.get('name')}, capabilities: {data.get('capabilities')}")
                elif path == "/tools":
                    print(f"    → {len(data.get('tools', []))} tools available")
            
            # Show CORS headers for OPTIONS
            if method == "OPTIONS":
                cors_origin = resp.headers.get("Access-Control-Allow-Origin", "missing")
                cors_methods = resp.headers.get("Access-Control-Allow-Methods", "missing")
                print(f"    → CORS Origin: {cors_origin}, Methods: {cors_methods}")
            
            print()

if __name__ == "__main__":
    test_all_endpoints()
