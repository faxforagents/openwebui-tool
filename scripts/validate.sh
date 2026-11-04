#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
python3 -m py_compile fax_for_agents.py
if ! python3 -c 'import pydantic' >/dev/null 2>&1; then
    echo 'Install the Open WebUI host dependency pydantic in your Python environment.' >&2
    exit 1
fi
if python3 -c 'import pytest' >/dev/null 2>&1; then
    python3 -m pytest -q tests
else
    python3 -m unittest discover -s tests -v
fi
