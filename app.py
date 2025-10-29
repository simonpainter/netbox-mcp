from fastmcp import FastMCP
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin
import httpx


# Configuration for NetBox API client

NETBOX_URL = os.getenv("NETBOX_URL", "https://netbox.example.com")
NETBOX_TOKEN = os.getenv("NETBOX_TOKEN", "")

class NetBoxClient:
    """Async NetBox API client"""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request to NetBox API"""
        url = urljoin(f"{self.base_url}/api/", endpoint.lstrip('/'))
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                # Handle all errors (connection, timeout, etc.)
                raise Exception(f"NetBox API error: {e}") from e
            

# Small reusable helpers to reduce repetition across tools

def _build_params(args: Dict[str, Any], mappings: Dict[str, str], default_limit: int = 10) -> Dict[str, Any]:
    """Build query params for NetBox from incoming args using a mapping.

    mappings: dict of incoming arg name -> NetBox query param name
    """
    params: Dict[str, Any] = {"limit": args.get("limit", default_limit)}
    for incoming_name, query_name in mappings.items():
        if incoming_name in args:
            params[query_name] = args[incoming_name]
    return params


async def _search(endpoint: str, args: Dict[str, Any], mappings: Dict[str, str], default_limit: int = 10) -> List[Dict[str, Any]]:
    params = _build_params(args, mappings, default_limit)
    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    result = await netbox_client.get(endpoint, params)
    return result.get("results", [])


async def _get_detail(endpoint_base: str, id_value: Any) -> List[Dict[str, Any]]:
    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    try:
        result = await netbox_client.get(f"{endpoint_base}{id_value}/")
        return [result] if isinstance(result, dict) else []
    except Exception:
        return []


mcp = FastMCP("NetBox Streaming MCP Server")

# Tool definitions

# --- circuits (circuits, circuit groups, providers, etc.) ---

# circuits

# circuits/circuits

@mcp.tool
async def search_circuits(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search circuits (circuits/circuits/).
    Accepts: provider, circuit_id, circuit_type, status, limit
        provider: Provider ID or name (case-insensitive contains match for name)
        circuit_id: Circuit ID (case-insensitive contains match)
        circuit_type: Circuit Type ID or name
        status: Status of the circuit (exact match), e.g., 'active', 'planned', 'decommissioning'
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox circuit objects (the `results` list) or an empty list.
    """
    mappings = {
        "provider": "provider",
        "circuit_id": "cid__ic",
        "circuit_type": "type",
        "status": "status"
    }
    return await _search("circuits/circuits/", args, mappings)


@mcp.tool
async def get_circuit_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get circuit by ID (circuits/circuits/{id}/).
    Accepts: id (required)
        id: Numeric ID of the circuit to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("circuits/circuits/", args["id"])


# circuits/circuit-groups

