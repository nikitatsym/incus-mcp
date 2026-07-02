def main() -> None:
    from .server import mcp
    mcp.run(transport="stdio")
