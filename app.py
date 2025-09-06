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

def check_empty_results(result: Dict[str, Any], resource_name: str) -> Optional[List[Dict[str, Any]]]:
    """
    Helper function to check if API results are empty and return appropriate response.
    
    Args:
        result: NetBox API response containing 'results' key
        resource_name: Human-readable name for the resource type (e.g., "virtual machines", "devices")
    
    Returns:
        None if results exist (caller should continue processing)
        List with "not found" message if results are empty
    """
    items = result.get("results", [])
    if not items:
        return [{"type": "text", "text": f"No {resource_name} found matching the criteria"}]
    return None

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
        },
        {
            "name": "get_rack_details",
            "description": "Get detailed information about a specific rack",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "rack_id": {"type": "integer", "description": "NetBox rack ID"},
                    "rack_name": {"type": "string", "description": "Rack name (alternative to ID)"}
                }
            }
        },
        {
            "name": "search_rack_reservations",
            "description": "Search for rack reservations",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "rack": {"type": "string", "description": "Rack name"},
                    "user": {"type": "string", "description": "User who made the reservation"},
                    "description": {"type": "string", "description": "Reservation description (partial match)"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "search_device_bays",
            "description": "Search for device bays in NetBox",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "integer", "description": "Device ID to filter bays"},
                    "device_name": {"type": "string", "description": "Device name to filter bays"},
                    "name": {"type": "string", "description": "Bay name (partial match)"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_device_bay_details",
            "description": "Get detailed information about a specific device bay",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bay_id": {"type": "integer", "description": "NetBox device bay ID"},
                    "device_id": {"type": "integer", "description": "Device ID (when combined with bay name)"},
                    "bay_name": {"type": "string", "description": "Bay name (when combined with device ID)"}
                }
            }
        },
        {
            "name": "search_device_bay_templates",
            "description": "Search for device bay templates in NetBox",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "device_type_id": {"type": "integer", "description": "Device type ID to filter templates"},
                    "name": {"type": "string", "description": "Template name (partial match)"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_rack_reservation_details",
            "description": "Get detailed information about a specific rack reservation",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "reservation_id": {"type": "integer", "description": "NetBox rack reservation ID"}
                }
            }
        },
        {
            "name": "search_rack_roles",
            "description": "Search for rack roles",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Rack role name (partial match)"},
                    "slug": {"type": "string", "description": "Rack role slug"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_device_bay_template_details",
            "description": "Get detailed information about a specific device bay template",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "template_id": {"type": "integer", "description": "NetBox device bay template ID"}
                }
            }
        },
        {
            "name": "search_device_roles",
            "description": "Search for device roles in NetBox",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Role name (partial match)"},
                    "slug": {"type": "string", "description": "Role slug"},
                    "color": {"type": "string", "description": "Role color"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "search_rack_types",
            "description": "Search for rack types",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "model": {"type": "string", "description": "Rack type model (partial match)"},
                    "manufacturer": {"type": "string", "description": "Manufacturer name"},
                    "slug": {"type": "string", "description": "Rack type slug"},
                    "u_height": {"type": "integer", "description": "Filter by rack height in units"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_device_role_details",
            "description": "Get detailed information about a specific device role",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "role_id": {"type": "integer", "description": "NetBox device role ID"},
                    "role_name": {"type": "string", "description": "Role name (alternative to ID)"},
                    "role_slug": {"type": "string", "description": "Role slug (alternative to ID)"}
                }
            }
        },
        {
            "name": "search_device_types",
            "description": "Search for device types in NetBox",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "model": {"type": "string", "description": "Device model (partial match)"},
                    "manufacturer": {"type": "string", "description": "Manufacturer name"},
                    "slug": {"type": "string", "description": "Device type slug"},
                    "part_number": {"type": "string", "description": "Part number"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_device_type_details",
            "description": "Get detailed information about a specific device type",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "type_id": {"type": "integer", "description": "NetBox device type ID"},
                    "model": {"type": "string", "description": "Device model (alternative to ID)"},
                    "slug": {"type": "string", "description": "Device type slug (alternative to ID)"}
                }
            }
        },
        {
            "name": "search_vlan_translation_policies",
            "description": "Search for VLAN translation policies",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Policy name (partial match)"},
                    "description": {"type": "string", "description": "Policy description (partial match)"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "search_asns",
            "description": "Search for Autonomous System Numbers (ASNs)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "asn": {"type": "integer", "description": "Specific ASN number"},
                    "name": {"type": "string", "description": "ASN name (partial match)"},
                    "rir": {"type": "string", "description": "Regional Internet Registry"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "search_vlan_translation_rules",
            "description": "Search for VLAN translation rules",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "policy_id": {"type": "integer", "description": "Translation policy ID"},
                    "original_vid": {"type": "integer", "description": "Original VLAN ID"},
                    "translated_vid": {"type": "integer", "description": "Translated VLAN ID"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_asn_details",
            "description": "Get detailed information about a specific ASN",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "asn_id": {"type": "integer", "description": "NetBox ASN ID"},
                    "asn": {"type": "integer", "description": "ASN number (alternative to ID)"}
                }
            }
        },
        {
            "name": "search_asn_ranges",
            "description": "Search for ASN ranges",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "ASN range name (partial match)"},
                    "rir": {"type": "string", "description": "Regional Internet Registry"},
                    "start": {"type": "integer", "description": "Range start ASN"},
                    "end": {"type": "integer", "description": "Range end ASN"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_asn_range_details",
            "description": "Get detailed information about a specific ASN range",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "range_id": {"type": "integer", "description": "NetBox ASN range ID"},
                    "name": {"type": "string", "description": "ASN range name (alternative to ID)"}
                }
            }
        },
        {
            "name": "search_aggregates",
            "description": "Search for IP address aggregates",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "prefix": {"type": "string", "description": "Aggregate prefix (e.g., '10.0.0.0/8')"},
                    "rir": {"type": "string", "description": "Regional Internet Registry"},
                    "family": {"type": "integer", "description": "IP family (4 or 6)"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "search_fhrp_groups",
            "description": "Search for FHRP (First Hop Redundancy Protocol) groups",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Group name (partial match)"},
                    "protocol": {"type": "string", "description": "FHRP protocol (hsrp, vrrp, glbp, carp)"},
                    "group_id": {"type": "integer", "description": "Group ID"},
                    "auth_type": {"type": "string", "description": "Authentication type"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_aggregate_details",
            "description": "Get detailed information about a specific aggregate",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "aggregate_id": {"type": "integer", "description": "NetBox aggregate ID"},
                    "prefix": {"type": "string", "description": "Aggregate prefix (alternative to ID)"}
                }
            }
        },
        {
            "name": "search_ip_ranges",
            "description": "Search for IP address ranges",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "start_address": {"type": "string", "description": "Range start address"},
                    "end_address": {"type": "string", "description": "Range end address"},
                    "vrf": {"type": "string", "description": "VRF name"},
                    "role": {"type": "string", "description": "IP range role"},
                    "status": {"type": "string", "description": "IP range status"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "search_fhrp_group_assignments",
            "description": "Search for FHRP group assignments to interfaces",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "group_id": {"type": "integer", "description": "FHRP group ID"},
                    "interface_id": {"type": "integer", "description": "Interface ID"},
                    "priority": {"type": "integer", "description": "Assignment priority"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_ip_range_details",
            "description": "Get detailed information about a specific IP range",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "range_id": {"type": "integer", "description": "NetBox IP range ID"},
                    "start_address": {"type": "string", "description": "Range start address (when combined with end_address)"},
                    "end_address": {"type": "string", "description": "Range end address (when combined with start_address)"}
                }
            }
        },
        {
            "name": "search_rirs",
            "description": "Search for Regional Internet Registries (RIRs)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "RIR name (partial match)"},
                    "slug": {"type": "string", "description": "RIR slug"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "search_route_targets",
            "description": "Search for BGP route targets",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Route target name (partial match)"},
                    "description": {"type": "string", "description": "Description (partial match)"},
                    "tenant": {"type": "string", "description": "Tenant name"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_rir_details",
            "description": "Get detailed information about a specific RIR",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "rir_id": {"type": "integer", "description": "NetBox RIR ID"},
                    "name": {"type": "string", "description": "RIR name (alternative to ID)"},
                    "slug": {"type": "string", "description": "RIR slug (alternative to ID)"}
                }
            }
        },
        {
            "name": "search_ipam_roles",
            "description": "Search for IPAM roles (prefix/VLAN roles)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Role name (partial match)"},
                    "slug": {"type": "string", "description": "Role slug"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "search_services",
            "description": "Search for network services",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Service name (partial match)"},
                    "device_id": {"type": "integer", "description": "Device ID"},
                    "virtual_machine_id": {"type": "integer", "description": "Virtual machine ID"},
                    "protocol": {"type": "string", "description": "Protocol (tcp, udp, sctp)"},
                    "ports": {"type": "string", "description": "Port numbers or ranges"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_ipam_role_details",
            "description": "Get detailed information about a specific IPAM role",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "role_id": {"type": "integer", "description": "NetBox IPAM role ID"},
                    "name": {"type": "string", "description": "Role name (alternative to ID)"},
                    "slug": {"type": "string", "description": "Role slug (alternative to ID)"}
                }
            }
        },
        {
            "name": "search_vrfs",
            "description": "Search for Virtual Routing and Forwarding instances (VRFs)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "VRF name (partial match)"},
                    "rd": {"type": "string", "description": "Route distinguisher"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "search_service_templates",
            "description": "Search for service templates",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Template name (partial match)"},
                    "protocol": {"type": "string", "description": "Protocol (tcp, udp, sctp)"},
                    "ports": {"type": "string", "description": "Port numbers or ranges"},
                    "description": {"type": "string", "description": "Description (partial match)"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_vrf_details",
            "description": "Get detailed information about a specific VRF",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "vrf_id": {"type": "integer", "description": "NetBox VRF ID"},
                    "name": {"type": "string", "description": "VRF name (alternative to ID)"},
                    "rd": {"type": "string", "description": "Route distinguisher (alternative to ID)"}
                }
            }
        },
        {
            "name": "search_vlan_groups",
            "description": "Search for VLAN groups",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "VLAN group name (partial match)"},
                    "slug": {"type": "string", "description": "VLAN group slug"},
                    "site": {"type": "string", "description": "Filter by site"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_vlan_group_details",
            "description": "Get detailed information about a specific VLAN group",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "group_id": {"type": "integer", "description": "NetBox VLAN group ID"},
                    "name": {"type": "string", "description": "VLAN group name (alternative to ID)"},
                    "slug": {"type": "string", "description": "VLAN group slug (alternative to ID)"}
                }
            }
        },
        {
            "name": "search_site_groups",
            "description": "Search for site groups in NetBox",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Site group name (partial match)"},
                    "slug": {"type": "string", "description": "Site group slug"},
                    "parent": {"type": "string", "description": "Parent site group name"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_site_group_details",
            "description": "Get detailed information about a specific site group",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "group_id": {"type": "integer", "description": "NetBox site group ID"},
                    "name": {"type": "string", "description": "Site group name (alternative to ID)"},
                    "slug": {"type": "string", "description": "Site group slug (alternative to ID)"}
                }
            }
        },
        {
            "name": "search_regions",
            "description": "Search for regions in NetBox",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Region name (partial match)"},
                    "slug": {"type": "string", "description": "Region slug"},
                    "parent": {"type": "string", "description": "Parent region name"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_region_details",
            "description": "Get detailed information about a specific region",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "region_id": {"type": "integer", "description": "NetBox region ID"},
                    "name": {"type": "string", "description": "Region name (alternative to ID)"},
                    "slug": {"type": "string", "description": "Region slug (alternative to ID)"}
                }
            }
        },
        {
            "name": "search_tenants",
            "description": "Search for tenants in NetBox",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Tenant name (partial match)"},
                    "slug": {"type": "string", "description": "Tenant slug"},
                    "group": {"type": "string", "description": "Tenant group name"},
                    "description": {"type": "string", "description": "Description (partial match)"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_tenant_details",
            "description": "Get detailed information about a specific tenant",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "tenant_id": {"type": "integer", "description": "NetBox tenant ID"},
                    "name": {"type": "string", "description": "Tenant name (alternative to ID)"},
                    "slug": {"type": "string", "description": "Tenant slug (alternative to ID)"}
                }
            }
        },
        {
            "name": "search_tenant_groups",
            "description": "Search for tenant groups in NetBox",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Tenant group name (partial match)"},
                    "slug": {"type": "string", "description": "Tenant group slug"},
                    "parent": {"type": "string", "description": "Parent group name"},
                    "description": {"type": "string", "description": "Description (partial match)"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_tenant_group_details",
            "description": "Get detailed information about a specific tenant group",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "group_id": {"type": "integer", "description": "NetBox tenant group ID"},
                    "name": {"type": "string", "description": "Tenant group name (alternative to ID)"},
                    "slug": {"type": "string", "description": "Tenant group slug (alternative to ID)"}
                }
            }
        },
        {
            "name": "search_contacts",
            "description": "Search for contacts in NetBox",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Contact name (partial match)"},
                    "email": {"type": "string", "description": "Email address (partial match)"},
                    "group": {"type": "string", "description": "Contact group name"},
                    "title": {"type": "string", "description": "Contact title (partial match)"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_contact_details",
            "description": "Get detailed information about a specific contact",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "contact_id": {"type": "integer", "description": "NetBox contact ID"},
                    "name": {"type": "string", "description": "Contact name (alternative to ID)"},
                    "email": {"type": "string", "description": "Email address (alternative to ID)"}
                }
            }
        },
        {
            "name": "search_contact_groups",
            "description": "Search for contact groups in NetBox",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Contact group name (partial match)"},
                    "slug": {"type": "string", "description": "Contact group slug"},
                    "parent": {"type": "string", "description": "Parent group name"},
                    "description": {"type": "string", "description": "Description (partial match)"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_contact_group_details",
            "description": "Get detailed information about a specific contact group",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "group_id": {"type": "integer", "description": "NetBox contact group ID"},
                    "name": {"type": "string", "description": "Contact group name (alternative to ID)"},
                    "slug": {"type": "string", "description": "Contact group slug (alternative to ID)"}
                }
            }
        },
        {
            "name": "search_contact_roles",
            "description": "Search for contact roles in NetBox",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Contact role name (partial match)"},
                    "slug": {"type": "string", "description": "Contact role slug"},
                    "description": {"type": "string", "description": "Description (partial match)"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_contact_role_details",
            "description": "Get detailed information about a specific contact role",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "role_id": {"type": "integer", "description": "NetBox contact role ID"},
                    "name": {"type": "string", "description": "Contact role name (alternative to ID)"},
                    "slug": {"type": "string", "description": "Contact role slug (alternative to ID)"}
                }
            }
        },
        {
            "name": "search_virtual_machines",
            "description": "Search for virtual machines in NetBox",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "VM name (partial match)"},
                    "cluster": {"type": "string", "description": "Cluster name"},
                    "site": {"type": "string", "description": "Site name"},
                    "status": {"type": "string", "description": "VM status"},
                    "role": {"type": "string", "description": "VM role"},
                    "platform": {"type": "string", "description": "Platform name"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_virtual_machine_details",
            "description": "Get detailed information about a specific virtual machine",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "vm_id": {"type": "integer", "description": "NetBox VM ID"},
                    "name": {"type": "string", "description": "VM name (alternative to ID)"}
                }
            }
        },
        {
            "name": "search_clusters",
            "description": "Search for virtualization clusters in NetBox",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Cluster name (partial match)"},
                    "type": {"type": "string", "description": "Cluster type"},
                    "group": {"type": "string", "description": "Cluster group"},
                    "site": {"type": "string", "description": "Site name"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_cluster_details",
            "description": "Get detailed information about a specific cluster",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "cluster_id": {"type": "integer", "description": "NetBox cluster ID"},
                    "name": {"type": "string", "description": "Cluster name (alternative to ID)"}
                }
            }
        },
        {
            "name": "search_manufacturers",
            "description": "Search for device manufacturers in NetBox",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Manufacturer name (partial match)"},
                    "slug": {"type": "string", "description": "Manufacturer slug"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "search_platforms",
            "description": "Search for device platforms in NetBox",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Platform name (partial match)"},
                    "slug": {"type": "string", "description": "Platform slug"},
                    "manufacturer": {"type": "string", "description": "Manufacturer name"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "search_cables",
            "description": "Search for cables in NetBox",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "description": "Cable label (partial match)"},
                    "type": {"type": "string", "description": "Cable type"},
                    "status": {"type": "string", "description": "Cable status"},
                    "color": {"type": "string", "description": "Cable color"},
                    "device": {"type": "string", "description": "Connected device name"},
                    "site": {"type": "string", "description": "Site name"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "get_cable_details",
            "description": "Get detailed information about a specific cable",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "cable_id": {"type": "integer", "description": "NetBox cable ID"}
                }
            }
        },
        {
            "name": "search_providers",
            "description": "Search for circuit providers in NetBox", 
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Provider name (partial match)"},
                    "slug": {"type": "string", "description": "Provider slug"},
                    "asn": {"type": "integer", "description": "Provider ASN"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "search_circuit_types",
            "description": "Search for circuit types in NetBox",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Circuit type name (partial match)"},
                    "slug": {"type": "string", "description": "Circuit type slug"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        },
        {
            "name": "search_tags",
            "description": "Search for tags in NetBox",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Tag name (partial match)"},
                    "slug": {"type": "string", "description": "Tag slug"},
                    "color": {"type": "string", "description": "Tag color"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                }
            }
        }
    ]

