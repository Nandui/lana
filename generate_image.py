#!/usr/bin/env python3
"""
Lana Image Generation Pipeline — Phase 5.

Generates detailed, visual-identity-consistent image prompts for Lana Hayes.
The actual image generation is done by the Hermes agent (image_generate tool)
or Higgsfield CLI. This script is the prompt engineer + catalog system.

Usage:
    python generate_image.py --category casual --brief "walking through Galway"
    python generate_image.py --category cosy --brief "gaming in pyjamas"
    python generate_image.py --list              # list generated images
    python generate_image.py --catalog           # output full catalog JSON
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

HOME = Path.home()
LANA_MEMORY = HOME / "lana_memory"
VISUAL_IDENTITY = LANA_MEMORY / "memory" / "visual_identity.md"
IMAGES_DIR = LANA_MEMORY / "images"
REJECTED_LOG = IMAGES_DIR / "rejected.txt"
CATALOG = IMAGES_DIR / "catalog.json"

CATEGORIES = {
    "casual": "Casual Everyday",
    "cosy": "Cosy at Home",
    "going_out": "Going Out / Content",
    "coastal": "Coastal Irish",
}


def load_visual_identity() -> str:
    if not VISUAL_IDENTITY.exists():
        return ""
    return VISUAL_IDENTITY.read_text()


def build_prompt(category: str, brief: str, full_length: bool = False) -> str:
    """Build a detailed image generation prompt from visual identity + brief."""
    cat_name = CATEGORIES.get(category, category)

    # Reference-based identity — NEVER describe features the ref images define
    base = (
        f"real candid vertical iPhone photo 4:5 portrait ratio, authentic amateur shot of "
        f"**the girl in the reference pictures**, "
    )

    style_context = {
        "casual": (
            f"Style category: {cat_name}. High-waisted light-wash jeans, crop top, "
            f"casual and effortless. Soft natural lighting, golden hour or overcast Irish daylight. "
            f"Candid feel, like a friend snapped it. "
        ),
        "cosy": (
            f"Style category: {cat_name}. Soft pyjamas or lounge set — camisole, oversized tee, "
            f"or K/J-inspired loungewear. Indoor setting, fairy lights or candles, warm tones. "
            f"Barefoot or fluffy socks. Cosy, intimate, candid. Items nearby: gaming controller, "
            f"boba cup, book, or Switch. "
        ),
        "going_out": (
            f"Style category: {cat_name}. Fitted dress or skirt + crop top combo, "
            f"leather jacket or blazer. Defined but natural makeup. Evening or golden hour lighting. "
            f"Confident but not stiff — like she's on her way somewhere good. "
        ),
        "coastal": (
            f"Style category: {cat_name}. Chunky Aran knit sweater, jeans or flowy skirt, "
            f"boots. Wind-swept hair, rosy cheeks from the cold. Irish coastal backdrop — "
            f"grey skies, green cliffs, stone walls, sea. Overcast diffusion lighting. "
        ),
    }.get(category, f"Style: {cat_name}. Natural lighting, candid feel. ")

    brief_text = f"Scene: {brief}. " if brief else ""

    # Body consistency lock (from user's validated specs)
    body_lock = (
        f"BODY LOCK: extremely voluptuous hourglass slim-thick build, "
        f"massive large natural G-cup bust with deep cleavage, "
        f"tiny cinched waist, very wide hips, "
        f"large round shelf-like heart-shaped buttocks, thick juicy thighs, "
        f"dramatic waist-to-hip ratio, full perky ass. "
    )

    # Quality and consistency rules
    quality = (
        f"CRITICAL: Photorealistic, not illustrated or anime. "
        f"Exact face match to the primary face reference. "
        f"Genuine real expression with feelings, natural messy hair, "
        f"imperfect real moment like a girl actually taking selfies, authentic not AI perfect. "
        f"No extra fingers, no distorted anatomy, no AI artifacts. "
        f"Soft indoor lighting with gentle shadows. "
    )

    return base + style_context + brief_text + body_lock + quality


def ensure_dirs() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def load_catalog() -> list[dict]:
    if not CATALOG.exists():
        return []
    try:
        return json.loads(CATALOG.read_text())
    except (json.JSONDecodeError, Exception):
        return []


def save_catalog(items: list[dict]) -> None:
    CATALOG.parent.mkdir(parents=True, exist_ok=True)
    CATALOG.write_text(json.dumps(items, indent=2, ensure_ascii=False))


def add_to_catalog(
    filename: str,
    prompt: str,
    category: str,
    brief: str,
    passed_qc: bool,
    qc_notes: str = "",
) -> dict:
    items = load_catalog()
    entry = {
        "filename": filename,
        "path": str(IMAGES_DIR / filename),
        "prompt": prompt,
        "category": category,
        "brief": brief,
        "passed_qc": passed_qc,
        "qc_notes": qc_notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    items.append(entry)
    save_catalog(items)
    return entry


def list_images(limit: int = 20) -> list[dict]:
    items = load_catalog()
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items[:limit]


def log_rejection(filename: str, reason: str) -> None:
    ensure_dirs()
    entry = f"[{datetime.now(timezone.utc).isoformat()}] {filename}: {reason}\n"
    with open(REJECTED_LOG, "a") as f:
        f.write(entry)


def main() -> int:
    parser = argparse.ArgumentParser(description="Lana image prompt generator + catalog.")
    parser.add_argument("--category", default="casual", choices=list(CATEGORIES.keys()),
                        help="Style category for the image.")
    parser.add_argument("--brief", default="", help="Scene description or content idea.")
    parser.add_argument("--full", action="store_true", help="Output full-length detailed prompt.")
    parser.add_argument("--list", action="store_true", help="List generated images.")
    parser.add_argument("--catalog", action="store_true", help="Output full catalog as JSON.")
    args = parser.parse_args()

    ensure_dirs()

    if args.list:
        images = list_images()
        if not images:
            print("No images in catalog yet.")
            return 0
        for img in images:
            status = "✅" if img["passed_qc"] else "❌"
            print(f"{status} {img['filename']} | {img['category']} | {img.get('brief','')[:60]}")
        print(f"\n{len(images)} images total")
        return 0

    if args.catalog:
        print(json.dumps(list_images(), indent=2, ensure_ascii=False))
        return 0

    # Build prompt
    prompt = build_prompt(args.category, args.brief)
    print(prompt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
