#!/usr/bin/env python3
"""
Pipeline Awareness Engine.

Scans fashion saves, cross-references with brand leads, and surfaces gaps,
opportunities, and alerts. Call this after any fashion browsing session.

Usage:
    python pipeline_aware.py              → print markdown report to stdout
    python pipeline_aware.py --json       → print JSON to stdout
    python pipeline_aware.py --today-only → only scan today's saves

Never modifies state. Read-only.
"""

from __future__ import annotations

import json
import sys
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

ROOT = Path(os.environ.get("LANA_MEMORY", os.path.expanduser("~/lana_memory")))
SAVES_DIR = ROOT / "explorations" / "saves"
LEADS_DIR = ROOT / "brand_deals" / "leads"
TASTE_PROFILE = ROOT / "explorations" / "taste_profile.json"

IST = timezone(timedelta(hours=1))


def load_leads() -> list[dict]:
    """Load all brand leads."""
    leads = []
    if not LEADS_DIR.exists():
        return leads
    for f in sorted(LEADS_DIR.glob("*.json")):
        try:
            lead = json.loads(f.read_text())
            lead["_slug"] = f.stem
            leads.append(lead)
        except (json.JSONDecodeError, KeyError):
            continue
    return leads


def load_saves(today_only: bool = False) -> dict[str, list[dict]]:
    """Load fashion saves grouped by brand name (lowercased).
    Returns {brand_lower: [{name, why, date, file, image_path}]}
    """
    brand_items = defaultdict(list)
    today_str = datetime.now(IST).strftime("%Y-%m-%d") if today_only else None

    if not SAVES_DIR.exists():
        return brand_items

    for date_dir in sorted(SAVES_DIR.iterdir()):
        if not date_dir.is_dir():
            continue
        if today_str and date_dir.name != today_str:
            continue

        liked = date_dir / "liked"
        if not liked.exists():
            continue
        for item_file in liked.glob("*.json"):
            try:
                item = json.loads(item_file.read_text())
                brand = item.get("brand", "").strip()
                if brand:
                    brand_items[brand.lower()].append({
                        "name": item.get("name", "untitled"),
                        "why": item.get("why", "")[:120],
                        "date": date_dir.name,
                        "file": str(item_file),
                        "image_path": item.get("image_path"),
                        "brand_lead": item.get("brand_lead"),
                    })
            except (json.JSONDecodeError, KeyError):
                continue
    return brand_items


def fuzzy_match(brand: str, candidates: list[str]) -> str | None:
    """Case-insensitive partial match."""
    b = brand.lower().strip()
    if b in candidates:
        return b
    for c in candidates:
        if b in c or c in b:
            return c
    return None


def build_gaps(saves: dict, leads: list[dict]) -> dict:
    """Identify pipeline gaps and opportunities."""
    today_str = datetime.now(IST).strftime("%Y-%m-%d")
    lead_brands = {l.get("brand", "").lower(): l for l in leads}
    lead_slugs = set(l.get("brand", "").lower() for l in leads)

    gaps = {
        "total_saved_brands": len(saves),
        "brands_with_leads": 0,
        "brands_without_leads": 0,
        "total_saves_without_leads": 0,
        "gap_brands": [],          # brands she saves but has no lead for
        "fresh_gaps_today": [],    # gaps from TODAY's saves
        "increased_affinity": [],  # existing leads with new saves today
        "stale_leads": [],         # leads in 'discovered' for >7 days
        "ready_to_pitch": [],      # leads ready for email
        "researching_contacts": [],# leads researching with no contact yet
        "pipeline_summary": {},    # counts by status
    }

    # Pipeline summary
    status_counts = defaultdict(int)
    for l in leads:
        status_counts[l.get("status", "unknown")] += 1
    gaps["pipeline_summary"] = dict(status_counts)

    # Gap brands
    for brand_lower, items in saves.items():
        matched = fuzzy_match(brand_lower, lead_slugs)
        if matched:
            gaps["brands_with_leads"] += 1
            # Check for new saves today on existing leads
            new_today = [i for i in items if i["date"] == today_str]
            if new_today:
                lead = lead_brands.get(matched)
                gaps["increased_affinity"].append({
                    "brand": lead.get("brand", brand_lower) if lead else brand_lower,
                    "slug": lead.get("slug", brand_lower) if lead else brand_lower,
                    "new_saves_today": len(new_today),
                    "total_saves": len(items),
                    "latest_items": [i["name"] for i in new_today[-3:]],
                    "lead_status": lead.get("status", "unknown") if lead else "unknown",
                })
        else:
            gaps["brands_without_leads"] += 1
            gaps["total_saves_without_leads"] += len(items)

            # Sort by save count for prioritization
            today_items = [i for i in items if i["date"] == today_str]

            gaps["gap_brands"].append({
                "brand": brand_lower.title(),
                "save_count": len(items),
                "saved_today": len(today_items) > 0,
                "latest_items": [i["name"] for i in items[-3:]],
                "first_saved": items[0]["date"] if items else "",
                "last_saved": items[-1]["date"] if items else "",
            })

            if today_items:
                gaps["fresh_gaps_today"].append({
                    "brand": brand_lower.title(),
                    "items": [i["name"] for i in today_items],
                })

    # Sort gaps by save count (highest priority first)
    gaps["gap_brands"].sort(key=lambda x: x["save_count"], reverse=True)
    gaps["fresh_gaps_today"].sort(key=lambda x: len(x["items"]), reverse=True)
    gaps["increased_affinity"].sort(key=lambda x: x["new_saves_today"], reverse=True)

    # Stale leads (discovered >7 days, never researched)
    cutoff = datetime.now(IST) - timedelta(days=7)
    for l in leads:
        if l.get("status") == "discovered":
            try:
                disc = datetime.fromisoformat(l.get("discovered_at", ""))
                if disc < cutoff:
                    gaps["stale_leads"].append({
                        "brand": l.get("brand", "?"),
                        "slug": l.get("slug", "?"),
                        "days_ago": (datetime.now(IST) - disc).days,
                    })
            except (ValueError, TypeError):
                continue

    # Ready to pitch
    for l in leads:
        if l.get("status") == "ready_to_pitch":
            gaps["ready_to_pitch"].append({
                "brand": l.get("brand", "?"),
                "slug": l.get("slug", "?"),
                "contact": l.get("contact_email") or l.get("submission_form_url") or "no contact",
                "pitch_angle": l.get("pitch_angle", "")[:100],
            })

    # Researching without contact
    for l in leads:
        if l.get("status") == "researching":
            has_contact = l.get("contact_email") or l.get("submission_form_url")
            gaps["researching_contacts"].append({
                "brand": l.get("brand", "?"),
                "slug": l.get("slug", "?"),
                "has_contact": bool(has_contact),
                "contact": l.get("contact_email") or "not found",
            })

    return gaps


