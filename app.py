#!/usr/bin/env python3
"""
Flask NetBox MCP Server - Streamable HTTP Transport
Implements the MCP Streamable HTTP protocol (2025-03-26 spec)
"""

import asyncio
import json
import os
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

# Configuration
NETBOX_URL = os.getenv("NETBOX_URL", "https://netbox.example.com")
NETBOX_TOKEN = os.getenv("NETBOX_TOKEN", "")

# Flask app setup
app = Flask(__name__)
CORS(app, origins="*")

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Session storage
sessions = {}

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
            except httpx.HTTPError as e:
                logger.error(f"NetBox API error: {e}")
                raise Exception(f"NetBox API error: {e}")

def run_async(func):
    """Decorator to run async functions in Flask routes"""
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(func(*args, **kwargs))
        finally:
            loop.close()
    return wrapper

def get_mcp_tools():
    """Return MCP tool definitions"""
    return [
        {
            "name": "search_devices",
            "description": "Search for devices in NetBox",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Device name (partial match)"},
                    "site": {"type": "string", "description": "Site name"},
                    "device_type": {"type": "string", "description": "Device type"},
                    "role": {"type": "string", "description": "Device role"},
                    "status": {"type": "string", "description": "Device status"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_device_details",
            "description": "Get detailed information about a specific device",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "integer", "description": "NetBox device ID"},
                    "device_name": {"type": "string", "description": "Device name (alternative to ID)"}
                }
            }
        },
        {
            "name": "get_device_interfaces",
            "description": "Get interfaces for a specific device",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "integer", "description": "NetBox device ID"},
                    "device_name": {"type": "string", "description": "Device name (alternative to ID)"},
                    "interface_type": {"type": "string", "description": "Filter by interface type"},
                    "enabled": {"type": "boolean", "description": "Filter by enabled status"}
                }
            }
        },
        {
            "name": "get_sites",
            "description": "List all sites in NetBox",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Site name filter"},
                    "region": {"type": "string", "description": "Region filter"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_site_details",
            "description": "Get comprehensive site information including devices and racks",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "site_id": {"type": "integer", "description": "NetBox site ID"},
                    "site_name": {"type": "string", "description": "Site name (alternative to ID)"},
                    "include_devices": {"type": "boolean", "description": "Include device summary (default: true)", "default": True},
                    "include_racks": {"type": "boolean", "description": "Include rack summary (default: true)", "default": True}
                }
            }
        },
        {
            "name": "search_ip_addresses",
            "description": "Search for IP addresses in NetBox",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "address": {"type": "string", "description": "IP address or network"},
                    "vrf": {"type": "string", "description": "VRF name"},
                    "status": {"type": "string", "description": "IP status"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_prefixes",
            "description": "Search and list IP prefixes/subnets",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "prefix": {"type": "string", "description": "Specific prefix (e.g., '192.168.1.0/24')"},
                    "within": {"type": "string", "description": "Find prefixes within a larger network"},
                    "family": {"type": "integer", "description": "IP family (4 or 6)"},
                    "status": {"type": "string", "description": "Prefix status"},
                    "site": {"type": "string", "description": "Filter by site"},
                    "vrf": {"type": "string", "description": "Filter by VRF"},
                    "role": {"type": "string", "description": "Prefix role"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_available_ips",
            "description": "Find available IP addresses within a prefix",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "prefix_id": {"type": "integer", "description": "NetBox prefix ID"},
                    "prefix": {"type": "string", "description": "Prefix in CIDR notation (alternative to ID)"},
                    "count": {"type": "integer", "description": "Number of IPs to return (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "search_vlans",
            "description": "Search for VLANs",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "vid": {"type": "integer", "description": "VLAN ID"},
                    "name": {"type": "string", "description": "VLAN name (partial match)"},
                    "site": {"type": "string", "description": "Filter by site"},
                    "group": {"type": "string", "description": "VLAN group"},
                    "status": {"type": "string", "description": "VLAN status"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "search_circuits",
            "description": "Search for circuits",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "cid": {"type": "string", "description": "Circuit ID (partial match)"},
                    "provider": {"type": "string", "description": "Provider name"},
                    "type": {"type": "string", "description": "Circuit type"},
                    "status": {"type": "string", "description": "Circuit status"},
                    "site": {"type": "string", "description": "Termination site"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "search_racks",
            "description": "Search for equipment racks",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Rack name (partial match)"},
                    "site": {"type": "string", "description": "Site name"},
                    "location": {"type": "string", "description": "Location within site"},
                    "status": {"type": "string", "description": "Rack status"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        }
    ]

# MCP Streamable HTTP Protocol Implementation
@app.route('/api/mcp', methods=['GET', 'POST', 'DELETE'])
def mcp_endpoint():
    """Single MCP endpoint implementing Streamable HTTP transport"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    # Validate Origin header for security
    origin = request.headers.get('Origin')
    if origin and origin not in ['https://claude.ai', 'https://localhost', 'http://localhost']:
        # Allow for development - in production, be more restrictive
        pass
    
    # Handle session management
    session_id = request.headers.get('Mcp-Session-Id')
    
    if request.method == 'DELETE':
        # Terminate session
        if session_id and session_id in sessions:
            del sessions[session_id]
            logger.info(f"Session {session_id} terminated")
        return '', 204
    
    elif request.method == 'GET':
        # GET request - could be for SSE streaming or session resumption
        accept_header = request.headers.get('Accept', '')
        
        if 'text/event-stream' in accept_header:
            # Client wants SSE stream
            return Response(
                stream_with_context(sse_generator(session_id)),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type, Mcp-Session-Id'
                }
            )
        else:
            # Return server info
            return jsonify({
                "name": "netbox-mcp-server",
                "version": "1.0.0",
                "protocolVersion": "2025-03-26",
                "capabilities": {
                    "tools": {}
                },
                "instructions": "NetBox MCP Server - Query your NetBox instance using the Streamable HTTP transport"
            })
    
    elif request.method == 'POST':
        # POST request - handle MCP messages
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }), 400
            
            # Handle the MCP message
            response = handle_mcp_message(data, session_id)
            
            # Check if we need to create a session
            if not session_id and data.get('method') == 'initialize':
                new_session_id = str(uuid.uuid4())
                sessions[new_session_id] = {
                    "created_at": datetime.utcnow(),
                    "initialized": True
                }
                response_headers = {'Mcp-Session-Id': new_session_id}
                return jsonify(response), 200, response_headers
            
            return jsonify(response)
            
        except Exception as e:
            logger.error(f"Error handling MCP message: {e}")
            return jsonify({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": "Internal error"
                }
            }), 500

def sse_generator(session_id):
    """Generate SSE events for streaming responses"""
    # For now, just send a heartbeat - in a real implementation,
    # this would stream responses for long-running operations
    import time
    
    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
    
    # Keep connection alive
    while True:
        time.sleep(30)
        yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.utcnow().isoformat()})}\n\n"

@run_async
async def handle_mcp_message(message, session_id=None):
    """Handle incoming MCP protocol messages"""
    method = message.get('method')
    msg_id = message.get('id')
    params = message.get('params', {})
    
    logger.info(f"Handling MCP message: {method}")
    
    try:
        if method == 'initialize':
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "netbox-mcp-server",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif method == 'tools/list':
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": get_mcp_tools()
                }
            }
        
        elif method == 'resources/list':
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "resources": []
                }
            }
        
        elif method == 'tools/call':
            tool_name = params.get('name')
            arguments = params.get('arguments', {})
            
            if not NETBOX_TOKEN:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32000,
                        "message": "NetBox token not configured"
                    }
                }
            
            # Execute the tool
            netbox_client = NetBoxClient(NETBOX_URL, NETBOX_TOKEN)
            result = await execute_tool(tool_name, arguments, netbox_client)
            
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": result
                }
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    except Exception as e:
        logger.error(f"Error executing MCP method {method}: {e}")
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "netbox_url": NETBOX_URL,
        "netbox_configured": bool(NETBOX_TOKEN),
        "transport": "streamable-http",
        "protocol_version": "2025-03-26",
        "mcp_endpoint": "/api/mcp"
    })

# Tool execution functions
async def execute_tool(tool_name: str, args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Execute a tool and return results"""
    tools = {
        "search_devices": search_devices,
        "get_device_details": get_device_details,
        "get_device_interfaces": get_device_interfaces,
        "get_sites": get_sites,
        "get_site_details": get_site_details,
        "search_ip_addresses": search_ip_addresses,
        "get_prefixes": get_prefixes,
        "get_available_ips": get_available_ips,
        "search_vlans": search_vlans,
        "search_circuits": search_circuits,
        "search_racks": search_racks
    }
    
    if tool_name not in tools:
        raise ValueError(f"Unknown tool: {tool_name}")
    
    return await tools[tool_name](args, netbox_client)

async def search_devices(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for devices"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "site" in args:
        params["site"] = args["site"]
    if "device_type" in args:
        params["device_type"] = args["device_type"]
    if "role" in args:
        params["role"] = args["role"]
    if "status" in args:
        params["status"] = args["status"]
    
    result = await netbox_client.get("dcim/devices/", params)
    devices = result.get("results", [])
    count = result.get("count", 0)
    
    if not devices:
        return [{"type": "text", "text": "No devices found matching the criteria."}]
    
    output = f"Found {count} devices:\n\n"
    for device in devices:
        site_name = device.get("site", {}).get("name", "Unknown")
        device_type = device.get("device_type", {}).get("model", "Unknown")
        role = device.get("role", {}).get("name", "Unknown")
        status = device.get("status", {}).get("label", "Unknown")
        
        output += f"• **{device['name']}** (ID: {device['id']})\n"
        output += f"  - Site: {site_name}\n"
        output += f"  - Type: {device_type}\n"
        output += f"  - Role: {role}\n"
        output += f"  - Status: {status}\n\n"
    
    return [{"type": "text", "text": output}]

async def get_device_interfaces(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get interfaces for a device"""
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
    
    result = await netbox_client.get("dcim/interfaces/", params)
    interfaces = result.get("results", [])
    
    if not interfaces:
        return [{"type": "text", "text": "No interfaces found for this device."}]
    
    output = f"Interfaces for device ID {device_id}:\n\n"
    for interface in interfaces:
        enabled = interface.get("enabled", False)
        iface_type = interface.get("type", {}).get("label", "Unknown")
        
        output += f"• **{interface['name']}**\n"
        output += f"  - Type: {iface_type}\n"
        output += f"  - Enabled: {'Yes' if enabled else 'No'}\n"
        
        if interface.get("description"):
            output += f"  - Description: {interface['description']}\n"
        
        if interface.get("mtu"):
            output += f"  - MTU: {interface['mtu']}\n"
        
        # Show connected cable if any
        if interface.get("cable"):
            cable_id = interface["cable"]["id"]
            output += f"  - Cable: {cable_id}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def get_site_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get comprehensive site information"""
    site_id = args.get("site_id")
    site_name = args.get("site_name")
    include_devices = args.get("include_devices", True)
    include_racks = args.get("include_racks", True)
    
    if not site_id and not site_name:
        return [{"type": "text", "text": "Either site_id or site_name must be provided"}]
    
    if site_name and not site_id:
        search_result = await netbox_client.get("dcim/sites/", {"name": site_name})
        sites = search_result.get("results", [])
        if not sites:
            return [{"type": "text", "text": f"Site '{site_name}' not found"}]
        site_id = sites[0]["id"]
    
    # Get site details
    site = await netbox_client.get(f"dcim/sites/{site_id}/")
    
    region_name = site.get("region", {}).get("name", "No region") if site.get("region") else "No region"
    status = site.get("status", {}).get("label", "Unknown")
    
    output = f"# Site Details: {site['name']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- ID: {site['id']}\n"
    output += f"- Name: {site['name']}\n"
    output += f"- Slug: {site['slug']}\n"
    output += f"- Status: {status}\n"
    output += f"- Region: {region_name}\n"
    
    if site.get("description"):
        output += f"- Description: {site['description']}\n"
    
    output += "\n"
    
    # Include device summary if requested
    if include_devices:
        device_result = await netbox_client.get("dcim/devices/", {"site_id": site_id, "limit": 100})
        devices = device_result.get("results", [])
        device_count = device_result.get("count", 0)
        
        output += f"**Devices ({device_count} total):**\n"
        if devices:
            # Group by role for summary
            roles = {}
            for device in devices:
                role = device.get("role", {}).get("name", "Unknown")
                if role not in roles:
                    roles[role] = 0
                roles[role] += 1
            
            for role, count in roles.items():
                output += f"- {role}: {count} devices\n"
        else:
            output += "- No devices found\n"
        output += "\n"
    
    # Include rack summary if requested
    if include_racks:
        rack_result = await netbox_client.get("dcim/racks/", {"site_id": site_id, "limit": 100})
        racks = rack_result.get("results", [])
        rack_count = rack_result.get("count", 0)
        
        output += f"**Racks ({rack_count} total):**\n"
        if racks:
            for rack in racks[:10]:  # Show first 10 racks
                status = rack.get("status", {}).get("label", "Unknown")
                u_height = rack.get("u_height", "Unknown")
                output += f"- {rack['name']}: {u_height}U, Status: {status}\n"
            
            if rack_count > 10:
                output += f"- ... and {rack_count - 10} more racks\n"
        else:
            output += "- No racks found\n"
    
    return [{"type": "text", "text": output}]

async def get_prefixes(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search and list IP prefixes/subnets"""
    params = {"limit": args.get("limit", 10)}
    
    if "prefix" in args:
        params["prefix"] = args["prefix"]
    if "within" in args:
        params["within"] = args["within"]
    if "family" in args:
        params["family"] = args["family"]
    if "status" in args:
        params["status"] = args["status"]
    if "site" in args:
        params["site"] = args["site"]
    if "vrf" in args:
        params["vrf"] = args["vrf"]
    if "role" in args:
        params["role"] = args["role"]
    
    result = await netbox_client.get("ipam/prefixes/", params)
    prefixes = result.get("results", [])
    count = result.get("count", 0)
    
    if not prefixes:
        return [{"type": "text", "text": "No prefixes found matching the criteria."}]
    
    output = f"Found {count} prefixes:\n\n"
    for prefix in prefixes:
        vrf_name = prefix.get("vrf", {}).get("name", "Global") if prefix.get("vrf") else "Global"
        status = prefix.get("status", {}).get("label", "Unknown")
        role = prefix.get("role", {}).get("name", "No role") if prefix.get("role") else "No role"
        site = prefix.get("site", {}).get("name", "No site") if prefix.get("site") else "No site"
        
        output += f"• **{prefix['prefix']}**\n"
        output += f"  - VRF: {vrf_name}\n"
        output += f"  - Status: {status}\n"
        output += f"  - Role: {role}\n"
        output += f"  - Site: {site}\n"
        
        if prefix.get("description"):
            output += f"  - Description: {prefix['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def get_available_ips(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Find available IP addresses within a prefix"""
    prefix_id = args.get("prefix_id")
    prefix = args.get("prefix")
    count = args.get("count", 10)
    
    if not prefix_id and not prefix:
        return [{"type": "text", "text": "Either prefix_id or prefix must be provided"}]
    
    if prefix and not prefix_id:
        search_result = await netbox_client.get("ipam/prefixes/", {"prefix": prefix})
        prefixes = search_result.get("results", [])
        if not prefixes:
            return [{"type": "text", "text": f"Prefix '{prefix}' not found"}]
        prefix_id = prefixes[0]["id"]
    
    # NetBox API endpoint for available IPs
    result = await netbox_client.get(f"ipam/prefixes/{prefix_id}/available-ips/", {"limit": count})
    
    if not result:
        return [{"type": "text", "text": "No available IP addresses found in this prefix."}]
    
    output = f"Available IP addresses (showing up to {count}):\n\n"
    for ip in result:
        output += f"• {ip['address']}\n"
    
    return [{"type": "text", "text": output}]

async def search_vlans(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for VLANs"""
    params = {"limit": args.get("limit", 10)}
    
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
    
    result = await netbox_client.get("ipam/vlans/", params)
    vlans = result.get("results", [])
    count = result.get("count", 0)
    
    if not vlans:
        return [{"type": "text", "text": "No VLANs found matching the criteria."}]
    
    output = f"Found {count} VLANs:\n\n"
    for vlan in vlans:
        status = vlan.get("status", {}).get("label", "Unknown")
        site = vlan.get("site", {}).get("name", "No site") if vlan.get("site") else "No site"
        group = vlan.get("group", {}).get("name", "No group") if vlan.get("group") else "No group"
        
        output += f"• **VLAN {vlan['vid']}** - {vlan['name']}\n"
        output += f"  - Status: {status}\n"
        output += f"  - Site: {site}\n"
        output += f"  - Group: {group}\n"
        
        if vlan.get("description"):
            output += f"  - Description: {vlan['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def search_circuits(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for circuits"""
    params = {"limit": args.get("limit", 10)}
    
    if "cid" in args:
        params["cid__icontains"] = args["cid"]
    if "provider" in args:
        params["provider"] = args["provider"]
    if "type" in args:
        params["type"] = args["type"]
    if "status" in args:
        params["status"] = args["status"]
    if "site" in args:
        params["site"] = args["site"]
    
    result = await netbox_client.get("circuits/circuits/", params)
    circuits = result.get("results", [])
    count = result.get("count", 0)
    
    if not circuits:
        return [{"type": "text", "text": "No circuits found matching the criteria."}]
    
    output = f"Found {count} circuits:\n\n"
    for circuit in circuits:
        provider = circuit.get("provider", {}).get("name", "Unknown")
        circuit_type = circuit.get("type", {}).get("name", "Unknown")
        status = circuit.get("status", {}).get("label", "Unknown")
        
        output += f"• **{circuit['cid']}** (ID: {circuit['id']})\n"
        output += f"  - Provider: {provider}\n"
        output += f"  - Type: {circuit_type}\n"
        output += f"  - Status: {status}\n"
        
        if circuit.get("description"):
            output += f"  - Description: {circuit['description']}\n"
        
        # Show terminations if available
        if circuit.get("termination_a"):
            term_a = circuit["termination_a"]
            if term_a.get("site"):
                output += f"  - Termination A: {term_a['site']['name']}\n"
        
        if circuit.get("termination_z"):
            term_z = circuit["termination_z"]
            if term_z.get("site"):
                output += f"  - Termination Z: {term_z['site']['name']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def search_racks(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for equipment racks"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "site" in args:
        params["site"] = args["site"]
    if "location" in args:
        params["location"] = args["location"]
    if "status" in args:
        params["status"] = args["status"]
    
    result = await netbox_client.get("dcim/racks/", params)
    racks = result.get("results", [])
    count = result.get("count", 0)
    
    if not racks:
        return [{"type": "text", "text": "No racks found matching the criteria."}]
    
    output = f"Found {count} racks:\n\n"
    for rack in racks:
        site = rack.get("site", {}).get("name", "Unknown")
        status = rack.get("status", {}).get("label", "Unknown")
        u_height = rack.get("u_height", "Unknown")
        location = rack.get("location", {}).get("name", "No location") if rack.get("location") else "No location"
        
        output += f"• **{rack['name']}** (ID: {rack['id']})\n"
        output += f"  - Site: {site}\n"
        output += f"  - Location: {location}\n"
        output += f"  - Height: {u_height}U\n"
        output += f"  - Status: {status}\n"
        
        if rack.get("description"):
            output += f"  - Description: {rack['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def get_device_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed device information"""
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
    
    device = await netbox_client.get(f"dcim/devices/{device_id}/")
    
    site_name = device.get("site", {}).get("name", "Unknown")
    device_type = device.get("device_type", {}).get("model", "Unknown")
    manufacturer = device.get("device_type", {}).get("manufacturer", {}).get("name", "Unknown")
    role = device.get("role", {}).get("name", "Unknown")
    status = device.get("status", {}).get("label", "Unknown")
    serial = device.get("serial", "N/A")
    
    output = f"# Device Details: {device['name']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- ID: {device['id']}\n"
    output += f"- Name: {device['name']}\n"
    output += f"- Status: {status}\n"
    output += f"- Site: {site_name}\n"
    output += f"- Role: {role}\n\n"
    
    output += f"**Hardware:**\n"
    output += f"- Manufacturer: {manufacturer}\n"
    output += f"- Model: {device_type}\n"
    output += f"- Serial Number: {serial}\n\n"
    
    if device.get("primary_ip4"):
        output += f"**Network:**\n"
        output += f"- Primary IPv4: {device['primary_ip4']['address']}\n"
    
    if device.get("primary_ip6"):
        output += f"- Primary IPv6: {device['primary_ip6']['address']}\n"
    
    return [{"type": "text", "text": output}]

async def get_sites(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get sites"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "region" in args:
        params["region"] = args["region"]
    
    result = await netbox_client.get("dcim/sites/", params)
    sites = result.get("results", [])
    count = result.get("count", 0)
    
    if not sites:
        return [{"type": "text", "text": "No sites found matching the criteria."}]
    
    output = f"Found {count} sites:\n\n"
    for site in sites:
        region_name = site.get("region", {}).get("name", "No region") if site.get("region") else "No region"
        status = site.get("status", {}).get("label", "Unknown")
        
        output += f"• **{site['name']}** (ID: {site['id']})\n"
        output += f"  - Slug: {site['slug']}\n"
        output += f"  - Status: {status}\n"
        output += f"  - Region: {region_name}\n"
        
        if site.get("description"):
            output += f"  - Description: {site['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def search_ip_addresses(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for IP addresses"""
    params = {"limit": args.get("limit", 10)}
    
    if "address" in args:
        params["address__contains"] = args["address"]
    if "vrf" in args:
        params["vrf"] = args["vrf"]
    if "status" in args:
        params["status"] = args["status"]
    
    result = await netbox_client.get("ipam/ip-addresses/", params)
    ips = result.get("results", [])
    count = result.get("count", 0)
    
    if not ips:
        return [{"type": "text", "text": "No IP addresses found matching the criteria."}]
    
    output = f"Found {count} IP addresses:\n\n"
    for ip in ips:
        vrf_name = ip.get("vrf", {}).get("name", "Global") if ip.get("vrf") else "Global"
        status = ip.get("status", {}).get("label", "Unknown")
        assigned_object = ip.get("assigned_object")
        
        output += f"• **{ip['address']}**\n"
        output += f"  - VRF: {vrf_name}\n"
        output += f"  - Status: {status}\n"
        
        if assigned_object:
            output += f"  - Assigned to: {assigned_object.get('name', 'Unknown')}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

if __name__ == "__main__":
    # Validate required environment variables
    if not NETBOX_URL or NETBOX_URL == "https://netbox.example.com":
        logger.error("ERROR: NETBOX_URL environment variable must be set")
        exit(1)
    
    if not NETBOX_TOKEN:
        logger.error("ERROR: NETBOX_TOKEN environment variable must be set")
        exit(1)
    
    port = int(os.getenv("PORT", "8080"))
    
    logger.info(f"Starting NetBox MCP Server with Streamable HTTP transport on port {port}")
    logger.info(f"NetBox URL: {NETBOX_URL}")
    logger.info(f"MCP Endpoint: http://localhost:{port}/api/mcp")
    logger.info(f"Protocol Version: 2025-03-26 (Streamable HTTP)")
    
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)