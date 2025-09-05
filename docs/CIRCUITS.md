# Circuits

## search_circuits

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

## search_providers

Search for circuit providers in NetBox.

**Parameters:**

- `name` (string, optional): Provider name (partial match)
- `slug` (string, optional): Provider slug
- `asn` (integer, optional): Provider ASN
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of providers with ID, name, slug, ASN, account, and portal information.

**Example queries:**

- "Search for providers with 'Verizon' in the name"
- "Find providers with ASN 1234"
- "Show all circuit providers"

## search_circuit_types

Search for circuit types in NetBox.

**Parameters:**

- `name` (string, optional): Circuit type name (partial match)
- `slug` (string, optional): Circuit type slug
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of circuit types with ID, name, slug, and description information.

**Example queries:**

- "Search for circuit types with 'MPLS' in the name"
- "Find all fiber circuit types"
- "Show all circuit types"
