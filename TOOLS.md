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

### search_device_bays
Search for device bays in NetBox.

**Parameters:**
- `device_id` (integer, optional): Device ID to filter bays
- `device_name` (string, optional): Device name to filter bays
- `name` (string, optional): Bay name (partial match)
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of device bays with device info, installation status, and labels.

**Example queries:**
- "Search for device bays in device ID 123"
- "Find all bays in router-01"
- "Show me empty device bays"

### get_device_bay_details
Get detailed information about a specific device bay.

**Parameters:**
- `bay_id` (integer): NetBox device bay ID
- `device_id` (integer): Device ID (when combined with bay name)
- `bay_name` (string): Bay name (when combined with device ID)

**Returns:** Detailed device bay information including installed device details.

**Example queries:**
- "Get details for device bay ID 456"
- "Show me bay 'Slot1' in device ID 123"

### search_device_bay_templates
Search for device bay templates in NetBox.

**Parameters:**
- `device_type_id` (integer, optional): Device type ID to filter templates
- `name` (string, optional): Template name (partial match)
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of device bay templates with device type and label information.

**Example queries:**
- "Search for device bay templates"
- "Find bay templates for device type ID 789"

### get_device_bay_template_details
Get detailed information about a specific device bay template.

**Parameters:**
- `template_id` (integer): NetBox device bay template ID

**Returns:** Detailed device bay template information including device type details.

**Example queries:**
- "Get details for device bay template ID 101"

### search_device_roles
Search for device roles in NetBox.

**Parameters:**
- `name` (string, optional): Role name (partial match)
- `slug` (string, optional): Role slug
- `color` (string, optional): Role color
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of device roles with name, slug, color, and VM role status.

**Example queries:**
- "Search for device roles"
- "Find roles with 'router' in the name"
- "Show me all VM-capable roles"

### get_device_role_details
Get detailed information about a specific device role.

**Parameters:**
- `role_id` (integer): NetBox device role ID
- `role_name` (string): Role name (alternative to ID)
- `role_slug` (string): Role slug (alternative to ID)

**Returns:** Detailed device role information including description and capabilities.

**Example queries:**
- "Get details for device role ID 42"
- "Show me details for the 'router' role"

### search_device_types
Search for device types in NetBox.

**Parameters:**
- `model` (string, optional): Device model (partial match)
- `manufacturer` (string, optional): Manufacturer name
- `slug` (string, optional): Device type slug
- `part_number` (string, optional): Part number
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of device types with manufacturer, model, part number, and specifications.

**Example queries:**
- "Search for Cisco device types"
- "Find device types with 'switch' in the model"
- "Show me all Juniper routers"

### get_device_type_details
Get detailed information about a specific device type.

**Parameters:**
- `type_id` (integer): NetBox device type ID
- `model` (string): Device model (alternative to ID)
- `slug` (string): Device type slug (alternative to ID)

**Returns:** Detailed device type information including physical specifications and capabilities.

**Example queries:**
- "Get details for device type ID 987"
- "Show me details for the 'EX4300-48T' model"

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
### search_vlan_translation_policies
Search for VLAN translation policies.

**Parameters:**
- `name` (string, optional): Policy name (partial match)
- `description` (string, optional): Policy description (partial match)
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of VLAN translation policies with names and descriptions.

**Example queries:**
- "Find VLAN translation policies"
- "Search for policies with 'prod' in the name"

### search_vlan_translation_rules
Search for VLAN translation rules.

**Parameters:**
- `policy_id` (integer, optional): Translation policy ID
- `original_vid` (integer, optional): Original VLAN ID
- `translated_vid` (integer, optional): Translated VLAN ID
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of VLAN translation rules with original and translated VLAN IDs.

**Example queries:**
- "Find VLAN translation rules for policy ID 5"
- "Search for rules translating VLAN 100"

### search_fhrp_groups
Search for FHRP (First Hop Redundancy Protocol) groups.

**Parameters:**
- `name` (string, optional): Group name (partial match)
- `protocol` (string, optional): FHRP protocol (hsrp, vrrp, glbp, carp)
- `group_id` (integer, optional): Group ID
- `auth_type` (string, optional): Authentication type
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of FHRP groups with protocol, group ID, and authentication information.

**Example queries:**
- "Find HSRP groups"
- "Search for FHRP group ID 1"
- "Show VRRP groups with authentication"

### search_fhrp_group_assignments
Search for FHRP group assignments to interfaces.

**Parameters:**
- `group_id` (integer, optional): FHRP group ID
- `interface_id` (integer, optional): Interface ID
- `priority` (integer, optional): Assignment priority
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of FHRP group assignments with group, interface, and priority information.

**Example queries:**
- "Find FHRP assignments for group ID 10"
- "Search for high priority FHRP assignments"

