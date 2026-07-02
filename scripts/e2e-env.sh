#!/bin/sh
# Idempotent Incus provisioner for the e2e smokes (Debian/Ubuntu, run as root).
# Every action guards on current state, so re-runs are no-ops. Emits a
# shell-sourceable .e2e/env whose var names match config.py's Settings fields.
set -eu

if [ "$(id -u)" -ne 0 ]; then
    echo "run as root: sudo $0" >&2
    exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
E2E_DIR="$REPO_ROOT/.e2e"
CERT="$E2E_DIR/client.crt"
KEY="$E2E_DIR/client.key"
ALIAS="e2e-alpine"

mkdir -p "$E2E_DIR"

# 1. Incus binary (noble universe).
if ! command -v incus >/dev/null 2>&1; then
    apt-get update
    apt-get install -y incus
fi

# 2. Storage pool. `admin init --minimal` is avoided throughout: its
# auto-subnet step fails inside nested VMs (lima/vz) and aborts init half-done,
# leaving no network and an empty default profile. Each piece below is
# provisioned explicitly and idempotently instead.
if ! incus storage list -f csv 2>/dev/null | grep -q "^default,"; then
    incus storage create default dir
fi

# 3. HTTPS listener (idempotent: setting the same value is a no-op).
incus config set core.https_address 127.0.0.1:8443

# 4. Managed network + default-profile devices. The sync silent-drop smoke
# needs a managed network to target; container creation needs a root disk on
# the default profile (the nic gives the container connectivity). Explicit
# subnet - auto-detection is unreliable in nested VMs.
if ! incus network list -f csv 2>/dev/null | awk -F, '$3=="YES"{f=1} END{exit !f}'; then
    incus network create incusbr0 ipv4.address=10.201.202.1/24 ipv4.nat=true ipv6.address=none
fi
if ! incus profile device list default 2>/dev/null | grep -qx root; then
    incus profile device add default root disk pool=default path=/
fi
if ! incus profile device list default 2>/dev/null | grep -qx eth0; then
    incus profile device add default eth0 nic network=incusbr0 name=eth0
fi

# 5. Pre-pull the smoke image and pin the alias the tests use.
if ! incus image alias list -f csv 2>/dev/null | grep -q "^${ALIAS},"; then
    incus image copy images:alpine/3.21 local: --alias "$ALIAS"
fi

# 6. Client cert + trust.
if [ ! -f "$CERT" ]; then
    openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:secp384r1 \
        -sha384 -nodes -days 3650 -subj "/CN=incus-mcp-e2e" \
        -keyout "$KEY" -out "$CERT"
fi
FP12="$(openssl x509 -in "$CERT" -outform der | sha256sum | cut -c1-12)"
if ! incus config trust list -f csv 2>/dev/null | grep -qi "$FP12"; then
    incus config trust add-certificate "$CERT"
fi

# 7. Shell-sourceable env (absolute paths; names match config.py Settings).
cat > "$E2E_DIR/env" <<EOF
export INCUS_URL=https://127.0.0.1:8443
export INCUS_CLIENT_CERT=$CERT
export INCUS_CLIENT_KEY=$KEY
export INCUS_VERIFY_SSL=false
EOF

# 8. Hand the dir back to the invoking user so the test process can read the key.
if [ -n "${SUDO_USER:-}" ]; then
    chown -R "$SUDO_USER" "$E2E_DIR"
fi

echo "provisioned. source $E2E_DIR/env then: uv run python dev.py e2e"