@mcp.tool
async def search_circuit_groups(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search circuit groups (circuits/circuit-groups/).
    Accepts: name, limit
        name: Name of the circuit group (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox circuit group objects (the `results` list) or an empty list.
    """
    mappings = {"name": "name__ic"}
    return await _search("circuits/circuit-groups/", args, mappings)


@mcp.tool
async def get_circuit_group_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get circuit group by ID (circuits/circuit-groups/{id}/).
    Accepts: id (required)
        id: Numeric ID of the circuit group to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("circuits/circuit-groups/", args["id"])


# circuits/circuit-group-assignments

@mcp.tool
async def search_circuit_group_assignments(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search circuit group assignments (circuits/circuit-group-assignments/).
    Accepts: priority, group, limit
        priority: Priority value (exact match)
        group: Circuit group ID (numeric)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox circuit group assignment objects (the `results` list) or an empty list.
    """
    mappings = {
        "priority": "priority",
        "group": "group_id"
    }
    return await _search("circuits/circuit-group-assignments/", args, mappings)


@mcp.tool
async def get_circuit_group_assignment_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get circuit group assignment by ID (circuits/circuit-group-assignments/{id}/).
    Accepts: id (required)
        id: Numeric ID of the circuit group assignment to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("circuits/circuit-group-assignments/", args["id"])


# circuits/circuit-terminations

@mcp.tool
async def search_circuit_terminations(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search circuit terminations (circuits/circuit-terminations/).
    Accepts: circuit, termination, limit
        circuit: Circuit ID (numeric)
        termination: Termination side, typically 'A' or 'Z'
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox circuit termination objects (the `results` list) or an empty list.
    """
    mappings = {
        "circuit": "circuit_id",
        "termination": "term_side"
    }
    return await _search("circuits/circuit-terminations/", args, mappings)


@mcp.tool
async def get_circuit_termination_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get circuit termination by ID (circuits/circuit-terminations/{id}/).
    Accepts: id (required)
        id: Numeric ID of the circuit termination to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("circuits/circuit-terminations/", args["id"])


# circuits/circuit-types

@mcp.tool
async def search_circuit_types(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search circuit types (circuits/circuit-types/).
    Accepts: name, limit
        name: Name of the circuit type (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox circuit type objects (the `results` list) or an empty list.
    """
    mappings = {"name": "name__ic"}
    return await _search("circuits/circuit-types/", args, mappings)


@mcp.tool
async def get_circuit_type_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get circuit type by ID (circuits/circuit-types/{id}/).
    Accepts: id (required)
        id: Numeric ID of the circuit type to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("circuits/circuit-types/", args["id"])


# circuits/providers

@mcp.tool
async def search_providers(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search providers (circuits/providers/).
    Accepts: name, limit
        name: Name of the provider (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox provider objects (the `results` list) or an empty list.
    """
    mappings = {"name": "name__ic"}
    return await _search("circuits/providers/", args, mappings)


@mcp.tool
async def get_provider_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get provider by ID (circuits/providers/{id}/).
    Accepts: id (required)
        id: Numeric ID of the provider to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("circuits/providers/", args["id"])


# circuits/provider-accounts

@mcp.tool
async def search_provider_accounts(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search provider accounts (circuits/provider-accounts/).
    Accepts: name, account_number, limit
        name: Name of the provider account (case-insensitive contains match)
        account_number: Account number (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox provider account objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "account_number": "account__ic"
    }
    return await _search("circuits/provider-accounts/", args, mappings)


@mcp.tool
async def get_provider_account_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get provider account by ID (circuits/provider-accounts/{id}/).
    Accepts: id (required)
        id: Numeric ID of the provider account to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("circuits/provider-accounts/", args["id"])


# circuits/provider-networks

@mcp.tool
async def search_provider_networks(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search provider networks (circuits/provider-networks/).
    Accepts: name, limit
        name: Name of the provider network (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox provider network objects (the `results` list) or an empty list.
    """
    mappings = {"name": "name__ic"}
    return await _search("circuits/provider-networks/", args, mappings)


@mcp.tool
async def get_provider_network_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get provider network by ID (circuits/provider-networks/{id}/).
    Accepts: id (required)
        id: Numeric ID of the provider network to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("circuits/provider-networks/", args["id"])


# circuits/virtual-circuits

@mcp.tool
async def search_virtual_circuits(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search virtual circuits (circuits/virtual-circuits/).
    Accepts: provider_network, provider_account, circuit_id, status, limit
        provider_network: Provider network ID (numeric)
        provider_account: Provider account ID (numeric)
        circuit_id: Virtual circuit ID (case-insensitive contains match)
        status: Status of the virtual circuit (exact match), e.g., 'active', 'planned', 'offline'
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox virtual circuit objects (the `results` list) or an empty list.
    """
    mappings = {
        "provider_network": "provider_network_id",
        "provider_account": "provider_account_id",
        "circuit_id": "cid__ic",
        "status": "status"
    }
    return await _search("circuits/virtual-circuits/", args, mappings)


@mcp.tool
async def get_virtual_circuit_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get virtual circuit by ID (circuits/virtual-circuits/{id}/).
    Accepts: id (required)
        id: Numeric ID of the virtual circuit to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("circuits/virtual-circuits/", args["id"])


# circuits/virtual-circuit-terminations

@mcp.tool
async def search_virtual_circuit_terminations(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search virtual circuit terminations (circuits/virtual-circuit-terminations/).
    Accepts: virtual_circuit, interface, limit
        virtual_circuit: Virtual circuit ID (numeric)
        interface: Interface ID (numeric)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox virtual circuit termination objects (the `results` list) or an empty list.
    """
    mappings = {
        "virtual_circuit": "virtual_circuit_id",
        "interface": "interface_id"
    }
    return await _search("circuits/virtual-circuit-terminations/", args, mappings)


@mcp.tool
async def get_virtual_circuit_termination_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get virtual circuit termination by ID (circuits/virtual-circuit-terminations/{id}/).
    Accepts: id (required)
        id: Numeric ID of the virtual circuit termination to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("circuits/virtual-circuit-terminations/", args["id"])


# circuits/virtual-circuit-types

@mcp.tool
async def search_virtual_circuit_types(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search virtual circuit types (circuits/virtual-circuit-types/).
    Accepts: name, limit
        name: Name of the virtual circuit type (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox virtual circuit type objects (the `results` list) or an empty list.
    """
    mappings = {"name": "name__ic"}
    return await _search("circuits/virtual-circuit-types/", args, mappings)


@mcp.tool
async def get_virtual_circuit_type_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get virtual circuit type by ID (circuits/virtual-circuit-types/{id}/).
    Accepts: id (required)
        id: Numeric ID of the virtual circuit type to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("circuits/virtual-circuit-types/", args["id"])


# --- dcim (sites, site-groups, devices, etc.) ---

# dcim

# dcim/sites

@mcp.tool
async def search_sites(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search sites (dcim/sites/).
    Accepts: name, status, location, region, limit
        name: Name of the site (case-insensitive search contains)
        status: Status of the site (exact match), e.g., 'active', 'planned', 'retired'
        location: Location name (case-insensitive search contains)
        region: Name of the region (case-insensitive search contains)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox site objects (the `results` list) or an empty list.
    """
    mappings = {"name": "name__ic", "status": "status", "location": "location__ic", "region": "region__ic"}
    return await _search("dcim/sites/", args, mappings)

@mcp.tool
async def get_site_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get site by ID (dcim/sites/).
    Accepts: id
        id: ID of the site - can be obtained from search_sites
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/sites/", args["id"])


@mcp.tool
async def search_site_groups(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search site groups (dcim/site-groups/).
    Accepts: name, limit
        name: Name of the site group (case-insensitive contains match)
        limit: maximum number of results to return (default 10)

    Returns a list of NetBox site group objects (the `results` list) or an empty list.
    """
    mappings = {"name": "name__ic"}
    return await _search("dcim/site-groups/", args, mappings)


@mcp.tool
async def get_site_group_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get site group details by ID (dcim/site-groups/{id}/).
    Accepts: id (required)
        id: Numeric ID of the site group to fetch. When provided, the tool will call
            the single-object endpoint and return a single-element list `[obj]` or `[]` if
            not found.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/site-groups/", args["id"])


# dcim/cables

@mcp.tool
async def search_cables(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search cables (dcim/cables/).
    Accepts: status, type, label, device, location, limit
        status: Status of the cable (exact match), e.g., 'connected', 'planned', 'decommissioning'
        type: Cable type (case-insensitive contains match), e.g., 'cat5e', 'cat6', 'fiber'
        label: Cable label (case-insensitive contains match)
        device: Device ID (numeric)
        location: Location ID (numeric)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox cable objects (the `results` list) or an empty list.
    """
    mappings = {
        "status": "status",
        "type": "type__ic",
        "label": "label__ic",
        "device": "device_id",
        "location": "location_id"
    }
    return await _search("dcim/cables/", args, mappings)


@mcp.tool
async def get_cable_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get cable by ID (dcim/cables/{id}/).
    Accepts: id (required)
        id: Numeric ID of the cable to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/cables/", args["id"])


# dcim/console-ports

@mcp.tool
async def search_console_ports(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search console ports (dcim/console-ports/).
    Accepts: name, device, type, label, limit
        name: Name of the console port (case-insensitive contains match)
        device: Device ID (numeric)
        type: Console port type (case-insensitive contains match)
        label: Console port label (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox console port objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "device": "device_id",
        "type": "type__ic",
        "label": "label__ic"
    }
    return await _search("dcim/console-ports/", args, mappings)


@mcp.tool
async def get_console_port_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get console port by ID (dcim/console-ports/{id}/).
    Accepts: id (required)
        id: Numeric ID of the console port to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/console-ports/", args["id"])


# dcim/console-port-templates

@mcp.tool
async def search_console_port_templates(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search console port templates (dcim/console-port-templates/).
    Accepts: name, device_type, type, label, limit
        name: Name of the console port template (case-insensitive contains match)
        device_type: Device type ID (numeric)
        type: Console port type (case-insensitive contains match)
        label: Console port template label (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox console port template objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "device_type": "device_type_id",
        "type": "type__ic",
        "label": "label__ic"
    }
    return await _search("dcim/console-port-templates/", args, mappings)


@mcp.tool
async def get_console_port_template_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get console port template by ID (dcim/console-port-templates/{id}/).
    Accepts: id (required)
        id: Numeric ID of the console port template to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/console-port-templates/", args["id"])


# dcim/console-server-ports

@mcp.tool
async def search_console_server_ports(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search console server ports (dcim/console-server-ports/).
    Accepts: name, device, type, label, limit
        name: Name of the console server port (case-insensitive contains match)
        device: Device ID (numeric)
        type: Console server port type (case-insensitive contains match)
        label: Console server port label (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox console server port objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "device": "device_id",
        "type": "type__ic",
        "label": "label__ic"
    }
    return await _search("dcim/console-server-ports/", args, mappings)


@mcp.tool
async def get_console_server_port_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get console server port by ID (dcim/console-server-ports/{id}/).
    Accepts: id (required)
        id: Numeric ID of the console server port to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/console-server-ports/", args["id"])


# dcim/console-server-port-templates

@mcp.tool
async def search_console_server_port_templates(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search console server port templates (dcim/console-server-port-templates/).
    Accepts: name, device_type, type, label, limit
        name: Name of the console server port template (case-insensitive contains match)
        device_type: Device type ID (numeric)
        type: Console server port type (case-insensitive contains match)
        label: Console server port template label (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox console server port template objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "device_type": "device_type_id",
        "type": "type__ic",
        "label": "label__ic"
    }
    return await _search("dcim/console-server-port-templates/", args, mappings)


@mcp.tool
async def get_console_server_port_template_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get console server port template by ID (dcim/console-server-port-templates/{id}/).
    Accepts: id (required)
        id: Numeric ID of the console server port template to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/console-server-port-templates/", args["id"])


# dcim/devices

@mcp.tool
async def search_devices(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search devices (dcim/devices/).
    Accepts: name, role, device_type, serial, asset_tag, rack, status, location, limit
        name: Name of the device (case-insensitive contains match)
        role: Device role ID or slug (NetBox API accepts numeric ID or slug)
        device_type: Device type ID or slug (NetBox API accepts numeric ID or slug)
        serial: Serial number (case-insensitive contains match)
        asset_tag: Asset tag (case-insensitive contains match)
        rack: Rack ID (numeric ID)
        status: Status of the device (exact match), e.g., 'active', 'planned', 'offline'
        location: Location ID (numeric)
        limit: maximum number of results to return (default 10)

    Returns a list of NetBox device objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "role": "role",
        "device_type": "device_type",
        "serial": "serial__ic",
        "asset_tag": "asset_tag__ic",
        "rack": "rack_id",
        "status": "status",
        "location": "location_id"
    }
    return await _search("dcim/devices/", args, mappings)


@mcp.tool
async def get_device_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get device details by ID (dcim/devices/{id}/).
    Accepts: id (required)
        id: Numeric ID of the device to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/devices/", args["id"])


# dcim/device-bays

@mcp.tool
async def search_device_bays(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search device bays (dcim/device-bays/).
    Accepts: name, device, label, limit
        name: Name of the device bay (case-insensitive contains match)
        device: Device ID (numeric)
        label: Device bay label (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox device bay objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "device": "device_id",
        "label": "label__ic"
    }
    return await _search("dcim/device-bays/", args, mappings)


@mcp.tool
async def get_device_bay_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get device bay by ID (dcim/device-bays/{id}/).
    Accepts: id (required)
        id: Numeric ID of the device bay to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/device-bays/", args["id"])


# dcim/device-bay-templates

@mcp.tool
async def search_device_bay_templates(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search device bay templates (dcim/device-bay-templates/).
    Accepts: name, device_type, label, limit
        name: Name of the device bay template (case-insensitive contains match)
        device_type: Device type ID (numeric)
        label: Device bay template label (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox device bay template objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "device_type": "device_type_id",
        "label": "label__ic"
    }
    return await _search("dcim/device-bay-templates/", args, mappings)


@mcp.tool
async def get_device_bay_template_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get device bay template by ID (dcim/device-bay-templates/{id}/).
    Accepts: id (required)
        id: Numeric ID of the device bay template to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/device-bay-templates/", args["id"])


# dcim/device-roles

@mcp.tool
async def search_device_roles(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search device roles (dcim/device-roles/).
    Accepts: name, limit
        name: Name of the device role (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox device role objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic"
    }
    return await _search("dcim/device-roles/", args, mappings)


@mcp.tool
async def get_device_role_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get device role by ID (dcim/device-roles/{id}/).
    Accepts: id (required)
        id: Numeric ID of the device role to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/device-roles/", args["id"])


# dcim/device-types

@mcp.tool
async def search_device_types(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search device types (dcim/device-types/).
    Accepts: name, manufacturer, limit
        name: Name of the device type (case-insensitive contains match)
        manufacturer: Manufacturer ID (numeric)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox device type objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "manufacturer": "manufacturer_id"
    }
    return await _search("dcim/device-types/", args, mappings)


@mcp.tool
async def get_device_type_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get device type by ID (dcim/device-types/{id}/).
    Accepts: id (required)
        id: Numeric ID of the device type to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/device-types/", args["id"])


# dcim/front-ports

@mcp.tool
async def search_front_ports(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search front ports (dcim/front-ports/).
    Accepts: name, device, type, label, limit
        name: Name of the front port (case-insensitive contains match)
        device: Device ID (numeric)
        type: Front port type (case-insensitive contains match)
        label: Front port label (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox front port objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "device": "device_id",
        "type": "type__ic",
        "label": "label__ic"
    }
    return await _search("dcim/front-ports/", args, mappings)


@mcp.tool
async def get_front_port_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get front port by ID (dcim/front-ports/{id}/).
    Accepts: id (required)
        id: Numeric ID of the front port to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/front-ports/", args["id"])


# dcim/front-port-templates

@mcp.tool
async def search_front_port_templates(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search front port templates (dcim/front-port-templates/).
    Accepts: name, device_type, type, label, limit
        name: Name of the front port template (case-insensitive contains match)
        device_type: Device type ID (numeric)
        type: Front port type (case-insensitive contains match)
        label: Front port template label (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox front port template objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "device_type": "device_type_id",
        "type": "type__ic",
        "label": "label__ic"
    }
    return await _search("dcim/front-port-templates/", args, mappings)


@mcp.tool
async def get_front_port_template_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get front port template by ID (dcim/front-port-templates/{id}/).
    Accepts: id (required)
        id: Numeric ID of the front port template to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/front-port-templates/", args["id"])


# dcim/interfaces

@mcp.tool
async def search_interfaces(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search interfaces (dcim/interfaces/).
    Accepts: name, device, type, label, limit
        name: Name of the interface (case-insensitive contains match)
        device: Device ID (numeric)
        type: Interface type (case-insensitive contains match)
        label: Interface label (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox interface objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "device": "device_id",
        "type": "type__ic",
        "label": "label__ic"
    }
    return await _search("dcim/interfaces/", args, mappings)


@mcp.tool
async def get_interface_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get interface by ID (dcim/interfaces/{id}/).
    Accepts: id (required)
        id: Numeric ID of the interface to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/interfaces/", args["id"])


# dcim/interface-templates

@mcp.tool
async def search_interface_templates(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search interface templates (dcim/interface-templates/).
    Accepts: name, device_type, type, label, limit
        name: Name of the interface template (case-insensitive contains match)
        device_type: Device type ID (numeric)
        type: Interface type (case-insensitive contains match)
        label: Interface template label (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox interface template objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "device_type": "device_type_id",
        "type": "type__ic",
        "label": "label__ic"
    }
    return await _search("dcim/interface-templates/", args, mappings)


@mcp.tool
async def get_interface_template_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get interface template by ID (dcim/interface-templates/{id}/).
    Accepts: id (required)
        id: Numeric ID of the interface template to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/interface-templates/", args["id"])


# dcim/inventory-items

@mcp.tool
async def search_inventory_items(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search inventory items (dcim/inventory-items/).
    Accepts: name, device, label, limit
        name: Name of the inventory item (case-insensitive contains match)
        device: Device ID (numeric)
        label: Inventory item label (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox inventory item objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "device": "device_id",
        "label": "label__ic"
    }
    return await _search("dcim/inventory-items/", args, mappings)


@mcp.tool
async def get_inventory_item_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get inventory item by ID (dcim/inventory-items/{id}/).
    Accepts: id (required)
        id: Numeric ID of the inventory item to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/inventory-items/", args["id"])


# dcim/inventory-item-roles

@mcp.tool
async def search_inventory_item_roles(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search inventory item roles (dcim/inventory-item-roles/).
    Accepts: name, limit
        name: Name of the inventory item role (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox inventory item role objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic"
    }
    return await _search("dcim/inventory-item-roles/", args, mappings)


@mcp.tool
async def get_inventory_item_role_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get inventory item role by ID (dcim/inventory-item-roles/{id}/).
    Accepts: id (required)
        id: Numeric ID of the inventory item role to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/inventory-item-roles/", args["id"])


# dcim/inventory-item-templates

@mcp.tool
async def search_inventory_item_templates(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search inventory item templates (dcim/inventory-item-templates/).
    Accepts: name, device_type, label, limit
        name: Name of the inventory item template (case-insensitive contains match)
        device_type: Device type ID (numeric)
        label: Inventory item template label (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox inventory item template objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "device_type": "device_type_id",
        "label": "label__ic"
    }
    return await _search("dcim/inventory-item-templates/", args, mappings)


@mcp.tool
async def get_inventory_item_template_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get inventory item template by ID (dcim/inventory-item-templates/{id}/).
    Accepts: id (required)
        id: Numeric ID of the inventory item template to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/inventory-item-templates/", args["id"])


# dcim/locations

@mcp.tool
async def search_locations(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search locations (dcim/locations/).
    Accepts: name, status, limit
        name: Name of the location (case-insensitive contains match)
        status: Status of the location (exact match), e.g., 'active', 'planned', 'retired'
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox location objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "status": "status"
    }
    return await _search("dcim/locations/", args, mappings)


@mcp.tool
async def get_location_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get location by ID (dcim/locations/{id}/).
    Accepts: id (required)
        id: Numeric ID of the location to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/locations/", args["id"])


# dcim/mac-addresses

@mcp.tool
async def search_mac_addresses(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search MAC addresses (dcim/mac-addresses/).
    Accepts: mac_address, device, limit
        mac_address: MAC address (case-insensitive contains match)
        device: Device ID (numeric)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox MAC address objects (the `results` list) or an empty list.
    """
    mappings = {
        "mac_address": "mac_address__ic",
        "device": "device_id"
    }
    return await _search("dcim/mac-addresses/", args, mappings)


@mcp.tool
async def get_mac_address_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get MAC address by ID (dcim/mac-addresses/{id}/).
    Accepts: id (required)
        id: Numeric ID of the MAC address to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/mac-addresses/", args["id"])


# dcim/manufacturers

@mcp.tool
async def search_manufacturers(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search manufacturers (dcim/manufacturers/).
    Accepts: name, limit
        name: Name of the manufacturer (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox manufacturer objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic"
    }
    return await _search("dcim/manufacturers/", args, mappings)


@mcp.tool
async def get_manufacturer_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get manufacturer by ID (dcim/manufacturers/{id}/).
    Accepts: id (required)
        id: Numeric ID of the manufacturer to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/manufacturers/", args["id"])


# dcim/modules

@mcp.tool
async def search_modules(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search modules (dcim/modules/).
    Accepts: device, status, limit
        device: Device ID (numeric)
        status: Status of the module (exact match), e.g., 'active', 'planned', 'offline'
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox module objects (the `results` list) or an empty list.
    """
    mappings = {
        "device": "device_id",
        "status": "status"
    }
    return await _search("dcim/modules/", args, mappings)


@mcp.tool
async def get_module_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get module by ID (dcim/modules/{id}/).
    Accepts: id (required)
        id: Numeric ID of the module to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/modules/", args["id"])


# dcim/module-bays

@mcp.tool
async def search_module_bays(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search module bays (dcim/module-bays/).
    Accepts: name, device, label, limit
        name: Name of the module bay (case-insensitive contains match)
        device: Device ID (numeric)
        label: Module bay label (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox module bay objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "device": "device_id",
        "label": "label__ic"
    }
    return await _search("dcim/module-bays/", args, mappings)


@mcp.tool
async def get_module_bay_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get module bay by ID (dcim/module-bays/{id}/).
    Accepts: id (required)
        id: Numeric ID of the module bay to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/module-bays/", args["id"])


# dcim/module-bay-templates

@mcp.tool
async def search_module_bay_templates(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search module bay templates (dcim/module-bay-templates/).
    Accepts: name, device_type, label, limit
        name: Name of the module bay template (case-insensitive contains match)
        device_type: Device type ID (numeric)
        label: Module bay template label (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox module bay template objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "device_type": "device_type_id",
        "label": "label__ic"
    }
    return await _search("dcim/module-bay-templates/", args, mappings)


@mcp.tool
async def get_module_bay_template_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get module bay template by ID (dcim/module-bay-templates/{id}/).
    Accepts: id (required)
        id: Numeric ID of the module bay template to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/module-bay-templates/", args["id"])


# dcim/module-types

@mcp.tool
async def search_module_types(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search module types (dcim/module-types/).
    Accepts: name, manufacturer, limit
        name: Name of the module type (case-insensitive contains match)
        manufacturer: Manufacturer ID (numeric)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox module type objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "manufacturer": "manufacturer_id"
    }
    return await _search("dcim/module-types/", args, mappings)


@mcp.tool
async def get_module_type_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get module type by ID (dcim/module-types/{id}/).
    Accepts: id (required)
        id: Numeric ID of the module type to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/module-types/", args["id"])


# dcim/module-type-profiles

@mcp.tool
async def search_module_type_profiles(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search module type profiles (dcim/module-type-profiles/).
    Accepts: name, limit
        name: Name of the module type profile (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox module type profile objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic"
    }
    return await _search("dcim/module-type-profiles/", args, mappings)


@mcp.tool
async def get_module_type_profile_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get module type profile by ID (dcim/module-type-profiles/{id}/).
    Accepts: id (required)
        id: Numeric ID of the module type profile to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/module-type-profiles/", args["id"])


# dcim/platforms

@mcp.tool
async def search_platforms(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search platforms (dcim/platforms/).
    Accepts: name, manufacturer, limit
        name: Name of the platform (case-insensitive contains match)
        manufacturer: Manufacturer ID (numeric)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox platform objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "manufacturer": "manufacturer_id"
    }
    return await _search("dcim/platforms/", args, mappings)


@mcp.tool
async def get_platform_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get platform by ID (dcim/platforms/{id}/).
    Accepts: id (required)
        id: Numeric ID of the platform to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/platforms/", args["id"])


# dcim/power-feeds

@mcp.tool
async def search_power_feeds(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search power feeds (dcim/power-feeds/).
    Accepts: name, status, type, limit
        name: Name of the power feed (case-insensitive contains match)
        status: Status of the power feed (exact match), e.g., 'active', 'planned', 'offline'
        type: Power feed type (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox power feed objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "status": "status",
        "type": "type__ic"
    }
    return await _search("dcim/power-feeds/", args, mappings)


@mcp.tool
async def get_power_feed_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get power feed by ID (dcim/power-feeds/{id}/).
    Accepts: id (required)
        id: Numeric ID of the power feed to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/power-feeds/", args["id"])


# dcim/power-outlets

@mcp.tool
async def search_power_outlets(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search power outlets (dcim/power-outlets/).
    Accepts: name, device, type, label, limit
        name: Name of the power outlet (case-insensitive contains match)
        device: Device ID (numeric)
        type: Power outlet type (case-insensitive contains match)
        label: Power outlet label (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox power outlet objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "device": "device_id",
        "type": "type__ic",
        "label": "label__ic"
    }
    return await _search("dcim/power-outlets/", args, mappings)


@mcp.tool
async def get_power_outlet_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get power outlet by ID (dcim/power-outlets/{id}/).
    Accepts: id (required)
        id: Numeric ID of the power outlet to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/power-outlets/", args["id"])


# dcim/power-outlet-templates

@mcp.tool
async def search_power_outlet_templates(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search power outlet templates (dcim/power-outlet-templates/).
    Accepts: name, device_type, type, label, limit
        name: Name of the power outlet template (case-insensitive contains match)
        device_type: Device type ID (numeric)
        type: Power outlet type (case-insensitive contains match)
        label: Power outlet template label (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox power outlet template objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "device_type": "device_type_id",
        "type": "type__ic",
        "label": "label__ic"
    }
    return await _search("dcim/power-outlet-templates/", args, mappings)


@mcp.tool
async def get_power_outlet_template_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get power outlet template by ID (dcim/power-outlet-templates/{id}/).
    Accepts: id (required)
        id: Numeric ID of the power outlet template to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/power-outlet-templates/", args["id"])


# dcim/power-panels

@mcp.tool
async def search_power_panels(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search power panels (dcim/power-panels/).
    Accepts: name, location, limit
        name: Name of the power panel (case-insensitive contains match)
        location: Location ID (numeric)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox power panel objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "location": "location_id"
    }
    return await _search("dcim/power-panels/", args, mappings)


@mcp.tool
async def get_power_panel_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get power panel by ID (dcim/power-panels/{id}/).
    Accepts: id (required)
        id: Numeric ID of the power panel to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/power-panels/", args["id"])


# dcim/power-ports

@mcp.tool
async def search_power_ports(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search power ports (dcim/power-ports/).
    Accepts: name, device, type, label, limit
        name: Name of the power port (case-insensitive contains match)
        device: Device ID (numeric)
        type: Power port type (case-insensitive contains match)
        label: Power port label (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox power port objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "device": "device_id",
        "type": "type__ic",
        "label": "label__ic"
    }
    return await _search("dcim/power-ports/", args, mappings)


@mcp.tool
async def get_power_port_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get power port by ID (dcim/power-ports/{id}/).
    Accepts: id (required)
        id: Numeric ID of the power port to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/power-ports/", args["id"])


# dcim/power-port-templates

@mcp.tool
async def search_power_port_templates(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search power port templates (dcim/power-port-templates/).
    Accepts: name, device_type, type, label, limit
        name: Name of the power port template (case-insensitive contains match)
        device_type: Device type ID (numeric)
        type: Power port type (case-insensitive contains match)
        label: Power port template label (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox power port template objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "device_type": "device_type_id",
        "type": "type__ic",
        "label": "label__ic"
    }
    return await _search("dcim/power-port-templates/", args, mappings)


@mcp.tool
async def get_power_port_template_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get power port template by ID (dcim/power-port-templates/{id}/).
    Accepts: id (required)
        id: Numeric ID of the power port template to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/power-port-templates/", args["id"])


# dcim/racks

@mcp.tool
async def search_racks(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search racks (dcim/racks/).
    Accepts: name, status, location, limit
        name: Name of the rack (case-insensitive contains match)
        status: Status of the rack (exact match), e.g., 'active', 'planned', 'reserved'
        location: Location ID (numeric)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox rack objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "status": "status",
        "location": "location_id"
    }
    return await _search("dcim/racks/", args, mappings)


@mcp.tool
async def get_rack_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get rack by ID (dcim/racks/{id}/).
    Accepts: id (required)
        id: Numeric ID of the rack to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/racks/", args["id"])


# dcim/rack-reservations

@mcp.tool
async def search_rack_reservations(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search rack reservations (dcim/rack-reservations/).
    Accepts: rack, limit
        rack: Rack ID (numeric)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox rack reservation objects (the `results` list) or an empty list.
    """
    mappings = {
        "rack": "rack_id"
    }
    return await _search("dcim/rack-reservations/", args, mappings)


@mcp.tool
async def get_rack_reservation_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get rack reservation by ID (dcim/rack-reservations/{id}/).
    Accepts: id (required)
        id: Numeric ID of the rack reservation to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/rack-reservations/", args["id"])


# dcim/rack-roles

@mcp.tool
async def search_rack_roles(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search rack roles (dcim/rack-roles/).
    Accepts: name, limit
        name: Name of the rack role (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox rack role objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic"
    }
    return await _search("dcim/rack-roles/", args, mappings)


@mcp.tool
async def get_rack_role_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get rack role by ID (dcim/rack-roles/{id}/).
    Accepts: id (required)
        id: Numeric ID of the rack role to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/rack-roles/", args["id"])


# dcim/rack-types

@mcp.tool
async def search_rack_types(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search rack types (dcim/rack-types/).
    Accepts: name, manufacturer, limit
        name: Name of the rack type (case-insensitive contains match)
        manufacturer: Manufacturer ID (numeric)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox rack type objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "manufacturer": "manufacturer_id"
    }
    return await _search("dcim/rack-types/", args, mappings)


@mcp.tool
async def get_rack_type_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get rack type by ID (dcim/rack-types/{id}/).
    Accepts: id (required)
        id: Numeric ID of the rack type to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/rack-types/", args["id"])


# dcim/rear-ports

@mcp.tool
async def search_rear_ports(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search rear ports (dcim/rear-ports/).
    Accepts: name, device, type, label, limit
        name: Name of the rear port (case-insensitive contains match)
        device: Device ID (numeric)
        type: Rear port type (case-insensitive contains match)
        label: Rear port label (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox rear port objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "device": "device_id",
        "type": "type__ic",
        "label": "label__ic"
    }
    return await _search("dcim/rear-ports/", args, mappings)


@mcp.tool
async def get_rear_port_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get rear port by ID (dcim/rear-ports/{id}/).
    Accepts: id (required)
        id: Numeric ID of the rear port to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/rear-ports/", args["id"])


# dcim/rear-port-templates

@mcp.tool
async def search_rear_port_templates(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search rear port templates (dcim/rear-port-templates/).
    Accepts: name, device_type, type, label, limit
        name: Name of the rear port template (case-insensitive contains match)
        device_type: Device type ID (numeric)
        type: Rear port type (case-insensitive contains match)
        label: Rear port template label (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox rear port template objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "device_type": "device_type_id",
        "type": "type__ic",
        "label": "label__ic"
    }
    return await _search("dcim/rear-port-templates/", args, mappings)


@mcp.tool
async def get_rear_port_template_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get rear port template by ID (dcim/rear-port-templates/{id}/).
    Accepts: id (required)
        id: Numeric ID of the rear port template to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/rear-port-templates/", args["id"])


# dcim/regions

@mcp.tool
async def search_regions(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search regions (dcim/regions/).
    Accepts: name, limit
        name: Name of the region (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox region objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic"
    }
    return await _search("dcim/regions/", args, mappings)


@mcp.tool
async def get_region_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get region by ID (dcim/regions/{id}/).
    Accepts: id (required)
        id: Numeric ID of the region to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/regions/", args["id"])


# dcim/virtual-chassis

@mcp.tool
async def search_virtual_chassis(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search virtual chassis (dcim/virtual-chassis/).
    Accepts: name, limit
        name: Name of the virtual chassis (case-insensitive contains match)
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox virtual chassis objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic"
    }
    return await _search("dcim/virtual-chassis/", args, mappings)


@mcp.tool
async def get_virtual_chassis_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get virtual chassis by ID (dcim/virtual-chassis/{id}/).
    Accepts: id (required)
        id: Numeric ID of the virtual chassis to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/virtual-chassis/", args["id"])


# dcim/virtual-device-contexts

@mcp.tool
async def search_virtual_device_contexts(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search virtual device contexts (dcim/virtual-device-contexts/).
    Accepts: name, device, status, limit
        name: Name of the virtual device context (case-insensitive contains match)
        device: Device ID (numeric)
        status: Status of the virtual device context (exact match), e.g., 'active', 'planned', 'offline'
        limit: Maximum number of results to return (default 10)
    
    Returns a list of NetBox virtual device context objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "device": "device_id",
        "status": "status"
    }
    return await _search("dcim/virtual-device-contexts/", args, mappings)


@mcp.tool
async def get_virtual_device_context_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get virtual device context by ID (dcim/virtual-device-contexts/{id}/).
    Accepts: id (required)
        id: Numeric ID of the virtual device context to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("dcim/virtual-device-contexts/", args["id"])


# --- tenancy (tenants, contacts, etc.) ---

# tenancy

# tenancy/tenants

@mcp.tool
async def search_tenants(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search tenants (tenancy/tenants/).
    Accepts: name, group, limit
        name: Name of the tenant (case-insensitive contains match)
        group: Tenant group id or name (optional)
        limit: maximum number of results to return (default 10)

    Returns a list of NetBox tenant objects (the `results` list) or an empty list.
    """
    mappings = {"name": "name__ic", "group": "tenant_group"}
    return await _search("tenancy/tenants/", args, mappings)


@mcp.tool
async def get_tenant_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get tenant details by ID (tenancy/tenants/{id}/).
    Accepts: id (required)
        id: Numeric ID of the tenant to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("tenancy/tenants/", args["id"])


# tenancy/tenant-groups

@mcp.tool
async def search_tenant_groups(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search tenant groups (tenancy/tenant-groups/).
    Accepts: name, limit
        name: Name of the tenant group (case-insensitive contains match)
        limit: maximum number of results to return (default 10)

    Returns a list of NetBox tenant group objects (the `results` list) or an empty list.
    """
    mappings = {"name": "name__ic"}
    return await _search("tenancy/tenant-groups/", args, mappings)


@mcp.tool
async def get_tenant_group_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get tenant group details by ID (tenancy/tenant-groups/{id}/).
    Accepts: id (required)
        id: Numeric ID of the tenant group to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("tenancy/tenant-groups/", args["id"])


# tenancy/contacts

@mcp.tool
async def search_contacts(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search contacts (tenancy/contacts/).
    Accepts: name, title, phone, email, address, limit
        name: Name of the contact (case-insensitive contains match)
        title: Contact's title or role (case-insensitive contains match)
        phone: Contact phone number (partial match)
        email: Contact email (case-insensitive contains match)
        address: Contact address (case-insensitive contains match)
        limit: maximum number of results to return (default 10)

    Returns a list of NetBox contact objects (the `results` list) or an empty list.
    """
    mappings = {
        "name": "name__ic",
        "title": "title__ic",
        "phone": "phone__ic",
        "email": "email__ic",
        "address": "address__ic",
    }
    return await _search("tenancy/contacts/", args, mappings)


@mcp.tool
async def get_contact_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get contact details by ID (tenancy/contacts/{id}/).
    Accepts: id (required)
        id: Numeric ID of the contact to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("tenancy/contacts/", args["id"])


# tenancy/contact-groups

@mcp.tool
async def search_contact_groups(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search contact groups (tenancy/contact-groups/).
    Accepts: name, limit
        name: Name of the contact group (case-insensitive contains match)
        limit: maximum number of results to return (default 10)

    Returns a list of NetBox contact group objects (the `results` list) or an empty list.
    """
    mappings = {"name": "name__ic"}
    return await _search("tenancy/contact-groups/", args, mappings)


@mcp.tool
async def get_contact_group_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get contact group details by ID (tenancy/contact-groups/{id}/).
    Accepts: id (required)
        id: Numeric ID of the contact group to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("tenancy/contact-groups/", args["id"])


# tenancy/contact-roles

@mcp.tool
async def search_contact_roles(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search contact roles (tenancy/contact-roles/).
    Accepts: name, limit
        name: Name of the contact role (case-insensitive contains match)
        limit: maximum number of results to return (default 10)

    Returns a list of NetBox contact role objects (the `results` list) or an empty list.
    """
    mappings = {"name": "name__ic"}
    return await _search("tenancy/contact-roles/", args, mappings)


@mcp.tool
async def get_contact_role_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get contact role details by ID (tenancy/contact-roles/{id}/).
    Accepts: id (required)
        id: Numeric ID of the contact role to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    return await _get_detail("tenancy/contact-roles/", args["id"])










if __name__ == "__main__":
    port_env = os.getenv("MCP_PORT")
    if port_env is None:
        port = 8000
    else:
        try:
            port = int(port_env)
        except ValueError:
            raise SystemExit(f"Invalid MCP_PORT value: {port_env} - must be an integer")

    mcp.run(transport="http", host="0.0.0.0", port=port)