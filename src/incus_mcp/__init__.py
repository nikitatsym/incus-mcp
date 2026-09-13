import argparse

from mcp.server.transport_security import TransportSecuritySettings

from .client import IncusClient
from .config import Settings
from .server import mcp
from .tools.helpers import _get_client, client_var

__all__ = ["IncusClient", "Settings", "client_var", "main", "mcp"]


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="incus-mcp",
        description="MCP server for Incus. Serves MCP over stdio unless --http is given.",
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="serve streamable HTTP at /mcp instead of stdio, for a gateway in front",
    )
    parser.add_argument("--host", default="127.0.0.1", help="bind address for --http")
    parser.add_argument("--port", type=int, default=8000, help="port for --http")
    args = parser.parse_args()

    # Fail here, with the failing request in the traceback, not on the first tool call.
    _get_client().check()

    if args.http:
        # Stateless: the gateway in front opens a session per call; nothing outlives a request.
        # It also forwards the public Host header, which the SDK's loopback rebinding guard 421s.
        mcp.run(
            transport="streamable-http",
            host=args.host,
            port=args.port,
            stateless_http=True,
            transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
        )
        return

    mcp.run(transport="stdio")
