# Extras

## search_tags

Search for tags in NetBox for better organization and categorization.

**Parameters:**

- `name` (string, optional): Tag name (partial match)
- `slug` (string, optional): Tag slug
- `color` (string, optional): Tag color
- `limit` (integer, optional): Max results (default: 10)

**Returns:** List of tags with ID, name, slug, color, and description information.

**Example queries:**

- "Search for tags with 'prod' in the name"
- "Find all red tags"
- "Show all available tags"
