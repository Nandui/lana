#!/bin/bash
# Lana Reach-Out — checks if she should text Fernando, generates message if yes.
# Silent when nothing to say. Designed for no_agent cron (stdout = delivery).
cd /Users/fernandoserina/lana_memory || exit 0
exec .venv/bin/python3 reach_out.py