def get_mcp_prompts():
    """Return MCP prompt definitions"""
    return [
        {
            "name": "device-overview",
            "description": "Get an overview of devices in NetBox",
            "arguments": [
                {
                    "name": "site",
                    "description": "Optional site name to filter devices",
                    "required": False
                }
            ]
        },
        {
            "name": "site-summary",
            "description": "Get a comprehensive summary of a specific site",
            "arguments": [
                {
                    "name": "site_name",
                    "description": "Name of the site to summarize",
                    "required": True
                }
            ]
        },
        {
            "name": "ip-management",
            "description": "Explore IP address management and available subnets",
            "arguments": [
                {
                    "name": "prefix",
                    "description": "Optional network prefix to focus on (e.g., '10.0.0.0/24')",
                    "required": False
                }
            ]
        },
        {
            "name": "device-troubleshoot",
            "description": "Troubleshoot connectivity and interface issues for a device",
            "arguments": [
                {
                    "name": "device_name",
                    "description": "Name or partial name of the device to troubleshoot",
                    "required": True
                }
            ]
        },
        {
            "name": "network-infrastructure",
            "description": "Analyze network infrastructure including VLANs, circuits, and racks",
            "arguments": [
                {
                    "name": "focus_area",
                    "description": "Area to focus on: 'vlans', 'circuits', 'racks', or 'all'",
                    "required": False
                }
            ]
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
                        "tools": {},
                        "prompts": {}
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
        
        elif method == 'prompts/list':
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "prompts": get_mcp_prompts()
                }
            }
        
        elif method == 'prompts/get':
            prompt_name = params.get('name')
            if not prompt_name:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32602,
                        "message": "Missing required parameter: name"
                    }
                }
            
            # Find the requested prompt
            prompts = get_mcp_prompts()
            prompt = next((p for p in prompts if p['name'] == prompt_name), None)
            
            if not prompt:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32602,
                        "message": f"Prompt not found: {prompt_name}"
                    }
                }
            
            # Generate prompt content based on the prompt type
            prompt_content = generate_prompt_content(prompt_name, params.get('arguments', {}))
            
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "description": prompt['description'],
                    "messages": prompt_content
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

