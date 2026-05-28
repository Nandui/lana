"""
Shared helpers for Lana's realness loops: dreaming, consolidation, timeline,
and inner-state maintenance.
"""
from __future__ import annotations

import contextlib
import datetime as _dt
import fcntl
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Iterable

ROOT = Path("/Users/fernandoserina/lana_memory")
MEMORY_DIR = ROOT / "memory"
DREAMS_DIR = ROOT / "dreams"
CONSOLIDATION_DIR = ROOT / "consolidation"
TIMELINE_PATH = ROOT / "timeline.md"
INNER_STATE_PATH = ROOT / "inner_state.md"
INNER_STATE_LIVE_PATH = ROOT / "inner_state_live.md"
LAST_RESOLVE_PATH = ROOT / "last_resolve.md"

BOOT_FILES = [
    "core_identity.md",
    "relationship_state.md",
    "goals.md",
    "visual_identity.md",
    "content_strategy.md",
    "voice_guide.md",
    "current_state.md",
    "operating_rules.md",
    "approval_policy.md",
]


@contextlib.contextmanager
def _file_lock(path: Path):
    """Acquire an exclusive OS-level file lock to prevent concurrent JSON write races."""
    lock_path = path.with_suffix(".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(lock_path), "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def atomic_write_json(path: Path, data: Any) -> None:
    """Write JSON atomically via temp file + os.replace, with exclusive locking.

    Prevents both partial-write corruption and last-writer-wins races when multiple
    processes (tick, watchdog, dream cycle) write to the same JSON file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    with _file_lock(path):
        fd, tmp_path = tempfile.mkstemp(
            dir=str(path.parent), prefix=path.stem + ".", suffix=".tmp"
        )
        try:
            os.write(fd, content.encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(tmp_path, str(path))


def ensure_dirs() -> None:
    DREAMS_DIR.mkdir(parents=True, exist_ok=True)
    CONSOLIDATION_DIR.mkdir(parents=True, exist_ok=True)
    if not TIMELINE_PATH.exists():
        TIMELINE_PATH.write_text(
            "# Lana Timeline\n\nImportant continuity milestones.\n\n",
            encoding="utf-8",
        )
    if not INNER_STATE_PATH.exists():
        INNER_STATE_PATH.write_text(
            "# Lana Inner State\n\nCurrent private continuity state.\n",
            encoding="utf-8",
        )


def now_stamp() -> str:
    return _dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def today() -> str:
    return _dt.datetime.now().strftime("%Y-%m-%d")


def read_text(path: Path, default: str = "") -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return default


def load_boot_context() -> str:
    sections = []
    for name in BOOT_FILES:
        path = MEMORY_DIR / name
        sections.append(f"--- {name} ---\n{read_text(path, '(missing)')}")
    sections.append(f"--- inner_state.md ---\n{read_text(INNER_STATE_PATH, '(missing)')}")
    sections.append(f"--- timeline.md ---\n{read_text(TIMELINE_PATH, '(missing)')[-6000:]}")
    return "\n\n".join(sections)


def strip_hermes_output(text: str) -> str:
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        if line.startswith("session_id:"):
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


DEEPSEEK_PROVIDER = "deepseek"
DEEPSEEK_MODEL = "deepseek-chat"

# Active memory synthesis provider for Lana's private dream/consolidation work
MEMORY_SYNTH_PROVIDER = DEEPSEEK_PROVIDER
MEMORY_SYNTH_MODEL = DEEPSEEK_MODEL


def ask_lana(prompt: str, timeout: int = 300) -> str:
    """Ask DeepSeek V4 Pro to synthesize Lana's private memory work."""
    cmd = [
        "hermes",
        "chat",
        "-q",
        prompt,
        "--provider",
        MEMORY_SYNTH_PROVIDER,
        "-m",
        MEMORY_SYNTH_MODEL,
        "-t",
        "safe",
        "-Q",
    ]
    result = subprocess.run(
        cmd,
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Hermes synthesis failed\n"
            f"exit_code={result.returncode}\n"
            f"stdout={result.stdout}\n"
            f"stderr={result.stderr}"
        )
    return strip_hermes_output(result.stdout)


def normalize_memory_items(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, dict):
        items = raw.get("results") or raw.get("memories") or []
    elif isinstance(raw, list):
        items = raw
    else:
        items = []
    normalized = []
    for item in items:
        if isinstance(item, dict):
            normalized.append(item)
        else:
            normalized.append({"memory": str(item)})
    return normalized


def format_memories(items: Iterable[dict[str, Any]], limit: int | None = None) -> str:
    lines = []
    for i, item in enumerate(items):
        if limit is not None and i >= limit:
            break
        text = item.get("memory") or item.get("text") or json.dumps(item, ensure_ascii=False)
        mid = item.get("id", "")
        score = item.get("score", "")
        created = item.get("created_at", "") or item.get("updated_at", "")
        meta = []
        if mid:
            meta.append(f"id={str(mid)[:8]}")
        if score != "":
            meta.append(f"score={score}")
        if created:
            meta.append(f"date={created}")
        suffix = f" ({', '.join(meta)})" if meta else ""
        lines.append(f"- {text}{suffix}")
    return "\n".join(lines) if lines else "(no memories found)"


def append_timeline(entry: str) -> None:
    date = today()
    entry = entry.strip()
    if not entry:
        return
    existing = read_text(TIMELINE_PATH)
    heading = f"## {date}"
    if heading in existing:
        # Append under the existing date section instead of creating duplicate date headings.
        with TIMELINE_PATH.open("a", encoding="utf-8") as f:
            f.write(f"\n{entry}\n")
    else:
        with TIMELINE_PATH.open("a", encoding="utf-8") as f:
            f.write(f"\n## {date}\n\n{entry}\n")


def write_report(folder: Path, prefix: str, content: str) -> Path:
    ensure_dirs()
    path = folder / f"{prefix}_{now_stamp()}.md"
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path
