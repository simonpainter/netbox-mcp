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
- `MCP_PORT` - Port for the FastMCP HTTP transport. Defaults to `8000` if not set. If the value is not a valid integer, the server will exit with an error.

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

`app.py` registers **118 MCP tools** for NetBox resources organized across three main API categories:

- **Circuits** (22 tools) - Circuit management, providers, terminations, and virtual circuits
- **DCIM** (86 tools) - Data center infrastructure: sites, devices, racks, cables, interfaces, and more
- **Tenancy** (10 tools) - Tenant and contact management

### Tool naming convention

Each NetBox resource is represented by two tools:

- `search_<resource>(args)` — Query the collection endpoint with optional filters (returns a list)
- `get_<resource>_details(args)` — Fetch a single object by ID (returns `[object]` or `[]`)

### Circuits Tools (22 tools)

Tools for managing circuits, providers, and circuit-related resources:

- **Circuits**: `search_circuits`, `get_circuit_details`
- **Circuit Groups**: `search_circuit_groups`, `get_circuit_group_details`
- **Circuit Group Assignments**: `search_circuit_group_assignments`, `get_circuit_group_assignment_details`
- **Circuit Terminations**: `search_circuit_terminations`, `get_circuit_termination_details`
- **Circuit Types**: `search_circuit_types`, `get_circuit_type_details`
- **Providers**: `search_providers`, `get_provider_details`
- **Provider Accounts**: `search_provider_accounts`, `get_provider_account_details`
- **Provider Networks**: `search_provider_networks`, `get_provider_network_details`
- **Virtual Circuits**: `search_virtual_circuits`, `get_virtual_circuit_details`
- **Virtual Circuit Terminations**: `search_virtual_circuit_terminations`, `get_virtual_circuit_termination_details`
- **Virtual Circuit Types**: `search_virtual_circuit_types`, `get_virtual_circuit_type_details`

### DCIM Tools (86 tools)

Tools for data center infrastructure management:

**Sites and Locations**
- **Sites**: `search_sites`, `get_site_details`
- **Site Groups**: `search_site_groups`, `get_site_group_details`
- **Locations**: `search_locations`, `get_location_details`
- **Regions**: `search_regions`, `get_region_details`

**Devices and Equipment**
- **Devices**: `search_devices`, `get_device_details`
- **Device Bays**: `search_device_bays`, `get_device_bay_details`
- **Device Bay Templates**: `search_device_bay_templates`, `get_device_bay_template_details`
- **Device Roles**: `search_device_roles`, `get_device_role_details`
- **Device Types**: `search_device_types`, `get_device_type_details`
- **Manufacturers**: `search_manufacturers`, `get_manufacturer_details`
- **Platforms**: `search_platforms`, `get_platform_details`
- **Virtual Chassis**: `search_virtual_chassis`, `get_virtual_chassis_details`
- **Virtual Device Contexts**: `search_virtual_device_contexts`, `get_virtual_device_context_details`

**Racks and Cabinets**
- **Racks**: `search_racks`, `get_rack_details`
- **Rack Reservations**: `search_rack_reservations`, `get_rack_reservation_details`
- **Rack Roles**: `search_rack_roles`, `get_rack_role_details`
- **Rack Types**: `search_rack_types`, `get_rack_type_details`

**Network Interfaces and Ports**
- **Interfaces**: `search_interfaces`, `get_interface_details`
- **Interface Templates**: `search_interface_templates`, `get_interface_template_details`
- **Console Ports**: `search_console_ports`, `get_console_port_details`
- **Console Port Templates**: `search_console_port_templates`, `get_console_port_template_details`
- **Console Server Ports**: `search_console_server_ports`, `get_console_server_port_details`
- **Console Server Port Templates**: `search_console_server_port_templates`, `get_console_server_port_template_details`
- **Front Ports**: `search_front_ports`, `get_front_port_details`
- **Front Port Templates**: `search_front_port_templates`, `get_front_port_template_details`
- **Rear Ports**: `search_rear_ports`, `get_rear_port_details`
- **Rear Port Templates**: `search_rear_port_templates`, `get_rear_port_template_details`
- **MAC Addresses**: `search_mac_addresses`, `get_mac_address_details`

