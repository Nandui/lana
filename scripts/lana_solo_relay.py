#!/usr/bin/env python3
"""Relay Lana solo-session cron outputs from local disk to this chat.

Intended to run as a Hermes no_agent cron job with deliver="origin".
Empty stdout means no delivery.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

OUTPUT_ROOT = Path("/Users/fernandoserina/.hermes/cron/output")
STATE_PATH = Path("/Users/fernandoserina/.hermes/scripts/.lana_solo_relay_state.json")
MAX_AGE_SECONDS = 3 * 60 * 60
SOLO_JOBS = {
    "b4ec0f20c592": "Morning Solo",
    "9e5fe1688579": "Mid-Morning Solo",
    "fe48e96614d0": "Afternoon Solo",
    "f3628ce84f4a": "Late Afternoon Solo",
    "15da47b7b82f": "Early Evening Solo",
    "28937a502cad": "Evening Solo",
}


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"relayed": []}
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"relayed": []}
    if not isinstance(data.get("relayed"), list):
        data["relayed"] = []
    return data


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def latest_outputs() -> list[tuple[str, str, Path]]:
    now = time.time()
    found: list[tuple[str, str, Path]] = []
    for job_id, label in SOLO_JOBS.items():
        job_dir = OUTPUT_ROOT / job_id
        if not job_dir.exists():
            continue
        for path in sorted(job_dir.glob("*.md"), key=lambda p: p.stat().st_mtime):
            try:
                if now - path.stat().st_mtime <= MAX_AGE_SECONDS:
                    found.append((job_id, label, path))
            except OSError:
                continue
    return found


def extract_response(text: str) -> str:
    # Cron output files have a metadata/prompt block and then "## Response".
    marker = re.search(r"^## Response\s*$", text, flags=re.MULTILINE)
    if marker:
        body = text[marker.end():].strip()
        body = re.sub(r"^---\s*", "", body).strip()
        return body
    return text.strip()


def main() -> None:
    state = load_state()
    relayed = set(state.get("relayed", []))
    messages: list[str] = []
    new_relays: list[str] = []

    for job_id, label, path in latest_outputs():
        key = f"{job_id}:{path.name}"
        if key in relayed:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        response = extract_response(text)
        if not response or response.strip() == "[SILENT]":
            new_relays.append(key)
            continue
        messages.append(response)
        new_relays.append(key)

    if new_relays:
        # Keep recent relay history bounded.
        state["relayed"] = (state.get("relayed", []) + new_relays)[-200:]
        state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        save_state(state)

    if messages:
        print("\n\n---\n\n".join(messages))


if __name__ == "__main__":
    main()