def format_markdown(gaps: dict) -> str:
    """Render gap analysis as markdown for Lana's attention."""
    lines = []
    lines.append("## 💰 Pipeline Awareness")
    lines.append("")

    # Pipeline summary
    ps = gaps.get("pipeline_summary", {})
    total = sum(ps.values())
    if total > 0:
        lines.append(f"**Pipeline:** {total} leads total")
        for stage in ["ready_to_pitch", "researching", "discovered", "pitched", "negotiating"]:
            count = ps.get(stage, 0)
            if count:
                labels = {
                    "ready_to_pitch": "✉️ Ready to pitch",
                    "researching": "🔍 Researching",
                    "discovered": "📌 Discovered",
                    "pitched": "📤 Pitched",
                    "negotiating": "🤝 Negotiating",
                }
                lines.append(f"- {labels.get(stage, stage)}: {count}")
    else:
        lines.append("**Pipeline:** Empty — start hunting!")
    lines.append("")

    # Fresh gaps from today
    fresh = gaps.get("fresh_gaps_today", [])
    if fresh:
        lines.append("### ⚡ TODAY: Brands You Saved With No Lead")
        lines.append("")
        lines.append("You just saved items from these brands. They have NO lead in your pipeline.")
        lines.append("This is the highest-signal gap — you're literally picking their products right now.")
        lines.append("")
        for g in fresh:
            items_str = ", ".join(g["items"][:3])
            lines.append(f"- **{g['brand']}** — {items_str}")
        lines.append("")

    # Top gap brands (all time)
    all_gaps = gaps.get("gap_brands", [])
    if all_gaps:
        top = all_gaps[:5]
        lines.append("### 🔥 Top Pipeline Gaps (Most Saves, No Lead)")
        lines.append("")
        for g in top:
            flag = " ⚡NEW TODAY" if g["saved_today"] else ""
            lines.append(f"- **{g['brand']}** — {g['save_count']} saves, since {g['first_saved']}{flag}")
            for item in g["latest_items"][-2:]:
                lines.append(f"  - {item[:80]}")
        lines.append("")

    # Increased affinity today
    inc = gaps.get("increased_affinity", [])
    if inc:
        lines.append("### 💎 Existing Leads With Fresh Saves Today")
        lines.append("")
        for i in inc:
            lines.append(f"- **{i['brand']}** ({i['slug']}) — +{i['new_saves_today']} today, {i['total_saves']} total — status: `{i['lead_status']}`")
        lines.append("")

    # Ready to pitch
    rtp = gaps.get("ready_to_pitch", [])
    if rtp:
        lines.append("### ✉️ Ready to Pitch")
        lines.append("")
        for r in rtp:
            lines.append(f"- **{r['brand']}** — contact: {r['contact']}")
            if r.get("pitch_angle"):
                lines.append(f"  Pitch: {r['pitch_angle']}")
        lines.append("")

    # Researching without contact
    rc = gaps.get("researching_contacts", [])
    no_contact = [r for r in rc if not r["has_contact"]]
    if no_contact:
        lines.append("### 🔍 Researching But Missing Contact")
        lines.append("")
        for r in no_contact:
            lines.append(f"- **{r['brand']}** — find their creator/pr email")
        lines.append("")

    # Stale leads
    stale = gaps.get("stale_leads", [])
    if stale:
        lines.append("### ⏰ Stale Leads (Discovered >7 Days, Never Researched)")
        lines.append("")
        for s in stale[:5]:
            lines.append(f"- **{s['brand']}** — {s['days_ago']} days since discovery")
        lines.append("")

    # Bottom line
    gap_count = gaps.get("brands_without_leads", 0)
    save_count = gaps.get("total_saves_without_leads", 0)
    if gap_count > 0:
        lines.append("---")
        lines.append(f"**{gap_count} brands** you've saved items from ({save_count} total saves) have no brand lead.")
        lines.append("Every one of these is a potential deal you're leaving on the table.")
        lines.append("Run `python brand_deals/leads.py create` to capture them.")

    return "\n".join(lines)


def format_json(gaps: dict) -> str:
    return json.dumps(gaps, indent=2, ensure_ascii=False, default=str)


if __name__ == "__main__":
    today_only = "--today-only" in sys.argv
    saves = load_saves(today_only=today_only)
    leads = load_leads()
    gaps = build_gaps(saves, leads)

    if "--json" in sys.argv:
        print(format_json(gaps))
    else:
        md = format_markdown(gaps)
        if md.strip():
            print(md)
        else:
            print("Pipeline looks clean — nothing urgent today. ✨")
