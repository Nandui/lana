#!/usr/bin/env python3
"""
Quarantine solo-session artifacts whose date doesn't match the expected year.

Usage:
  python explorations/cleanup_bad_dates.py            # dry-run (safe, default)
  python explorations/cleanup_bad_dates.py --apply    # actually move files
  python explorations/cleanup_bad_dates.py --year 2027  # override expected year

Bad-date criteria:
  - The YYYY extracted from the file/directory name is not the expected year.
  - The date is older than --max-age-days (default: 45) relative to today.
  - The date is more than --future-days (default: 1) in the future.

Files are moved to  explorations/quarantine/bad-dates/<original-relative-path>
and a manifest is written to explorations/quarantine/bad-dates/manifest.json.
"""

import argparse
import json
import re
import shutil
import sys
from datetime import date, datetime, timezone
from pathlib import Path

EXPLORATIONS = Path(__file__).parent
SESSIONS_DIR = EXPLORATIONS / "sessions"
SAVES_DIR = EXPLORATIONS / "saves"
QUARANTINE_DIR = EXPLORATIONS / "quarantine" / "bad-dates"

DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def _extract_date(path: Path) -> date | None:
    """Return the first YYYY-MM-DD date found in any path component (dir or filename)."""
    # Walk from saves/ or sessions/ root toward the file, checking each part.
    for part in path.parts:
        m = DATE_RE.match(part)
        if not m:
            continue
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    return None


def _extract_year(path: Path) -> int | None:
    found = _extract_date(path)
    return found.year if found else None


def _collect_artifacts() -> list[Path]:
    """Yield all individual artifact files under sessions/ and saves/."""
    files = []
    for base in (SESSIONS_DIR, SAVES_DIR):
        if base.exists():
            for p in sorted(base.rglob("*")):
                if p.is_file():
                    files.append(p)
    return files


def _bad_date_reason(path: Path, expected_year: int, today: date, max_age_days: int, future_days: int) -> str | None:
    found = _extract_date(path)
    if found is None:
        return None  # no date in path — don't touch it
    if found.year != expected_year:
        return f"year {found.year} != expected {expected_year}"
    age_days = (today - found).days
    if age_days > max_age_days:
        return f"date {found.isoformat()} is {age_days} days old (> {max_age_days})"
    if age_days < -future_days:
        return f"date {found.isoformat()} is {-age_days} days in the future (> {future_days})"
    return None


def _relative_to_explorations(path: Path) -> Path:
    return path.relative_to(EXPLORATIONS)


def run(apply: bool, expected_year: int, max_age_days: int, future_days: int) -> None:
    artifacts = _collect_artifacts()
    today = datetime.now().date()
    bad_with_reasons: list[tuple[Path, str]] = []
    for artifact in artifacts:
        reason = _bad_date_reason(artifact, expected_year, today, max_age_days, future_days)
        if reason:
            bad_with_reasons.append((artifact, reason))

    if not bad_with_reasons:
        print(
            f"[cleanup] No bad-date artifacts found "
            f"(expected year: {expected_year}, max age: {max_age_days} days, future allowance: {future_days} days)."
        )
        return

    print(f"[cleanup] {'DRY RUN — ' if not apply else ''}Found {len(bad_with_reasons)} bad-date artifact(s):")
    manifest_entries = []

    for src, reason in bad_with_reasons:
        rel = _relative_to_explorations(src)
        dest = QUARANTINE_DIR / rel
        print(f"  {'WOULD MOVE' if not apply else 'MOVING':12s}  {rel}  ({reason})")
        manifest_entries.append(
            {
                "original": str(rel),
                "quarantine_path": str(QUARANTINE_DIR / rel),
                "reason": reason,
                "moved_at": datetime.now(tz=timezone.utc).isoformat(),
                "applied": apply,
            }
        )

    if apply:
        for src, _reason in bad_with_reasons:
            rel = _relative_to_explorations(src)
            dest = QUARANTINE_DIR / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))

        QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
        manifest_path = QUARANTINE_DIR / "manifest.json"
        existing = []
        if manifest_path.exists():
            try:
                existing = json.loads(manifest_path.read_text())
            except json.JSONDecodeError:
                pass
        manifest_path.write_text(
            json.dumps(existing + manifest_entries, indent=2, ensure_ascii=False)
        )
        print(f"\n[cleanup] Moved {len(bad_with_reasons)} file(s). Manifest → {manifest_path}")
    else:
        print(
            f"\n[cleanup] DRY RUN complete. Re-run with --apply to actually move files."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually move bad-date files (default: dry-run only)",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=datetime.now().year,
        help="Expected year for valid artifacts (default: current year)",
    )
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=45,
        help="Quarantine dated artifacts older than this many days (default: 45)",
    )
    parser.add_argument(
        "--future-days",
        type=int,
        default=1,
        help="Quarantine artifacts dated more than this many days in the future (default: 1)",
    )
    args = parser.parse_args()
    run(
        apply=args.apply,
        expected_year=args.year,
        max_age_days=args.max_age_days,
        future_days=args.future_days,
    )


if __name__ == "__main__":
    main()