**Power Management**
- **Power Feeds**: `search_power_feeds`, `get_power_feed_details`
- **Power Outlets**: `search_power_outlets`, `get_power_outlet_details`
- **Power Outlet Templates**: `search_power_outlet_templates`, `get_power_outlet_template_details`
- **Power Panels**: `search_power_panels`, `get_power_panel_details`
- **Power Ports**: `search_power_ports`, `get_power_port_details`
- **Power Port Templates**: `search_power_port_templates`, `get_power_port_template_details`

**Cables and Connectivity**
- **Cables**: `search_cables`, `get_cable_details`

**Inventory and Modules**
- **Inventory Items**: `search_inventory_items`, `get_inventory_item_details`
- **Inventory Item Roles**: `search_inventory_item_roles`, `get_inventory_item_role_details`
- **Inventory Item Templates**: `search_inventory_item_templates`, `get_inventory_item_template_details`
- **Modules**: `search_modules`, `get_module_details`
- **Module Bays**: `search_module_bays`, `get_module_bay_details`
- **Module Bay Templates**: `search_module_bay_templates`, `get_module_bay_template_details`
- **Module Types**: `search_module_types`, `get_module_type_details`
- **Module Type Profiles**: `search_module_type_profiles`, `get_module_type_profile_details`

### Tenancy Tools (10 tools)

Tools for tenant and contact management:

- **Tenants**: `search_tenants`, `get_tenant_details`
- **Tenant Groups**: `search_tenant_groups`, `get_tenant_group_details`
- **Contacts**: `search_contacts`, `get_contact_details`
- **Contact Groups**: `search_contact_groups`, `get_contact_group_details`
- **Contact Roles**: `search_contact_roles`, `get_contact_role_details`

### Common parameters

**Search tools** typically accept:
- `limit` — Maximum number of results (default varies by endpoint, typically 10)
- `name` — Name filter (usually case-insensitive contains match)
- `status` — Status filter (exact match, e.g., 'active', 'planned', 'offline')
- Resource-specific filters (e.g., `site`, `rack`, `device`, `role`, `type`)

**Get tools** require:
- `id` — Numeric ID of the resource to fetch

### Example usage

```python
# Search for sites with "dc" in the name
sites = await search_sites({"name": "dc", "limit": 20})

# Get details for a specific site
site = await get_site_details({"id": 42})

# Search for active devices at a specific site
devices = await search_devices({"site": 5, "status": "active", "limit": 50})

# Find circuits by provider
circuits = await search_circuits({"provider": "Level3", "limit": 100})
```

### Adding new tools

Follow the repository conventions documented in `.github/copilot-instructions.md`: each resource should have a `search_` and a `get_` tool with descriptive docstrings and consistent parameter mapping.

## Verifying / testing

- Quick syntax check:

```bash
python3 -m py_compile app.py
```

- Start the server and use an HTTP client that supports streaming (for example, `curl --no-buffer` or a custom MCP client) to connect to the FastMCP HTTP transport and invoke tools.

Because the exact HTTP request shape (paths, headers and payload) is defined by the FastMCP runtime and clients, prefer using an existing MCP client library where available. If you're building a custom client, make sure it supports reading chunked responses so streamed results can be consumed incrementally.

## Contributing

This repository includes 118 tools covering the most commonly used NetBox resources. To add new tools:

1. Follow the repo conventions documented in `.github/copilot-instructions.md`
2. Each resource should have a `search_` and a `get_` tool with descriptive docstrings
3. Use consistent parameter mapping (e.g., `name__ic` for case-insensitive name searches)
4. Place tools in the appropriate API category section (circuits, dcim, or tenancy)
5. Include clear documentation of accepted parameters in the tool's docstring

## License

This project is provided as-is.
