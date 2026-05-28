#!/usr/bin/env python3
"""
D2 taste analysis — reads all saves under explorations/saves/ and writes:
  explorations/taste_profile.md
  explorations/taste_profile.json

Handles two save formats:
  1. saves/YYYY-MM-DD/liked/item-NNN.json         — per-item, directory decides liked/not-for-me
  2. saves/YYYY-MM-DD/not-for-me/item-NNN.json    — per-item
  3. saves/YYYY-MM-DD_name.json                   — flat file with a "saves" array + "rating" field
"""

import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

EXPLORATIONS = Path(__file__).parent
SAVES_DIR = EXPLORATIONS / "saves"

# Stopwords to filter from word frequency analysis
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "it", "its", "this", "that", "is", "are", "was", "were",
    "i", "me", "my", "you", "your", "we", "our", "they", "their", "he",
    "she", "so", "be", "do", "have", "has", "had", "not", "just", "like",
    "by", "from", "as", "if", "up", "out", "about", "what", "when", "how",
    "which", "who", "all", "more", "would", "could", "want", "feel", "feels",
    "really", "very", "much", "even", "also", "still", "into", "than",
    "too", "can", "will", "am", "been", "there", "here", "some", "no",
    "it's", "i'm", "i'd", "i've", "it's", "that's", "it", "–", "—",
}


def _words(text: str) -> list[str]:
    if not text:
        return []
    tokens = re.findall(r"[a-zA-Z']+", text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]


def _load_standard_item(path: Path, sentiment: str) -> dict | None:
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    data["_sentiment"] = sentiment
    data["_source_file"] = str(path.relative_to(EXPLORATIONS))
    return data


def _load_flat_session(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, dict):
        return []
    saves = data.get("saves", [])
    if not isinstance(saves, list):
        return []
    results = []
    for save in saves:
        if not isinstance(save, dict):
            continue
        rating = save.get("rating", "")
        if rating in ("love", "like"):
            sentiment = "liked"
        elif rating in ("not-for-me", "no", "dislike"):
            sentiment = "not-for-me"
        else:
            sentiment = "liked"  # default: if saved, treat as liked
        save["_sentiment"] = sentiment
        save["_source_file"] = str(path.relative_to(EXPLORATIONS))
        results.append(save)
    return results


def collect_saves() -> tuple[list[dict], list[dict]]:
    liked, not_for_me = [], []

    if not SAVES_DIR.exists():
        return liked, not_for_me

    for path in sorted(SAVES_DIR.rglob("*.json")):
        parts = path.relative_to(SAVES_DIR).parts

        # Flat session file: saves/YYYY-MM-DD_something.json (directly under saves/)
        if len(parts) == 1:
            items = _load_flat_session(path)
            for item in items:
                if item["_sentiment"] == "liked":
                    liked.append(item)
                else:
                    not_for_me.append(item)
            continue

        # Standard per-item file: saves/YYYY-MM-DD/liked/item-NNN.json
        if len(parts) >= 2:
            sentiment_dir = parts[1].lower()
            if sentiment_dir == "liked":
                item = _load_standard_item(path, "liked")
                if item:
                    liked.append(item)
            elif sentiment_dir in ("not-for-me", "not_for_me", "disliked"):
                item = _load_standard_item(path, "not-for-me")
                if item:
                    not_for_me.append(item)
            else:
                # Unknown sub-folder — treat as liked
                item = _load_standard_item(path, "liked")
                if item:
                    liked.append(item)

    return liked, not_for_me


def _extract_patterns(items: list[dict]) -> dict:
    brands: Counter = Counter()
    categories: Counter = Counter()
    theme_words: Counter = Counter()

    for item in items:
        brand = item.get("brand") or item.get("source") or ""
        if brand:
            # Normalize "Pinterest / Outfit Daily" → "Pinterest" and dedupe case variants.
            brand_clean = brand.split("/")[0].strip()
            if brand_clean:
                brands[brand_clean.title()] += 1

        cat = item.get("category") or item.get("type") or ""
        if cat:
            categories[cat.lower()] += 1

        for field in ("why", "feeling", "name", "description", "query"):
            text = item.get(field, "") or ""
            theme_words.update(_words(text))

    return {
        "brands": dict(brands.most_common(10)),
        "categories": dict(categories.most_common(10)),
        "theme_words": dict(theme_words.most_common(20)),
    }


