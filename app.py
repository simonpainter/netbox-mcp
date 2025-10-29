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

@mcp.tool
async def search_sites(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search sites (dcim/sites/).
    Accepts: name, status, location, region, limit
        name: Name of the site (case-insensitive search contains)
        status: Status of the site (exact match) active
        location: Location name or ID (case-insensitive search contains)
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


@mcp.tool
async def search_devices(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search devices (dcim/devices/).
    Accepts: name, role, device_type, serial, asset_tag, rack, limit
        name: Name of the device (case-insensitive contains match)
        role: Device role ID or slug (NetBox API accepts numeric ID or slug)
        device_type: Device type ID or slug (NetBox API accepts numeric ID or slug)
        serial: Serial number (case-insensitive contains match)
        asset_tag: Asset tag (case-insensitive contains match)
        rack: Rack ID (numeric ID)
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