# Server Installation

## 1. Clone and Setup

The installation in production is out of scope for this, as there is a need for authentication to the MCP server. I have been using flask dev with ngrok. You will need to export the following environment variables on the server.

```bash
export NETBOX_URL="https://your-netbox-instance.com"
export NETBOX_TOKEN="your_netbox_api_token_here"
```

## Claude Desktop Configuration

## 1. Install mcp-remote

```bash
npm install -g mcp-remote
```

## 2. Configure Claude Desktop

Edit your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`  
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "Netbox": {
      "command": "npx",
      "args": ["mcp-remote", "https://your-server-url.com/api/mcp"]
    }
  }
}
```

## 3. Restart Claude Desktop

**Important**: Completely quit and restart Claude Desktop for changes to take effect.

1. Quit Claude Desktop (Cmd+Q on macOS)
2. Wait a few seconds
3. Reopen Claude Desktop
