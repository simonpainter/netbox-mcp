from fastmcp import FastMCP
import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin
import httpx


# Configuration
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
                raise Exception(f"NetBox API error: {e}")
            

mcp = FastMCP("NetBox Streaming MCP Server")



@mcp.tool
async def search_sites(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get comprehensive site information
      This tool queries the NetBox DCIM sites endpoint and supports the
    following filters (passed via `args`):

    - site_id: ID of the site (exact match)
    - site_name: Name of the site (case-insensitive search contains)
    The function returns a list of site objects as returned by NetBox
    (each item contains at least `id`, `name`, `status`, `region`,
    `tenant`, and other relevant fields). This output is
    JSON-serializable and suitable for use as MCP structured content.
    """

    
    params = {"limit": args.get("limit", 10)}

    if "site_name" in args:
        params["name__ic"] = args["site_name"]
    if "site_id" in args:
        params["site"] = args["site_id"]

    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    result = await netbox_client.get("dcim/sites/", params)

    return result.get("results", [])

@mcp.tool
async def search_devices(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search NetBox devices and return a JSON-serializable list of summaries.

    This tool queries the NetBox DCIM devices endpoint and supports the
    following optional filters (passed via `args`):
      - name: partial device name match (name__icontains)
      - site: filter by site name or ID
      - device_type: filter by device type identifier or name
      - role: device role
      - status: device status
      - limit: maximum number of results (default: 10)

    The function returns a list of device objects as returned by NetBox
    (each item contains at least `id`, `name`, and nested `site`,
    `device_type`, `role`, and `status` fields). This output is
    JSON-serializable and suitable for use as MCP structured content.
    """
    params = {"limit": args.get("limit", 10)}

    if "name" in args:
        params["name__ic"] = args["name"]
    if "site" in args:
        params["site"] = args["site"]
    if "device_type" in args:
        params["device_type"] = args["device_type"]
    if "role" in args:
        params["role"] = args["role"]
    if "status" in args:
        params["status"] = args["status"]

    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    result = await netbox_client.get("dcim/devices/", params)

    return result.get("results", [])

@mcp.tool
async def search_device_interfaces(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get interfaces for a device and return JSON-serializable results.

        Accepts arguments in `args`:
            - device_id (int): NetBox device ID (preferred).
            - device_name (str): Device name (used to look up the ID if device_id is not provided).
            - interface_type (str, optional): Filter interfaces by type (e.g. 'physical').
            - enabled (bool, optional): Filter interfaces by enabled status.

        Returns:
            - On success: a list of interface objects as returned by NetBox (each object is
                JSON-serializable and contains fields like `name`, `type`, `enabled`, `description`, etc.).
            - On user error (missing device identifier) or not found: a list containing a
                single MCP text message `[{"type":"text","text": "..."}]` suitable for the
                MCP structured content model.
    """
    device_id = args.get("device_id")
    device_name = args.get("device_name")
    
    if not device_id and not device_name:
        return [{"type": "text", "text": "Either device_id or device_name must be provided"}]
    
    if device_name and not device_id:
        search_result = await netbox_client.get("dcim/devices/", {"name": device_name})
        devices = search_result.get("results", [])
        if not devices:
            return [{"type": "text", "text": f"Device '{device_name}' not found"}]
        device_id = devices[0]["id"]
    
    params = {"device_id": device_id}
    if "interface_type" in args:
        params["type"] = args["interface_type"]
    if "enabled" in args:
        params["enabled"] = args["enabled"]

    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    result = await netbox_client.get("dcim/interfaces/", params)
    return result.get("results", [])


@mcp.tool
async def search_racks(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search for equipment racks and return the raw NetBox API results list.

    Supported args (filters passed directly to NetBox API):
      - limit (int): maximum results (default 10)
      - name (str): partial name match
      - site (str|int): site name or ID
      - location (str|int): location filter
      - status (str): status filter

    Returns:
      - A list of rack objects as returned by NetBox (i.e. `result['results']`).
    """
    params: Dict[str, Any] = {"limit": args.get("limit", 10)}

    if "name" in args:
        params["name__icontains"] = args["name"]
    if "site" in args:
        params["site"] = args["site"]
    if "location" in args:
        params["location"] = args["location"]
    if "status" in args:
        params["status"] = args["status"]

    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    result = await netbox_client.get("dcim/racks/", params)

    return result.get("results", []) if isinstance(result, dict) else []

@mcp.tool
async def search_prefixes(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search and return IP prefixes (structured NetBox results).

    Supported args (passed to NetBox API):
      - prefix (str): prefix string to match (e.g., '10.0.0.0/24')


    Returns:
      - A list of prefix objects as returned by NetBox (`result['results']`).
    """
    params: Dict[str, Any] = {"limit": args.get("limit", 10)}

    if "prefix" in args:
        params["prefix"] = args["prefix"]


    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    result = await netbox_client.get("ipam/prefixes/", params)

    return result.get("results", []) if isinstance(result, dict) else []

@mcp.tool
async def get_available_ips(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Find available IP addresses within a prefix and return structured results.

    Args accepted in `args`:
      - prefix_id (int): NetBox prefix ID (preferred).
      - prefix (str): Prefix string (e.g., '10.0.0.0/24') to look up the prefix_id if not provided.
      - count (int): Maximum number of available IPs to return (default: 10).

    Returns:
      - A list of available IP objects as returned by NetBox (usually a plain list).
      - Returns an empty list when no prefix is found or no available IPs.
    """
    prefix_id = args.get("prefix_id")
    prefix = args.get("prefix")
    count = args.get("count", 10)

    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)

    if not prefix_id and prefix:
        search_result = await netbox_client.get("ipam/prefixes/", {"prefix": prefix})
        prefixes = search_result.get("results", []) if isinstance(search_result, dict) else []
        if not prefixes:
            return []
        prefix_id = prefixes[0]["id"]

    if not prefix_id:
        return []

    result = await netbox_client.get(f"ipam/prefixes/{prefix_id}/available-ips/", {"limit": count})

    if result is None:
        return []
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        return result.get("results", [])
    return []

@mcp.tool
async def search_vlans(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search VLANs and return structured NetBox results.

    Supported args (passed to NetBox API):
      - vid (int): VLAN ID
      - name (str): partial VLAN name match
      - site (str|int): site name or ID
      - group (str|int): VLAN group
      - status (str): status filter
      - limit (int): maximum results (default 10)

    Returns a list of VLAN objects (`result['results']`).
    """
    params: Dict[str, Any] = {"limit": args.get("limit", 10)}

    if "vid" in args:
        params["vid"] = args["vid"]
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "site" in args:
        params["site"] = args["site"]
    if "group" in args:
        params["group"] = args["group"]
    if "status" in args:
        params["status"] = args["status"]

    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    result = await netbox_client.get("ipam/vlans/", params)

    return result.get("results", []) if isinstance(result, dict) else []




@mcp.tool
async def search_prefixes(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search and return IP prefixes (structured NetBox results).

    Supported args (passed to NetBox API):
      - prefix (str): prefix string to match (e.g., '10.0.0.0/24')


    Returns:
      - A list of prefix objects as returned by NetBox (`result['results']`).
    """
    params: Dict[str, Any] = {"limit": args.get("limit", 10)}

    if "prefix" in args:
        params["prefix"] = args["prefix"]


    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    result = await netbox_client.get("ipam/prefixes/", params)

    return result.get("results", []) if isinstance(result, dict) else []


@mcp.tool
async def get_available_ips(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Find available IP addresses within a prefix and return structured results.

    Args accepted in `args`:
      - prefix_id (int): NetBox prefix ID (preferred).
      - prefix (str): Prefix string (e.g., '10.0.0.0/24') to look up the prefix_id if not provided.
      - count (int): Maximum number of available IPs to return (default: 10).

    Returns:
      - A list of available IP objects as returned by NetBox (usually a plain list).
      - Returns an empty list when no prefix is found or no available IPs.
    """
    prefix_id = args.get("prefix_id")
    prefix = args.get("prefix")
    count = args.get("count", 10)

    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)

    if not prefix_id and prefix:
        search_result = await netbox_client.get("ipam/prefixes/", {"prefix": prefix})
        prefixes = search_result.get("results", []) if isinstance(search_result, dict) else []
        if not prefixes:
            return []
        prefix_id = prefixes[0]["id"]

    if not prefix_id:
        return []

    result = await netbox_client.get(f"ipam/prefixes/{prefix_id}/available-ips/", {"limit": count})

    if result is None:
        return []
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        return result.get("results", [])
    return []

@mcp.tool
async def search_circuits(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search circuits and return structured NetBox results.

    Supported args:
      - provider (str|int): provider name or ID
      - cid (str|int): circuit identifier
      - status (str): status filter
      - type (str): circuit type
      - tenant (str|int): tenant filter
      - limit (int): maximum results (default 10)
    """
    params: Dict[str, Any] = {"limit": args.get("limit", 10)}
    if "provider" in args:
        params["provider"] = args["provider"]
    if "cid" in args:
        params["cid"] = args["cid"]
    if "status" in args:
        params["status"] = args["status"]
    if "type" in args:
        params["type"] = args["type"]
    if "tenant" in args:
        params["tenant"] = args["tenant"]

    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    result = await netbox_client.get("circuits/circuits/", params)
    return result.get("results", []) if isinstance(result, dict) else []


@mcp.tool
async def search_rack_reservations(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search rack reservations and return structured NetBox results.

    Supported args:
      - rack (int): rack ID
      - user (str|int): user or owner
      - created_after (str): ISO date to filter
      - limit (int): maximum results (default 10)
    """
    params: Dict[str, Any] = {"limit": args.get("limit", 10)}
    if "rack" in args:
        params["rack"] = args["rack"]
    if "user" in args:
        params["user"] = args["user"]
    if "created_after" in args:
        params["created_after"] = args["created_after"]

    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    result = await netbox_client.get("dcim/rack-reservations/", params)
    return result.get("results", []) if isinstance(result, dict) else []


@mcp.tool
async def search_rack_roles(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search rack roles and return structured NetBox results.

    Supported args:
      - name (str): partial name match
      - slug (str): slug
      - limit (int): maximum results (default 10)
    """
    params: Dict[str, Any] = {"limit": args.get("limit", 10)}
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "slug" in args:
        params["slug"] = args["slug"]

    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    result = await netbox_client.get("dcim/rack-roles/", params)
    return result.get("results", []) if isinstance(result, dict) else []


@mcp.tool
async def search_rack_types(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search rack types and return structured NetBox results.

    Supported args:
      - name (str): partial name match
      - width (int): width filter
      - limit (int): maximum results (default 10)
    """
    params: Dict[str, Any] = {"limit": args.get("limit", 10)}
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "width" in args:
        params["width"] = args["width"]

    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    result = await netbox_client.get("dcim/rack-types/", params)
    return result.get("results", []) if isinstance(result, dict) else []


@mcp.tool
async def search_device_bays(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search device bays and return structured NetBox results.

    Supported args:
      - device (int): device ID
      - name (str): partial name match
      - is_empty (bool): whether bay has a device installed
      - limit (int): maximum results (default 10)
    """
    params: Dict[str, Any] = {"limit": args.get("limit", 10)}
    if "device" in args:
        params["device_id"] = args["device"]
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "is_empty" in args:
        # NetBox may expose installed_device or similar; try 'device' presence
        if args["is_empty"]:
            params["device_id__isnull"] = True
        else:
            params["device_id__isnull"] = False

    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    result = await netbox_client.get("dcim/device-bays/", params)
    return result.get("results", []) if isinstance(result, dict) else []

























if __name__ == "__main__":
    port_env = os.getenv("MCP_PORT") or os.getenv("PORT")
    if port_env is None:
        port = 8000
    else:
        try:
            port = int(port_env)
        except ValueError:
            raise SystemExit(f"Invalid MCP_PORT/PORT value: {port_env} - must be an integer")

    mcp.run(transport="http", host="0.0.0.0", port=port)