#!/usr/bin/env bash
# Launch PDF Tool — macOS & Linux Launcher

# Navigate to the script directory
cd "$(dirname "$0")" || exit 1

# Detect python3 or python
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "Error: Python 3 could not be found."
    echo "Please install Python (https://www.python.org) and ensure it is in your PATH."
    read -rp "Press Enter to exit..."
    exit 1
fi

# Run the app
"$PYTHON_BIN" pdf_tool_main.py
STATUS=$?

if [ $STATUS -ne 0 ]; then
    echo ""
    echo "Application exited with error code $STATUS."
    echo "Make sure all dependencies are installed:"
    echo "    $PYTHON_BIN -m pip install -r requirements.txt"
    echo ""
    read -rp "Press Enter to exit..."
    exit $STATUS
fi
