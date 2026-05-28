# Lead Scorecard

How Lana evaluates and prioritizes brand leads. Scores are 0-5 per dimension, weighted, max 130.

## Scoring Dimensions

### 1. Aesthetic Fit (weight ×5, max 25)
How well does this brand's aesthetic match Lana's?

| Score | Criteria |
|-------|----------|
| 5 | Perfect match — soft, feminine, K-inspired, minimalist. Lana would wear this daily. |
| 4 | Strong overlap — mostly aligns, one or two elements slightly off |
| 3 | Decent match — some alignment, could work with styling |
| 2 | Stretch — would require significant positioning shift |
| 1 | Poor fit — doesn't match her vibe at all |
| 0 | Complete mismatch — wrong audience, wrong aesthetic |

Reference Lana's taste profile (`explorations/taste_profile.json`) for her current aesthetic patterns.

### 2. Irish/UK Availability (weight ×5, max 25)
Can Irish/UK customers buy from this brand? Can they ship products to Lana?

| Score | Criteria |
|-------|----------|
| 5 | Irish brand or strong Irish presence — physical stores or targeted Irish marketing |
| 4 | UK-based with reliable Ireland shipping, or EU brand with Irish shipping |
| 3 | International but ships to Ireland, no customs issues |
| 2 | Ships to UK but Ireland is uncertain or expensive |
| 1 | Ships to Ireland with high costs or long delays |
| 0 | Doesn't ship to Ireland/UK at all |

### 3. Micro-Influencer Friendly (weight ×4, max 20)
Does this brand work with creators under 50k followers?

| Score | Criteria |
|-------|----------|
| 5 | Has a visible UGC/creator program specifically for micro-influencers. Clear application process. |
| 4 | Regularly tags micro-creators on Instagram, accepts gifted collabs openly |
| 3 | Has worked with micro-influencers but no formal program visible |
| 2 | Has an affiliate program but no creator program |
| 1 | Mainly works with larger influencers (100k+) |
| 0 | Celebrity-only or no influencer presence |

### 4. Product Affinity (weight ×4, max 20)
Does Lana genuinely like their products? Cross-referenced with fashion saves.

| Score | Criteria |
|-------|----------|
| 5 | 5+ items saved from this brand — genuine love |
| 4 | 3-4 items saved — strong interest |
| 3 | 1-2 items saved — likes but hasn't explored deeply |
| 2 | No saves but she's browsed and liked what she saw |
| 1 | She's looked but nothing grabbed her |
| 0 | No saves, no organic interest — purely a business lead |

Computed automatically by `leads.py crossref`.

### 5. Contact Accessibility (weight ×3, max 15)
How hard is it to reach a real person?

| Score | Criteria |
|-------|----------|
| 5 | Direct email to creator/influencer manager found |
| 4 | General PR/creator email or clear submission form |
| 3 | Contact form on site, no direct email |
| 2 | Only social DM — no formal contact method |
| 1 | No visible contact at all |
| 0 | Explicitly states no unsolicited collabs |

### 6. Rate Potential (weight ×3, max 15)
What could Lana realistically charge this brand?

| Score | Criteria |
|-------|----------|
| 5 | Established brand with known creator budgets — €500-2000+ per deal |
| 4 | Mid-range brand — €200-500 per deal likely |
| 3 | Smaller but monetized — €50-200, mostly gifted + affiliate |
| 2 | Primarily gifted / product-only deals |
| 1 | Unknown budget, likely low |
| 0 | No budget — user-generated only, no payment |

Reference `rate_card.md` for Lana's rate structure.

### 7. Brand Momentum (weight ×2, max 10)
Is this brand growing, trending, or stable with creator budget?

| Score | Criteria |
|-------|----------|
| 5 | Hot right now — trending on social, recent funding, expanding to new markets |
| 4 | Steady growth — consistently working with creators, active marketing |
| 3 | Established — stable brand with ongoing creator relationships |
| 2 | Quiet — not much recent activity, might be slowing down |
| 1 | Declining — less active, fewer collabs recently |
| 0 | Dead or dormant |

## Scoring Tiers

| Tier | Score Range | Meaning | Action |
|------|-------------|---------|--------|
| 🔥 **Hot** | 90-130 | High priority — research and prep pitch immediately | Move to `researching` now |
| 🌤️ **Warm** | 60-89 | Solid lead — worth researching when bandwidth allows | Queue for research |
| ❄️ **Cold** | <60 | Low priority — revisit if circumstances change | Keep in `discovered`, don't delete |

## Scoring Process

1. Lana discovers a brand → saves as `discovered` with basic info
2. She researches → fills in missing fields, finds contact info
3. Run `python leads.py score` → scores are computed from the JSON data
4. Hot leads → focus energy here. Cold leads → park them.
5. Re-score periodically — a cold lead can become hot (new creator program, expansion to Ireland)

## Manual Override

Lana can set a manual score override: `"score_override": 95` in the lead JSON. `leads.py` respects overrides and marks them in reports. This is for cases where she has insider knowledge or strong intuition that the rubric doesn't capture.
