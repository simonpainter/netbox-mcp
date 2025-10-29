# NetBox MCP Server

A small Model Context Protocol (MCP) server built with FastMCP that provides an interface to a NetBox instance.

This repository exposes NetBox resources (sites, site-groups, devices, etc.) as MCP tools and runs a streaming HTTP transport so clients can connect and receive streamed responses from the MCP server.

## Architecture (FastMCP + streaming HTTP)

- FastMCP: The MCP tool registry and runtime. Tools are defined in `app.py` and decorated with `@mcp.tool`.
- NetBoxClient: a tiny async helper in `app.py` that wraps `httpx.AsyncClient` to call the NetBox API.
- Streaming HTTP transport: the MCP server is started with `mcp.run(transport="http", ...)` which runs an HTTP server that supports a streaming/chunked response transport. This is useful for clients that want to consume events or long-running responses incrementally rather than waiting for the entire result.

Conceptually the flow is:

1. Client connects to the FastMCP streaming HTTP endpoint.
2. Client requests a tool (for example, `search_sites` or `get_site_group_details`).
3. FastMCP calls the associated Python function in `app.py`, which may in turn call NetBox via `NetBoxClient`.
4. The result is streamed back over the HTTP transport as it becomes available.

> Note: The low-level HTTP path/shape is provided by the FastMCP runtime. Clients that wish to connect should use a compatible MCP client or an HTTP client that supports reading chunked / streaming responses.

## Environment variables

Set these before running the server:

- `NETBOX_URL` - Base URL to your NetBox instance (default: `https://netbox.example.com`).
- `NETBOX_TOKEN` - NetBox API token with read permissions.
- `MCP_PORT` or `PORT` - Port for the FastMCP HTTP transport (defaults to `8000`).

Example (macOS / zsh):

```bash
export NETBOX_URL="https://netbox.example.com"
export NETBOX_TOKEN="0123456789abcdef0123456789abcdef01234567"
export MCP_PORT=8000
```

## Run the server

Start the MCP server with Python:

```bash
python3 app.py
```

The server will bind to 0.0.0.0 on the configured port and serve the FastMCP HTTP transport.

## Tools included

`app.py` registers MCP tools for NetBox resources. Examples included in this repository:

- `search_sites` — search of `dcim/sites/` (supports partial/case-insensitive name queries)
- `get_site_details` — site lookup
- `search_site_groups` — search of `dcim/site-groups/` (supports `name__ic`)
- `get_site_group_details` — single site-group lookup by `id`

You can add more tools following the repository conventions: each NetBox resource has a `search_<resource>` and `get_<resource>_details` tool.

## Verifying / testing

- Quick syntax check:

```bash
python3 -m py_compile app.py
```

- Start the server and use an HTTP client that supports streaming (for example, `curl --no-buffer` or a custom MCP client) to connect to the FastMCP HTTP transport and invoke tools.

Because the exact HTTP request shape (paths, headers and payload) is defined by the FastMCP runtime and clients, prefer using an existing MCP client library where available. If you're building a custom client, make sure it supports reading chunked responses so streamed results can be consumed incrementally.

## Contributing

If you add tools, follow the repo conventions documented in `.github/copilot-instructions.md`: each resource should have a `search_` and a `get_` tool with descriptive docstrings and consistent parameter mapping.

## License

This project is provided as-is.
