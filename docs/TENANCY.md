# Tenancy

## search_tenants

Search for tenants in NetBox.

**Parameters:**

- `name` (string, optional): Tenant name (partial match)
- `slug` (string, optional): Tenant slug
- `group` (string, optional): Tenant group name
- `description` (string, optional): Description (partial match)
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of tenants with ID, name, slug, group, and description information.

**Example queries:**

- "Search for tenants with 'corp' in the name"
- "Find all tenants in the enterprise group"
- "Show me all tenants"

## get_tenant_details

Get detailed information about a specific tenant.

**Parameters:**

- `tenant_id` (integer): NetBox tenant ID
- `name` (string): Tenant name (alternative to ID)
- `slug` (string): Tenant slug (alternative to ID)

**Returns:** Comprehensive tenant information including basic details, group membership, and comments.

**Example queries:**

- "Get details for tenant ID 42"
- "Show me details for the main-corp tenant"

## search_tenant_groups

Search for tenant groups in NetBox.

**Parameters:**

- `name` (string, optional): Tenant group name (partial match)
- `slug` (string, optional): Tenant group slug
- `parent` (string, optional): Parent group name
- `description` (string, optional): Description (partial match)
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of tenant groups with ID, name, slug, parent, and description information.

**Example queries:**

- "Search for tenant groups with 'enterprise' in the name"
- "Find groups under the corporate parent"
- "Show all tenant groups"

## get_tenant_group_details

Get detailed information about a specific tenant group.

**Parameters:**

- `group_id` (integer): NetBox tenant group ID
- `name` (string): Tenant group name (alternative to ID)
- `slug` (string): Tenant group slug (alternative to ID)

**Returns:** Comprehensive tenant group information including tenant count and child groups.

**Example queries:**

- "Get details for tenant group ID 15"
- "Show me details for the enterprise-group"

## search_contacts

Search for contacts in NetBox.

**Parameters:**

- `name` (string, optional): Contact name (partial match)
- `email` (string, optional): Email address (partial match)
- `group` (string, optional): Contact group name
- `title` (string, optional): Contact title (partial match)
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of contacts with ID, name, email, group, title, and phone information.

**Example queries:**

- "Search for contacts named John"
- "Find contacts with admin in their title"
- "Show contacts in the IT group"

## get_contact_details

Get detailed information about a specific contact.

**Parameters:**

- `contact_id` (integer): NetBox contact ID
- `name` (string): Contact name (alternative to ID)
- `email` (string): Email address (alternative to ID)

**Returns:** Comprehensive contact information including all contact details and group membership.

**Example queries:**

- "Get details for contact ID 25"
- "Show me details for <john.doe@company.com>"

## search_contact_groups

Search for contact groups in NetBox.

**Parameters:**

- `name` (string, optional): Contact group name (partial match)
- `slug` (string, optional): Contact group slug
- `parent` (string, optional): Parent group name
- `description` (string, optional): Description (partial match)
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of contact groups with ID, name, slug, parent, and description information.

**Example queries:**

- "Search for contact groups with 'IT' in the name"
- "Find groups under the engineering parent"
- "Show all contact groups"

## get_contact_group_details

Get detailed information about a specific contact group.

**Parameters:**

- `group_id` (integer): NetBox contact group ID
- `name` (string): Contact group name (alternative to ID)
- `slug` (string): Contact group slug (alternative to ID)

**Returns:** Comprehensive contact group information including contact count and child groups.

**Example queries:**

- "Get details for contact group ID 8"
- "Show me details for the IT-team group"

## search_contact_roles

Search for contact roles in NetBox.

**Parameters:**

- `name` (string, optional): Contact role name (partial match)
- `slug` (string, optional): Contact role slug
- `description` (string, optional): Description (partial match)
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of contact roles with ID, name, slug, and description information.

**Example queries:**

- "Search for contact roles with 'admin' in the name"
- "Find all management roles"
- "Show contact roles"

## get_contact_role_details

Get detailed information about a specific contact role.

**Parameters:**

- `role_id` (integer): NetBox contact role ID
- `name` (string): Contact role name (alternative to ID)
- `slug` (string): Contact role slug (alternative to ID)

**Returns:** Comprehensive contact role information including description and usage details.

**Example queries:**

- "Get details for contact role ID 3"
- "Show me details for the admin-role"
