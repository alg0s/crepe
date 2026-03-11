#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${CREPE_REPO_URL:-https://github.com/alg0s/crepe.git}"
INSTALL_DIR="${CREPE_INSTALL_DIR:-$HOME/.local/share/crepe}"
BIN_DIR="${CREPE_BIN_DIR:-$HOME/.local/bin}"
CONFIG_DIR="${CREPE_CONFIG_DIR:-$HOME/.config/crepe}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-url)
      REPO_URL="$2"
      shift 2
      ;;
    --install-dir)
      INSTALL_DIR="$2"
      shift 2
      ;;
    --bin-dir)
      BIN_DIR="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

for cmd in git python3 npm; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command: $cmd" >&2
    exit 1
  fi
done

mkdir -p "$INSTALL_DIR"
if [[ -d "$INSTALL_DIR/.git" ]]; then
  echo "Updating existing install at $INSTALL_DIR"
  git -C "$INSTALL_DIR" fetch --all --tags
  git -C "$INSTALL_DIR" pull --ff-only
else
  rm -rf "$INSTALL_DIR"
  echo "Cloning $REPO_URL into $INSTALL_DIR"
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi

"$INSTALL_DIR/.venv/bin/python" -m pip install --upgrade pip
"$INSTALL_DIR/.venv/bin/pip" install -r requirements.txt

cd "$INSTALL_DIR/frontend"
npm install

mkdir -p "$CONFIG_DIR"
touch "$CONFIG_DIR/.env"
chmod 600 "$CONFIG_DIR/.env" || true
mkdir -p "$CONFIG_DIR/data"

(
  cd "$INSTALL_DIR/backend"
  CREPE_CONFIG_DIR="$CONFIG_DIR" CREPE_BASE_DIR="$CONFIG_DIR/data" CREPE_DB_PATH="$CONFIG_DIR/data/crepe.sqlite3" PYTHONPATH=. \
    "$INSTALL_DIR/.venv/bin/python" - <<'PY'
from crepe.config import load_config
from crepe.storage.db import RunDatabase

cfg = load_config()
RunDatabase(cfg.db_path)
print(cfg.db_path)
PY
)

mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/crepe" <<EOF
#!/usr/bin/env bash
exec "$INSTALL_DIR/run-crepe.sh" "\$@"
EOF
chmod +x "$BIN_DIR/crepe"

echo "Installed crepe launcher at $BIN_DIR/crepe"
echo "Config directory: $CONFIG_DIR"
echo "SQLite job DB: $CONFIG_DIR/data/crepe.sqlite3"
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  echo "Add this to your shell profile:"
  echo "  export PATH=\"$BIN_DIR:\$PATH\""
fi
echo ""
echo "Next steps:"
echo "  crepe web"
