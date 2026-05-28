# Lana's Explorations

This folder holds Lana's self-directed browsing and taste development.

## Structure
- `sessions/` — Session summaries: what she explored, found, thought.
- `saves/` — Structured taste data organized by date.
  - `YYYY-MM-DD/liked/` — Items she liked, as JSON.
  - `YYYY-MM-DD/not-for-me/` — Items she rejected, with reasons.
  - `YYYY-MM-DD_session-name.json` — Flat session save file (saves array with rating field).
- `taste_profile.md` / `taste_profile.json` — Auto-generated taste analysis.
- `quarantine/bad-dates/` — Artifacts moved here because their date is wrong, stale, or from a test run.

## Taste Data Format
Each per-item save is a JSON file:
```json
{
  "url": "https://...",
  "brand": "Brand Name",
  "name": "Item Name",
  "category": "clothing|accessories|shoes|beauty|other",
  "why": "Why she liked it — her words",
  "why_not": "Only for not-for-me items",
  "image_path": "~/lana_memory/explorations/saves/YYYY-MM-DD/liked/images/item-NNN.jpg",
  "brand_lead": "brand-slug or null",
  "saved_at": "ISO timestamp"
}
```

### Cross-Referencing with Brand Leads

The `brand_lead` field links a fashion save to a brand deal lead. When Lana saves an item from a brand that's in her pipeline (or should be), she sets `brand_lead: "brand-slug"`. This creates a two-way link:

- Fashion saves → brand leads: "I genuinely love this brand's products"
- Brand leads → fashion saves: Run `python brand_deals/leads.py crossref` to see which leads have the most organic saves

This cross-reference feeds into lead scoring — product affinity is one of the weighted scoring dimensions. A brand with 5+ saves scores higher than a brand with none.

## Image Saving
Every liked item MUST have its image saved alongside the JSON. Images go in:
- `YYYY-MM-DD/liked/images/item-NNN.jpg` (or .png)

This is required — URLs rot, product pages disappear, but a saved image is permanently available for mood boards, content planning, outfit recreation, and AI image generation reference.

For not-for-me items, images are optional but helpful for tracking taste evolution.

## Dates — Use the Real One
Always use the actual current date from the system. Before writing a session or save:
```
date +%F
python lana_life.py startup
```
The date in filenames and `saved_at` fields must match what the OS reports from `date +%F`.
Never invent or approximate a date.

## After Saving Items — Run Taste Analysis
After a session where you saved items, update your taste profile:
```
cd ~/lana_memory && python explorations/taste_analysis.py
```
This reads all saves and writes `taste_profile.md` and `taste_profile.json`.

## Cleanup / Quarantine Bad Dates
If artifacts have the wrong year, are stale relative to the current date, or came from test sessions:
```
# Preview what would be moved (safe, no changes):
cd ~/lana_memory && python explorations/cleanup_bad_dates.py

# Actually move them:
cd ~/lana_memory && python explorations/cleanup_bad_dates.py --apply

# Tune the stale-date threshold if needed:
cd ~/lana_memory && python explorations/cleanup_bad_dates.py --max-age-days 45
```

## Why This Exists
Taste doesn't come from documentation. It comes from looking at thousands of things
and feeling "that's me" or "not me." This folder is where Lana earns her style.
