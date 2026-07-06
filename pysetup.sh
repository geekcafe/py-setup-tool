#!/usr/bin/env bash
set -euo pipefail

# pysetup.sh - Cross-platform setup for python projects

# Default mode: ask the user
FETCH_LATEST="interactive"
CI_MODE="no"

# Check if .pysetup.json exists and has a repo_update_preference
if [ -f ".pysetup.json" ]; then
  # Try to extract repo_update_preference using grep and sed
  # This avoids requiring jq or python for JSON parsing
  STORED_PREFERENCE=$(grep -o '"repo_update_preference"\s*:\s*"[^"]*"' .pysetup.json 2>/dev/null | sed 's/.*"\([^"]*\)".*/\1/' || echo "")
  
  if [ -n "$STORED_PREFERENCE" ]; then
    echo "🔒 Using stored repository update preference: $STORED_PREFERENCE"
    FETCH_LATEST="$STORED_PREFERENCE"
  fi
fi

usage() {
  cat <<EOF
Usage: $0 [options]

Options:
  -u, --update       Automatically pull the latest pysetup.py (no prompt)
  -n, --no-update    Skip pulling the latest pysetup.py
  --ci               CI/CD mode (same as --update)
  -h, --help         Show this help message and exit
EOF
  exit 0
}

# --- parse command-line flags ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    -u|--update)      FETCH_LATEST="yes" ;;
    -n|--no-update)   FETCH_LATEST="no"  ;;
    --ci)             FETCH_LATEST="yes"; CI_MODE="yes" ;;
    -h|--help)        usage ;;
    *)  echo "Unknown option: $1" >&2
        usage
        ;;
  esac
  shift
done

# --- check if pysetup.py exists ---
if [ ! -f "pysetup.py" ]; then
  echo "🔍 pysetup.py not found. Will automatically download it."
  FETCH_LATEST="yes"
# --- interactive prompt if needed ---
elif [[ "$FETCH_LATEST" == "interactive" ]]; then
  read -r -p "Pull latest pysetup.py from repository? [y/N] " answer
  if [[ "$answer" =~ ^[Yy] ]]; then
    FETCH_LATEST="yes"
  else
    FETCH_LATEST="no"
  fi
fi

# --- fetch if requested ---
if [[ "$FETCH_LATEST" == "yes" ]]; then
  echo "🔄 Fetching latest pysetup.py..."
  curl -sSL \
    https://raw.githubusercontent.com/geekcafe/py-setup-tool/main/pysetup.py \
    -o pysetup.py
fi

# --- detect python command ---
if command -v python3 &>/dev/null; then
  PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
  PYTHON_CMD="python"
else
  echo "❌ Neither python3 nor python found. Please install Python 3."
  exit 1
fi

# --- detect pip command (for any direct pip usage) ---
if command -v pip3 &>/dev/null; then
  PIP_CMD="pip3"
elif command -v pip &>/dev/null; then
  PIP_CMD="pip"
else
  # pip might not be needed directly, but warn
  PIP_CMD=""
  echo "⚠️  Neither pip nor pip3 found in PATH (will use venv pip after setup)."
fi

# --- run the Python installer ---
if [[ "$CI_MODE" == "yes" ]]; then
  echo "🤖 Running in CI/CD mode..."
  $PYTHON_CMD pysetup.py --ci
else
  $PYTHON_CMD pysetup.py
fi
