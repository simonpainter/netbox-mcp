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
async def get_site(args: Dict[str, Any]) -> List[Dict[str, Any]]:
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