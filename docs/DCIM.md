# DCIM (Data Center Infrastructure Management)

## search_devices

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

## get_device_details

Get comprehensive information about a specific device.

**Parameters:**

- `device_id` (integer): NetBox device ID
- `device_name` (string): Device name (alternative to ID)

**Returns:** Detailed device information including basic info, hardware specs, and network configuration.

**Example queries:**

- "Get details for device ID 123"
- "Show me details for router-01"

## get_device_interfaces

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

## search_device_bays

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

## get_device_bay_details

Get detailed information about a specific device bay.

**Parameters:**

- `bay_id` (integer): NetBox device bay ID
- `device_id` (integer): Device ID (when combined with bay name)
- `bay_name` (string): Bay name (when combined with device ID)

**Returns:** Detailed device bay information including installed device details.

**Example queries:*

- "Get details for device bay ID 456"
- "Show me bay 'Slot1' in device ID 123"

## search_device_bay_templates

Search for device bay templates in NetBox.

**Parameters:**

- `device_type_id` (integer, optional): Device type ID to filter templates
- `name` (string, optional): Template name (partial match)
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of device bay templates with device type and label information.

**Example queries:**

- "Search for device bay templates"
- "Find bay templates for device type ID 789"

## get_device_bay_template_details

Get detailed information about a specific device bay template.

**Parameters:**

- `template_id` (integer): NetBox device bay template ID

**Returns:** Detailed device bay template information including device type details.

**Example queries:**

- "Get details for device bay template ID 101"

## search_device_roles

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

## get_device_role_details

Get detailed information about a specific device role.

**Parameters:**

- `role_id` (integer): NetBox device role ID
- `role_name` (string): Role name (alternative to ID)
- `role_slug` (string): Role slug (alternative to ID)

**Returns:** Detailed device role information including description and capabilities.

**Example queries:**

- "Get details for device role ID 42"
- "Show me details for the 'router' role"

## search_device_types

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

## get_device_type_details

Get detailed information about a specific device type.

**Parameters:**

- `type_id` (integer): NetBox device type ID
- `model` (string): Device model (alternative to ID)
- `slug` (string): Device type slug (alternative to ID)

**Returns:** Detailed device type information including physical specifications and capabilities.

**Example queries:**

- "Get details for device type ID 987"
- "Show me details for the 'EX4300-48T' model"

## search_sites

Search for sites in NetBox with flexible filtering options.

**Parameters:**

- `name` (string, optional): Site name filter (partial match)
- `region` (string, optional): Region filter
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of sites with ID, name, slug, status, and region information.

**Example queries:**

- "List all sites"
- "Find sites in the Europe region"
- "Search for sites with 'data' in the name"

## get_site_details

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

## search_site_groups

Search for site groups in NetBox. Site groups organize sites by role or function and can be nested hierarchically.

**Parameters:**

- `name` (string, optional): Site group name (partial match)
- `slug` (string, optional): Site group slug
- `parent` (string, optional): Parent site group name
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of site groups with ID, name, slug, parent, and description information.

**Example queries:**

- "List all site groups"
- "Find site groups with 'datacenter' in the name"
- "Search for child groups under corporate group"

## get_site_group_details

Get detailed information about a specific site group including hierarchy and site count.

**Parameters:**

- `group_id` (integer): NetBox site group ID
- `name` (string): Site group name (alternative to ID)
- `slug` (string): Site group slug (alternative to ID)

**Returns:** Detailed site group information including parent relationships and site count.

**Example queries:**

- "Get details for site group ID 42"
- "Show me details for the corporate site group"
- "Get info about the datacenter-east group"

## search_regions

Search for regions in NetBox. Regions arrange sites geographically and can be nested hierarchically to create continent/country/city structures.

**Parameters:**

- `name` (string, optional): Region name (partial match)
- `slug` (string, optional): Region slug
- `parent` (string, optional): Parent region name
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of regions with ID, name, slug, parent, and description information.

**Example queries:**

- "List all regions"
- "Find regions with 'europe' in the name"
- "Search for child regions under North America"

## get_region_details

Get detailed information about a specific region including hierarchy and site count.

**Parameters:**

- `region_id` (integer): NetBox region ID
- `name` (string): Region name (alternative to ID)
- `slug` (string): Region slug (alternative to ID)

**Returns:** Detailed region information including parent relationships, child region count, and site count.

**Example queries:**

- "Get details for region ID 15"
- "Show me details for the Europe region"
- "Get info about the asia-pacific region"

## search_racks

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

## get_rack_details

Get comprehensive information about a specific rack.

**Parameters:**

- `rack_id` (integer): NetBox rack ID
- `rack_name` (string): Rack name (alternative to ID)

**Returns:** Detailed rack information including physical specifications, utilization, and location details.

**Example queries:**

- "Get details for rack ID 456"
- "Show me details for rack-01"
- "What are the specifications of the main rack?"

## search_rack_reservations

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

## get_rack_reservation_details

Get detailed information about a specific rack reservation.

**Parameters:**

- `reservation_id` (integer): NetBox rack reservation ID

**Returns:** Comprehensive reservation details including rack, user, units, and timeline.

**Example queries:**

- "Get details for reservation ID 123"
- "Show me reservation details for ID 456"

## search_rack_roles

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

## search_rack_types

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

## search_manufacturers

Search for device manufacturers in NetBox.

**Parameters:**

- `name` (string, optional): Manufacturer name (partial match)
- `slug` (string, optional): Manufacturer slug
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of manufacturers with ID, name, slug, and description information.

**Example queries:**

- "Search for manufacturers with 'Cisco' in the name"
- "Find all network equipment manufacturers"
- "Show all manufacturers"

## search_platforms

Search for device platforms in NetBox.

**Parameters:**

- `name` (string, optional): Platform name (partial match)
- `slug` (string, optional): Platform slug
- `manufacturer` (string, optional): Manufacturer name
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of platforms with ID, name, slug, manufacturer, and description information.

**Example queries:**

- "Search for platforms with 'iOS' in the name"
- "Find all Cisco platforms"
- "Show all network platforms"

## search_cables

Search for cables in NetBox with various filtering options.

**Parameters:**

- `label` (string, optional): Cable label (partial match)
- `type` (string, optional): Cable type
- `status` (string, optional): Cable status
- `color` (string, optional): Cable color
- `device` (string, optional): Connected device name
- `site` (string, optional): Site name
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of cables with ID, label, type, status, color, length, and termination information.

**Example queries:**

- "Search for cables with 'trunk' in the label"
- "Find all fiber optic cables"
- "Show cables connected to switch-01"

## get_cable_details

Get detailed information about a specific cable.

**Parameters:**

- `cable_id` (integer): NetBox cable ID

**Returns:** Comprehensive cable information including type, status, length, color, and termination details.

**Example queries:**

- "Get details for cable ID 89"
- "Show me details for the backbone fiber cable"
