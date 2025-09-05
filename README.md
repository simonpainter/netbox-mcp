# NetBox MCP Server

A Model Context Protocol (MCP) server that provides Claude Desktop with direct access to your NetBox instance. Query devices, sites, IP addresses, and more using natural language.

## Architecture

```text
Claude Desktop → mcp-remote → Flask Server → NetBox API
```

- **Claude Desktop**: AI assistant with MCP support
- **mcp-remote**: Adapter for connecting to remote MCP servers
- **Flask Server**: Your centralised MCP server (this project)
- **NetBox API**: Your NetBox instance

## Prerequisites

- Python 3.8+
- NetBox instance with API access
- NetBox API token
- Claude Desktop
- Node.js (for mcp-remote)

## Installation

See [INSTALL.md](docs/INSTALL.md) for detailed installation instructions.

## Usage

Once configured, you can ask Claude natural language questions about your NetBox instance:

### Device Queries

- "What devices do you see in NetBox?"
- "Search for devices at the Skipton site"
- "Show me all Cisco devices"
- "Find devices with 'router' in the name"

## Available Tools

See [TOOLS.md](docs/TOOLS.md) for a comprehensive reference of all available MCP tools and their parameters.
See [PROMPTS.md](docs/PROMPTS.md) for a reference of supported prompts.
