#!/bin/bash

echo "========================================"
echo "  Face Check-in System - Mock Mode"
echo "========================================"
echo ""
echo "Starting local server on port 3000..."
echo ""

cd "$(dirname "$0")"

# Open browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:3000
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open http://localhost:3000 2>/dev/null || echo "Please open http://localhost:3000 manually"
fi

# Start server
python3 -m http.server 3000
