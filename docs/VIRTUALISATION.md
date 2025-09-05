# Virtualization

## search_virtual_machines

Search for virtual machines in NetBox with flexible filtering options.

**Parameters:**

- `name` (string, optional): VM name (partial match)
- `cluster` (string, optional): Cluster name
- `site` (string, optional): Site name
- `status` (string, optional): VM status
- `role` (string, optional): VM role
- `platform` (string, optional): Platform name
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of virtual machines with ID, name, cluster, site, status, role, platform, and resource information.

**Example queries:**

- "Search for VMs with 'web' in the name"
- "Find all VMs in the production cluster"
- "Show VMs at the main datacenter site"

## get_virtual_machine_details

Get comprehensive information about a specific virtual machine.

**Parameters:**

- `vm_id` (integer): NetBox VM ID
- `name` (string): VM name (alternative to ID)

**Returns:** Detailed VM information including resources, cluster, platform, and configuration details.

**Example queries:**

- "Get details for VM ID 45"
- "Show me details for web-server-01"

## search_clusters

Search for virtualization clusters in NetBox.

**Parameters:**

- `name` (string, optional): Cluster name (partial match)
- `type` (string, optional): Cluster type
- `group` (string, optional): Cluster group
- `site` (string, optional): Site name
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of clusters with ID, name, type, group, site, and description information.

**Example queries:**

- "Search for clusters with 'prod' in the name"
- "Find all VMware clusters"
- "Show clusters at the datacenter site"

## get_cluster_details

Get detailed information about a specific cluster.

**Parameters:**

- `cluster_id` (integer): NetBox cluster ID
- `name` (string): Cluster name (alternative to ID)

**Returns:** Comprehensive cluster information including type, group, site, and configuration details.

**Example queries:**

- "Get details for cluster ID 12"
- "Show me details for the production-cluster"
