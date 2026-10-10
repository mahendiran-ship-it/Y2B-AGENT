#!/usr/bin/env bash
# Y2B Agent installer  -  Made by : Mahzend
# Usage:  bash install.sh            install / update (also installs the PDF/Word/PowerPoint/Excel packages)
#         bash install.sh --no-docs  skip the document packages (chat + coding agent only)
#         bash install.sh --uninstall
set -e

APP_DIR="${Y2B_HOME:-$HOME/.y2b}"
IS_TERMUX=0
if [ -n "${PREFIX:-}" ] && [ -d "$PREFIX/bin" ] && [[ "$PREFIX" == *com.termux* ]]; then IS_TERMUX=1; fi
if [ "$IS_TERMUX" = 1 ]; then BIN_DIR="$PREFIX/bin"; else BIN_DIR="$HOME/.local/bin"; fi

if [ "${1:-}" = "--uninstall" ]; then
  rm -f "$BIN_DIR/y2b" "$APP_DIR/y2b_agent.py" "$APP_DIR/y2b_docs.py"
  echo "Y2B Agent removed (your memory/config in $APP_DIR was kept)."
  exit 0
fi

WANT_DOCS=1
if [ "${1:-}" = "--no-docs" ] || [ "${Y2B_SKIP_DOCS:-}" = "1" ]; then WANT_DOCS=0; fi

echo "==> Y2B Agent installer"

if [ "$IS_TERMUX" = 1 ]; then
  echo "==> Installing Termux packages (python, llama-cpp)..."
  pkg install -y python || true
  pkg install -y llama-cpp || echo "!! Could not install llama-cpp from pkg. Build llama.cpp yourself or use --url."
  if [ "$WANT_DOCS" = 1 ]; then
    # Prebuilt Pillow/lxml avoid a long (and often failing) compile on the phone.
    echo "==> Installing Termux packages for documents (python-pip, python-pillow, python-lxml)..."
    pkg install -y python-pip || true
    pkg install -y python-pillow python-lxml || echo "!! Could not install python-pillow / python-lxml from pkg; pip will try to build them."
  fi
fi

PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then echo "!! Python 3 not found. Install it first."; exit 1; fi

mkdir -p "$APP_DIR" "$BIN_DIR"
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$SRC_DIR/y2b_agent.py" "$APP_DIR/y2b_agent.py"
cp "$SRC_DIR/y2b_docs.py" "$APP_DIR/y2b_docs.py"

cat > "$BIN_DIR/y2b" <<EOF
#!/usr/bin/env bash
exec "$PY" "$APP_DIR/y2b_agent.py" "\$@"
EOF
chmod +x "$BIN_DIR/y2b"

case ":$PATH:" in *":$BIN_DIR:"*) ;; *) echo "!! Add $BIN_DIR to your PATH:  export PATH=\"$BIN_DIR:\$PATH\"" ;; esac

if [ "$WANT_DOCS" = 1 ]; then
  echo "==> Installing document packages (reportlab, python-docx, python-pptx, openpyxl)..."
  DOCS_OK=0
  for flags in "" "--user" "--break-system-packages"; do
    # shellcheck disable=SC2086
    if "$PY" -m pip install $flags -r "$SRC_DIR/requirements.txt"; then DOCS_OK=1; break; fi
  done
  if [ "$DOCS_OK" = 1 ] && "$PY" -c "import reportlab, docx, pptx, openpyxl" 2>/dev/null; then
    echo "==> Document tools ready (PDF, Word, PowerPoint, Excel)."
  else
    echo "!! Could not install the document packages. Y2B still works for chat and coding."
    echo "   Try by hand:  $PY -m pip install reportlab python-docx python-pptx openpyxl"
    echo "   (needs internet once; afterwards documents are created fully offline)"
  fi
  if [ "$IS_TERMUX" = 1 ] && [ ! -d "$HOME/storage/shared" ]; then
    echo "==> To save documents in your phone's \"AGENT WORK\" folder, grant storage access once:"
    echo "      termux-setup-storage      (tap Allow), then restart Termux"
  fi
fi

if command -v llama-server >/dev/null 2>&1; then echo "==> llama-server found: fast mode ready."; else echo "!! llama-server not found (slow fallback or --url will be used)."; fi
if ls "$HOME"/models/*.gguf >/dev/null 2>&1; then echo "==> Model(s) found in ~/models."; else
  echo "==> No model yet. Put any .gguf in ~/models, e.g.:"
  echo "    mkdir -p ~/models && cd ~/models"
  echo "    curl -L -O https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"
fi

echo
echo "Done!  Start it with:  y2b"
echo "Made by : Mahzend"