def _render_md(
    liked: list[dict],
    not_for_me: list[dict],
    liked_patterns: dict,
    not_for_me_patterns: dict,
    generated_at: str,
) -> str:
    lines = [
        "# Lana's Taste Profile",
        "",
        f"_Generated: {generated_at}_",
        f"_Liked: {len(liked)} items · Not-for-me: {len(not_for_me)} items_",
        "",
    ]

    if not liked and not not_for_me:
        lines += [
            "## No saves yet",
            "",
            "Start saving items during solo sessions and run taste_analysis.py again.",
        ]
        return "\n".join(lines)

    # Liked section
    if liked:
        lines += ["## What I'm Drawn To", ""]

        brands = liked_patterns["brands"]
        if brands:
            lines.append("**Brands / Sources:**")
            for brand, count in brands.items():
                lines.append(f"- {brand} ({count}x)")
            lines.append("")

        cats = liked_patterns["categories"]
        if cats:
            lines.append("**Categories:**")
            for cat, count in cats.items():
                lines.append(f"- {cat} ({count}x)")
            lines.append("")

        words = liked_patterns["theme_words"]
        if words:
            top_words = list(words.items())[:15]
            word_str = "  ·  ".join(f"{w} ({c})" for w, c in top_words)
            lines += ["**Recurring themes:**", word_str, ""]

    # Not-for-me section
    if not_for_me:
        lines += ["## What's Not Me", ""]

        cats = not_for_me_patterns["categories"]
        if cats:
            lines.append("**Categories I'm skipping:**")
            for cat, count in cats.items():
                lines.append(f"- {cat} ({count}x)")
            lines.append("")

        words = not_for_me_patterns["theme_words"]
        if words:
            top_words = list(words.items())[:10]
            word_str = "  ·  ".join(f"{w} ({c})" for w, c in top_words)
            lines += ["**Words from rejections:**", word_str, ""]

    # Recent liked items sample
    lines += ["## Recent Saves (liked)", ""]
    for item in liked[-5:]:
        name = item.get("name") or item.get("description") or "(untitled)"
        brand = item.get("brand") or item.get("source") or ""
        why = item.get("why") or item.get("feeling") or ""
        brand_str = f" · {brand}" if brand else ""
        lines.append(f"- **{name}**{brand_str}")
        if why:
            # Truncate long why text
            short = why[:120] + ("…" if len(why) > 120 else "")
            lines.append(f"  _{short}_")
    lines.append("")

    lines += [
        "---",
        "",
        "_This profile is auto-generated. Run `python explorations/taste_analysis.py` after adding saves._",
    ]

    return "\n".join(lines)


def main() -> None:
    liked, not_for_me = collect_saves()

    if not liked and not not_for_me:
        print("[taste] No save files found — writing empty profile.")

    liked_patterns = _extract_patterns(liked)
    not_for_me_patterns = _extract_patterns(not_for_me)
    generated_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    profile_json = {
        "generated_at": generated_at,
        "stats": {
            "liked_count": len(liked),
            "not_for_me_count": len(not_for_me),
        },
        "liked_patterns": liked_patterns,
        "not_for_me_patterns": not_for_me_patterns,
    }

    md = _render_md(liked, not_for_me, liked_patterns, not_for_me_patterns, generated_at)

    md_path = EXPLORATIONS / "taste_profile.md"
    json_path = EXPLORATIONS / "taste_profile.json"

    md_path.write_text(md, encoding="utf-8")
    json_path.write_text(
        json.dumps(profile_json, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(
        f"[taste] Done. Liked: {len(liked)}, Not-for-me: {len(not_for_me)}\n"
        f"        → {md_path}\n"
        f"        → {json_path}"
    )


if __name__ == "__main__":
    main()
