# Contributing to NetBox MCP Server

Thank you for your interest in contributing to the NetBox MCP Server project!

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/simonpainter/netbox-mcp.git
   cd netbox-mcp
   ```

2. **Install dependencies**
   ```bash
   pip install fastmcp httpx
   ```

3. **Set up environment variables**
   ```bash
   export NETBOX_URL="https://netbox.example.com"
   export NETBOX_TOKEN="your-api-token"
   export MCP_PORT=8000
   ```

4. **Test your setup**
   ```bash
   python3 -m py_compile app.py
   python3 app.py
   ```

## Development Guidelines

This repository follows specific conventions for adding NetBox MCP tools. **Please read the detailed guidelines in [`.github/copilot-instructions.md`](.github/copilot-instructions.md)** before contributing.

### Quick Summary

- Each NetBox resource must have two tools: `search_<resource>` and `get_<resource>_details`
- Tools must be organized by NetBox API root (circuits, dcim, ipam, etc.)
- All tools require descriptive docstrings with clear parameter documentation
- Use the helper functions `_search()` and `_get_detail()` (defined in `app.py`) to reduce code duplication
- Return structured JSON objects (no human-readable messages in responses)

### Adding a New Resource

1. Identify the NetBox API endpoint and appropriate section in `app.py`
2. Create `search_<resource>` function with proper docstring and parameter mapping
3. Create `get_<resource>_details` function for single object lookup
4. Run syntax check: `python3 -m py_compile app.py`
5. Test your changes with a running NetBox instance
6. Commit with a clear message describing what was added

For detailed step-by-step instructions, see the "How to add a new resource (step-by-step)" section in [`.github/copilot-instructions.md`](.github/copilot-instructions.md).

## Code Style

- Follow Python conventions (PEP 8)
- Use type hints: `async def func(args: Dict[str, Any]) -> List[Dict[str, Any]]`
- Keep functions focused and single-purpose
- Include comprehensive docstrings for all tools

## Testing

Before submitting a PR:

1. Run syntax check: `python3 -m py_compile app.py`
2. Test with your NetBox instance to verify tools work correctly
3. Verify parameter mapping matches NetBox API expectations

## Questions or Issues?

If you have questions or encounter issues:
- Check the [`.github/copilot-instructions.md`](.github/copilot-instructions.md) for detailed guidance
- Review existing tools in `app.py` for examples
- Open an issue on GitHub for discussion

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project.
