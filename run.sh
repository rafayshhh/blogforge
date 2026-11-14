#!/usr/bin/env bash
# BlogForge Linux/macOS launcher

set -e

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

python3 -m app.main "$@"
