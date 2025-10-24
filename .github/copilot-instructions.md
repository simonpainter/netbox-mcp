# COPILOT_INSTRUCTIONS — FastMCP NetBox tools

Purpose
------
This document describes the expected structure, conventions, and contributor guidance for the FastMCP-based NetBox tool collection in this repository (primary runtime: `app2.py`). The core rule: every NetBox data element in the model must be represented by two explicit MCP tools:

- `search_<resource>(args)`: queries the API collection endpoint and supports a set of optional filters.
- `get_<resource>_details(args)`: fetches a single object by ID and returns a single-element list or an empty list.

This repository requires hand-written, descriptive docstrings for each tool (no programmatic/dynamic registrar for final production code). Tools must be grouped and ordered by NetBox API root.

Repository conventions
---------------------
- Main MCP tool file: `app.py`.
- NetBox HTTP helper: `NetBoxClient` defined in `app.py` (wraps `httpx.AsyncClient` and performs `get(endpoint, params)`).
- MCP registration: functions are decorated with `@mcp.tool` and are async functions with signature `async def func(args: Dict[str, Any]) -> List[Dict[str, Any]]`.

API grouping and ordering
-------------------------
Tools in `app.py` should be physically ordered by API root in this sequence and separated by a clear comment block for readability:

1. circuits
2. core
3. dcim
4. extras
5. ipam
6. plugins
7. status
8. tenancy
9. users
10. virtualization
11. vpn
12. wireless

Insert a comment block like:

# --- dcim (devices, racks, interfaces, etc.) ---

above each group to make the file navigable.

Naming and signatures
---------------------
- Search tool naming: `search_<resource>` where `<resource>` is a concise, snake_case name matching the API resource (examples: `search_sites`, `search_devices`, `search_vlans`).
- Get tool naming: `get_<resource>_details` (examples: `get_site_details`, `get_device_details`).
- All tools: `async def name(args: Dict[str, Any]) -> List[Dict[str, Any]]`.
- `search_` behavior: accept a limited set of optional filter args (documented in the docstring) and return the NetBox `results` list or an empty list.
- `get_` behavior: accept at minimum `id` in `args`; if present fetch the `.../{id}/` endpoint and return `[object]` or `[]`.

Docstrings and content requirements
----------------------------------
Each tool must include a multi-line docstring that:
- Briefly describes the purpose and which NetBox endpoint it queries.
- Lists accepted args and their types/semantics. Be explicit about which args are required vs optional.
- Describes the return value (list of NetBox objects or single-element list) and error behavior.
- Notes any edge-cases or special semantics (e.g., when name lookup is supported, how multiple matches are handled).

Do not include long human chatter in the return value: return structured JSON objects (NetBox dicts) so downstream tools can consume them reliably.

Parameter mapping guidance
--------------------------
Map incoming `args` to NetBox query parameters in a consistent way:
- Partial/case-insensitive string matches: use `name__ic` where appropriate.
- Exact ID filters: pass numeric ids as-is (e.g., `site`, `device`).
- Defaults: set a reasonable `limit` default (typically 10 or 100 depending on the endpoint). Always read `args.get("limit", <default>)`.

Errors and exceptions
---------------------
- Network or server errors should raise exceptions so the MCP server can surface them.
- Validation errors (missing required arguments) should return an empty list rather than raising, following existing repo behavior.

Testing & verification
----------------------
When you add or reorder tools:

- Run a quick syntax check:

```bash
python3 -m py_compile app2.py
```

- Verify imports (ensure `fastmcp`, `httpx`, and typing hints are present).
- Keep changes small and run the syntax check after reordering large blocks.

How to add a new resource (step-by-step)
----------------------------------------
1. Choose the API group (see ordering above) and open the corresponding section in `app2.py`.
2. Create `search_<resource>` function with:
   - A clear docstring (purpose, accepted args, returns).
   - `params` mapping built from `args`.
   - Instantiate `NetBoxClient(NETBOX_URL, NETBOX_TOKEN)` and call the collection endpoint (e.g., `await client.get("dcim/example/", params)`).
   - Return `result.get("results", [])` if result is a dict, otherwise an empty list.
3. Create `get_<resource>_details` function with:
   - Docstring describing it accepts `id`.
   - If `id` present: call `await client.get(f"dcim/example/{id}/")` and return `[result]` or `[]`.
4. Run `python3 -m py_compile app2.py` and fix any syntax issues.
5. Commit only the minimal relevant changes and include a short commit message describing the resource added.

Examples
--------
Example Search (sites):

- Function name: `search_sites`
- Endpoint: `dcim/sites/`
- Accepted args: `site_id` (exact), `site_name` (partial)
- Return: list of site dicts

Example Get (site details):

- Function name: `get_site_details`
- Endpoint: `dcim/sites/{id}/`
- Accepted args: `id` (required)
- Return: `[site_dict]` or `[]`
