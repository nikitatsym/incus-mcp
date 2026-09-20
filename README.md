# incus-mcp

MCP server for [Incus](https://linuxcontainers.org/incus/) container and VM manager.

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

### HTTP

`incus-mcp --http` serves streamable HTTP at `http://127.0.0.1:8000/mcp` (`--host`, `--port`) instead of stdio, same environment variables. No authentication: put a gateway in front.

The package can also be imported: `mcp`, `Settings`, the client class, and `client_var` (a `ContextVar` the host sets per request) let one process serve several instances.

Either transport refuses to start on a bad credential: `main()` calls `IncusClient.check()` after parsing arguments, so the failing request is in the traceback instead of in the first tool call. The check is one `GET /1.0`, and its answer must say the client is trusted - Incus serves that endpoint to untrusted clients as well, so a 200 alone proves nothing. A host serving several instances calls `check()` on each client itself.

## v2.5 features

- **Write verification.** Every verifiable write is checked sent-vs-returned recursively: a silently dropped key (e.g. `config.limits.cpu` accepted then ignored by Incus) is reported as an error naming the full path instead of a phantom "201 Created".
- **`operation='schema'`.** Any group returns a machine-readable JSON Schema for an operation: `params={"op": "CreateInstance"}`.
- **Richer `help`.** `operation='help'` renders each parameter with its type, `?` for optional, `T | None` for nullable, and a bullet with the parameter's description.
- **`_UNSET` semantics.** Omitting a parameter differs from passing `null`: omitted params never reach the API; an explicit `null` clears a server-side value on PUT/PATCH.
- **Non-blocking waiters.** `operation_wait_start` / `operation_wait_poll` / `operation_wait_cancel` (+ `waits_list`) poll a long-running Incus operation in the background instead of blocking the session; `wait_operation` stays for short one-shot waits.
- **Post-terminal verify on async writes.** When an async write's operation finishes, the target resource is fetched and verified; a drop surfaces as `verify_error` on the wait handle (non-blocking) or as the `wait_operation` error result (blocking).

## Groups

| Group | Description |
|---|---|
| `incus_read` | Instances, images, networks, storage, profiles, projects, cluster, certificates, operations, warnings, resources, metrics, operation waiters |
| `incus_write` | Create/update instances, images, networks, storage, profiles, projects, cluster, certificates |
| `incus_execute` | Instance state changes (start/stop/restart/freeze), exec commands |
| `incus_delete` | Delete all resource types |
| `incus_admin` | Server config, warnings management |

Each group is a single MCP tool. Call with `operation="help"` to list available operations, or pass `operation="OperationName"` with `params={...}`.

## Development

`uv run python dev.py check` runs lint (`ruff` + `mypy --strict`) and the test suite - the same command the pre-commit hook and CI use. Install the hook once:

```bash
git config core.hooksPath .githooks
```

Integration smoke tests hit a real Incus server and are excluded from the default run (`-m integration`). Provision a throwaway Incus and run them:

- **Linux host or VM:** `sudo scripts/e2e-env.sh && (. .e2e/env && uv run python dev.py e2e)`. The script installs Incus, does a minimal `incus admin init`, pre-pulls the `e2e-alpine` image, mints a client cert, and writes `.e2e/env` (git-ignored) with the matching `INCUS_*` vars. Idempotent - re-runs are no-ops.
- **macOS:** Incus has no macOS daemon, so run the same recipe inside a Linux VM: `limactl start template://ubuntu-lts`, then clone the repo and run the Linux recipe inside the VM. This is the environment CI uses.

CI runs the same smokes in a dedicated `e2e` job (`.github/workflows/build.yml`) that gates the release build.

### Swagger conformance

`tests/test_swagger_conformance.py` reads every registered operation off its own AST and checks method, path, query-param names, body-field names and enum values against Incus's swagger spec - Incus ignores names it does not know, so a typo returns 200 and silently does nothing. It runs in the default gate against the copy of `doc/rest-api.yaml` vendored in `tests/data/`, since no running Incus serves that spec. Re-pin it to a newer Incus with:

```bash
uv run --with pyyaml python scripts/fetch-incus-spec.py v7.3.0
```
