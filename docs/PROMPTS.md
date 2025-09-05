# NetBox MCP Prompts Reference

This document describes all the prompts exposed by the NetBox MCP server for guiding Claude Desktop interactions with your NetBox instance. Prompts provide structured ways to generate specific types of queries and analyses.

## What are MCP Prompts?

MCP prompts are predefined conversation starters that help structure your interactions with Claude when working with NetBox data. They provide a standardized way to request common types of analysis and information gathering tasks.

## Available Prompts

### device-overview

Get an overview of devices in NetBox with optional site filtering.

**Description:** Provides a comprehensive overview of all devices in your NetBox instance, including device counts by type and role, and highlights important status information.

**Arguments:**

- `site` (string, optional): Site name to filter devices

**Generated Query:** "Please provide an overview of all devices{at site 'SITE'} in NetBox. Include device counts by type and role, and highlight any important status information."

**Usage Examples:**

- Use without site filter: "Use the device-overview prompt to see all devices"
- Use with site filter: "Use the device-overview prompt for the main-datacenter site"
- Natural language: "Give me a device overview for the London office"

**What You'll Get:**

- Total device counts
- Breakdown by device types (switches, routers, servers, etc.)
- Breakdown by device roles (core, access, edge, etc.)
- Status summary (active, planned, decommissioned, etc.)
- Notable issues or warnings

---

### site-summary

Get a comprehensive summary of a specific site in your NetBox instance.

**Description:** Provides detailed information about a specific site including devices, racks, IP allocations, and other relevant infrastructure information.

**Arguments:**

- `site_name` (string, required): Name of the site to summarize

**Generated Query:** "Please provide a comprehensive summary of the 'SITE_NAME' site in NetBox. Include details about devices, racks, IP allocations, and any other relevant infrastructure information."

**Usage Examples:**

- "Use the site-summary prompt for headquarters"
- "Give me a site summary for the Chicago datacenter"
- "Summarize the branch-office-1 site"

**What You'll Get:**

- Site overview and basic information
- Device inventory at the site
- Rack utilization and layout
- IP address allocations and prefixes
- VLAN assignments
- Circuit terminations
- Power and space utilization
- Any issues or optimization opportunities

---

### ip-management

Explore IP address management and available subnets with optional network prefix focus.

**Description:** Helps you understand IP address allocation, utilization, and available address space in your NetBox instance.

**Arguments:**

- `prefix` (string, optional): Network prefix to focus on (e.g., '10.0.0.0/24')

**Generated Query:** "Help me explore IP address management in NetBox{for the PREFIX network}. Show me available prefixes, IP utilization, and suggest any optimization opportunities."

**Usage Examples:**

- Use without prefix: "Use the ip-management prompt to analyze IP usage"
- Use with specific prefix: "Use the ip-management prompt for 192.168.1.0/24"
- Natural language: "Analyze IP management for the 10.0.0.0/8 network"

**What You'll Get:**

- Available IP prefixes and their utilization
- Subnet allocation patterns
- Available IP addresses for assignment
- IP address conflicts or issues
- Suggestions for optimization
- VRF assignments and routing context
- DHCP pool availability

---

### device-troubleshoot

Troubleshoot connectivity and interface issues for a specific device.

**Description:** Helps diagnose network connectivity problems, interface status issues, and configuration problems for a specific device.

**Arguments:**

- `device_name` (string, required): Name or partial name of the device to troubleshoot

**Generated Query:** "Help me troubleshoot connectivity and interface issues for device 'DEVICE_NAME'. Check the device details, interface status, IP assignments, and identify any potential problems."

**Usage Examples:**

- "Use the device-troubleshoot prompt for core-switch-01"
- "Troubleshoot the router-london device"
- "Help me debug issues with web-server-05"

**What You'll Get:**

- Device status and configuration details
- Interface status and configuration
- IP address assignments and conflicts
- Cable connections and physical topology
- Port utilization and errors
- Potential connectivity issues
- Configuration recommendations
- Related device dependencies

---

### network-infrastructure

Analyze network infrastructure including VLANs, circuits, and racks with optional focus area.

**Description:** Provides comprehensive analysis of your network infrastructure components and their utilization patterns.

**Arguments:**

- `focus_area` (string, optional): Area to focus on: 'vlans', 'circuits', 'racks', or 'all' (default: 'all')

**Generated Query:** "Analyze the network infrastructure in NetBox, {focusing on FOCUS_AREA|covering all areas}. Provide insights about VLANs, circuits, racks, and their utilization patterns."

**Usage Examples:**

- Use for all areas: "Use the network-infrastructure prompt"
- Focus on VLANs: "Use the network-infrastructure prompt focusing on vlans"
- Focus on circuits: "Analyze circuits using the network-infrastructure prompt"
- Focus on racks: "Use the network-infrastructure prompt for racks analysis"

**What You'll Get:**

**For VLANs:**
- VLAN utilization and assignment patterns
- VLAN conflicts or overlaps
- VLAN groups and organization
- Trunk configurations

**For Circuits:**
- Circuit utilization and capacity
- Provider distribution
- Circuit types and technologies
- Termination points and routing

**For Racks:**
- Rack space utilization
- Power consumption patterns
- Cooling requirements
- Cable management

**For All Areas:**
- Comprehensive infrastructure overview
- Cross-component dependencies
- Optimization opportunities
- Capacity planning insights

## Usage Tips

**Getting Started:**

1. **Use prompts to structure complex queries:** Instead of asking "Show me everything about my network," use the device-overview prompt for a structured overview.

2. **Combine prompts with follow-up questions:** Start with a prompt, then ask specific follow-up questions based on the results.

3. **Choose the right prompt for your goal:**
   - **Planning**: Use device-overview and network-infrastructure
   - **Troubleshooting**: Use device-troubleshoot and ip-management
   - **Documentation**: Use site-summary
   - **Capacity Planning**: Use network-infrastructure with specific focus areas

**Example Workflows:**

**Network Health Check:**
1. Start with device-overview to see overall device status
2. Use network-infrastructure to analyze utilization patterns
3. Follow up with specific device-troubleshoot for any problematic devices

**Site Migration Planning:**
1. Use site-summary for the source site
2. Use ip-management to understand IP allocations
3. Use network-infrastructure focusing on circuits for connectivity planning

**Troubleshooting Workflow:**
1. Use device-troubleshoot for the specific problematic device
2. Use ip-management to check for IP conflicts
3. Follow up with targeted questions about specific interfaces or connections

**Best Practices:**

- **Be specific with device and site names** - use exact names from NetBox when possible
- **Use optional parameters** to narrow focus when dealing with large infrastructures
- **Follow up with detailed questions** after getting prompt results
- **Combine multiple prompts** for comprehensive analysis
- **Save prompt results** for documentation and planning purposes

## Integration with Natural Language

While you can explicitly request prompts using their names, Claude Desktop will also automatically use these prompts when appropriate based on your natural language requests:

- "Tell me about devices at the London site" → device-overview prompt with site filter
- "What's the status of core-router-01?" → device-troubleshoot prompt
- "How are our IP addresses allocated?" → ip-management prompt
- "Analyze our VLAN setup" → network-infrastructure prompt with vlans focus

This seamless integration allows you to work naturally while benefiting from the structured analysis that prompts provide.