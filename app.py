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
    result = await netbox_client.get("dcim/sites/", params)
    return result.get("results", [])





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