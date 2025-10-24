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

# Tool definitions

# dcim

# dcim/sites


@mcp.tool
async def search_sites(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search sites (dcim/sites/).
    Accepts: name, status, region, limit
        name: Name of the site (case-insensitive search contains)
        status: Status of the site (exact match) active
        region: Name of the region (case-insensitive search contains)
    """
    params = {"limit": args.get("limit", 10)}
    if "name" in args:
        params["name__ic"] = args["site_name"]
    if "status" in args:
        params["status"] = args["status"]
    if "region" in args:
        params["region__ic"] = args["region"]
    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    result = await netbox_client.get("dcim/sites/", params)
    return result.get("results", [])

@mcp.tool
async def get_site_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get site by ID (dcim/sites/).
    Accepts: id
        id: ID of the site - can be obtained from search_sites
    """

    params = {"limit": args.get("limit", 1)}
    if "id" in args:
        params["site"] = args["id"]
    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    try:
        result = await netbox_client.get(f"dcim/sites/{args['id']}/")
        return [result] if isinstance(result, dict) else []
    except Exception:
        # Surface errors as empty list per repo behavior for validation-like issues
        return []


# dcim/site-groups


@mcp.tool
async def search_site_groups(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search site groups (dcim/site-groups/).
    Accepts: name, limit
        name: Name of the site group (case-insensitive contains match)
        limit: maximum number of results to return (default 10)

    Returns a list of NetBox site group objects (the `results` list) or an empty list.
    """
    params = {"limit": args.get("limit", 10)}
    if "name" in args:
        params["name__ic"] = args["name"]
    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    result = await netbox_client.get("dcim/site-groups/", params)
    return result.get("results", [])


@mcp.tool
async def get_site_group_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get site group details by ID (dcim/site-groups/{id}/).
    Accepts: id (required)
        id: Numeric ID of the site group to fetch. When provided, the tool will call
            the single-object endpoint and return a single-element list `[obj]` or `[]` if
            not found.
    """
    if "id" not in args:
        # Follow repository convention: return empty list when required args missing
        return []
    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    try:
        result = await netbox_client.get(f"dcim/site-groups/{args['id']}/")
        return [result] if isinstance(result, dict) else []
    except Exception:
        # Surface errors as empty list per repo behavior for validation-like issues
        return []


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
    params = {"limit": args.get("limit", 10)}
    if "name" in args:
        params["name__ic"] = args["name"]
    if "group" in args:
        # Accept either group id or name; map to tenant_group if numeric else name__ic
        params["tenant_group"] = args["group"]
    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    result = await netbox_client.get("tenancy/tenants/", params)
    return result.get("results", [])


@mcp.tool
async def get_tenant_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get tenant details by ID (tenancy/tenants/{id}/).
    Accepts: id (required)
        id: Numeric ID of the tenant to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    try:
        result = await netbox_client.get(f"tenancy/tenants/{args['id']}/")
        return [result] if isinstance(result, dict) else []
    except Exception:
        return []



# tenancy/tenant-groups


@mcp.tool
async def search_tenant_groups(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search tenant groups (tenancy/tenant-groups/).
    Accepts: name, limit
        name: Name of the tenant group (case-insensitive contains match)
        limit: maximum number of results to return (default 10)

    Returns a list of NetBox tenant group objects (the `results` list) or an empty list.
    """
    params = {"limit": args.get("limit", 10)}
    if "name" in args:
        params["name__ic"] = args["name"]
    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    result = await netbox_client.get("tenancy/tenant-groups/", params)
    return result.get("results", [])


@mcp.tool
async def get_tenant_group_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get tenant group details by ID (tenancy/tenant-groups/{id}/).
    Accepts: id (required)
        id: Numeric ID of the tenant group to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    try:
        result = await netbox_client.get(f"tenancy/tenant-groups/{args['id']}/")
        return [result] if isinstance(result, dict) else []
    except Exception:
        return []


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
    params = {"limit": args.get("limit", 10)}
    if "name" in args:
        params["name__ic"] = args["name"]
    if "title" in args:
        params["title__ic"] = args["title"]
    if "phone" in args:
        params["phone__ic"] = args["phone"]
    if "email" in args:
        params["email__ic"] = args["email"]
    if "address" in args:
        params["address__ic"] = args["address"]
    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    result = await netbox_client.get("tenancy/contacts/", params)
    return result.get("results", [])


@mcp.tool
async def get_contact_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get contact details by ID (tenancy/contacts/{id}/).
    Accepts: id (required)
        id: Numeric ID of the contact to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    try:
        result = await netbox_client.get(f"tenancy/contacts/{args['id']}/")
        return [result] if isinstance(result, dict) else []
    except Exception:
        return []


# tenancy/contact-groups


@mcp.tool
async def search_contact_groups(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search contact groups (tenancy/contact-groups/).
    Accepts: name, limit
        name: Name of the contact group (case-insensitive contains match)
        limit: maximum number of results to return (default 10)

    Returns a list of NetBox contact group objects (the `results` list) or an empty list.
    """
    params = {"limit": args.get("limit", 10)}
    if "name" in args:
        params["name__ic"] = args["name"]
    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    result = await netbox_client.get("tenancy/contact-groups/", params)
    return result.get("results", [])


@mcp.tool
async def get_contact_group_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get contact group details by ID (tenancy/contact-groups/{id}/).
    Accepts: id (required)
        id: Numeric ID of the contact group to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    try:
        result = await netbox_client.get(f"tenancy/contact-groups/{args['id']}/")
        return [result] if isinstance(result, dict) else []
    except Exception:
        return []


# tenancy/contact-roles


@mcp.tool
async def search_contact_roles(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search contact roles (tenancy/contact-roles/).
    Accepts: name, limit
        name: Name of the contact role (case-insensitive contains match)
        limit: maximum number of results to return (default 10)

    Returns a list of NetBox contact role objects (the `results` list) or an empty list.
    """
    params = {"limit": args.get("limit", 10)}
    if "name" in args:
        params["name__ic"] = args["name"]
    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    result = await netbox_client.get("tenancy/contact-roles/", params)
    return result.get("results", [])


@mcp.tool
async def get_contact_role_details(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get contact role details by ID (tenancy/contact-roles/{id}/).
    Accepts: id (required)
        id: Numeric ID of the contact role to fetch. Returns `[obj]` or `[]`.
    """
    if "id" not in args:
        return []
    netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
    try:
        result = await netbox_client.get(f"tenancy/contact-roles/{args['id']}/")
        return [result] if isinstance(result, dict) else []
    except Exception:
        return []





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