def generate_prompt_content(prompt_name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate content for MCP prompts"""
    
    if prompt_name == "device-overview":
        site_filter = arguments.get('site', '')
        site_text = f" at site '{site_filter}'" if site_filter else ""
        return [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": f"Please provide an overview of all devices{site_text} in NetBox. Include device counts by type and role, and highlight any important status information."
                }
            }
        ]
    
    elif prompt_name == "site-summary":
        site_name = arguments.get('site_name', '')
        return [
            {
                "role": "user", 
                "content": {
                    "type": "text",
                    "text": f"Please provide a comprehensive summary of the '{site_name}' site in NetBox. Include details about devices, racks, IP allocations, and any other relevant infrastructure information."
                }
            }
        ]
    
    elif prompt_name == "ip-management":
        prefix = arguments.get('prefix', '')
        prefix_text = f" for the {prefix} network" if prefix else ""
        return [
            {
                "role": "user",
                "content": {
                    "type": "text", 
                    "text": f"Help me explore IP address management in NetBox{prefix_text}. Show me available prefixes, IP utilization, and suggest any optimization opportunities."
                }
            }
        ]
    
    elif prompt_name == "device-troubleshoot":
        device_name = arguments.get('device_name', '')
        return [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": f"Help me troubleshoot connectivity and interface issues for device '{device_name}'. Check the device details, interface status, IP assignments, and identify any potential problems."
                }
            }
        ]
    
    elif prompt_name == "network-infrastructure":
        focus_area = arguments.get('focus_area', 'all')
        focus_text = f"focusing on {focus_area}" if focus_area != 'all' else "covering all areas"
        return [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": f"Analyze the network infrastructure in NetBox, {focus_text}. Provide insights about VLANs, circuits, racks, and their utilization patterns."
                }
            }
        ]
    
    else:
        return [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": f"Unknown prompt: {prompt_name}"
                }
            }
        ]

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
        "search_racks": search_racks,
        "get_rack_details": get_rack_details,
        "search_rack_reservations": search_rack_reservations,
        "get_rack_reservation_details": get_rack_reservation_details,
        "search_rack_roles": search_rack_roles,
        "search_rack_types": search_rack_types,
        "search_device_bays": search_device_bays,
        "get_device_bay_details": get_device_bay_details,
        "search_device_bay_templates": search_device_bay_templates,
        "get_device_bay_template_details": get_device_bay_template_details,
        "search_device_roles": search_device_roles,
        "get_device_role_details": get_device_role_details,
        "search_device_types": search_device_types,
        "get_device_type_details": get_device_type_details,
        "search_vlan_translation_policies": search_vlan_translation_policies,
        "search_vlan_translation_rules": search_vlan_translation_rules,
        "search_fhrp_groups": search_fhrp_groups,
        "search_fhrp_group_assignments": search_fhrp_group_assignments,
        "search_route_targets": search_route_targets,
        "search_services": search_services,
        "search_service_templates": search_service_templates,
        "search_asns": search_asns,
        "get_asn_details": get_asn_details,
        "search_asn_ranges": search_asn_ranges,
        "get_asn_range_details": get_asn_range_details,
        "search_aggregates": search_aggregates,
        "get_aggregate_details": get_aggregate_details,
        "search_ip_ranges": search_ip_ranges,
        "get_ip_range_details": get_ip_range_details,
        "search_rirs": search_rirs,
        "get_rir_details": get_rir_details,
        "search_ipam_roles": search_ipam_roles,
        "get_ipam_role_details": get_ipam_role_details,
        "search_vrfs": search_vrfs,
        "get_vrf_details": get_vrf_details,
        "search_vlan_groups": search_vlan_groups,
        "get_vlan_group_details": get_vlan_group_details,
        "search_site_groups": search_site_groups,
        "get_site_group_details": get_site_group_details,
        "search_regions": search_regions,
        "get_region_details": get_region_details,
        "search_tenants": search_tenants,
        "get_tenant_details": get_tenant_details,
        "search_tenant_groups": search_tenant_groups,
        "get_tenant_group_details": get_tenant_group_details,
        "search_contacts": search_contacts,
        "get_contact_details": get_contact_details,
        "search_contact_groups": search_contact_groups,
        "get_contact_group_details": get_contact_group_details,
        "search_contact_roles": search_contact_roles,
        "get_contact_role_details": get_contact_role_details,
        "search_virtual_machines": search_virtual_machines,
        "get_virtual_machine_details": get_virtual_machine_details,
        "search_clusters": search_clusters,
        "get_cluster_details": get_cluster_details,
        "search_manufacturers": search_manufacturers,
        "search_platforms": search_platforms,
        "search_cables": search_cables,
        "get_cable_details": get_cable_details,
        "search_providers": search_providers,
        "search_circuit_types": search_circuit_types,
        "search_tags": search_tags
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
    
    # Check for empty results
    empty_check = check_empty_results(result, "devices")
    if empty_check:
        return empty_check
    
    devices = result.get("results", [])
    count = result.get("count", 0)
    
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
    
    # Check for empty results
    empty_check = check_empty_results(result, "prefixes")
    if empty_check:
        return empty_check
    
    prefixes = result.get("results", [])
    count = result.get("count", 0)
    
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
    
    # Check for empty results
    empty_check = check_empty_results(result, "VLANs")
    if empty_check:
        return empty_check
    
    vlans = result.get("results", [])
    count = result.get("count", 0)
    
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
    
    # Check for empty results
    empty_check = check_empty_results(result, "circuits")
    if empty_check:
        return empty_check
    
    circuits = result.get("results", [])
    count = result.get("count", 0)
    
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
    
    # Check for empty results
    empty_check = check_empty_results(result, "racks")
    if empty_check:
        return empty_check
    
    racks = result.get("results", [])
    count = result.get("count", 0)
    
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

async def get_rack_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed rack information"""
    rack_id = args.get("rack_id")
    rack_name = args.get("rack_name")
    
    if not rack_id and not rack_name:
        return [{"type": "text", "text": "Either rack_id or rack_name must be provided"}]
    
    if rack_name and not rack_id:
        search_result = await netbox_client.get("dcim/racks/", {"name": rack_name})
        racks = search_result.get("results", [])
        if not racks:
            return [{"type": "text", "text": f"Rack '{rack_name}' not found"}]
        rack_id = racks[0]["id"]
    
    rack = await netbox_client.get(f"dcim/racks/{rack_id}/")
    
    site_name = rack.get("site", {}).get("name", "Unknown")
    location = rack.get("location", {}).get("name", "No location") if rack.get("location") else "No location"
    status = rack.get("status", {}).get("label", "Unknown")
    role = rack.get("role", {}).get("name", "No role") if rack.get("role") else "No role"
    rack_type = rack.get("type", {}).get("model", "No type") if rack.get("type") else "No type"
    manufacturer = rack.get("type", {}).get("manufacturer", {}).get("name", "Unknown") if rack.get("type", {}).get("manufacturer") else "Unknown"
    
    output = f"# Rack Details: {rack['name']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- ID: {rack['id']}\n"
    output += f"- Name: {rack['name']}\n"
    output += f"- Status: {status}\n"
    output += f"- Site: {site_name}\n"
    output += f"- Location: {location}\n"
    output += f"- Role: {role}\n\n"
    
    output += f"**Physical Specifications:**\n"
    output += f"- Height: {rack.get('u_height', 'Unknown')}U\n"
    output += f"- Type: {rack_type}\n"
    output += f"- Manufacturer: {manufacturer}\n"
    output += f"- Width: {rack.get('width', {}).get('label', 'Unknown') if rack.get('width') else 'Unknown'}\n"
    output += f"- Depth: {rack.get('depth_mm', 'Unknown')}mm\n\n"
    
    if rack.get("description"):
        output += f"**Description:**\n{rack['description']}\n\n"
    
    if rack.get("comments"):
        output += f"**Comments:**\n{rack['comments']}\n\n"
    
    # Get rack utilization info
    try:
        elevation = await netbox_client.get(f"dcim/racks/{rack_id}/elevation/")
        if elevation:
            output += f"**Utilization:**\n"
            used_units = sum(1 for unit in elevation if unit.get("device"))
            total_units = rack.get("u_height", 0)
            if total_units > 0:
                utilization = (used_units / total_units) * 100
                output += f"- Used Units: {used_units}/{total_units} ({utilization:.1f}%)\n"
    except Exception:
        # Elevation endpoint might not be available or accessible
        pass
    
    return [{"type": "text", "text": output}]

async def search_rack_reservations(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for rack reservations"""
    params = {"limit": args.get("limit", 10)}
    
    if "rack" in args:
        params["rack"] = args["rack"]
    if "user" in args:
        params["user"] = args["user"]
    if "description" in args:
        params["description__icontains"] = args["description"]
    
    result = await netbox_client.get("dcim/rack-reservations/", params)
    
    # Check for empty results
    empty_check = check_empty_results(result, "rack reservations")
    if empty_check:
        return empty_check
    
    reservations = result.get("results", [])
    count = result.get("count", 0)
    
    output = f"Found {count} rack reservations:\n\n"
    for reservation in reservations:
        rack_name = reservation.get("rack", {}).get("name", "Unknown")
        user = reservation.get("user", {}).get("username", "Unknown")
        units = reservation.get("units", [])
        created = reservation.get("created", "Unknown")
        
        output += f"• **Reservation ID: {reservation['id']}**\n"
        output += f"  - Rack: {rack_name}\n"
        output += f"  - User: {user}\n"
        output += f"  - Units: {', '.join(map(str, units)) if units else 'No units specified'}\n"
        output += f"  - Created: {created[:10] if created != 'Unknown' else 'Unknown'}\n"
        
        if reservation.get("description"):
            output += f"  - Description: {reservation['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def get_rack_reservation_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed rack reservation information"""
    reservation_id = args.get("reservation_id")
    
    if not reservation_id:
        return [{"type": "text", "text": "reservation_id must be provided"}]
    
    try:
        reservation = await netbox_client.get(f"dcim/rack-reservations/{reservation_id}/")
    except Exception as e:
        return [{"type": "text", "text": f"Rack reservation with ID {reservation_id} not found"}]
    
    rack_name = reservation.get("rack", {}).get("name", "Unknown")
    rack_id = reservation.get("rack", {}).get("id", "Unknown")
    user = reservation.get("user", {}).get("username", "Unknown")
    units = reservation.get("units", [])
    created = reservation.get("created", "Unknown")
    
    output = f"# Rack Reservation Details: {reservation['id']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- ID: {reservation['id']}\n"
    output += f"- Rack: {rack_name} (ID: {rack_id})\n"
    output += f"- User: {user}\n"
    output += f"- Created: {created}\n\n"
    
    if units:
        output += f"**Reserved Units:**\n"
        units.sort()
        output += f"- Units: {', '.join(map(str, units))}\n"
        output += f"- Total Units Reserved: {len(units)}\n\n"
    
    if reservation.get("description"):
        output += f"**Description:**\n{reservation['description']}\n\n"
    
    return [{"type": "text", "text": output}]

async def search_rack_roles(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for rack roles"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "slug" in args:
        params["slug"] = args["slug"]
    
    result = await netbox_client.get("dcim/rack-roles/", params)
    
    # Check for empty results
    empty_check = check_empty_results(result, "rack roles")
    if empty_check:
        return empty_check
    
    roles = result.get("results", [])
    count = result.get("count", 0)
    
    output = f"Found {count} rack roles:\n\n"
    for role in roles:
        color = role.get("color", "Unknown")
        
        output += f"• **{role['name']}** (ID: {role['id']})\n"
        output += f"  - Slug: {role['slug']}\n"
        output += f"  - Color: #{color}\n"
        
        if role.get("description"):
            output += f"  - Description: {role['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def search_rack_types(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for rack types"""
    params = {"limit": args.get("limit", 10)}
    
    if "model" in args:
        params["model__icontains"] = args["model"]
    if "manufacturer" in args:
        params["manufacturer"] = args["manufacturer"]
    if "slug" in args:
        params["slug"] = args["slug"]
    if "u_height" in args:
        params["u_height"] = args["u_height"]
    
    result = await netbox_client.get("dcim/rack-types/", params)
    
    # Check for empty results
    empty_check = check_empty_results(result, "rack types")
    if empty_check:
        return empty_check
    
    rack_types = result.get("results", [])
    count = result.get("count", 0)
    
    output = f"Found {count} rack types:\n\n"
    for rack_type in rack_types:
        manufacturer = rack_type.get("manufacturer", {}).get("name", "Unknown")
        
        output += f"• **{rack_type['model']}** (ID: {rack_type['id']})\n"
        output += f"  - Manufacturer: {manufacturer}\n"
        output += f"  - Slug: {rack_type['slug']}\n"
        output += f"  - Height: {rack_type.get('u_height', 'Unknown')}U\n"
        output += f"  - Width: {rack_type.get('width', {}).get('label', 'Unknown')}\n"
        output += f"  - Depth: {rack_type.get('depth_mm', 'Unknown')}mm\n"
        
        if rack_type.get("description"):
            output += f"  - Description: {rack_type['description']}\n"
        
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
    
    # Check for empty results
    empty_check = check_empty_results(result, "sites")
    if empty_check:
        return empty_check
    
    sites = result.get("results", [])
    count = result.get("count", 0)
    
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
    
    # Check for empty results
    empty_check = check_empty_results(result, "IP addresses")
    if empty_check:
        return empty_check
    
    ips = result.get("results", [])
    count = result.get("count", 0)
    
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

async def search_device_bays(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for device bays"""
    params = {"limit": args.get("limit", 10)}
    
    # Handle device filtering by ID or name
    device_id = args.get("device_id")
    device_name = args.get("device_name")
    
    if device_name and not device_id:
        search_result = await netbox_client.get("dcim/devices/", {"name": device_name})
        devices = search_result.get("results", [])
        if not devices:
            return [{"type": "text", "text": f"Device '{device_name}' not found"}]
        device_id = devices[0]["id"]
    
    if device_id:
        params["device_id"] = device_id
    if "name" in args:
        params["name__icontains"] = args["name"]
    
    result = await netbox_client.get("dcim/device-bays/", params)
    
    # Check for empty results
    empty_check = check_empty_results(result, "device bays")
    if empty_check:
        return empty_check
    
    bays = result.get("results", [])
    count = result.get("count", 0)
    
    output = f"Found {count} device bays:\n\n"
    for bay in bays:
        device_name = bay.get("device", {}).get("name", "Unknown")
        installed_device = bay.get("installed_device")
        
        output += f"• **{bay['name']}** (ID: {bay['id']})\n"
        output += f"  - Device: {device_name}\n"
        output += f"  - Label: {bay.get('label', 'N/A')}\n"
        
        if installed_device:
            output += f"  - Installed Device: {installed_device.get('name', 'Unknown')}\n"
        else:
            output += f"  - Status: Empty\n"
        
        if bay.get("description"):
            output += f"  - Description: {bay['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def get_device_bay_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed device bay information"""
    bay_id = args.get("bay_id")
    device_id = args.get("device_id")
    bay_name = args.get("bay_name")
    
    if not bay_id and not (device_id and bay_name):
        return [{"type": "text", "text": "Either bay_id or both device_id and bay_name must be provided"}]
    
    if not bay_id:
        # Search for bay by device and name
        search_result = await netbox_client.get("dcim/device-bays/", {"device_id": device_id, "name": bay_name})
        bays = search_result.get("results", [])
        if not bays:
            return [{"type": "text", "text": f"Device bay '{bay_name}' not found in device ID {device_id}"}]
        bay_id = bays[0]["id"]
    
    bay = await netbox_client.get(f"dcim/device-bays/{bay_id}/")
    
    device_name = bay.get("device", {}).get("name", "Unknown")
    installed_device = bay.get("installed_device")
    
    output = f"# Device Bay Details: {bay['name']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- ID: {bay['id']}\n"
    output += f"- Name: {bay['name']}\n"
    output += f"- Label: {bay.get('label', 'N/A')}\n"
    output += f"- Device: {device_name}\n\n"
    
    if installed_device:
        output += f"**Installed Device:**\n"
        output += f"- Name: {installed_device.get('name', 'Unknown')}\n"
        output += f"- Model: {installed_device.get('device_type', {}).get('model', 'Unknown')}\n"
    else:
        output += f"**Status:** Empty bay\n"
    
    if bay.get("description"):
        output += f"\n**Description:** {bay['description']}\n"
    
    return [{"type": "text", "text": output}]

async def search_device_bay_templates(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for device bay templates"""
    params = {"limit": args.get("limit", 10)}
    
    if "device_type_id" in args:
        params["device_type_id"] = args["device_type_id"]
    if "name" in args:
        params["name__icontains"] = args["name"]
    
    result = await netbox_client.get("dcim/device-bay-templates/", params)
    
    # Check for empty results
    empty_check = check_empty_results(result, "device bay templates")
    if empty_check:
        return empty_check
    
    templates = result.get("results", [])
    count = result.get("count", 0)
    
    output = f"Found {count} device bay templates:\n\n"
    for template in templates:
        device_type = template.get("device_type", {})
        device_type_name = f"{device_type.get('manufacturer', {}).get('name', 'Unknown')} {device_type.get('model', 'Unknown')}"
        
        output += f"• **{template['name']}** (ID: {template['id']})\n"
        output += f"  - Device Type: {device_type_name}\n"
        output += f"  - Label: {template.get('label', 'N/A')}\n"
        
        if template.get("description"):
            output += f"  - Description: {template['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def get_device_bay_template_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed device bay template information"""
    template_id = args.get("template_id")
    
    if not template_id:
        return [{"type": "text", "text": "template_id must be provided"}]
    
    template = await netbox_client.get(f"dcim/device-bay-templates/{template_id}/")
    
    device_type = template.get("device_type", {})
    device_type_name = f"{device_type.get('manufacturer', {}).get('name', 'Unknown')} {device_type.get('model', 'Unknown')}"
    
    output = f"# Device Bay Template Details: {template['name']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- ID: {template['id']}\n"
    output += f"- Name: {template['name']}\n"
    output += f"- Label: {template.get('label', 'N/A')}\n"
    output += f"- Device Type: {device_type_name}\n"
    
    if template.get("description"):
        output += f"\n**Description:** {template['description']}\n"
    
    return [{"type": "text", "text": output}]

async def search_device_roles(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for device roles"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "slug" in args:
        params["slug"] = args["slug"]
    if "color" in args:
        params["color"] = args["color"]
    
    result = await netbox_client.get("dcim/device-roles/", params)
    
    # Check for empty results
    empty_check = check_empty_results(result, "device roles")
    if empty_check:
        return empty_check
    
    roles = result.get("results", [])
    count = result.get("count", 0)
    output = f"Found {count} device roles:\n\n"
    for role in roles:
        output += f"• **{role['name']}** (ID: {role['id']})\n"
        output += f"  - Slug: {role['slug']}\n"
        output += f"  - Color: {role.get('color', 'N/A')}\n"
        output += f"  - VM Role: {'Yes' if role.get('vm_role') else 'No'}\n"
        
        if role.get("description"):
            output += f"  - Description: {role['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def get_device_role_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed device role information"""
    role_id = args.get("role_id")
    role_name = args.get("role_name")
    role_slug = args.get("role_slug")
    
    if not role_id and not role_name and not role_slug:
        return [{"type": "text", "text": "Either role_id, role_name, or role_slug must be provided"}]
    
    if not role_id:
        # Search for role by name or slug
        if role_name:
            search_result = await netbox_client.get("dcim/device-roles/", {"name": role_name})
        else:
            search_result = await netbox_client.get("dcim/device-roles/", {"slug": role_slug})
        
        roles = search_result.get("results", [])
        if not roles:
            identifier = role_name or role_slug
            return [{"type": "text", "text": f"Device role '{identifier}' not found"}]
        role_id = roles[0]["id"]
    
    role = await netbox_client.get(f"dcim/device-roles/{role_id}/")
    
    output = f"# Device Role Details: {role['name']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- ID: {role['id']}\n"
    output += f"- Name: {role['name']}\n"
    output += f"- Slug: {role['slug']}\n"
    output += f"- Color: {role.get('color', 'N/A')}\n"
    output += f"- VM Role: {'Yes' if role.get('vm_role') else 'No'}\n"
    
    if role.get("description"):
        output += f"\n**Description:** {role['description']}\n"
    
    return [{"type": "text", "text": output}]

async def search_device_types(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for device types"""
    params = {"limit": args.get("limit", 10)}
    
    if "model" in args:
        params["model__icontains"] = args["model"]
    if "manufacturer" in args:
        params["manufacturer"] = args["manufacturer"]
    if "slug" in args:
        params["slug"] = args["slug"]
    if "part_number" in args:
        params["part_number__icontains"] = args["part_number"]
    
    result = await netbox_client.get("dcim/device-types/", params)
    
    # Check for empty results
    empty_check = check_empty_results(result, "device types")
    if empty_check:
        return empty_check
    
    device_types = result.get("results", [])
    count = result.get("count", 0)
    
    output = f"Found {count} device types:\n\n"
    for device_type in device_types:
        manufacturer_name = device_type.get("manufacturer", {}).get("name", "Unknown")
        
        output += f"• **{device_type['model']}** (ID: {device_type['id']})\n"
        output += f"  - Manufacturer: {manufacturer_name}\n"
        output += f"  - Slug: {device_type['slug']}\n"
        output += f"  - Part Number: {device_type.get('part_number', 'N/A')}\n"
        output += f"  - Height (U): {device_type.get('u_height', 'N/A')}\n"
        
        if device_type.get("description"):
            output += f"  - Description: {device_type['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def get_device_type_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed device type information"""
    type_id = args.get("type_id")
    model = args.get("model")
    slug = args.get("slug")
    
    if not type_id and not model and not slug:
        return [{"type": "text", "text": "Either type_id, model, or slug must be provided"}]
    
    if not type_id:
        # Search for device type by model or slug
        if model:
            search_result = await netbox_client.get("dcim/device-types/", {"model": model})
        else:
            search_result = await netbox_client.get("dcim/device-types/", {"slug": slug})
        
        device_types = search_result.get("results", [])
        if not device_types:
            identifier = model or slug
            return [{"type": "text", "text": f"Device type '{identifier}' not found"}]
        type_id = device_types[0]["id"]
    
    device_type = await netbox_client.get(f"dcim/device-types/{type_id}/")
    
    manufacturer_name = device_type.get("manufacturer", {}).get("name", "Unknown")
    
    output = f"# Device Type Details: {device_type['model']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- ID: {device_type['id']}\n"
    output += f"- Model: {device_type['model']}\n"
    output += f"- Manufacturer: {manufacturer_name}\n"
    output += f"- Slug: {device_type['slug']}\n"
    output += f"- Part Number: {device_type.get('part_number', 'N/A')}\n\n"
    
    output += f"**Physical Specifications:**\n"
    output += f"- Height (U): {device_type.get('u_height', 'N/A')}\n"
    output += f"- Full Depth: {'Yes' if device_type.get('is_full_depth') else 'No'}\n"
    output += f"- Subdevice Role: {device_type.get('subdevice_role', {}).get('label', 'None') if device_type.get('subdevice_role') else 'None'}\n"
    
    if device_type.get("weight"):
        output += f"- Weight: {device_type['weight']} {device_type.get('weight_unit', {}).get('label', '')}\n"
    
    if device_type.get("description"):
        output += f"\n**Description:** {device_type['description']}\n"
    
    return [{"type": "text", "text": output}]

async def search_vlan_translation_policies(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for VLAN translation policies"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "description" in args:
        params["description__icontains"] = args["description"]
    
    result = await netbox_client.get("ipam/vlan-translation-policies/", params)
    policies = result.get("results", [])
    count = result.get("count", 0)
    
    if not policies:
        return [{"type": "text", "text": "No VLAN translation policies found matching the criteria."}]
    
    output = f"Found {count} VLAN translation policies:\n\n"
    for policy in policies:
        output += f"• **{policy['name']}** (ID: {policy['id']})\n"
        if policy.get("description"):
            output += f"  - Description: {policy['description']}\n"

# New IPAM Tools
async def search_asns(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for Autonomous System Numbers (ASNs)"""
    params = {"limit": args.get("limit", 10)}
    
    if "asn" in args:
        params["asn"] = args["asn"]
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "rir" in args:
        params["rir"] = args["rir"]
    
    result = await netbox_client.get("ipam/asns/", params)
    
    # Check for empty results
    empty_check = check_empty_results(result, "ASNs")
    if empty_check:
        return empty_check
    
    asns = result.get("results", [])
    count = result.get("count", 0)
    
    output = f"Found {count} ASNs:\n\n"
    for asn in asns:
        rir_name = asn.get("rir", {}).get("name", "Unknown") if asn.get("rir") else "No RIR"
        
        output += f"• **AS{asn['asn']}** - {asn.get('name', 'Unnamed')}\n"
        output += f"  - RIR: {rir_name}\n"
        
        if asn.get("description"):
            output += f"  - Description: {asn['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def get_asn_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed information about a specific ASN"""
    asn_id = args.get("asn_id")
    asn_number = args.get("asn")
    
    if not asn_id and not asn_number:
        return [{"type": "text", "text": "Either asn_id or asn must be provided"}]
    
    if asn_number and not asn_id:
        search_result = await netbox_client.get("ipam/asns/", {"asn": asn_number})
        asns = search_result.get("results", [])
        if not asns:
            return [{"type": "text", "text": f"ASN {asn_number} not found"}]
        asn_id = asns[0]["id"]
    
    asn = await netbox_client.get(f"ipam/asns/{asn_id}/")
    rir_name = asn.get("rir", {}).get("name", "Unknown") if asn.get("rir") else "No RIR"
    
    output = f"# ASN Details: AS{asn['asn']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- ASN: {asn['asn']}\n"
    output += f"- Name: {asn.get('name', 'Unnamed')}\n"
    output += f"- RIR: {rir_name}\n"
    
    if asn.get("description"):
        output += f"- Description: {asn['description']}\n"
    
    return [{"type": "text", "text": output}]

async def search_asn_ranges(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for ASN ranges"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "rir" in args:
        params["rir"] = args["rir"]
    if "start" in args:
        params["start"] = args["start"]
    if "end" in args:
        params["end"] = args["end"]
    
    result = await netbox_client.get("ipam/asn-ranges/", params)
    ranges = result.get("results", [])
    count = result.get("count", 0)
    
    if not ranges:
        return [{"type": "text", "text": "No ASN ranges found matching the criteria."}]
    
    output = f"Found {count} ASN ranges:\n\n"
    for asn_range in ranges:
        rir_name = asn_range.get("rir", {}).get("name", "Unknown") if asn_range.get("rir") else "No RIR"
        
        output += f"• **{asn_range['name']}** (AS{asn_range['start']} - AS{asn_range['end']})\n"
        output += f"  - RIR: {rir_name}\n"
        output += f"  - Size: {asn_range['end'] - asn_range['start'] + 1} ASNs\n"
        
        if asn_range.get("description"):
            output += f"  - Description: {asn_range['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def search_vlan_translation_rules(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for VLAN translation rules"""
    params = {"limit": args.get("limit", 10)}
    
    if "policy_id" in args:
        params["policy_id"] = args["policy_id"]
    if "original_vid" in args:
        params["original_vid"] = args["original_vid"]
    if "translated_vid" in args:
        params["translated_vid"] = args["translated_vid"]
    
    result = await netbox_client.get("ipam/vlan-translation-rules/", params)
    rules = result.get("results", [])
    count = result.get("count", 0)
    
    if not rules:
        return [{"type": "text", "text": "No VLAN translation rules found matching the criteria."}]
    
    output = f"Found {count} VLAN translation rules:\n\n"
    for rule in rules:
        policy_name = rule.get("policy", {}).get("name", "Unknown")
        output += f"• **Rule {rule['id']}** - Policy: {policy_name}\n"
        output += f"  - Original VLAN: {rule.get('original_vid', 'N/A')}\n"
        output += f"  - Translated VLAN: {rule.get('translated_vid', 'N/A')}\n"
async def get_asn_range_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed information about a specific ASN range"""
    range_id = args.get("range_id")
    name = args.get("name")
    
    if not range_id and not name:
        return [{"type": "text", "text": "Either range_id or name must be provided"}]
    
    if name and not range_id:
        search_result = await netbox_client.get("ipam/asn-ranges/", {"name": name})
        ranges = search_result.get("results", [])
        if not ranges:
            return [{"type": "text", "text": f"ASN range '{name}' not found"}]
        range_id = ranges[0]["id"]
    
    asn_range = await netbox_client.get(f"ipam/asn-ranges/{range_id}/")
    rir_name = asn_range.get("rir", {}).get("name", "Unknown") if asn_range.get("rir") else "No RIR"
    
    output = f"# ASN Range Details: {asn_range['name']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- Name: {asn_range['name']}\n"
    output += f"- Start ASN: {asn_range['start']}\n"
    output += f"- End ASN: {asn_range['end']}\n"
    output += f"- Size: {asn_range['end'] - asn_range['start'] + 1} ASNs\n"
    output += f"- RIR: {rir_name}\n"
    
    if asn_range.get("description"):
        output += f"- Description: {asn_range['description']}\n"
    
    return [{"type": "text", "text": output}]

async def search_aggregates(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for IP address aggregates"""
    params = {"limit": args.get("limit", 10)}
    
    if "prefix" in args:
        params["prefix"] = args["prefix"]
    if "rir" in args:
        params["rir"] = args["rir"]
    if "family" in args:
        params["family"] = args["family"]
    
    result = await netbox_client.get("ipam/aggregates/", params)
    
    # Check for empty results
    empty_check = check_empty_results(result, "aggregates")
    if empty_check:
        return empty_check
    
    aggregates = result.get("results", [])
    count = result.get("count", 0)
    
    output = f"Found {count} aggregates:\n\n"
    for aggregate in aggregates:
        rir_name = aggregate.get("rir", {}).get("name", "Unknown") if aggregate.get("rir") else "No RIR"
        
        output += f"• **{aggregate['prefix']}**\n"
        output += f"  - RIR: {rir_name}\n"
        output += f"  - Family: IPv{aggregate.get('family', 'Unknown')}\n"
        
        if aggregate.get("description"):
            output += f"  - Description: {aggregate['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def search_fhrp_groups(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for FHRP groups"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "protocol" in args:
        params["protocol"] = args["protocol"]
    if "group_id" in args:
        params["group_id"] = args["group_id"]
    if "auth_type" in args:
        params["auth_type"] = args["auth_type"]
    
    result = await netbox_client.get("ipam/fhrp-groups/", params)
    groups = result.get("results", [])
    count = result.get("count", 0)
    
    if not groups:
        return [{"type": "text", "text": "No FHRP groups found matching the criteria."}]
    
    output = f"Found {count} FHRP groups:\n\n"
    for group in groups:
        protocol = group.get("protocol", {}).get("label", "Unknown") if group.get("protocol") else "Unknown"
        auth_type = group.get("auth_type", {}).get("label", "None") if group.get("auth_type") else "None"
        
        output += f"• **{group['name']}** (ID: {group['id']})\n"
        output += f"  - Protocol: {protocol}\n"
        output += f"  - Group ID: {group.get('group_id', 'N/A')}\n"
        output += f"  - Authentication: {auth_type}\n"
        if group.get("description"):
            output += f"  - Description: {group['description']}\n"

async def get_aggregate_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed information about a specific aggregate"""
    aggregate_id = args.get("aggregate_id")
    prefix = args.get("prefix")
    
    if not aggregate_id and not prefix:
        return [{"type": "text", "text": "Either aggregate_id or prefix must be provided"}]
    
    if prefix and not aggregate_id:
        search_result = await netbox_client.get("ipam/aggregates/", {"prefix": prefix})
        aggregates = search_result.get("results", [])
        if not aggregates:
            return [{"type": "text", "text": f"Aggregate '{prefix}' not found"}]
        aggregate_id = aggregates[0]["id"]
    
    aggregate = await netbox_client.get(f"ipam/aggregates/{aggregate_id}/")
    rir_name = aggregate.get("rir", {}).get("name", "Unknown") if aggregate.get("rir") else "No RIR"
    
    output = f"# Aggregate Details: {aggregate['prefix']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- Prefix: {aggregate['prefix']}\n"
    output += f"- RIR: {rir_name}\n"
    output += f"- Family: IPv{aggregate.get('family', 'Unknown')}\n"
    output += f"- Date Added: {aggregate.get('date_added', 'Unknown')}\n"
    
    if aggregate.get("description"):
        output += f"- Description: {aggregate['description']}\n"
    
    return [{"type": "text", "text": output}]

async def search_ip_ranges(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for IP address ranges"""
    params = {"limit": args.get("limit", 10)}
    
    if "start_address" in args:
        params["start_address"] = args["start_address"]
    if "end_address" in args:
        params["end_address"] = args["end_address"]
    if "vrf" in args:
        params["vrf"] = args["vrf"]
    if "role" in args:
        params["role"] = args["role"]
    if "status" in args:
        params["status"] = args["status"]
    
    result = await netbox_client.get("ipam/ip-ranges/", params)
    ranges = result.get("results", [])
    count = result.get("count", 0)
    
    if not ranges:
        return [{"type": "text", "text": "No IP ranges found matching the criteria."}]
    
    output = f"Found {count} IP ranges:\n\n"
    for ip_range in ranges:
        vrf_name = ip_range.get("vrf", {}).get("name", "Global") if ip_range.get("vrf") else "Global"
        status = ip_range.get("status", {}).get("label", "Unknown")
        role = ip_range.get("role", {}).get("name", "No role") if ip_range.get("role") else "No role"
        
        output += f"• **{ip_range['start_address']} - {ip_range['end_address']}**\n"
        output += f"  - VRF: {vrf_name}\n"
        output += f"  - Status: {status}\n"
        output += f"  - Role: {role}\n"
        output += f"  - Size: {ip_range.get('size', 'Unknown')} addresses\n"
        
        if ip_range.get("description"):
            output += f"  - Description: {ip_range['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def search_fhrp_group_assignments(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for FHRP group assignments"""
    params = {"limit": args.get("limit", 10)}
    
    if "group_id" in args:
        params["group_id"] = args["group_id"]
    if "interface_id" in args:
        params["interface_id"] = args["interface_id"]
    if "priority" in args:
        params["priority"] = args["priority"]
    
    result = await netbox_client.get("ipam/fhrp-group-assignments/", params)
    assignments = result.get("results", [])
    count = result.get("count", 0)
    
    if not assignments:
        return [{"type": "text", "text": "No FHRP group assignments found matching the criteria."}]
    
    output = f"Found {count} FHRP group assignments:\n\n"
    for assignment in assignments:
        group_name = assignment.get("group", {}).get("name", "Unknown")
        interface_name = assignment.get("interface", {}).get("name", "Unknown")
        device_name = assignment.get("interface", {}).get("device", {}).get("name", "Unknown")
        
        output += f"• **Assignment {assignment['id']}**\n"
        output += f"  - Group: {group_name}\n"
        output += f"  - Interface: {interface_name} ({device_name})\n"
        output += f"  - Priority: {assignment.get('priority', 'N/A')}\n"

async def get_ip_range_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed information about a specific IP range"""
    range_id = args.get("range_id")
    start_address = args.get("start_address")
    end_address = args.get("end_address")
    
    if not range_id and not (start_address and end_address):
        return [{"type": "text", "text": "Either range_id or both start_address and end_address must be provided"}]
    
    if start_address and end_address and not range_id:
        search_result = await netbox_client.get("ipam/ip-ranges/", {
            "start_address": start_address,
            "end_address": end_address
        })
        ranges = search_result.get("results", [])
        if not ranges:
            return [{"type": "text", "text": f"IP range '{start_address} - {end_address}' not found"}]
        range_id = ranges[0]["id"]
    
    ip_range = await netbox_client.get(f"ipam/ip-ranges/{range_id}/")
    vrf_name = ip_range.get("vrf", {}).get("name", "Global") if ip_range.get("vrf") else "Global"
    status = ip_range.get("status", {}).get("label", "Unknown")
    role = ip_range.get("role", {}).get("name", "No role") if ip_range.get("role") else "No role"
    
    output = f"# IP Range Details: {ip_range['start_address']} - {ip_range['end_address']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- Start Address: {ip_range['start_address']}\n"
    output += f"- End Address: {ip_range['end_address']}\n"
    output += f"- Size: {ip_range.get('size', 'Unknown')} addresses\n"
    output += f"- VRF: {vrf_name}\n"
    output += f"- Status: {status}\n"
    output += f"- Role: {role}\n"
    
    if ip_range.get("description"):
        output += f"- Description: {ip_range['description']}\n"
    
    return [{"type": "text", "text": output}]

async def search_rirs(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for Regional Internet Registries (RIRs)"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "slug" in args:
        params["slug"] = args["slug"]
    
    result = await netbox_client.get("ipam/rirs/", params)
    rirs = result.get("results", [])
    count = result.get("count", 0)
    
    if not rirs:
        return [{"type": "text", "text": "No RIRs found matching the criteria."}]
    
    output = f"Found {count} RIRs:\n\n"
    for rir in rirs:
        output += f"• **{rir['name']}** ({rir['slug']})\n"
        
        if rir.get("description"):
            output += f"  - Description: {rir['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def search_route_targets(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for route targets"""
async def get_rir_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed information about a specific RIR"""
    rir_id = args.get("rir_id")
    name = args.get("name")
    slug = args.get("slug")
    
    if not rir_id and not name and not slug:
        return [{"type": "text", "text": "Either rir_id, name, or slug must be provided"}]
    
    if not rir_id:
        if name:
            search_result = await netbox_client.get("ipam/rirs/", {"name": name})
        else:
            search_result = await netbox_client.get("ipam/rirs/", {"slug": slug})
        
        rirs = search_result.get("results", [])
        if not rirs:
            identifier = name or slug
            return [{"type": "text", "text": f"RIR '{identifier}' not found"}]
        rir_id = rirs[0]["id"]
    
    rir = await netbox_client.get(f"ipam/rirs/{rir_id}/")
    
    output = f"# RIR Details: {rir['name']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- Name: {rir['name']}\n"
    output += f"- Slug: {rir['slug']}\n"
    
    if rir.get("description"):
        output += f"- Description: {rir['description']}\n"
    
    return [{"type": "text", "text": output}]

async def search_ipam_roles(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for IPAM roles (prefix/VLAN roles)"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "description" in args:
        params["description__icontains"] = args["description"]
    if "tenant" in args:
        params["tenant"] = args["tenant"]
    
    result = await netbox_client.get("ipam/route-targets/", params)
    route_targets = result.get("results", [])
    count = result.get("count", 0)
    
    if not route_targets:
        return [{"type": "text", "text": "No route targets found matching the criteria."}]
    
    output = f"Found {count} route targets:\n\n"
    for rt in route_targets:
        tenant = rt.get("tenant", {}).get("name", "No tenant") if rt.get("tenant") else "No tenant"
        
        output += f"• **{rt['name']}** (ID: {rt['id']})\n"
        output += f"  - Tenant: {tenant}\n"
        if rt.get("description"):
            output += f"  - Description: {rt['description']}\n"
    if "slug" in args:
        params["slug"] = args["slug"]
    
    result = await netbox_client.get("ipam/roles/", params)
    roles = result.get("results", [])
    count = result.get("count", 0)
    
    if not roles:
        return [{"type": "text", "text": "No IPAM roles found matching the criteria."}]
    
    output = f"Found {count} IPAM roles:\n\n"
    for role in roles:
        output += f"• **{role['name']}** ({role['slug']})\n"
        output += f"  - Weight: {role.get('weight', 'Unknown')}\n"
        
        if role.get("description"):
            output += f"  - Description: {role['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def search_services(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for services"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "device_id" in args:
        params["device_id"] = args["device_id"]
    if "virtual_machine_id" in args:
        params["virtual_machine_id"] = args["virtual_machine_id"]
    if "protocol" in args:
        params["protocol"] = args["protocol"]
    if "ports" in args:
        params["ports"] = args["ports"]
    
    result = await netbox_client.get("ipam/services/", params)
    
    # Check for empty results
    empty_check = check_empty_results(result, "services")
    if empty_check:
        return empty_check
    
    services = result.get("results", [])
    count = result.get("count", 0)
    
    output = f"Found {count} services:\n\n"
    for service in services:
        protocol = service.get("protocol", {}).get("label", "Unknown") if service.get("protocol") else "Unknown"
        device_name = service.get("device", {}).get("name", "") if service.get("device") else ""
        vm_name = service.get("virtual_machine", {}).get("name", "") if service.get("virtual_machine") else ""
        host = device_name or vm_name or "No host"
        
        output += f"• **{service['name']}** (ID: {service['id']})\n"
        output += f"  - Protocol: {protocol}\n"
        output += f"  - Ports: {', '.join(map(str, service.get('ports', [])))}\n"
        output += f"  - Host: {host}\n"
        if service.get("description"):
            output += f"  - Description: {service['description']}\n"
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def get_ipam_role_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed information about a specific IPAM role"""
    role_id = args.get("role_id")
    name = args.get("name")
    slug = args.get("slug")
    
    if not role_id and not name and not slug:
        return [{"type": "text", "text": "Either role_id, name, or slug must be provided"}]
    
    if not role_id:
        if name:
            search_result = await netbox_client.get("ipam/roles/", {"name": name})
        else:
            search_result = await netbox_client.get("ipam/roles/", {"slug": slug})
        
        roles = search_result.get("results", [])
        if not roles:
            identifier = name or slug
            return [{"type": "text", "text": f"IPAM role '{identifier}' not found"}]
        role_id = roles[0]["id"]
    
    role = await netbox_client.get(f"ipam/roles/{role_id}/")
    
    output = f"# IPAM Role Details: {role['name']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- Name: {role['name']}\n"
    output += f"- Slug: {role['slug']}\n"
    output += f"- Weight: {role.get('weight', 'Unknown')}\n"
    
    if role.get("description"):
        output += f"- Description: {role['description']}\n"
    
    return [{"type": "text", "text": output}]

async def search_vrfs(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for Virtual Routing and Forwarding instances (VRFs)"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "rd" in args:
        params["rd"] = args["rd"]
    
    result = await netbox_client.get("ipam/vrfs/", params)
    
    # Check for empty results
    empty_check = check_empty_results(result, "VRFs")
    if empty_check:
        return empty_check
    
    vrfs = result.get("results", [])
    count = result.get("count", 0)
    
    output = f"Found {count} VRFs:\n\n"
    for vrf in vrfs:
        output += f"• **{vrf['name']}**\n"
        output += f"  - Route Distinguisher: {vrf.get('rd', 'None')}\n"
        
        if vrf.get("description"):
            output += f"  - Description: {vrf['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def search_service_templates(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for service templates"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "protocol" in args:
        params["protocol"] = args["protocol"]
    if "ports" in args:
        params["ports"] = args["ports"]
    if "description" in args:
        params["description__icontains"] = args["description"]
    
    result = await netbox_client.get("ipam/service-templates/", params)
    
    # Check for empty results
    empty_check = check_empty_results(result, "service templates")
    if empty_check:
        return empty_check
    
    templates = result.get("results", [])
    count = result.get("count", 0)
    
    output = f"Found {count} service templates:\n\n"
    for template in templates:
        protocol = template.get("protocol", {}).get("label", "Unknown") if template.get("protocol") else "Unknown"
        
        output += f"• **{template['name']}** (ID: {template['id']})\n"
        output += f"  - Protocol: {protocol}\n"
        output += f"  - Ports: {', '.join(map(str, template.get('ports', [])))}\n"
        if template.get("description"):
            output += f"  - Description: {template['description']}\n"
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def get_vrf_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed information about a specific VRF"""
    vrf_id = args.get("vrf_id")
    name = args.get("name")
    rd = args.get("rd")
    
    if not vrf_id and not name and not rd:
        return [{"type": "text", "text": "Either vrf_id, name, or rd must be provided"}]
    
    if not vrf_id:
        if name:
            search_result = await netbox_client.get("ipam/vrfs/", {"name": name})
        else:
            search_result = await netbox_client.get("ipam/vrfs/", {"rd": rd})
        
        vrfs = search_result.get("results", [])
        if not vrfs:
            identifier = name or rd
            return [{"type": "text", "text": f"VRF '{identifier}' not found"}]
        vrf_id = vrfs[0]["id"]
    
    try:
        vrf = await netbox_client.get(f"ipam/vrfs/{vrf_id}/")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [{"type": "text", "text": f"VRF with ID {vrf_id} not found"}]
        else:
            raise
    
    output = f"# VRF Details: {vrf['name']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- Name: {vrf['name']}\n"
    output += f"- Route Distinguisher: {vrf.get('rd', 'None')}\n"
    
    if vrf.get("description"):
        output += f"- Description: {vrf['description']}\n"
    
    return [{"type": "text", "text": output}]

async def search_vlan_groups(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for VLAN groups"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "slug" in args:
        params["slug"] = args["slug"]
    if "site" in args:
        params["site"] = args["site"]
    
    result = await netbox_client.get("ipam/vlan-groups/", params)
    
    # Check for empty results
    empty_check = check_empty_results(result, "VLAN groups")
    if empty_check:
        return empty_check
    
    groups = result.get("results", [])
    count = result.get("count", 0)
    
    output = f"Found {count} VLAN groups:\n\n"
    for group in groups:
        site = group.get("site", {}).get("name", "No site") if group.get("site") else "No site"
        
        output += f"• **{group['name']}** ({group['slug']})\n"
        output += f"  - Site: {site}\n"
        
        if group.get("description"):
            output += f"  - Description: {group['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def get_vlan_group_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed information about a specific VLAN group"""
    group_id = args.get("group_id")
    name = args.get("name")
    slug = args.get("slug")
    
    if not group_id and not name and not slug:
        return [{"type": "text", "text": "Either group_id, name, or slug must be provided"}]
    
    if not group_id:
        if name:
            search_result = await netbox_client.get("ipam/vlan-groups/", {"name": name})
        else:
            search_result = await netbox_client.get("ipam/vlan-groups/", {"slug": slug})
        
        groups = search_result.get("results", [])
        if not groups:
            identifier = name or slug
            return [{"type": "text", "text": f"VLAN group '{identifier}' not found"}]
        group_id = groups[0]["id"]
    
    group = await netbox_client.get(f"ipam/vlan-groups/{group_id}/")
    site = group.get("site", {}).get("name", "No site") if group.get("site") else "No site"
    
    output = f"# VLAN Group Details: {group['name']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- Name: {group['name']}\n"
    output += f"- Slug: {group['slug']}\n"
    output += f"- Site: {site}\n"
    
    if group.get("description"):
        output += f"- Description: {group['description']}\n"
    
    return [{"type": "text", "text": output}]

async def search_site_groups(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for site groups"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "slug" in args:
        params["slug"] = args["slug"]
    if "parent" in args:
        params["parent"] = args["parent"]
    
    result = await netbox_client.get("dcim/site-groups/", params)
    groups = result.get("results", [])
    count = result.get("count", 0)
    
    if not groups:
        return [{"type": "text", "text": "No site groups found matching the criteria."}]
    
    output = f"Found {count} site groups:\n\n"
    for group in groups:
        parent_name = group.get("parent", {}).get("name", "No parent") if group.get("parent") else "No parent"
        
        output += f"• **{group['name']}** ({group['slug']})\n"
        output += f"  - ID: {group['id']}\n"
        output += f"  - Parent: {parent_name}\n"
        
        if group.get("description"):
            output += f"  - Description: {group['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def get_site_group_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed information about a specific site group"""
    group_id = args.get("group_id")
    name = args.get("name")
    slug = args.get("slug")
    
    if not group_id and not name and not slug:
        return [{"type": "text", "text": "Either group_id, name, or slug must be provided"}]
    
    if not group_id:
        if name:
            search_result = await netbox_client.get("dcim/site-groups/", {"name": name})
        else:
            search_result = await netbox_client.get("dcim/site-groups/", {"slug": slug})
        
        groups = search_result.get("results", [])
        if not groups:
            identifier = name or slug
            return [{"type": "text", "text": f"Site group '{identifier}' not found"}]
        group_id = groups[0]["id"]
    
    group = await netbox_client.get(f"dcim/site-groups/{group_id}/")
    parent_name = group.get("parent", {}).get("name", "No parent") if group.get("parent") else "No parent"
    
    output = f"# Site Group Details: {group['name']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- ID: {group['id']}\n"
    output += f"- Name: {group['name']}\n"
    output += f"- Slug: {group['slug']}\n"
    output += f"- Parent: {parent_name}\n"
    
    if group.get("description"):
        output += f"- Description: {group['description']}\n"
    
    # Get site count for this group
    try:
        sites_result = await netbox_client.get("dcim/sites/", {"group": group['id'], "limit": 1})
        site_count = sites_result.get("count", 0)
        output += f"- Sites in this group: {site_count}\n"
    except Exception as e:
        logger.warning(f"Failed to retrieve site count for group {group['id']}: {e}")
        # If sites endpoint doesn't support group filter, skip the count
    
    return [{"type": "text", "text": output}]

async def search_regions(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for regions"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "slug" in args:
        params["slug"] = args["slug"]
    if "parent" in args:
        params["parent"] = args["parent"]
    
    result = await netbox_client.get("dcim/regions/", params)
    regions = result.get("results", [])
    count = result.get("count", 0)
    
    if not regions:
        return [{"type": "text", "text": "No regions found matching the criteria."}]
    
    output = f"Found {count} regions:\n\n"
    for region in regions:
        parent_name = region.get("parent", {}).get("name", "No parent") if region.get("parent") else "No parent"
        
        output += f"• **{region['name']}** ({region['slug']})\n"
        output += f"  - ID: {region['id']}\n"
        output += f"  - Parent: {parent_name}\n"
        
        if region.get("description"):
            output += f"  - Description: {region['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def get_region_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed information about a specific region"""
    region_id = args.get("region_id")
    name = args.get("name")
    slug = args.get("slug")
    
    if not region_id and not name and not slug:
        return [{"type": "text", "text": "Either region_id, name, or slug must be provided"}]
    
    if not region_id:
        if name:
            search_result = await netbox_client.get("dcim/regions/", {"name": name})
        else:
            search_result = await netbox_client.get("dcim/regions/", {"slug": slug})
        
        regions = search_result.get("results", [])
        if not regions:
            identifier = name or slug
            return [{"type": "text", "text": f"Region '{identifier}' not found"}]
        region_id = regions[0]["id"]
    
    region = await netbox_client.get(f"dcim/regions/{region_id}/")
    parent_name = region.get("parent", {}).get("name", "No parent") if region.get("parent") else "No parent"
    
    output = f"# Region Details: {region['name']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- ID: {region['id']}\n"
    output += f"- Name: {region['name']}\n"
    output += f"- Slug: {region['slug']}\n"
    output += f"- Parent: {parent_name}\n"
    
    if region.get("description"):
        output += f"- Description: {region['description']}\n"
    
    # Get site count for this region
    try:
        sites_result = await netbox_client.get("dcim/sites/", {"region": region['id'], "limit": 1})
        site_count = sites_result.get("count", 0)
        output += f"- Sites in this region: {site_count}\n"
    except Exception as e:
        logger.warning(f"Failed to retrieve site count for region {region['id']}: {e}")
    
    # Get child regions count
    try:
        children_result = await netbox_client.get("dcim/regions/", {"parent": region['id'], "limit": 1})
        children_count = children_result.get("count", 0)
        output += f"- Child regions: {children_count}\n"
    except Exception as e:
        logger.warning(f"Failed to retrieve child regions count for region {region['id']}: {e}")
    
    return [{"type": "text", "text": output}]

# Tenancy Tools

async def search_tenants(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for tenants"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "slug" in args:
        params["slug"] = args["slug"]
    if "group" in args:
        params["group"] = args["group"]
    if "description" in args:
        params["description__icontains"] = args["description"]
    
    result = await netbox_client.get("tenancy/tenants/", params)
    
    # Check for empty results
    empty_check = check_empty_results(result, "tenants")
    if empty_check:
        return empty_check
    
    tenants = result.get("results", [])
    count = result.get("count", 0)
    
    output = f"Found {count} tenants:\n\n"
    for tenant in tenants:
        group_name = tenant.get("group", {}).get("name", "No group") if tenant.get("group") else "No group"
        
        output += f"• **{tenant['name']}** ({tenant['slug']})\n"
        output += f"  - ID: {tenant['id']}\n"
        output += f"  - Group: {group_name}\n"
        
        if tenant.get("description"):
            output += f"  - Description: {tenant['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def get_tenant_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed information about a specific tenant"""
    tenant_id = args.get("tenant_id")
    name = args.get("name")
    slug = args.get("slug")
    
    if not tenant_id and not name and not slug:
        return [{"type": "text", "text": "Either tenant_id, name, or slug must be provided"}]
    
    if not tenant_id:
        if name:
            search_result = await netbox_client.get("tenancy/tenants/", {"name": name})
        else:
            search_result = await netbox_client.get("tenancy/tenants/", {"slug": slug})
        
        tenants = search_result.get("results", [])
        if not tenants:
            identifier = name or slug
            return [{"type": "text", "text": f"Tenant '{identifier}' not found"}]
        tenant_id = tenants[0]["id"]
    
    tenant = await netbox_client.get(f"tenancy/tenants/{tenant_id}/")
    group_name = tenant.get("group", {}).get("name", "No group") if tenant.get("group") else "No group"
    
    output = f"# Tenant Details: {tenant['name']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- ID: {tenant['id']}\n"
    output += f"- Name: {tenant['name']}\n"
    output += f"- Slug: {tenant['slug']}\n"
    output += f"- Group: {group_name}\n"
    
    if tenant.get("description"):
        output += f"- Description: {tenant['description']}\n"
    
    if tenant.get("comments"):
        output += f"- Comments: {tenant['comments']}\n"
    
    return [{"type": "text", "text": output}]

async def search_tenant_groups(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for tenant groups"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "slug" in args:
        params["slug"] = args["slug"]
    if "parent" in args:
        params["parent"] = args["parent"]
    if "description" in args:
        params["description__icontains"] = args["description"]
    
    result = await netbox_client.get("tenancy/tenant-groups/", params)
    groups = result.get("results", [])
    count = result.get("count", 0)
    
    if not groups:
        return [{"type": "text", "text": "No tenant groups found matching the criteria."}]
    
    output = f"Found {count} tenant groups:\n\n"
    for group in groups:
        parent_name = group.get("parent", {}).get("name", "No parent") if group.get("parent") else "No parent"
        
        output += f"• **{group['name']}** ({group['slug']})\n"
        output += f"  - ID: {group['id']}\n"
        output += f"  - Parent: {parent_name}\n"
        
        if group.get("description"):
            output += f"  - Description: {group['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def get_tenant_group_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed information about a specific tenant group"""
    group_id = args.get("group_id")
    name = args.get("name")
    slug = args.get("slug")
    
    if not group_id and not name and not slug:
        return [{"type": "text", "text": "Either group_id, name, or slug must be provided"}]
    
    if not group_id:
        if name:
            search_result = await netbox_client.get("tenancy/tenant-groups/", {"name": name})
        else:
            search_result = await netbox_client.get("tenancy/tenant-groups/", {"slug": slug})
        
        groups = search_result.get("results", [])
        if not groups:
            identifier = name or slug
            return [{"type": "text", "text": f"Tenant group '{identifier}' not found"}]
        group_id = groups[0]["id"]
    
    group = await netbox_client.get(f"tenancy/tenant-groups/{group_id}/")
    parent_name = group.get("parent", {}).get("name", "No parent") if group.get("parent") else "No parent"
    
    output = f"# Tenant Group Details: {group['name']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- ID: {group['id']}\n"
    output += f"- Name: {group['name']}\n"
    output += f"- Slug: {group['slug']}\n"
    output += f"- Parent: {parent_name}\n"
    
    if group.get("description"):
        output += f"- Description: {group['description']}\n"
    
    # Get tenant count for this group
    try:
        tenants_result = await netbox_client.get("tenancy/tenants/", {"group": group['id'], "limit": 1})
        tenant_count = tenants_result.get("count", 0)
        output += f"- Tenants in this group: {tenant_count}\n"
    except Exception as e:
        logger.warning(f"Failed to retrieve tenant count for group {group['id']}: {e}")
    
    # Get child groups count
    try:
        children_result = await netbox_client.get("tenancy/tenant-groups/", {"parent": group['id'], "limit": 1})
        children_count = children_result.get("count", 0)
        output += f"- Child groups: {children_count}\n"
    except Exception as e:
        logger.warning(f"Failed to retrieve child groups count for group {group['id']}: {e}")
    
    return [{"type": "text", "text": output}]

async def search_contacts(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for contacts"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "email" in args:
        params["email__icontains"] = args["email"]
    if "group" in args:
        params["group"] = args["group"]
    if "title" in args:
        params["title__icontains"] = args["title"]
    
    result = await netbox_client.get("tenancy/contacts/", params)
    
    # Check for empty results
    empty_check = check_empty_results(result, "contacts")
    if empty_check:
        return empty_check
    
    contacts = result.get("results", [])
    count = result.get("count", 0)
    
    output = f"Found {count} contacts:\n\n"
    for contact in contacts:
        group_name = contact.get("group", {}).get("name", "No group") if contact.get("group") else "No group"
        
        output += f"• **{contact['name']}**\n"
        output += f"  - ID: {contact['id']}\n"
        output += f"  - Email: {contact.get('email', 'No email')}\n"
        output += f"  - Group: {group_name}\n"
        
        if contact.get("title"):
            output += f"  - Title: {contact['title']}\n"
        if contact.get("phone"):
            output += f"  - Phone: {contact['phone']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def get_contact_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed information about a specific contact"""
    contact_id = args.get("contact_id")
    name = args.get("name")
    email = args.get("email")
    
    if not contact_id and not name and not email:
        return [{"type": "text", "text": "Either contact_id, name, or email must be provided"}]
    
    if not contact_id:
        if name:
            search_result = await netbox_client.get("tenancy/contacts/", {"name": name})
        else:
            search_result = await netbox_client.get("tenancy/contacts/", {"email": email})
        
        contacts = search_result.get("results", [])
        if not contacts:
            identifier = name or email
            return [{"type": "text", "text": f"Contact '{identifier}' not found"}]
        contact_id = contacts[0]["id"]
    
    contact = await netbox_client.get(f"tenancy/contacts/{contact_id}/")
    group_name = contact.get("group", {}).get("name", "No group") if contact.get("group") else "No group"
    
    output = f"# Contact Details: {contact['name']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- ID: {contact['id']}\n"
    output += f"- Name: {contact['name']}\n"
    output += f"- Email: {contact.get('email', 'No email')}\n"
    output += f"- Group: {group_name}\n"
    
    if contact.get("title"):
        output += f"- Title: {contact['title']}\n"
    if contact.get("phone"):
        output += f"- Phone: {contact['phone']}\n"
    if contact.get("address"):
        output += f"- Address: {contact['address']}\n"
    if contact.get("comments"):
        output += f"- Comments: {contact['comments']}\n"
    
    return [{"type": "text", "text": output}]

async def search_contact_groups(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for contact groups"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "slug" in args:
        params["slug"] = args["slug"]
    if "parent" in args:
        params["parent"] = args["parent"]
    if "description" in args:
        params["description__icontains"] = args["description"]
    
    result = await netbox_client.get("tenancy/contact-groups/", params)
    groups = result.get("results", [])
    count = result.get("count", 0)
    
    if not groups:
        return [{"type": "text", "text": "No contact groups found matching the criteria."}]
    
    output = f"Found {count} contact groups:\n\n"
    for group in groups:
        parent_name = group.get("parent", {}).get("name", "No parent") if group.get("parent") else "No parent"
        
        output += f"• **{group['name']}** ({group['slug']})\n"
        output += f"  - ID: {group['id']}\n"
        output += f"  - Parent: {parent_name}\n"
        
        if group.get("description"):
            output += f"  - Description: {group['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def get_contact_group_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed information about a specific contact group"""
    group_id = args.get("group_id")
    name = args.get("name")
    slug = args.get("slug")
    
    if not group_id and not name and not slug:
        return [{"type": "text", "text": "Either group_id, name, or slug must be provided"}]
    
    if not group_id:
        if name:
            search_result = await netbox_client.get("tenancy/contact-groups/", {"name": name})
        else:
            search_result = await netbox_client.get("tenancy/contact-groups/", {"slug": slug})
        
        groups = search_result.get("results", [])
        if not groups:
            identifier = name or slug
            return [{"type": "text", "text": f"Contact group '{identifier}' not found"}]
        group_id = groups[0]["id"]
    
    group = await netbox_client.get(f"tenancy/contact-groups/{group_id}/")
    parent_name = group.get("parent", {}).get("name", "No parent") if group.get("parent") else "No parent"
    
    output = f"# Contact Group Details: {group['name']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- ID: {group['id']}\n"
    output += f"- Name: {group['name']}\n"
    output += f"- Slug: {group['slug']}\n"
    output += f"- Parent: {parent_name}\n"
    
    if group.get("description"):
        output += f"- Description: {group['description']}\n"
    
    # Get contact count for this group
    try:
        contacts_result = await netbox_client.get("tenancy/contacts/", {"group": group['id'], "limit": 1})
        contact_count = contacts_result.get("count", 0)
        output += f"- Contacts in this group: {contact_count}\n"
    except Exception as e:
        logger.warning(f"Failed to retrieve contact count for group {group['id']}: {e}")
    
    # Get child groups count
    try:
        children_result = await netbox_client.get("tenancy/contact-groups/", {"parent": group['id'], "limit": 1})
        children_count = children_result.get("count", 0)
        output += f"- Child groups: {children_count}\n"
    except Exception as e:
        logger.warning(f"Failed to retrieve child groups count for group {group['id']}: {e}")
    
    return [{"type": "text", "text": output}]

async def search_contact_roles(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for contact roles"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "slug" in args:
        params["slug"] = args["slug"]
    if "description" in args:
        params["description__icontains"] = args["description"]
    
    result = await netbox_client.get("tenancy/contact-roles/", params)
    roles = result.get("results", [])
    count = result.get("count", 0)
    
    if not roles:
        return [{"type": "text", "text": "No contact roles found matching the criteria."}]
    
    output = f"Found {count} contact roles:\n\n"
    for role in roles:
        output += f"• **{role['name']}** ({role['slug']})\n"
        output += f"  - ID: {role['id']}\n"
        
        if role.get("description"):
            output += f"  - Description: {role['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def get_contact_role_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed information about a specific contact role"""
    role_id = args.get("role_id")
    name = args.get("name")
    slug = args.get("slug")
    
    if not role_id and not name and not slug:
        return [{"type": "text", "text": "Either role_id, name, or slug must be provided"}]
    
    if not role_id:
        if name:
            search_result = await netbox_client.get("tenancy/contact-roles/", {"name": name})
        else:
            search_result = await netbox_client.get("tenancy/contact-roles/", {"slug": slug})
        
        roles = search_result.get("results", [])
        if not roles:
            identifier = name or slug
            return [{"type": "text", "text": f"Contact role '{identifier}' not found"}]
        role_id = roles[0]["id"]
    
    role = await netbox_client.get(f"tenancy/contact-roles/{role_id}/")
    
    output = f"# Contact Role Details: {role['name']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- ID: {role['id']}\n"
    output += f"- Name: {role['name']}\n"
    output += f"- Slug: {role['slug']}\n"
    
    if role.get("description"):
        output += f"- Description: {role['description']}\n"
    
    return [{"type": "text", "text": output}]

async def search_virtual_machines(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for virtual machines"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "cluster" in args:
        params["cluster"] = args["cluster"]
    if "site" in args:
        params["site"] = args["site"]
    if "status" in args:
        params["status"] = args["status"]
    if "role" in args:
        params["role"] = args["role"]
    if "platform" in args:
        params["platform"] = args["platform"]
    
    result = await netbox_client.get("virtualization/virtual-machines/", params)
    
    # Check for empty results
    empty_check = check_empty_results(result, "virtual machines")
    if empty_check:
        return empty_check
    
    vms = result.get("results", [])
    
    output = f"# Virtual Machines ({len(vms)} found)\n\n"
    
    for vm in vms:
        cluster_name = vm.get("cluster", {}).get("name", "Unknown") if vm.get("cluster") else "None"
        site_name = vm.get("site", {}).get("name", "Unknown") if vm.get("site") else "None"
        status = vm.get("status", {}).get("label", "Unknown")
        role = vm.get("role", {}).get("name", "None") if vm.get("role") else "None"
        platform = vm.get("platform", {}).get("name", "None") if vm.get("platform") else "None"
        
        output += f"• **{vm['name']}** (ID: {vm['id']})\n"
        output += f"  - Cluster: {cluster_name}\n"
        output += f"  - Site: {site_name}\n"
        output += f"  - Status: {status}\n"
        output += f"  - Role: {role}\n"
        output += f"  - Platform: {platform}\n"
        
        if vm.get("vcpus"):
            output += f"  - vCPUs: {vm['vcpus']}\n"
        if vm.get("memory"):
            output += f"  - Memory: {vm['memory']} MB\n"
        if vm.get("disk"):
            output += f"  - Disk: {vm['disk']} GB\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def get_virtual_machine_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed information about a specific virtual machine"""
    vm_id = args.get("vm_id")
    name = args.get("name")
    
    if not vm_id and not name:
        return [{"type": "text", "text": "Either vm_id or name must be provided"}]
    
    if not vm_id:
        search_result = await netbox_client.get("virtualization/virtual-machines/", {"name": name})
        vms = search_result.get("results", [])
        if not vms:
            return [{"type": "text", "text": f"Virtual machine '{name}' not found"}]
        vm_id = vms[0]["id"]
    
    vm = await netbox_client.get(f"virtualization/virtual-machines/{vm_id}/")
    
    output = f"# Virtual Machine Details: {vm['name']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- ID: {vm['id']}\n"
    output += f"- Name: {vm['name']}\n"
    
    if vm.get("cluster"):
        output += f"- Cluster: {vm['cluster']['name']}\n"
    if vm.get("site"):
        output += f"- Site: {vm['site']['name']}\n"
    if vm.get("status"):
        output += f"- Status: {vm['status']['label']}\n"
    if vm.get("role"):
        output += f"- Role: {vm['role']['name']}\n"
    if vm.get("platform"):
        output += f"- Platform: {vm['platform']['name']}\n"
    
    output += f"\n**Resources:**\n"
    if vm.get("vcpus"):
        output += f"- vCPUs: {vm['vcpus']}\n"
    if vm.get("memory"):
        output += f"- Memory: {vm['memory']} MB\n"
    if vm.get("disk"):
        output += f"- Disk: {vm['disk']} GB\n"
    
    if vm.get("description"):
        output += f"\n**Description:**\n{vm['description']}\n"
    
    if vm.get("comments"):
        output += f"\n**Comments:**\n{vm['comments']}\n"
    
    return [{"type": "text", "text": output}]

async def search_clusters(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for virtualization clusters"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "type" in args:
        params["type"] = args["type"]
    if "group" in args:
        params["group"] = args["group"]
    if "site" in args:
        params["site"] = args["site"]
    
    result = await netbox_client.get("virtualization/clusters/", params)
    
    # Check for empty results
    empty_check = check_empty_results(result, "clusters")
    if empty_check:
        return empty_check
    
    clusters = result.get("results", [])
    
    output = f"# Virtualization Clusters ({len(clusters)} found)\n\n"
    
    for cluster in clusters:
        cluster_type = cluster.get("type", {}).get("name", "Unknown") if cluster.get("type") else "Unknown"
        group_name = cluster.get("group", {}).get("name", "None") if cluster.get("group") else "None"
        site_name = cluster.get("site", {}).get("name", "None") if cluster.get("site") else "None"
        
        output += f"• **{cluster['name']}** (ID: {cluster['id']})\n"
        output += f"  - Type: {cluster_type}\n"
        output += f"  - Group: {group_name}\n"
        output += f"  - Site: {site_name}\n"
        
        if cluster.get("description"):
            output += f"  - Description: {cluster['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def get_cluster_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed information about a specific cluster"""
    cluster_id = args.get("cluster_id")
    name = args.get("name")
    
    if not cluster_id and not name:
        return [{"type": "text", "text": "Either cluster_id or name must be provided"}]
    
    if not cluster_id:
        search_result = await netbox_client.get("virtualization/clusters/", {"name": name})
        clusters = search_result.get("results", [])
        if not clusters:
            return [{"type": "text", "text": f"Cluster '{name}' not found"}]
        cluster_id = clusters[0]["id"]
    
    cluster = await netbox_client.get(f"virtualization/clusters/{cluster_id}/")
    
    output = f"# Cluster Details: {cluster['name']}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- ID: {cluster['id']}\n"
    output += f"- Name: {cluster['name']}\n"
    
    if cluster.get("type"):
        output += f"- Type: {cluster['type']['name']}\n"
    if cluster.get("group"):
        output += f"- Group: {cluster['group']['name']}\n"
    if cluster.get("site"):
        output += f"- Site: {cluster['site']['name']}\n"
    
    if cluster.get("description"):
        output += f"\n**Description:**\n{cluster['description']}\n"
    
    if cluster.get("comments"):
        output += f"\n**Comments:**\n{cluster['comments']}\n"
    
    return [{"type": "text", "text": output}]

async def search_manufacturers(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for device manufacturers"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "slug" in args:
        params["slug"] = args["slug"]
    
    result = await netbox_client.get("dcim/manufacturers/", params)
    
    # Check for empty results
    empty_check = check_empty_results(result, "manufacturers")
    if empty_check:
        return empty_check
    
    manufacturers = result.get("results", [])
    
    output = f"# Device Manufacturers ({len(manufacturers)} found)\n\n"
    
    for manufacturer in manufacturers:
        output += f"• **{manufacturer['name']}** (ID: {manufacturer['id']})\n"
        output += f"  - Slug: {manufacturer['slug']}\n"
        
        if manufacturer.get("description"):
            output += f"  - Description: {manufacturer['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def search_platforms(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for device platforms"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "slug" in args:
        params["slug"] = args["slug"]
    if "manufacturer" in args:
        params["manufacturer"] = args["manufacturer"]
    
    result = await netbox_client.get("dcim/platforms/", params)
    
    # Check for empty results
    empty_check = check_empty_results(result, "platforms")
    if empty_check:
        return empty_check
    
    platforms = result.get("results", [])
    
    output = f"# Device Platforms ({len(platforms)} found)\n\n"
    
    for platform in platforms:
        manufacturer_name = platform.get("manufacturer", {}).get("name", "None") if platform.get("manufacturer") else "None"
        
        output += f"• **{platform['name']}** (ID: {platform['id']})\n"
        output += f"  - Slug: {platform['slug']}\n"
        output += f"  - Manufacturer: {manufacturer_name}\n"
        
        if platform.get("description"):
            output += f"  - Description: {platform['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def search_cables(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for cables"""
    params = {"limit": args.get("limit", 10)}
    
    if "label" in args:
        params["label__icontains"] = args["label"]
    if "type" in args:
        params["type"] = args["type"]
    if "status" in args:
        params["status"] = args["status"]
    if "color" in args:
        params["color"] = args["color"]
    
    result = await netbox_client.get("dcim/cables/", params)
    
    # Check for empty results
    empty_check = check_empty_results(result, "cables")
    if empty_check:
        return empty_check
    
    cables = result.get("results", [])
    
    output = f"# Cables ({len(cables)} found)\n\n"
    
    for cable in cables:
        label = cable.get("label", f"Cable {cable['id']}")
        status = cable.get("status", {}).get("label", "Unknown") if cable.get("status") else "Unknown"
        cable_type = cable.get("type", {}).get("label", "Unknown") if cable.get("type") else "Unknown"
        color = cable.get("color", "None")
        
        output += f"• **{label}** (ID: {cable['id']})\n"
        output += f"  - Type: {cable_type}\n"
        output += f"  - Status: {status}\n"
        output += f"  - Color: {color}\n"
        
        if cable.get("length"):
            output += f"  - Length: {cable['length']} {cable.get('length_unit', {}).get('label', '')}\n"
        
        # Show terminations if available
        if cable.get("a_terminations"):
            output += f"  - A-side connections: {len(cable['a_terminations'])}\n"
        if cable.get("z_terminations"):
            output += f"  - Z-side connections: {len(cable['z_terminations'])}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def get_cable_details(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Get detailed information about a specific cable"""
    cable_id = args.get("cable_id")
    
    if not cable_id:
        return [{"type": "text", "text": "cable_id must be provided"}]
    
    cable = await netbox_client.get(f"dcim/cables/{cable_id}/")
    
    label = cable.get("label", f"Cable {cable['id']}")
    output = f"# Cable Details: {label}\n\n"
    output += f"**Basic Information:**\n"
    output += f"- ID: {cable['id']}\n"
    
    if cable.get("label"):
        output += f"- Label: {cable['label']}\n"
    if cable.get("type"):
        output += f"- Type: {cable['type']['label']}\n"
    if cable.get("status"):
        output += f"- Status: {cable['status']['label']}\n"
    if cable.get("color"):
        output += f"- Color: {cable['color']}\n"
    if cable.get("length"):
        length_unit = cable.get("length_unit", {}).get("label", "") if cable.get("length_unit") else ""
        output += f"- Length: {cable['length']} {length_unit}\n"
    
    if cable.get("description"):
        output += f"\n**Description:**\n{cable['description']}\n"
    
    return [{"type": "text", "text": output}]

async def search_providers(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for circuit providers"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "slug" in args:
        params["slug"] = args["slug"]
    if "asn" in args:
        params["asn"] = args["asn"]
    
    result = await netbox_client.get("circuits/providers/", params)
    providers = result.get("results", [])
    
    if not providers:
        return [{"type": "text", "text": "No providers found matching the criteria"}]
    
    output = f"# Circuit Providers ({len(providers)} found)\n\n"
    
    for provider in providers:
        output += f"• **{provider['name']}** (ID: {provider['id']})\n"
        output += f"  - Slug: {provider['slug']}\n"
        
        if provider.get("asn"):
            output += f"  - ASN: {provider['asn']}\n"
        if provider.get("account"):
            output += f"  - Account: {provider['account']}\n"
        if provider.get("portal_url"):
            output += f"  - Portal URL: {provider['portal_url']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def search_circuit_types(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for circuit types"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "slug" in args:
        params["slug"] = args["slug"]
    
    result = await netbox_client.get("circuits/circuit-types/", params)
    circuit_types = result.get("results", [])
    
    if not circuit_types:
        return [{"type": "text", "text": "No circuit types found matching the criteria"}]
    
    output = f"# Circuit Types ({len(circuit_types)} found)\n\n"
    
    for circuit_type in circuit_types:
        output += f"• **{circuit_type['name']}** (ID: {circuit_type['id']})\n"
        output += f"  - Slug: {circuit_type['slug']}\n"
        
        if circuit_type.get("description"):
            output += f"  - Description: {circuit_type['description']}\n"
        
        output += "\n"
    
    return [{"type": "text", "text": output}]

async def search_tags(args: Dict[str, Any], netbox_client: NetBoxClient) -> List[Dict[str, Any]]:
    """Search for tags"""
    params = {"limit": args.get("limit", 10)}
    
    if "name" in args:
        params["name__icontains"] = args["name"]
    if "slug" in args:
        params["slug"] = args["slug"]
    if "color" in args:
        params["color"] = args["color"]
    
    result = await netbox_client.get("extras/tags/", params)
    tags = result.get("results", [])
    
    if not tags:
        return [{"type": "text", "text": "No tags found matching the criteria"}]
    
    output = f"# Tags ({len(tags)} found)\n\n"
    
    for tag in tags:
        output += f"• **{tag['name']}** (ID: {tag['id']})\n"
        output += f"  - Slug: {tag['slug']}\n"
        output += f"  - Color: {tag['color']}\n"
        
        if tag.get("description"):
            output += f"  - Description: {tag['description']}\n"
        
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