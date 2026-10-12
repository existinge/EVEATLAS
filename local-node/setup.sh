#!/usr/bin/env bash
# Idempotent setup for the paired local node. Never modifies an installed Ollama app.
set -euo pipefail
cd "$(dirname "$0")"

[[ "$(uname -s)" == "Darwin" && "$(uname -m)" == "arm64" ]] || { echo "Requires macOS on Apple Silicon"; exit 1; }
cfg() { python3 -c "import json,sys;d=json.load(open('node.json'))
for k in sys.argv[1].split('.'): d=d[k]
print(d)" "$1"; }

MINV=$(cfg ollama.min_version); PIN=$(cfg ollama.pinned); URL=$(cfg ollama.download)
PORT=$(cfg server.port); WORKER=$(cfg worker.model); DECIDER=$(cfg decider.model)
DEST="$HOME/.localnode/ollama-$PIN"

RAM_GB=$(( $(sysctl -n hw.memsize) / 1073741824 ))
FREE_GB=$(df -g / | awk 'NR==2{print $4}')
echo "RAM ${RAM_GB} GB, free disk ${FREE_GB} GB"
[[ $RAM_GB -ge 16 ]] || echo "WARNING: <16 GB RAM; the pair (~6 GB + context) may swap."
[[ $FREE_GB -ge 8 ]] || echo "WARNING: <8 GB free disk; model pulls may fail."

ver_ge() { [[ "$(printf '%s\n%s\n' "$2" "$1" | sort -V | head -n1)" == "$2" ]]; }  # $1 >= $2
BIN=""
for c in "$DEST/ollama" "$(command -v ollama || true)"; do
  [[ -n "$c" && -x "$c" ]] || continue
  v=$("$c" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)
  if [[ -n "$v" ]] && ver_ge "$v" "$MINV"; then BIN="$c"; break; fi
done
if [[ -z "$BIN" ]]; then
  echo "Installing pinned Ollama $PIN sidecar to $DEST (installed app is untouched)"
  mkdir -p "$DEST"; curl -fsSL -o "$DEST/o.tgz" "$URL"; tar xzf "$DEST/o.tgz" -C "$DEST"; rm "$DEST/o.tgz"
  BIN="$DEST/ollama"
fi
echo "Using $BIN ($("$BIN" --version 2>&1 | tail -1))"

# Pull models through a temporary server on the node port (reuses a running one).
STARTED=""
if ! curl -sf "http://127.0.0.1:$PORT/api/version" >/dev/null; then
  OLLAMA_HOST="127.0.0.1:$PORT" "$BIN" serve >/tmp/localnode-setup-server.log 2>&1 & STARTED=$!
  for _ in $(seq 1 30); do curl -sf "http://127.0.0.1:$PORT/api/version" >/dev/null && break; sleep 1; done
fi
for m in "$WORKER" "$DECIDER"; do echo "Pulling $m"; OLLAMA_HOST="127.0.0.1:$PORT" "$BIN" pull "$m"; done
[[ -n "$STARTED" ]] && kill "$STARTED" 2>/dev/null || true

echo; echo "Setup complete. Next:  python3 localnode.py start && python3 smoke_test.py"
