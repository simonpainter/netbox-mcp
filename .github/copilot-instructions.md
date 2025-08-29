# NetBox MCP Server Development Instructions

**ALWAYS follow these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

NetBox MCP Server is a Python Flask application that implements the Model Context Protocol (MCP) to provide Claude Desktop with direct access to NetBox instances. It acts as a bridge between Claude Desktop and NetBox APIs, allowing natural language queries about network infrastructure.

## Working Effectively

### Bootstrap, Build, and Test the Repository

1. **Install Python dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```
   - Takes ~5 seconds to complete. NEVER CANCEL.

2. **Compile and validate Python code:**
   ```bash
   python3 -m py_compile app.py
   ```

3. **Install Node.js dependencies (required for Claude Desktop integration):**
   ```bash
   npm install -g mcp-remote
   ```
   - Takes ~3 seconds to complete. NEVER CANCEL.

### Running the Application

**CRITICAL:** The application requires two environment variables to start:

```bash
export NETBOX_URL="https://your-netbox-instance.com"
export NETBOX_TOKEN="your_netbox_api_token_here"
```

**Start the Flask development server:**
```bash
python3 app.py
```

- Default port: 8080
- Server starts immediately (< 2 seconds)
- Accessible at `http://localhost:8080`

**Without environment variables, the application will exit with error code 1:**
- `ERROR: NETBOX_URL environment variable must be set`
- `ERROR: NETBOX_TOKEN environment variable must be set`

### Testing and Validation

**CRITICAL VALIDATION REQUIREMENT:** After making changes, ALWAYS run these validation steps:

1. **Health Check Endpoint:**
   ```bash
   curl -s http://localhost:8080/health | python3 -m json.tool
   ```
   Expected response includes: `"status": "healthy"`, `"netbox_configured": true`

2. **MCP Protocol Initialize:**
   ```bash
   curl -s -X POST -H "Content-Type: application/json" \
     -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26", "capabilities": {}}}' \
     http://localhost:8080/api/mcp | python3 -m json.tool
   ```
   Expected: Valid JSON-RPC response with `"name": "netbox-mcp-server"`

3. **MCP Tools List:**
   ```bash
   curl -s -X POST -H "Content-Type: application/json" \
     -d '{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}' \
     http://localhost:8080/api/mcp | python3 -m json.tool
   ```
   Expected: List of available MCP tools (search_devices, get_sites, etc.)

4. **Test Tool Call (will fail with connection error but validates request handling):**
   ```bash
   curl -s -X POST -H "Content-Type: application/json" \
     -d '{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "search_devices", "arguments": {"limit": 1}}}' \
     http://localhost:8080/api/mcp
   ```
   Expected: JSON-RPC error response (NetBox connection will fail with dummy credentials)

## Manual Validation Scenarios

**ALWAYS execute these complete end-to-end scenarios after making changes:**

### Scenario 1: Basic Server Functionality
1. Start server with dummy credentials: `NETBOX_URL="https://demo.netbox.dev" NETBOX_TOKEN="dummy" python3 app.py`
2. Verify health endpoint returns healthy status
3. Test MCP initialize handshake
4. Verify tools list contains all expected tools
5. Stop server gracefully (Ctrl+C)

### Scenario 2: MCP Protocol Compliance
1. Send initialize request and verify protocol version `2025-03-26`
2. Request tools list and verify all 11 tools are present:
   - search_devices, get_device_details, get_device_interfaces
   - get_sites, get_site_details
   - search_ip_addresses, get_prefixes, get_available_ips
   - search_vlans, search_circuits, search_racks
3. Test invalid method calls return proper JSON-RPC errors

### Scenario 3: Error Handling
1. Start without environment variables - verify proper error messages
2. Send malformed JSON to MCP endpoint - verify error response
3. Call non-existent tool - verify "Unknown tool" error

## Repository Structure and Navigation

### Key Files and Locations
- `app.py` - Main Flask application and MCP protocol implementation
- `requirements.txt` - Python dependencies (Flask, Flask-CORS, httpx)
- `README.md` - Setup and usage documentation
- `TOOLS.md` - Comprehensive MCP tools reference

### Python Code Organization
```
app.py structure:
├── Configuration and imports (lines 1-33)
├── NetBoxClient class (async HTTP client)
├── MCP tool definitions (get_mcp_tools function)
├── MCP protocol implementation (handle_mcp_message)
├── Flask routes (/health, /api/mcp)
├── Tool execution functions (search_devices, get_sites, etc.)
└── Main entry point (lines 933-950)
```

### Common Development Tasks

**Adding new MCP tools:**
1. Add tool definition to `get_mcp_tools()` function
2. Implement tool function (async, takes args and netbox_client)
3. Add tool to `execute_tool()` dispatcher
4. Update TOOLS.md documentation

**Modifying API endpoints:**
- Health endpoint: `/health` (GET)
- MCP endpoint: `/api/mcp` (GET, POST, DELETE)

## Build and Test Timing Expectations

- **Dependency installation:** 5 seconds - NEVER CANCEL
- **Server startup:** < 2 seconds
- **Health check response:** < 1 second  
- **MCP protocol requests:** < 1 second (without NetBox connection)
- **Node.js mcp-remote install:** 3 seconds - NEVER CANCEL

## Development Environment

**Python version:** 3.8+ (tested with 3.12.3)
**Node.js version:** Any recent version (tested with 20.19.4)

**No existing test framework** - Manual validation through curl commands and server responses is the primary testing method.

**No built-in linting** - Code uses standard Python practices. Use `python3 -m py_compile app.py` to verify syntax.

## Integration with Claude Desktop

**Production deployment requires:**
1. Hosted Flask server (e.g., with ngrok for development)
2. Claude Desktop configuration with mcp-remote
3. Valid NetBox instance and API token

**Configuration example for Claude Desktop:**
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

## Critical Notes

- **NEVER use default timeout values** for any commands - all complete within seconds
- **Application does NOT build** - it's a runtime Python Flask app
- **No database dependencies** - connects directly to external NetBox APIs
- **Environment variables are required** for startup but can use dummy values for testing MCP protocol
- **Real NetBox connectivity testing requires valid NetBox instance and token**
- **Manual testing is essential** - automated test suite does not exist

## Common Output References

### Repository Root Contents
```
.
├── .git/
├── .github/
├── README.md
├── TOOLS.md  
├── app.py
├── requirements.txt
└── .gitignore
```

### Successful Server Startup Output
```
INFO:__main__:Starting NetBox MCP Server with Streamable HTTP transport on port 8080
INFO:__main__:NetBox URL: https://your-netbox-instance.com
INFO:__main__:MCP Endpoint: http://localhost:8080/api/mcp
INFO:__main__:Protocol Version: 2025-03-26 (Streamable HTTP)
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8080
```

### Health Check Response
```json
{
    "status": "healthy",
    "timestamp": "2025-08-29T18:37:45.662193",
    "netbox_url": "https://your-netbox-instance.com", 
    "netbox_configured": true,
    "transport": "streamable-http",
    "protocol_version": "2025-03-26",
    "mcp_endpoint": "/api/mcp"
}
```