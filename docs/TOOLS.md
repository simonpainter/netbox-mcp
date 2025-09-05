# NetBox MCP Tools Reference

This document describes all the tools exposed by the NetBox MCP server for querying your NetBox instance through Claude Desktop. Tools are organized according to NetBox's official data model groupings.

- [Circuits](CIRCUITS.md)
- [DCIM](DCIM.md)
- [IPAM](IPAM.md)
- [Tenancy](TENANCY.md)
- [Virtualization](VIRTUALIZATION.md)
- [Extras](EXTRAS.md)

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
- "List all site groups"
- "Find site groups with 'datacenter' in the name"
- "Get details for the corporate site group"
- "Show me all production site groups"
- "Find all 42U racks in the datacenter"
- "Show me rack reservations for the server room"
- "What rack types do we have from Dell?"
- "Get details for rack-01 including utilization"
- "Search for tenants with 'corp' in the name"
- "Show me all tenants in the enterprise group"
- "Get details for the main-corp tenant"
- "Find contacts with admin in their title"
- "Show contacts in the IT group"
- "Search for contact roles with 'manager' in the name"
- "What VMs are running on the production cluster?"
- "Show me details for web-server-01"
- "Find all VMware clusters"
- "Search for Cisco manufacturers"
- "Show all fiber optic cables"
- "Find cables connected to core-switch-01"
- "List all circuit providers"
- "Search for MPLS circuit types"
- "Show me all production tags"
- "Find red colored tags"
