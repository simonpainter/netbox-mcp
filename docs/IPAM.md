# IPAM (IP Address Management)

## search_ip_addresses

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

## get_prefixes

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

## get_available_ips

Find available IP addresses within a specific prefix.

**Parameters:**

- `prefix_id` (integer): NetBox prefix ID
- `prefix` (string): Prefix in CIDR notation (alternative to ID)
- `count` (integer, optional): Number of IPs to return (default: 10)

**Returns:** List of available IP addresses within the specified prefix.

**Example queries:**

- "Find available IPs in 192.168.1.0/24"
- "Show me 5 available addresses in prefix ID 123"

## search_vlans

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

## search_vlan_translation_policies

Search for VLAN translation policies.

**Parameters:**

- `name` (string, optional): Policy name (partial match)
- `description` (string, optional): Policy description (partial match)
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of VLAN translation policies with names and descriptions.

**Example queries:**

- "Find VLAN translation policies"
- "Search for policies with 'prod' in the name"

## search_vlan_translation_rules

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

## search_fhrp_groups

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

## search_fhrp_group_assignments

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

## search_route_targets

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

## search_services

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

## search_service_templates

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

## search_asns

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

## get_asn_details

Get detailed information about a specific ASN.

**Parameters:**

- `asn_id` (integer): NetBox ASN ID
- `asn` (integer): ASN number (alternative to ID)

**Returns:** Detailed ASN information including RIR and description.

**Example queries:**

- "Get details for ASN 64512"
- "Show me details for ASN ID 123"

## search_asn_ranges

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

## get_asn_range_details

Get detailed information about a specific ASN range.

**Parameters:**

- `range_id` (integer): NetBox ASN range ID
- `name` (string): ASN range name (alternative to ID)

**Returns:** Detailed ASN range information including size and RIR.

**Example queries:**

- "Get details for ASN range 'Private Range 1'"

## search_aggregates

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

## get_aggregate_details

Get detailed information about a specific aggregate.

**Parameters:**

- `aggregate_id` (integer): NetBox aggregate ID
- `prefix` (string): Aggregate prefix (alternative to ID)

**Returns:** Detailed aggregate information including RIR and date added.

**Example queries:**

- "Get details for aggregate 10.0.0.0/8"

## search_ip_ranges

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

## get_ip_range_details

Get detailed information about a specific IP range.

**Parameters:**

- `range_id` (integer): NetBox IP range ID
- `start_address` (string): Range start address (when combined with end_address)
- `end_address` (string): Range end address (when combined with start_address)

**Returns:** Detailed IP range information including size, VRF, and role.

**Example queries:**

- "Get details for IP range 192.168.1.1 to 192.168.1.100"

## search_rirs

Search for Regional Internet Registries (RIRs).

**Parameters:**

- `name` (string, optional): RIR name (partial match)
- `slug` (string, optional): RIR slug
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of RIRs with name and slug information.

**Example queries:**

- "Find RIR ARIN"
- "Search for all RIRs"

## get_rir_details

Get detailed information about a specific RIR.

**Parameters:**

- `rir_id` (integer): NetBox RIR ID
- `name` (string): RIR name (alternative to ID)
- `slug` (string): RIR slug (alternative to ID)

**Returns:** Detailed RIR information including description.

**Example queries:**

- "Get details for ARIN"
- "Show me details for RIR ID 1"

## search_ipam_roles

Search for IPAM roles (prefix/VLAN roles).

**Parameters:**

- `name` (string, optional): Role name (partial match)
- `slug` (string, optional): Role slug
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of IPAM roles with name, slug, and weight information.

**Example queries:**

- "Find IPAM roles"
- "Search for roles with 'DMZ' in the name"

## get_ipam_role_details

Get detailed information about a specific IPAM role.

**Parameters:**

- `role_id` (integer): NetBox IPAM role ID
- `name` (string): Role name (alternative to ID)
- `slug` (string): Role slug (alternative to ID)

**Returns:** Detailed IPAM role information including weight and description.

**Example queries:**

- "Get details for DMZ role"
- "Show me details for IPAM role ID 5"

## search_vrfs

Search for Virtual Routing and Forwarding instances (VRFs).

**Parameters:**

- `name` (string, optional): VRF name (partial match)
- `rd` (string, optional): Route distinguisher
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of VRFs with name and route distinguisher information.

**Example queries:**

- "Find production VRF"
- "Search for VRFs with RD 65000:100"

## get_vrf_details

Get detailed information about a specific VRF.

**Parameters:**

- `vrf_id` (integer): NetBox VRF ID
- `name` (string): VRF name (alternative to ID)
- `rd` (string): Route distinguisher (alternative to ID)

**Returns:** Detailed VRF information including route distinguisher and description.

**Example queries:**

- "Get details for production VRF"
- "Show me details for VRF with RD 65000:100"

## search_vlan_groups

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

## get_vlan_group_details

Get detailed information about a specific VLAN group.

**Parameters:**

- `group_id` (integer): NetBox VLAN group ID
- `name` (string): VLAN group name (alternative to ID)
- `slug` (string): VLAN group slug (alternative to ID)

**Returns:** Detailed VLAN group information including site and description.

**Example queries:**

- "Get details for server VLAN group"
- "Show me details for VLAN group ID 10"
