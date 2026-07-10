#!/usr/bin/env bash
# Loop Engineering OS — GitHub installer
# curl -fsSL https://raw.githubusercontent.com/harshpgoti/loop-engineer/main/install.sh | bash
# curl -fsSL .../install.sh | bash -s -- --use-cwd   # local memory in current folder

set -euo pipefail

REPO="${LOOP_ENGINE_REPO:-https://github.com/harshpgoti/loop-engineer.git}"
REF="${LOOP_ENGINE_REF:-main}"
DRY_RUN=0
NO_PATH=0
WORKSPACE_NAME="${LOOP_WORKSPACE_NAME:-global}"
MEMORY_MODE="${LOOP_MEMORY_MODE:-}"
USE_CWD=0
WORKSPACE=""

usage() {
  cat <<'EOF'
Loop Engineer installer

  --dry-run
  --no-path
  --use-cwd              Local memory in current directory
  --workspace PATH       Local product folder
  --name NAME            Registry name (default: global, or folder name with --use-cwd)
  --memory-mode MODE     local or global (default: global)
  --ref REF
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --no-path) NO_PATH=1; shift ;;
    --use-cwd) USE_CWD=1; shift ;;
    --workspace) WORKSPACE="${2:-}"; shift 2 ;;
    --name) WORKSPACE_NAME="${2:-}"; shift 2 ;;
    --memory-mode) MEMORY_MODE="${2:-}"; shift 2 ;;
    --ref) REF="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ "$(uname -s)" == MINGW* || "$(uname -s)" == MSYS* || "$(uname -s)" == CYGWIN* ]]; then
  echo "Use install.ps1 on Windows." >&2
  exit 1
fi

LOOP_HOME="${LOOP_ENGINEER_HOME:-${LOOP_HOME:-$HOME/.loop-engineer}}"
APP="$LOOP_HOME/app"
BIN="$LOOP_HOME/bin"

if [[ "$USE_CWD" -eq 1 ]]; then
  WORKSPACE="$(pwd)"
  MEMORY_MODE="local"
  if [[ "$WORKSPACE_NAME" == "global" ]]; then
    WORKSPACE_NAME="$(basename "$WORKSPACE")"
  fi
fi

if [[ -n "$MEMORY_MODE" && "$MEMORY_MODE" != "local" && "$MEMORY_MODE" != "global" ]]; then
  echo "Invalid --memory-mode '$MEMORY_MODE'. Valid values: local, global." >&2
  exit 1
fi

if [[ -z "$MEMORY_MODE" ]]; then
  if [[ -n "$WORKSPACE" ]]; then MEMORY_MODE="local"; else MEMORY_MODE="global"; fi
fi

if [[ "$MEMORY_MODE" == "global" ]]; then
  WORKSPACE="$LOOP_HOME/data"
elif [[ -z "$WORKSPACE" ]]; then
  WORKSPACE="$(pwd)"
fi

run() { if [[ "$DRY_RUN" -eq 1 ]]; then printf '[dry-run] %s\n' "$*"; else "$@"; fi; }

pick_python() {
  if command -v python3 >/dev/null 2>&1; then echo python3
  elif command -v python >/dev/null 2>&1; then echo python
  else echo "Python 3.10+ required." >&2; exit 1; fi
}

command -v git >/dev/null 2>&1 || { echo "git required." >&2; exit 1; }
PYTHON="$(pick_python)"

echo "==> Loop Engineer installer"
echo "==> Home=$LOOP_HOME"
echo "==> App=$APP"
echo "==> Memory mode=$MEMORY_MODE"
echo "==> Data workspace=$WORKSPACE"

run mkdir -p "$LOOP_HOME" "$APP" "$LOOP_HOME/data/registry" "$BIN"

if [[ -d "$APP/.git" ]]; then
  run git -C "$APP" fetch origin "$REF" --tags
  run git -C "$APP" checkout "$REF"
  run git -C "$APP" pull --ff-only origin "$REF" || true
else
  run git clone --depth 1 --branch "$REF" "$REPO" "$APP"
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "[dry-run] write $BIN/loop"
else
  cat >"$BIN/loop" <<EOF
#!/usr/bin/env bash
export LOOP_ENGINEER_HOME="$LOOP_HOME"
exec "$PYTHON" "$APP/scripts/loop_cli.py" "\$@"
EOF
  chmod +x "$BIN/loop"
fi

if [[ "$NO_PATH" -eq 0 ]]; then
  line="export LOOP_ENGINEER_HOME=\"$LOOP_HOME\"; export PATH=\"\$LOOP_HOME/bin:\$PATH\""
  for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
    if [[ -f "$rc" ]] && grep -Fq 'LOOP_ENGINEER_HOME' "$rc" 2>/dev/null; then continue; fi
    if [[ "$DRY_RUN" -eq 1 ]]; then echo "[dry-run] PATH -> $rc"; elif [[ -f "$rc" || "$rc" == "$HOME/.bashrc" ]]; then
      printf '\n# Loop Engineer\n%s\n' "$line" >>"$rc"
    fi
  done
  export LOOP_ENGINEER_HOME="$LOOP_HOME"
  export PATH="$BIN:$PATH"
fi

SETUP_ARGS=(--workspace "$WORKSPACE" --name "$WORKSPACE_NAME")
if [[ "$MEMORY_MODE" == "local" ]]; then
  SETUP_ARGS+=(--memory-mode local)
fi

run "$PYTHON" "$APP/scripts/setup_loop_engine.py" "${SETUP_ARGS[@]}"
run "$PYTHON" "$APP/scripts/doctor.py" --workspace "$WORKSPACE" || true

cat <<EOF

Installed.
  Home:         $LOOP_HOME
  App:          $APP
  Memory mode:  $MEMORY_MODE
  Data:         $WORKSPACE
  CLI:          loop

Open your agent in: $APP
Then run: /plan-loop
EOF
