# incus-mcp

MCP server for [Incus](https://linuxcontainers.org/incus/) container and VM manager.

204 operations across 5 groups: read (82), write (75), execute (9), delete (34), admin (4).

## Install

### OIDC (Authentik app_password)

1. In Authentik, create an OAuth2/OpenID provider for Incus (public client)
2. Create an `app_password` token: Admin → Directory → Tokens → Create (intent: `app_password`, user: your user, expiring: off)
3. Copy the token key — this goes into `INCUS_PASSWORD`

```json
{
  "mcpServers": {
    "incus": {
      "command": "uvx",
      "args": ["--refresh", "--extra-index-url", "https://nikitatsym.github.io/incus-mcp/simple", "incus-mcp"],
      "env": {
        "INCUS_URL": "https://incus.example.com:8443",
        "INCUS_OIDC_ISSUER": "https://auth.example.com/application/o/incus/",
        "INCUS_OIDC_CLIENT_ID": "your-client-id",
        "INCUS_USERNAME": "your-username",
        "INCUS_PASSWORD": "your-authentik-app-password-token"
      }
    }
  }
}
```

The server handles OIDC token exchange and refresh automatically (Resource Owner Password Grant).

### TLS client certificate

```bash
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:secp384r1 \
  -sha384 -keyout incus-mcp.key -out incus-mcp.crt \
  -nodes -days 3650 -subj "/CN=incus-mcp"
incus config trust add-certificate incus-mcp.crt
```

```json
{
  "mcpServers": {
    "incus": {
      "command": "uvx",
      "args": ["--refresh", "--extra-index-url", "https://nikitatsym.github.io/incus-mcp/simple", "incus-mcp"],
      "env": {
        "INCUS_URL": "https://incus.example.com:8443",
        "INCUS_CLIENT_CERT": "/path/to/incus-mcp.crt",
        "INCUS_CLIENT_KEY": "/path/to/incus-mcp.key"
      }
    }
  }
}
```

### Where to paste

- **Claude Code**: `~/.claude.json` → `mcpServers`
- **Claude Desktop**: Settings → Developer → Edit Config
- **Cursor**: Settings → MCP Servers

Or use the [setup page](https://nikitatsym.github.io/incus-mcp/) to generate the config.

## Groups

| Group | Operations | Description |
|---|---|---|
| `incus_read` | 82 | Instances, images, networks, storage, profiles, projects, cluster, certificates, operations, warnings, resources, metrics |
| `incus_write` | 75 | Create/update instances, images, networks, storage, profiles, projects, cluster, certificates |
| `incus_execute` | 9 | Instance state changes (start/stop/restart/freeze), exec commands |
| `incus_delete` | 34 | Delete all resource types |
| `incus_admin` | 4 | Server config, warnings management |

Each group is a single MCP tool. Call with `operation="help"` to list available operations, or pass `operation="OperationName"` with `params={...}`.
