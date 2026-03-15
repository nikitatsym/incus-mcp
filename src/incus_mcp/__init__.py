def main():
    from .server import mcp
    mcp.run(transport="stdio")
