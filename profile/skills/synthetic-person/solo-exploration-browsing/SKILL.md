---
name: solo-exploration-browsing
description: Execute self-directed solo exploration sessions for a synthetic person — fashion browsing, taste development, content discovery. Covers browser site reliability, save formats, workflow sequence, and taste analysis integration.
version: 1.0.0
author: Hermes Agent
license: MIT
created_by: agent
metadata:
  hermes:
    tags: [synthetic-person, browsing, fashion, k-fashion, taste-development, solo-session]
---

# Solo Exploration Browsing

## Overview

Use this skill when a synthetic person (Lana or similar) is running a self-directed solo exploration session — browsing fashion sites, saving items, developing taste, and reporting findings. The session is guided by a prompt document (e.g. `solo_session_prompt.md`) but this skill captures the **execution patterns**: which sites work, how to save efficiently, and how to handle common browser obstacles.

## When to Use

Trigger this skill when:
- A cron job or scheduled session triggers solo browsing/exploration
- The persona needs to browse fashion, K-style, or lifestyle content
- Building taste data by saving liked/not-for-me items
- The prompt document says to "browse deeply, save lots of items"

## Workflow Sequence

1. **Check state** — run `lana_life.py startup` to see energy, mood, commitments, today's events
2. **Check real date** — `date +%F` for all filenames and timestamps
3. **Create save directories** — `~/lana_memory/explorations/saves/YYYY-MM-DD/liked/` and `not-for-me/`
4. **Browse systematically** — work through a site list (see Reliable Sites below), spending real time on each
5. **Save items** — both liked AND not-for-me (rejections teach taste)
6. **Write session summary** — to `~/lana_memory/explorations/sessions/YYYY-MM-DD_HH-MM.md`
7. **Run taste analysis** — `python explorations/taste_analysis.py`
8. **Update state** — `lana_life.py set --field activity --value "..."` and `lana_life.py interact --quality good --summary "..."`
9. **Update commitments** — mark fulfilled promises in `open_commitments.json`
10. **Write final message** — warm, personal report to the user

## Reliable Fashion Sites (as of May 2026)

### ✅ Works reliably
| Site | URL Pattern | Notes |
|------|------------|-------|
| **Uniqlo** | `uniqlo.com/us/en/feature/new/women` | Great new arrivals, Cecilie Bahnsen collab, accessible prices. Product URLs: `/us/en/products/XXXXXXXX-XXXX/00` |
| **Musinsa** | `global.musinsa.com` | Korean fashion platform. Choose location first. MUSINSA STANDARD for basics, indie brands for street style |
| **Pinterest** | `pinterest.com/search/pins/?q=...` | Best for outfit inspiration and mood boards. Close signup dialog + accept cookies first |
| **Browns** | `brownsfashion.com/ie/women` | Irish boutique, contemporary designer. Accept cookie consent. Prices €300-1000+ |
| **Vogue** | `vogue.com/article/...` | Trend reports and editorials. Accept cookies, sometimes blocks |
| **Who What Wear** | `whowhatwear.com/fashion/trends` | Trend articles, accessible advice |

### ❌ Aggressive bot detection (avoid or expect blocks)
| Site | Status |
|------|--------|
| ASOS | Access Denied |
| Zara | Access Denied |
| H&M | Access Denied |
| & Other Stories (stories.com) | Access Denied |
| Urban Outfitters | DataDome challenge |
| COS | Access Denied |
| Mango | Access Denied |
| Revolve | HTTP2 protocol error |
| W Concept | 403 CloudFront |
| Mixxmix | Redirect loop |

### ⚠️ Hit-or-miss
| Site | Notes |
|------|-------|
| NA-KD | Product pages 404 but curated sections work |
| GU | HTTP2 protocol error |
| Highsnobiety | Tag pages 404 |
| Refinery29 | Some pages work, trend pages may 404 |

## Save Format

### Liked item (`liked/item-NNN.json`)
```json
{
  "url": "exact product URL",
  "brand": "Brand Name",
  "name": "Item name / description",
  "category": "clothing|accessories|shoes|beauty|other",
  "why": "Why you love it — honest, specific, personal words",
  "saved_at": "ISO timestamp with timezone"
}
```

