# incus-mcp

MCP server for [Incus](https://linuxcontainers.org/incus/) container and VM manager.

210 operations = 209 grouped + 1 ROOT: read (87), write (75), execute (9), delete (34), admin (4).

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

## v2.5 features

- **Write verification.** Every verifiable write is checked sent-vs-returned recursively: a silently dropped key (e.g. `config.limits.cpu` accepted then ignored by Incus) raises `ValueError` naming the full path instead of a phantom "201 Created".
- **`operation='schema'`.** Any group returns a machine-readable JSON Schema for an operation: `params={"op": "CreateInstance"}`.
- **Richer `help`.** `operation='help'` renders each parameter with its type, `?` for optional, `T | None` for nullable, and a bullet with the parameter's description.
- **`_UNSET` semantics.** Omitting a parameter differs from passing `null`: omitted params never reach the API; an explicit `null` clears a server-side value on PUT/PATCH.
- **Non-blocking waiters.** `operation_wait_start` / `operation_wait_poll` / `operation_wait_cancel` (+ `waits_list`) poll a long-running Incus operation in the background instead of blocking the session; `wait_operation` stays for short one-shot waits.
- **Post-terminal verify on async writes.** When an async write's operation finishes, the target resource is fetched and verified; a drop surfaces as `verify_error` on the wait handle (non-blocking) or raises from `wait_operation` (blocking).

## Groups

| Group | Operations | Description |
|---|---|---|
| `incus_read` | 87 | Instances, images, networks, storage, profiles, projects, cluster, certificates, operations, warnings, resources, metrics, operation waiters |
| `incus_write` | 75 | Create/update instances, images, networks, storage, profiles, projects, cluster, certificates |
| `incus_execute` | 9 | Instance state changes (start/stop/restart/freeze), exec commands |
| `incus_delete` | 34 | Delete all resource types |
| `incus_admin` | 4 | Server config, warnings management |

Each group is a single MCP tool. Call with `operation="help"` to list available operations, or pass `operation="OperationName"` with `params={...}`.

## Development

`uv run python dev.py check` runs lint (`ruff` + `mypy --strict`) and the test suite - the same command the pre-commit hook and CI use. Install the hook once:

```bash
git config core.hooksPath .githooks
```

Integration smoke tests hit a real Incus server and are excluded from the default run; execute them with `uv run python dev.py e2e` (requires `INCUS_URL` plus the auth env from Install).
