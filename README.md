# DonutSMP MCP Server

An MCP (Model Context Protocol) server for the DonutSMP Public API. This server provides access to all DonutSMP API endpoints including auction houses, leaderboards, player lookups, statistics, and shield configurations.

**🚀 Deploy Options:** Local (STDIO/HTTP/SSE) | Vercel (Serverless) | Docker (Coming Soon)

## Features

- **Auction House**: List current auction entries and transaction history
- **Leaderboards**: Access 10 different leaderboards (kills, deaths, money, playtime, blocks, etc.)
- **Player Lookup**: Get player information similar to `/findplayer` command
- **Player Statistics**: Retrieve detailed player stats like `/stats` command
- **Shield Management**: Get and update Shield configurations for Java and Bedrock services
- **Shield Monitoring**: Access service metrics and stats

## Deployment Options

### 🚀 Deploy to Vercel (Recommended for Production)

Deploy as a serverless REST API on Vercel:

```bash
vercel
```

See [VERCEL_DEPLOY.md](VERCEL_DEPLOY.md) for complete deployment guide.

### 💻 Local Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your DonutSMP API key as an environment variable:
```bash
# Windows (PowerShell)
$env:DONUTSMP_API_KEY = "your_api_key_here"

# Windows (Command Prompt)
set DONUTSMP_API_KEY=your_api_key_here

# Linux/Mac
export DONUTSMP_API_KEY=your_api_key_here
```

To get an API key, use the `/api` command in-game on DonutSMP.

## Usage

### Running the Server

The server supports three transport modes:

#### 1. STDIO Mode (Default - for Claude Desktop)
```bash
python main.py
# or explicitly
python main.py --mode stdio
```

#### 2. SSE Mode (Server-Sent Events)
```bash
python main.py --mode sse --host 127.0.0.1 --port 8000
```
SSE endpoint will be available at: `http://127.0.0.1:8000/sse`

#### 3. HTTP Mode (REST API)
```bash
python main.py --mode http --host 127.0.0.1 --port 8000
```
REST API will be available at: `http://127.0.0.1:8000`

### Command Line Options

- `--mode` - Transport mode: `stdio`, `sse`, or `http` (default: `stdio`)
- `--host` - Host to bind to for SSE/HTTP modes (default: `127.0.0.1`)
- `--port` - Port to bind to for SSE/HTTP modes (default: `8000`)

### HTTP Mode REST Endpoints

When running in HTTP mode, the following REST endpoints are available:

- `GET /health` - Health check
- `GET /tools` - List all available tools
- `GET /auction/list/{page}` - Auction house listings
- `GET /auction/transactions/{page}` - Auction transactions
- `GET /leaderboards/{type}/{page}` - Leaderboards (types: brokenblocks, deaths, kills, mobskilled, money, placedblocks, playtime, sell, shards, shop)
- `GET /lookup/{user}` - Player lookup
- `GET /stats/{user}` - Player statistics
- `GET /shield/{platform}/config/{service}` - Shield config (platform: java/bedrock)
- `GET /shield/metrics/{service}` - Shield metrics
- `GET /shield/stats/{service}` - Shield stats

Example HTTP requests:
```bash
# Health check
curl http://127.0.0.1:8000/health

# Get player stats
curl http://127.0.0.1:8000/stats/Notch

# Get money leaderboard page 1
curl http://127.0.0.1:8000/leaderboards/money/1
```

### Configuring with Claude Desktop

Add to your Claude Desktop configuration file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "donutsmp": {
      "command": "python",
      "args": [
        "d:\\ai playground\\mcp_donut\\main.py"
      ],
      "env": {
        "DONUTSMP_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Available Tools

### Auction
- `auction_list` - Get current Auction House entries (paginated)
- `auction_transactions` - Get Auction House transaction history (paginated)

### Leaderboards
- `leaderboard_broken_blocks` - Blocks broken leaderboard
- `leaderboard_deaths` - Deaths leaderboard
- `leaderboard_kills` - Kills leaderboard
- `leaderboard_mobs_killed` - Mobs killed leaderboard
- `leaderboard_money` - Money leaderboard
- `leaderboard_placed_blocks` - Blocks placed leaderboard
- `leaderboard_playtime` - Playtime leaderboard
- `leaderboard_sell` - Amount made on /sell leaderboard
- `leaderboard_shards` - Shards leaderboard
- `leaderboard_shop` - Amount spent on /shop leaderboard

### Player Information
- `lookup_player` - Look up player by username or UUID
- `player_stats` - Get detailed player statistics

### Shield (Admin)
- `shield_bedrock_config_get` - Get Bedrock Shield config
- `shield_bedrock_config_update` - Update Bedrock Shield config
- `shield_java_config_get` - Get Java Shield config
- `shield_java_config_update` - Update Java Shield config
- `shield_metrics` - Get Shield service metrics
- `shield_stats` - Get Shield service stats

## API Reference

Base URL: `https://api.donutsmp.net/v1`

Rate Limit: 250 requests per minute per API key

For full API documentation, visit: https://api.donutsmp.net/index.html

## Examples

### Check Player Stats
```
Can you show me the stats for player "Notch"?
```

### View Leaderboard
```
What are the top players on the money leaderboard?
```

### Auction House
```
Show me the current auction house listings on page 1
```

## License

This project is licensed under the GUN GPL.3 License. See [LICENSE](LICENSE.md) for details.
