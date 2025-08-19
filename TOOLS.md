# NetBox MCP Tools Reference

This document describes all the tools exposed by the NetBox MCP server for querying your NetBox instance through Claude Desktop.

## Device Management Tools

### search_devices
Search for devices in NetBox with flexible filtering options.

**Parameters:**
- `name` (string, optional): Device name (partial match)
- `site` (string, optional): Site name
- `device_type` (string, optional): Device type
- `role` (string, optional): Device role
- `status` (string, optional): Device status
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of devices with ID, name, site, type, role, and status information.

**Example queries:**
- "Search for devices with 'router' in the name"
- "Find all Cisco devices at the London site"
- "Show me devices with 'active' status"

### get_device_details
Get comprehensive information about a specific device.

**Parameters:**
- `device_id` (integer): NetBox device ID
- `device_name` (string): Device name (alternative to ID)

**Returns:** Detailed device information including basic info, hardware specs, and network configuration.

**Example queries:**
- "Get details for device ID 123"
- "Show me details for router-01"

### get_device_interfaces
Retrieve network interfaces for a specific device.

**Parameters:**
- `device_id` (integer): NetBox device ID
- `device_name` (string): Device name (alternative to ID)
- `interface_type` (string, optional): Filter by interface type
- `enabled` (boolean, optional): Filter by enabled status

**Returns:** List of interfaces with type, enabled status, description, MTU, and cable information.

**Example queries:**
- "Show interfaces for switch-01"
- "Get enabled interfaces for device ID 456"

## Site Management Tools

### get_sites
List and search sites in your NetBox instance.

**Parameters:**
- `name` (string, optional): Site name filter (partial match)
- `region` (string, optional): Region filter
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of sites with ID, name, slug, status, and region information.

**Example queries:**
- "List all sites"
- "Find sites in the Europe region"
- "Search for sites with 'data' in the name"

### get_site_details
Get comprehensive site information including device and rack summaries.

**Parameters:**
- `site_id` (integer): NetBox site ID
- `site_name` (string): Site name (alternative to ID)
- `include_devices` (boolean, optional): Include device summary (default: true)
- `include_racks` (boolean, optional): Include rack summary (default: true)

**Returns:** Detailed site information with device counts by role and rack inventory.

**Example queries:**
- "Get full details for the London site"
- "Show me site details for ID 789 without racks"

## IP Address Management Tools

### search_ip_addresses
Search for IP addresses with various filtering options.

**Parameters:**
- `address` (string, optional): IP address or network (partial match)
- `vrf` (string, optional): VRF name
- `status` (string, optional): IP status
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of IP addresses with VRF, status, and assignment information.

**Example queries:**
- "Find IP addresses in 192.168.1.0 network"
- "Search for active IPs in production VRF"

### get_prefixes
Search and list IP prefixes/subnets with advanced filtering.

**Parameters:**
- `prefix` (string, optional): Specific prefix (e.g., '192.168.1.0/24')
- `within` (string, optional): Find prefixes within a larger network
- `family` (integer, optional): IP family (4 or 6)
- `status` (string, optional): Prefix status
- `site` (string, optional): Filter by site
- `vrf` (string, optional): Filter by VRF
- `role` (string, optional): Prefix role
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of prefixes with VRF, status, role, and site information.

**Example queries:**
- "Show me all /24 prefixes"
- "Find prefixes within 10.0.0.0/8"
- "List IPv6 prefixes at the datacenter site"

### get_available_ips
Find available IP addresses within a specific prefix.

**Parameters:**
- `prefix_id` (integer): NetBox prefix ID
- `prefix` (string): Prefix in CIDR notation (alternative to ID)
- `count` (integer, optional): Number of IPs to return (default: 10)

**Returns:** List of available IP addresses within the specified prefix.

**Example queries:**
- "Find available IPs in 192.168.1.0/24"
- "Show me 5 available addresses in prefix ID 123"

## Network Infrastructure Tools

### search_vlans
Search for VLANs across your network infrastructure.

**Parameters:**
- `vid` (integer, optional): VLAN ID
- `name` (string, optional): VLAN name (partial match)
- `site` (string, optional): Filter by site
- `group` (string, optional): VLAN group
- `status` (string, optional): VLAN status
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of VLANs with ID, name, status, site, and group information.

**Example queries:**
- "Find VLAN 100"
- "Search for management VLANs"
- "Show VLANs at the branch office"

### search_circuits
Search for network circuits and connections.

**Parameters:**
- `cid` (string, optional): Circuit ID (partial match)
- `provider` (string, optional): Provider name
- `type` (string, optional): Circuit type
- `status` (string, optional): Circuit status
- `site` (string, optional): Termination site
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of circuits with ID, provider, type, status, and termination information.

**Example queries:**
- "Find circuits from Verizon"
- "Search for MPLS circuits"
- "Show circuits terminating at headquarters"

### search_racks
Search for equipment racks and their locations.

**Parameters:**
- `name` (string, optional): Rack name (partial match)
- `site` (string, optional): Site name
- `location` (string, optional): Location within site
- `status` (string, optional): Rack status
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of racks with name, site, location, height, and status information.

**Example queries:**
- "Find racks in datacenter-01"
- "Search for 42U racks"
- "Show racks in the server room location"

## Usage Tips

**General Query Patterns:**
- Use natural language - Claude will map your requests to the appropriate tools
- Combine filters: "Find active Cisco routers at the London site"
- Use partial matches: Tools support partial name matching for flexible searches
- Specify limits: Add "show me the first 5" or "limit to 20 results" to control output size

**Common Query Examples:**
- "What devices do you see in NetBox?"
- "Search for devices at the Skipton site"
- "Show me all available IPs in 10.1.0.0/24"
- "Find VLAN 100 and show its details"
- "List all circuits from AT&T"
- "Get details for site ID 42 including devices and racks"