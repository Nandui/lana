#!/usr/bin/env python3
"""Lana's brand deals pipeline manager.

Usage:
  python leads.py list [--status STATUS] [--category CAT] [--region REGION] [--min-score N]
  python leads.py show SLUG
  python leads.py score
  python leads.py report
  python leads.py crossref
  python leads.py missing
  python leads.py create BRAND --url URL --category CAT [options...]
  python leads.py update SLUG [--status STATUS] [--field value...]
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

BASE = Path(os.environ.get("LANA_MEMORY", os.path.expanduser("~/lana_memory")))
LEADS_DIR = BASE / "brand_deals" / "leads"
SAVES_DIR = BASE / "explorations" / "saves"
TASTE_PROFILE = BASE / "explorations" / "taste_profile.json"

# ── helpers ───────────────────────────────────────────────

def load_leads():
    """Load all lead JSON files from leads_dir."""
    leads = []
    if not LEADS_DIR.exists():
        return leads
    for f in sorted(LEADS_DIR.glob("*.json")):
        try:
            lead = json.loads(f.read_text())
            lead["_file"] = str(f)
            leads.append(lead)
        except (json.JSONDecodeError, KeyError):
            print(f"Warning: skipping invalid lead file: {f}", file=sys.stderr)
    return leads


def load_fashion_saves():
    """Scan all fashion saves and return {brand_name: [item_summaries]}."""
    brand_items = defaultdict(list)
    if not SAVES_DIR.exists():
        return brand_items
    for date_dir in sorted(SAVES_DIR.iterdir()):
        if not date_dir.is_dir():
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
                    })
            except (json.JSONDecodeError, KeyError):
                continue
    return brand_items


def load_taste_profile():
    """Load taste profile for aesthetic keyword matching."""
    if not TASTE_PROFILE.exists():
        return {}
    try:
        return json.loads(TASTE_PROFILE.read_text())
    except json.JSONDecodeError:
        return {}


def fuzzy_brand_match(lead_brand, fashion_brands):
    """Match a lead brand against fashion save brand names (case-insensitive, partial)."""
    b = lead_brand.lower().strip()
    if b in fashion_brands:
        return b
    for fb in fashion_brands:
        if b in fb or fb in b:
            return fb
    return None


# ── scoring engine ────────────────────────────────────────

def score_leads(leads, fashion_saves, taste):
    """Score all leads and return sorted list with score fields populated."""
    scored = []
    for lead in leads:
        s = compute_score(lead, fashion_saves, taste)
        lead["score"] = s["total"]
        lead["_score_breakdown"] = s
        scored.append(lead)
    scored.sort(key=lambda x: x.get("score_override") or x["score"] or 0, reverse=True)
    return scored


def compute_score(lead, fashion_saves, taste):
    """Compute individual lead score with breakdown."""
    dims = {}

    # 1. Aesthetic fit (0-5, x5)
    tags = [t.lower() for t in lead.get("aesthetic_tags", [])]
    liked_theme_words = set()
    if taste:
        for w in taste.get("liked_patterns", {}).get("theme_words", {}):
            liked_theme_words.add(w.lower())
    tag_match = sum(1 for t in tags if t in liked_theme_words)
    if tag_match >= 4:
        dims["aesthetic_fit"] = 5
    elif tag_match >= 2:
        dims["aesthetic_fit"] = 4
    elif tag_match >= 1:
        dims["aesthetic_fit"] = 3
    elif lead.get("niche_match"):
        dims["aesthetic_fit"] = 3  # at least they wrote something
    else:
        dims["aesthetic_fit"] = 1

    # 2. Irish/UK availability (0-5, x5)
    ie_uk = lead.get("irish_uk_available", False)
    ships = lead.get("ships_to_ireland", False)
    if ie_uk and ships:
        dims["irish_uk_available"] = 5
    elif ie_uk or ships:
        dims["irish_uk_available"] = 3
    else:
        dims["irish_uk_available"] = 1

    # 3. Micro-influencer friendly (0-5, x4)
    ugc = lead.get("ugc_program_url")
    deal_type = lead.get("typical_deal_type", "unknown")
    if ugc and deal_type in ("paid_post", "ugc_license", "ambassador"):
        dims["micro_friendly"] = 5
    elif ugc:
        dims["micro_friendly"] = 4
    elif deal_type in ("affiliate", "gifted"):
        dims["micro_friendly"] = 3
    elif deal_type == "unknown":
        dims["micro_friendly"] = 1
    else:
        dims["micro_friendly"] = 1

    # 4. Product affinity (0-5, x4) — from fashion saves
    match_key = fuzzy_brand_match(lead["brand"], fashion_saves)
    if match_key:
        count = len(fashion_saves[match_key])
        if count >= 5:
            dims["product_affinity"] = 5
        elif count >= 3:
            dims["product_affinity"] = 4
        elif count >= 1:
            dims["product_affinity"] = 3
        else:
            dims["product_affinity"] = 2
        lead["_saved_items_count"] = count
    else:
        dims["product_affinity"] = 2  # no saves but may have browsed

    # 5. Contact accessibility (0-5, x3)
    email = lead.get("contact_email")
    form = lead.get("submission_form_url")
    source = lead.get("contact_source", "not_found")
    if email:
        dims["contact_access"] = 4 if source == "submission_form" else 5
    elif form:
        dims["contact_access"] = 3
    elif source == "instagram_bio":
        dims["contact_access"] = 2
    elif source == "not_found":
        dims["contact_access"] = 1
    else:
        dims["contact_access"] = 0

    # 6. Rate potential (0-5, x3)
    rate_low = lead.get("estimated_rate_low") or 0
    if rate_low >= 500:
        dims["rate_potential"] = 5
    elif rate_low >= 200:
        dims["rate_potential"] = 4
    elif rate_low >= 100:
        dims["rate_potential"] = 3
    elif rate_low >= 50:
        dims["rate_potential"] = 2
    elif rate_low > 0:
        dims["rate_potential"] = 1
    else:
        dims["rate_potential"] = 2  # unknown, assume mid

    # 7. Brand momentum (0-5, x2)
    dims["brand_momentum"] = 3  # default — needs manual research

    # Weighted total
    weights = {
        "aesthetic_fit": 5,
        "irish_uk_available": 5,
        "micro_friendly": 4,
        "product_affinity": 4,
        "contact_access": 3,
        "rate_potential": 3,
        "brand_momentum": 2,
    }
    total = sum(dims[k] * weights[k] for k in weights)
    max_possible = sum(5 * weights[k] for k in weights)  # all 5s = 130
    dims["_raw_total"] = total
    dims["_max"] = max_possible
    dims["total"] = round(total / max_possible * 100)

    # Override
    override = lead.get("score_override")
    if override is not None:
        dims["total"] = override
        dims["_overridden"] = True

    return dims


def tier_name(score):
    if score is None:
        return "?"
    if score >= 90:
        return "\U0001f525 HOT"
    if score >= 60:
        return "\u2600\ufe0f WARM"
    return "\u2744\ufe0f COLD"


# ── commands ───────────────────────────────────────────────

def cmd_list(args):
    leads = load_leads()
    fashion = load_fashion_saves()
    taste = load_taste_profile()
    leads = score_leads(leads, fashion, taste)

    # filters
    status = None
    category = None
    region = None
    min_score = None
    i = 0
    while i < len(args):
        if args[i] == "--status" and i + 1 < len(args):
            status = args[i + 1].lower()
            i += 2
        elif args[i] == "--category" and i + 1 < len(args):
            category = args[i + 1].lower()
            i += 2
        elif args[i] == "--region" and i + 1 < len(args):
            region = args[i + 1].lower()
            i += 2
        elif args[i] == "--min-score" and i + 1 < len(args):
            min_score = int(args[i + 1])
            i += 2
        else:
            i += 1

    if status:
        leads = [l for l in leads if l.get("status", "").lower() == status]
    if category:
        leads = [l for l in leads if l.get("category", "").lower() == category]
    if region == "ireland":
        leads = [l for l in leads if l.get("irish_uk_available")]
    if min_score is not None:
        leads = [l for l in leads if (l.get("score") or 0) >= min_score]

    if not leads:
        print("No leads match your filters.")
        return

    print(f"{'SCORE':>5}  {'TIER':<8}  {'STATUS':<15}  {'BRAND':<25}  {'CATEGORY'}")
    print("-" * 85)
    for l in leads:
        score = l.get("score")
        score_str = str(score) if score is not None else "?"
        print(f"{score_str:>5}  {tier_name(score):<8}  {l.get('status','?'):<15}  {l.get('brand','?')[:24]:<25}  {l.get('category','?')}")


def cmd_show(args):
    slug = args[0] if args else None
    if not slug:
        print("Usage: leads.py show <slug>")
        return
    leads = load_leads()
    fashion = load_fashion_saves()
    taste = load_taste_profile()
    leads = score_leads(leads, fashion, taste)

    lead = next((l for l in leads if l.get("slug") == slug), None)
    if not lead:
        print(f"No lead found with slug: {slug}")
        return

    print(f"\n  {lead['brand']}")
    print(f"  {'=' * len(lead['brand'])}")
    print(f"  Score: {lead.get('score')} / 100  ({tier_name(lead.get('score'))})")
    overridden = lead.get("_score_breakdown", {}).get("_overridden")
    if overridden:
        print(f"  \u26a0\ufe0f  Score manually overridden")
    print(f"  Status: {lead.get('status')}")
    print(f"  Category: {lead.get('category')} / {lead.get('subcategory', '-')}")
    print(f"  URL: {lead.get('url', '-')}")
    print(f"  Instagram: {lead.get('instagram', '-')}")
    print(f"  Irish/UK: {'Yes' if lead.get('irish_uk_available') else 'No'}  |  Ships to IE: {'Yes' if lead.get('ships_to_ireland') else 'No'}")
    print(f"  Deal type: {lead.get('typical_deal_type', 'unknown')}")
    rate_l = lead.get('estimated_rate_low')
    rate_h = lead.get('estimated_rate_high')
    if rate_l or rate_h:
        print(f"  Est. rate: €{rate_l or '?'} - €{rate_h or '?'}")
    print(f"  UGC program: {lead.get('ugc_program_url', '-')}")
    print(f"  Contact: {lead.get('contact_email') or lead.get('submission_form_url') or 'not found'}")
    print(f"  Niche match: {lead.get('niche_match', '-')}")
    print(f"  Pitch angle: {lead.get('pitch_angle', '-')}")
    products = lead.get("products_of_interest", [])
    if products:
        print(f"  Products: {', '.join(products)}")

    # cross-references
    match_key = fuzzy_brand_match(lead["brand"], fashion)
    if match_key and fashion[match_key]:
        items = fashion[match_key]
        print(f"\n  \U0001f48e Fashion Saves ({len(items)} items):")
        for item in items[-10:]:  # last 10
            print(f"    [{item['date']}] {item['name']}")
            if item.get("why"):
                print(f"      \"{item['why'][:100]}\"")

    # score breakdown
    bd = lead.get("_score_breakdown", {})
    if bd:
        print(f"\n  Score Breakdown:")
        weights = {"aesthetic_fit": 5, "irish_uk_available": 5, "micro_friendly": 4,
                   "product_affinity": 4, "contact_access": 3, "rate_potential": 3, "brand_momentum": 2}
        for key, label in [("aesthetic_fit", "Aesthetic fit"), ("irish_uk_available", "Irish/UK avail"),
                           ("micro_friendly", "Micro-friendly"), ("product_affinity", "Product affinity"),
                           ("contact_access", "Contact access"), ("rate_potential", "Rate potential"),
                           ("brand_momentum", "Brand momentum")]:
            raw = bd.get(key, "?")
            w = weights.get(key, 0)
            print(f"    {label}: {raw}/5 (×{w})")

    print()


def cmd_score(args):
    leads = load_leads()
    fashion = load_fashion_saves()
    taste = load_taste_profile()
    leads = score_leads(leads, fashion, taste)

    print(f"\n  Top Leads by Score")
    print(f"  {'─' * 50}")
    for l in leads[:10]:
        score = l.get("score") or 0
        saved = l.get("_saved_items_count", 0)
        saved_str = f" [{saved} saves]" if saved else ""
        print(f"  {score:>3}  {l['brand'][:30]:<30}  {l.get('status','?'):<16} {saved_str}")
    print()

    # summary by tier
    hot = sum(1 for l in leads if (l.get("score") or 0) >= 90)
    warm = sum(1 for l in leads if 60 <= (l.get("score") or 0) < 90)
    cold = sum(1 for l in leads if (l.get("score") or 0) < 60)
    print(f"  \U0001f525 Hot (90+):  {hot}")
    print(f"  \u2600\ufe0f Warm (60-89): {warm}")
    print(f"  \u2744\ufe0f Cold (<60): {cold}")
    print()


def cmd_report(args):
    leads = load_leads()
    if not leads:
        print("No leads in pipeline.")
        return

    stages = defaultdict(list)
    for l in leads:
        stages[l.get("status", "unknown")].append(l)

    order = ["discovered", "researching", "ready_to_pitch", "pitched", "negotiating", "won", "lost"]
    total = len(leads)

    print(f"\n  Pipeline Report — {total} lead{'s' if total != 1 else ''}")
    print(f"  {'─' * 40}")
    for stage in order:
        items = stages.get(stage, [])
        count = len(items)
        bar = "\u2588" * min(count, 30)
        ready = sum(1 for l in items if l.get("contact_email"))
        ready_str = f" (contacts: {ready})" if stage in ("researching", "ready_to_pitch") and ready else ""
        print(f"  {stage:<18} {count:>3}  {bar}{ready_str}")

    ready_pitch = len(stages.get("ready_to_pitch", []))
    with_email = sum(1 for l in stages.get("ready_to_pitch", []) if l.get("contact_email"))
    print(f"\n  \u2709\ufe0f  Ready to pitch: {ready_pitch} ({with_email} with email)")
    print(f"  \U0001f4cb Researching: {len(stages.get('researching', []))}")
    print()


def cmd_crossref(args):
    leads = load_leads()
    fashion = load_fashion_saves()
    if not leads:
        print("No leads to cross-reference.")
        return

    matched = []
    unmatched_fashion = set(fashion.keys())
    for lead in leads:
        match_key = fuzzy_brand_match(lead["brand"], fashion)
        if match_key:
            count = len(fashion[match_key])
            matched.append((count, lead["brand"], match_key))
            unmatched_fashion.discard(match_key)

    matched.sort(reverse=True)

    print(f"\n  Fashion Saves → Brand Leads")
    print(f"  {'─' * 50}")
    if matched:
        for count, brand, key in matched:
            print(f"  {count:>3} saves  →  {brand}")
            for item in fashion[key][-3:]:
                print(f"          {item['name'][:60]}")
    else:
        print("  No cross-references found. When Lana saves items from brands that are in her lead pipeline, they'll show up here.")

    if unmatched_fashion:
        print(f"\n  \U0001f4a1 {len(unmatched_fashion)} brands in fashion saves have no lead yet:")
        for b in sorted(unmatched_fashion)[:15]:
            count = len(fashion[b])
            print(f"    {b} ({count} saves)")
        if len(unmatched_fashion) > 15:
            print(f"    ... and {len(unmatched_fashion) - 15} more")

    also_not_leads = set()
    for b in unmatched_fashion:
        if not any(fuzzy_brand_match(b, {l["brand"].lower(): True}) for l in leads):
            also_not_leads.add(b)
    if also_not_leads:
        print(f"\n  \u26a1 {len(also_not_leads)} brands she loves but hasn't made leads for — gap in the pipeline!")
    print()


def cmd_missing(args):
    leads = load_leads()
    missing_email = [l for l in leads
                     if not l.get("contact_email")
                     and not l.get("submission_form_url")
                     and l.get("status") not in ("won", "lost")]
    if not missing_email:
        print("All active leads have contact info. \u2705")
        return

    print(f"\n  Leads Missing Contact Info ({len(missing_email)})")
    print(f"  {'─' * 50}")
    for l in missing_email:
        print(f"  {l.get('status','?'):<16}  {l['brand'][:30]:<30}  {l.get('contact_source','not_found')}")
    print()


def cmd_create(args):
    """Simple create: leads.py create BRAND --url URL --category CAT [--subcategory SUB] [--instagram @handle]"""
    if len(args) < 4:
        print("Usage: leads.py create BRAND --url URL --category CAT [--subcategory SUB] [--instagram @handle]")
        return
    brand = args[0]
    url = None
    category = None
    subcategory = None
    instagram = None
    i = 1
    while i < len(args):
        if args[i] == "--url" and i + 1 < len(args):
            url = args[i + 1]; i += 2
        elif args[i] == "--category" and i + 1 < len(args):
            category = args[i + 1]; i += 2
        elif args[i] == "--subcategory" and i + 1 < len(args):
            subcategory = args[i + 1]; i += 2
        elif args[i] == "--instagram" and i + 1 < len(args):
            instagram = args[i + 1]; i += 2
        else:
            i += 1

    if not url or not category:
        print("--url and --category are required")
        return

    slug = brand.lower().replace(" ", "-").replace("&", "and")
    now = datetime.now(timezone.utc).isoformat()

    lead = {
        "brand": brand,
        "slug": slug,
        "url": url,
        "category": category,
        "subcategory": subcategory,
        "niche_match": "",
        "aesthetic_tags": [],
        "ugc_program_url": None,
        "contact_email": None,
        "contact_name": None,
        "contact_source": "not_found",
        "submission_form_url": None,
        "pitch_angle": "",
        "products_of_interest": [],
        "instagram": instagram,
        "typical_deal_type": "unknown",
        "estimated_rate_low": None,
        "estimated_rate_high": None,
        "irish_uk_available": False,
        "ships_to_ireland": False,
        "status": "discovered",
        "score": None,
        "notes": "",
        "discovered_at": now,
        "last_updated": now,
        "last_researched_at": None,
        "pitched_at": None,
        "follow_up_at": None,
        "follow_up_count": 0,
        "why_lost": None,
        "deal_terms": None,
        "deal_value": None,
    }

    out_path = LEADS_DIR / f"{slug}.json"
    out_path.write_text(json.dumps(lead, indent=2) + "\n")
    print(f"Created: {out_path}")
    print(f"Next: python leads.py show {slug}")


def cmd_update(args):
    """Simple update: leads.py update SLUG --status STATUS [--field value ...]"""
    if len(args) < 3:
        print("Usage: leads.py update SLUG --status STATUS [--field value ...]")
        print("Fields: --status, --contact-email, --contact-source, --pitch-angle, --notes")
        return

    slug = args[0]
    lead_path = LEADS_DIR / f"{slug}.json"
    if not lead_path.exists():
        print(f"No lead found: {slug}")
        return

    lead = json.loads(lead_path.read_text())

    i = 1
    field_map = {
        "--status": "status",
        "--contact-email": "contact_email",
        "--contact-source": "contact_source",
        "--pitch-angle": "pitch_angle",
        "--notes": "notes",
        "--ugc-program": "ugc_program_url",
        "--rate-low": "estimated_rate_low",
        "--rate-high": "estimated_rate_high",
    }
    while i < len(args):
        key = args[i]
        if key in field_map and i + 1 < len(args):
            val = args[i + 1]
            # type coercion
            if key in ("--rate-low", "--rate-high"):
                val = int(val) if val.isdigit() else None
            lead[field_map[key]] = val
            i += 2
        else:
            i += 1

    lead["last_updated"] = datetime.now(timezone.utc).isoformat()
    if lead.get("status") == "researching" and not lead.get("last_researched_at"):
        lead["last_researched_at"] = lead["last_updated"]

    lead_path.write_text(json.dumps(lead, indent=2) + "\n")
    print(f"Updated: {slug}")
    print(f"Status now: {lead.get('status')}")


# ── main ───────────────────────────────────────────────────

USAGE = """Usage:
  leads.py list [--status S] [--category C] [--region ireland] [--min-score N]
  leads.py show <slug>
  leads.py score
  leads.py report
  leads.py crossref
  leads.py missing
  leads.py create BRAND --url URL --category CAT
  leads.py update SLUG --status S [--contact-email E] [...]"""

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(USAGE)
        sys.exit(0)

    cmd = args[0]
    rest = args[1:]

    if cmd == "list":
        cmd_list(rest)
    elif cmd == "show":
        cmd_show(rest)
    elif cmd == "score":
        cmd_score(rest)
    elif cmd == "report":
        cmd_report(rest)
    elif cmd == "crossref":
        cmd_crossref(rest)
    elif cmd == "missing":
        cmd_missing(rest)
    elif cmd == "create":
        cmd_create(rest)
    elif cmd == "update":
        cmd_update(rest)
    else:
        print(f"Unknown command: {cmd}")
        print(USAGE)
        sys.exit(1)
