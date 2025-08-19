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
        "get_sites": get_sites,
        "search_ip_addresses": search_ip_addresses
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