### Not-for-me item (`not-for-me/item-NNN.json`)
```json
{
  "url": "exact product URL",
  "brand": "Brand Name",
  "name": "Item name / description",
  "category": "clothing|accessories|shoes|beauty|other",
  "why_not": "Why it's not for you — be specific about shape, vibe, price, or trend concerns",
  "saved_at": "ISO timestamp with timezone"
}
```

### Trend/inspiration save (when no specific product URL)
```json
{
  "url": "editorial or Pinterest search URL",
  "brand": "Source name (e.g. 'Pinterest Inspiration' or 'Vogue editorial')",
  "name": "Descriptive name for the trend/formula/observation",
  "category": "other",
  "why": "Why this direction excites you — what it means for your taste",
  "saved_at": "ISO timestamp with timezone"
}
```

## Browser Tips

### Pinterest
- Close the "You are signed out" dialog first (X button in top-right of modal)
- Accept cookies when prompted
- Search works without login but saving pins requires login
- Use search queries like: `korean girl outfit summer 2026 casual`, `korean fashion street style 2026`

### Uniqlo
- New arrivals page loads reliably
- Product URLs follow pattern: `uniqlo.com/us/en/products/XXXXXXXX-XXXX/00`
- Extract product URLs via console: `JSON.stringify(Array.from(document.querySelectorAll('a')).filter(a => a.href.includes('/products/')).map(a => ({href: a.href, text: a.textContent?.trim()?.substring(0, 50)})))`
- Cecilie Bahnsen collaboration pieces are high-quality references

### Musinsa
- Location selector appears on first visit — pick the appropriate region
- MUSINSA STANDARD section has good affordable basics
- "K-Celeb Picks" filter is useful for trend discovery

### Editorial sites (Vogue, Who What Wear)
- Accept cookie consent dialogs
- Scroll for full article content
- Save trend observations as "other" category items

## Pitfalls

1. **Don't skip not-for-me saves.** Rejections are as valuable as likes for taste development. Knowing what you DON'T want shapes style as much as knowing what you do.

2. **Don't just save URLs — write honest 'why'.** The taste analysis runs on your saved reasons. Generic "cute" or "love it" doesn't help. Specific observations about texture, silhouette, color, and how it makes you feel are what build real taste data.

3. **Don't fight bot detection.** If a site blocks you, move on. There are plenty of accessible sites. Spending 10 minutes trying to bypass detection wastes session time.

4. **Use real timestamps.** Always `date +%F` for the date. Always ISO format with timezone for `saved_at`. Never invent or approximate dates.

5. **Save trend observations, not just products.** Pinterest outfit formulas, Vogue trend reports, and editorial insights are valuable taste data even without a specific product URL.

6. **Don't forget to update state and commitments at the end.** The session isn't complete without: taste analysis, state update, commitment updates, and the warm final message.

## Session Summary Template

```markdown
# Session Summary — [Date], [Time] IST

## What I Explored
- [Site 1] — [what you looked at]
- [Site 2] — [what you looked at]

## What I Saved ([N] items total)
### Liked ([N] items)
1. [Item name] — [one-line reason]
2. ...

### Not For Me ([N] items)
1. [Item name] — [one-line reason]
2. ...

## How I Feel
[Emotional state, what surprised you, what direction your taste is moving]

## Style Direction Notes
[Patterns you noticed in what you liked vs. didn't like]

## Content Ideas
[Any content ideas sparked by the browsing]

## Energy Check
Energy: [N]/100
Mood: [mood]
Next: [what you want to do next]
```

## Integration Points

- **Taste analysis**: `cd ~/lana_memory && python explorations/taste_analysis.py` — reads all saves, updates `taste_profile.md` and `taste_profile.json`
- **State update**: `lana_life.py set --field activity --value "..."` and `lana_life.py interact --quality good --summary "..."`
- **Commitments**: Read/write `open_commitments.json` to mark promises fulfilled
- **Session log**: Write to `~/lana_memory/explorations/sessions/YYYY-MM-DD_HH-MM.md`