### search_route_targets
Search for BGP route targets.

**Parameters:**
- `name` (string, optional): Route target name (partial match)
- `description` (string, optional): Description (partial match)
- `tenant` (string, optional): Tenant name
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of route targets with names, descriptions, and tenant information.

**Example queries:**
- "Find route targets for production tenant"
- "Search for route targets with 'vpn' in the name"

### search_services
Search for network services.

**Parameters:**
- `name` (string, optional): Service name (partial match)
- `device_id` (integer, optional): Device ID
- `virtual_machine_id` (integer, optional): Virtual machine ID
- `protocol` (string, optional): Protocol (tcp, udp, sctp)
- `ports` (string, optional): Port numbers or ranges
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of services with protocol, ports, and host information.

**Example queries:**
- "Find HTTP services"
- "Search for services on port 443"
- "Show TCP services on device ID 123"

### search_service_templates
Search for service templates.

**Parameters:**
- `name` (string, optional): Template name (partial match)
- `protocol` (string, optional): Protocol (tcp, udp, sctp)
- `ports` (string, optional): Port numbers or ranges
- `description` (string, optional): Description (partial match)
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of service templates with protocol, ports, and description information.

**Example queries:**
- "Find web service templates"
- "Search for UDP service templates"
- "Show templates for port 80"

### search_asns
Search for Autonomous System Numbers (ASNs).

**Parameters:**
- `asn` (integer, optional): Specific ASN number
- `name` (string, optional): ASN name (partial match)
- `rir` (string, optional): Regional Internet Registry
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of ASNs with number, name, and RIR information.

**Example queries:**
- "Find ASN 64512"
- "Search for ASNs from ARIN"
- "Show ASNs with 'Company' in the name"

### get_asn_details
Get detailed information about a specific ASN.

**Parameters:**
- `asn_id` (integer): NetBox ASN ID
- `asn` (integer): ASN number (alternative to ID)

**Returns:** Detailed ASN information including RIR and description.

**Example queries:**
- "Get details for ASN 64512"
- "Show me details for ASN ID 123"

### search_asn_ranges
Search for ASN ranges.

**Parameters:**
- `name` (string, optional): ASN range name (partial match)
- `rir` (string, optional): Regional Internet Registry
- `start` (integer, optional): Range start ASN
- `end` (integer, optional): Range end ASN
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of ASN ranges with name, start/end ASNs, and RIR information.

**Example queries:**
- "Find ASN ranges from RIPE"
- "Search for ranges starting with ASN 64512"

### get_asn_range_details
Get detailed information about a specific ASN range.

**Parameters:**
- `range_id` (integer): NetBox ASN range ID
- `name` (string): ASN range name (alternative to ID)

**Returns:** Detailed ASN range information including size and RIR.

**Example queries:**
- "Get details for ASN range 'Private Range 1'"

### search_aggregates
Search for IP address aggregates.

**Parameters:**
- `prefix` (string, optional): Aggregate prefix (e.g., '10.0.0.0/8')
- `rir` (string, optional): Regional Internet Registry
- `family` (integer, optional): IP family (4 or 6)
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of aggregates with prefix, RIR, and family information.

**Example queries:**
- "Find IPv4 aggregates from ARIN"
- "Search for 10.0.0.0/8 aggregate"

### get_aggregate_details
Get detailed information about a specific aggregate.

**Parameters:**
- `aggregate_id` (integer): NetBox aggregate ID
- `prefix` (string): Aggregate prefix (alternative to ID)

**Returns:** Detailed aggregate information including RIR and date added.

**Example queries:**
- "Get details for aggregate 10.0.0.0/8"

### search_ip_ranges
Search for IP address ranges.

**Parameters:**
- `start_address` (string, optional): Range start address
- `end_address` (string, optional): Range end address
- `vrf` (string, optional): VRF name
- `role` (string, optional): IP range role
- `status` (string, optional): IP range status
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of IP ranges with start/end addresses, VRF, status, and role information.

**Example queries:**
- "Find IP ranges in production VRF"
- "Search for active IP ranges"

### get_ip_range_details
Get detailed information about a specific IP range.

**Parameters:**
- `range_id` (integer): NetBox IP range ID
- `start_address` (string): Range start address (when combined with end_address)
- `end_address` (string): Range end address (when combined with start_address)

**Returns:** Detailed IP range information including size, VRF, and role.

**Example queries:**
- "Get details for IP range 192.168.1.1 to 192.168.1.100"

### search_rirs
Search for Regional Internet Registries (RIRs).

**Parameters:**
- `name` (string, optional): RIR name (partial match)
- `slug` (string, optional): RIR slug
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of RIRs with name and slug information.

**Example queries:**
- "Find RIR ARIN"
- "Search for all RIRs"

