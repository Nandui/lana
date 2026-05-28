#!/bin/bash
# Lana Life Tick — run via launchd every 30 minutes
cd /Users/fernandoserina/lana_memory
OUTPUT=$(.venv/bin/python3 life_tick.py 2>&1)
# Only print if there's meaningful output (not no-change)
if [ -n "$OUTPUT" ] && ! echo "$OUTPUT" | grep -qi "no change"; then
    echo "$OUTPUT"
fi
