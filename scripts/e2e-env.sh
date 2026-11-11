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
ZABBLY_KEY=/etc/apt/keyrings/zabbly.asc
ZABBLY_SOURCES=/etc/apt/sources.list.d/zabbly-incus-lts-7.0.sources
# Published at https://github.com/zabbly/incus#repository-key
ZABBLY_FPR=4EFC590696CB15B87C73A3AD82CC8797C838DCFD

mkdir -p "$E2E_DIR"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Fails unless the file holds exactly one primary key, Zabbly's.
check_zabbly_key() {
    fpr="$(gpg --quiet --homedir "$TMP" --show-keys --with-colons "$1" |
        awk -F: '$1 == "pub" {p = 1; next} $1 == "fpr" && p {print $10; p = 0}')"
    if [ "$fpr" != "$ZABBLY_FPR" ]; then
        echo "$1: key fingerprint '$fpr' is not Zabbly's $ZABBLY_FPR" >&2
        exit 1
    fi
}

# 1. Incus 7.0 LTS from the Zabbly repository, set up per its README.
if ! command -v curl >/dev/null 2>&1 || ! command -v gpg >/dev/null 2>&1; then
    apt-get update
    apt-get install -y curl gpg
fi
if [ -f "$ZABBLY_KEY" ]; then
    check_zabbly_key "$ZABBLY_KEY"
else
    curl -fsSL https://pkgs.zabbly.com/key.asc -o "$TMP/zabbly.asc"
    check_zabbly_key "$TMP/zabbly.asc"
    install -D -m 0644 "$TMP/zabbly.asc" "$ZABBLY_KEY"
fi
SOURCES="Enabled: yes
Types: deb
URIs: https://pkgs.zabbly.com/incus/lts-7.0
Suites: $(. /etc/os-release && echo "$VERSION_CODENAME")
Components: main
Architectures: $(dpkg --print-architecture)
Signed-By: $ZABBLY_KEY"
if [ "$(cat "$ZABBLY_SOURCES" 2>/dev/null)" != "$SOURCES" ]; then
    printf '%s\n' "$SOURCES" > "$ZABBLY_SOURCES"
fi
# Zabbly versions carry epoch 1, so they also win over the distro's own incus.
case "$(dpkg-query -W -f='${Version}' incus 2>/dev/null)" in
    1:7.0.*) ;;
    *)
        apt-get update
        apt-get install -y incus
        version="$(dpkg-query -W -f='${Version}' incus)"
        case "$version" in
            1:7.0.*) ;;
            *)
                echo "installed incus $version, expected Zabbly 7.0 LTS (1:7.0.*)" >&2
                exit 1
                ;;
        esac
        ;;
esac

# 2. Storage pool. `admin init --minimal` is avoided throughout: its
# auto-subnet step fails inside nested VMs (lima/vz) and aborts init half-done,
# leaving no network and an empty default profile. Each piece below is
# provisioned explicitly and idempotently instead.
if ! incus storage list -f csv 2>/dev/null | grep -q "^default,"; then
    incus storage create default dir
fi

# 3. HTTPS listener (idempotent: setting the same value is a no-op).
incus config set core.https_address=127.0.0.1:8443

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
    incus image copy images:alpine/3.24 local: --alias "$ALIAS"
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

incus version
echo "provisioned. source $E2E_DIR/env then: uv run python dev.py e2e"