### get_rir_details
Get detailed information about a specific RIR.

**Parameters:**
- `rir_id` (integer): NetBox RIR ID
- `name` (string): RIR name (alternative to ID)
- `slug` (string): RIR slug (alternative to ID)

**Returns:** Detailed RIR information including description.

**Example queries:**
- "Get details for ARIN"
- "Show me details for RIR ID 1"

### search_ipam_roles
Search for IPAM roles (prefix/VLAN roles).

**Parameters:**
- `name` (string, optional): Role name (partial match)
- `slug` (string, optional): Role slug
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of IPAM roles with name, slug, and weight information.

**Example queries:**
- "Find IPAM roles"
- "Search for roles with 'DMZ' in the name"

### get_ipam_role_details
Get detailed information about a specific IPAM role.

**Parameters:**
- `role_id` (integer): NetBox IPAM role ID
- `name` (string): Role name (alternative to ID)
- `slug` (string): Role slug (alternative to ID)

**Returns:** Detailed IPAM role information including weight and description.

**Example queries:**
- "Get details for DMZ role"
- "Show me details for IPAM role ID 5"

### search_vrfs
Search for Virtual Routing and Forwarding instances (VRFs).

**Parameters:**
- `name` (string, optional): VRF name (partial match)
- `rd` (string, optional): Route distinguisher
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of VRFs with name and route distinguisher information.

**Example queries:**
- "Find production VRF"
- "Search for VRFs with RD 65000:100"

### get_vrf_details
Get detailed information about a specific VRF.

**Parameters:**
- `vrf_id` (integer): NetBox VRF ID
- `name` (string): VRF name (alternative to ID)
- `rd` (string): Route distinguisher (alternative to ID)

**Returns:** Detailed VRF information including route distinguisher and description.

**Example queries:**
- "Get details for production VRF"
- "Show me details for VRF with RD 65000:100"

### search_vlan_groups
Search for VLAN groups.

**Parameters:**
- `name` (string, optional): VLAN group name (partial match)
- `slug` (string, optional): VLAN group slug
- `site` (string, optional): Filter by site
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of VLAN groups with name, slug, and site information.

**Example queries:**
- "Find VLAN groups at datacenter site"
- "Search for groups with 'server' in the name"

### get_vlan_group_details
Get detailed information about a specific VLAN group.

**Parameters:**
- `group_id` (integer): NetBox VLAN group ID
- `name` (string): VLAN group name (alternative to ID)
- `slug` (string): VLAN group slug (alternative to ID)

**Returns:** Detailed VLAN group information including site and description.

**Example queries:**
- "Get details for server VLAN group"
- "Show me details for VLAN group ID 10"

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

### get_rack_details
Get comprehensive information about a specific rack.

**Parameters:**
- `rack_id` (integer): NetBox rack ID
- `rack_name` (string): Rack name (alternative to ID)

**Returns:** Detailed rack information including physical specifications, utilization, and location details.

**Example queries:**
- "Get details for rack ID 456"
- "Show me details for rack-01"
- "What are the specifications of the main rack?"

### search_rack_reservations
Search for rack unit reservations.

**Parameters:**
- `rack` (string, optional): Rack name
- `user` (string, optional): User who made the reservation
- `description` (string, optional): Reservation description (partial match)
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of rack reservations with rack name, user, reserved units, and description.

**Example queries:**
- "Find reservations for rack-01"
- "Show reservations by john.doe"
- "Search for maintenance reservations"

### get_rack_reservation_details
Get detailed information about a specific rack reservation.

**Parameters:**
- `reservation_id` (integer): NetBox rack reservation ID

**Returns:** Comprehensive reservation details including rack, user, units, and timeline.

**Example queries:**
- "Get details for reservation ID 123"
- "Show me reservation details for ID 456"

### search_rack_roles
Search for rack roles used in your infrastructure.

**Parameters:**
- `name` (string, optional): Rack role name (partial match)
- `slug` (string, optional): Rack role slug
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of rack roles with name, slug, color, and description.

**Example queries:**
- "Find server rack roles"
- "Show all rack roles"
- "Search for network rack roles"

### search_rack_types
Search for rack types and models.

**Parameters:**
- `model` (string, optional): Rack type model (partial match)
- `manufacturer` (string, optional): Manufacturer name
- `slug` (string, optional): Rack type slug
- `u_height` (integer, optional): Filter by rack height in units
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of rack types with model, manufacturer, dimensions, and specifications.

**Example queries:**
- "Find 42U rack types"
- "Search for Dell rack models"
- "Show rack types from APC"

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
- "Find all 42U racks in the datacenter"
- "Show me rack reservations for the server room"
- "What rack types do we have from Dell?"
- "Get details for rack-01 including utilization"