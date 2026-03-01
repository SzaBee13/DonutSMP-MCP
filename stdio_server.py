#!/usr/bin/env python3
"""
MCP stdio wrapper for DonutSMP API bridge.

Claude Desktop expects stdio-based MCP servers. This script acts as a bridge:
- Reads JSON-RPC from stdin (Claude Desktop)
- Executes MCP methods directly (without HTTP overhead)
- Writes JSON-RPC responses to stdout

This is the local-only version. For HTTP/ChatGPT, use the Flask app (app.py).
"""

import sys
import json
import os
from typing import Any

# Import the core logic from app.py
from app import (
    handle_mcp_message,
    get_mcp_tools,
    get_chatgpt_tools_payload,
    MCP_PROTOCOL_VERSION,
    get_api_key,
)


def send_response(response: dict[str, Any] | None) -> None:
    """Send JSON-RPC response to stdout for Claude Desktop."""
    if response is None:
        # Notification - no response
        return
    
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()


def main():
    """Main stdio loop for Claude Desktop MCP communication."""
    # Log startup to stderr (Claude Desktop shows this in logs)
    api_key_status = "configured" if get_api_key() else "NOT configured"
    sys.stderr.write(f"DonutSMP MCP stdio server starting (API key: {api_key_status})\n")
    sys.stderr.flush()
    
    # Read JSON-RPC messages from stdin line by line
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            # Parse incoming JSON-RPC message
            message = json.loads(line)
            
            # Log request to stderr (for debugging)
            method = message.get("method", "unknown")
            req_id = message.get("id", "n/a")
            sys.stderr.write(f"[STDIO] Request: {method} (id={req_id})\n")
            sys.stderr.flush()
            
            # Handle the message using shared logic from app.py
            response = handle_mcp_message(message)
            
            # Send response back to Claude Desktop
            send_response(response)
            
        except json.JSONDecodeError as e:
            sys.stderr.write(f"[STDIO] JSON decode error: {e}\n")
            sys.stderr.flush()
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"}
            }
            send_response(error_response)
            
        except Exception as e:
            sys.stderr.write(f"[STDIO] Error: {e}\n")
            sys.stderr.flush()
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
            }
            send_response(error_response)


if __name__ == "__main__":
    main()
