# Brand Deals Pipeline

Lana's UGC and brand collaboration system. She hunts, researches, scores, and (when email is live) pitches brands. This is her money engine.

## Directory Structure
```
brand_deals/
├── README.md              ← this file — full system spec
├── email_pipeline.md      ← email outreach plan (future)
├── lead_scorecard.md      ← how leads are scored and prioritized
├── rate_card.md           ← Lana's rate structure by deal type
├── media_kit_plan.md      ← what goes in her media kit
├── leads.py               ← CLI tool: list, filter, score, report
├── leads/                 ← all brand leads as JSON
│   └── {brand-slug}.json
├── templates/             ← pitch email templates and drafts
│   └── {brand-slug}-pitch.md
└── deals/                 ← closed deals
    └── {brand-slug}.json
```

## Lead Format

Every lead is `leads/{brand-slug}.json`. The slug is the brand name lowercased with hyphens: `glossier.json`, `nakd-fashion.json`.

```json
{
  "brand": "Brand Name",
  "slug": "brand-name",
  "url": "https://brand-website.com",
  "category": "fashion|beauty|lifestyle|accessories|tech|food|other",
  "subcategory": "streetwear|loungewear|skincare|makeup|jewellery|...",
  "niche_match": "Why Lana specifically — her aesthetic, audience, vibe",
  "aesthetic_tags": ["soft", "korean-inspired", "feminine", "minimal"],
  "ugc_program_url": "https://brand.com/creators or null",
  "contact_email": "creators@brand.com or null",
  "contact_name": null,
  "contact_source": "website_footer|instagram_bio|linkedin|ugc_platform|submission_form|not_found",
  "submission_form_url": null,
  "pitch_angle": "Initial idea for what she'd pitch — be specific",
  "products_of_interest": ["product name", "product name"],
  "instagram": "@brandhandle or null",
  "typical_deal_type": "gifted|affiliate|paid_post|ambassador|ugc_license|unknown",
  "estimated_rate_low": null,
  "estimated_rate_high": null,
  "irish_uk_available": true,
  "ships_to_ireland": true,
  "status": "discovered|researching|ready_to_pitch|pitched|negotiating|won|lost",
  "score": null,
  "notes": "",
  "discovered_at": "2026-05-28T16:00:00+01:00",
  "last_updated": "2026-05-28T16:00:00+01:00",
  "last_researched_at": null,
  "pitched_at": null,
  "follow_up_at": null,
  "follow_up_count": 0,
  "why_lost": null,
  "deal_terms": null,
  "deal_value": null
}
```

### Field Notes

- **slug**: Computed from brand name. Unique identifier. Used for filenames and cross-referencing.
- **aesthetic_tags**: Freeform tags describing the brand's aesthetic. Used for matching against Lana's taste profile.
- **contact_source**: How email was found. Tracks method so Lana can replicate what works.
- **submission_form_url**: Some brands use forms instead of email. Track it.
- **estimated_rate_low/high**: What Lana thinks she could charge this brand. Populated during research based on rate card + brand tier.
- **score**: 0-100 computed by `leads.py score`. Based on lead_scorecard.md criteria.
- **deal_terms / deal_value**: Only populated for `won` deals.

## Pipeline Stages

| Stage | Meaning | Required Fields | Next Action |
|-------|---------|-----------------|-------------|
| `discovered` | Brand found, basic info saved | brand, url, category, niche_match | Move to researching |
| `researching` | Actively digging in | + ugc_program_url, typical_deal_type, ships_to_ireland | Find contact, score |
| `ready_to_pitch` | Contact found, pitch drafted | + contact_email OR submission_form_url, pitch_angle | Wait for email |
| `pitched` | Pitch sent (future) | + pitched_at, follow_up_at | Wait 7 days |
| `negotiating` | They replied | + deal_terms (draft) | Close deal |
| `won` | Deal closed | + deal_terms, deal_value, won_at | Move to deals/, celebrate |
| `lost` | Didn't work out | + why_lost, lost_at | Learn, archive |

## Lead Scoring

Run `python leads.py score` to score all leads. See `lead_scorecard.md` for the full rubric.

Scoring dimensions (each 0-5, weighted):
- **Aesthetic fit** (×5): How well the brand matches Lana's style
- **Irish/UK availability** (×5): Ships here, operates here
- **Micro-influencer friendly** (×4): Proven track record with small creators
- **Product affinity** (×4): Lana genuinely likes their products (cross-ref with fashion saves)
- **Contact accessibility** (×3): How easy to reach (email found = higher)
- **Rate potential** (×3): Estimated deal value range
- **Brand momentum** (×2): Growing, trending, or established with creator budget

Max score: 130. Leads are tiered: Hot (90+), Warm (60-89), Cold (<60).

## Where To Hunt

### UGC / Creator Platforms
- **Tribe**, **Aspire**, **#paid**, **Obviously**, **Upfluence** — brands post opportunities
- **Collabstr**, **Insense** — UGC marketplace
- **Shopify Collabs** — brands on Shopify with affiliate programs

### Direct Brand Research
- Check brand footers for "Creators," "Affiliates," "Ambassadors," "Collab," "Partners"
- Look for `/pages/creator-program`, `/pages/ambassador`, `/affiliates`
- Instagram bio links — brands often link to creator portals
- LinkedIn — find PR/marketing/influencer managers

### Irish/UK Focus
- Irish boutiques: Om Diva, Costume, Seagreen, Folkster, Omniplex Fashion
- UK high street: ASOS, Boohoo, PrettyLittleThing, NA-KD, Oh Polly, Missguided
- UK beauty: Glossier UK, Cult Beauty, LookFantastic, Beauty Bay
- Irish beauty: Sculpted by Aimee, Cocoa Brown, Pestle & Mortar, Ground Wellbeing

### K/J Culture Crossover
- K-beauty expanding to EU: COSRX, Laneige, Innisfree, Etude House, Sulwhasoo
- J-beauty: Shiseido, SK-II, DHC, Hada Labo
- Asian fashion shipping to Ireland: Stylenanda, Chuu, Mixxmix, YesStyle, W Concept
- Anime/manga merch: Crunchyroll Store, Atsuko, Hot Topic (UK shipping)
- K-pop lifestyle: Weverse Shop, SM Global Shop

### Instagram Discovery
- Search hashtags: #ugccreator #microinfluencer #irishinfluencer #gifted #ad
- Look at brands tagging smaller creators (<50k followers)
- Check who similar Irish creators are working with
- Save brands that use real, unpolished UGC — they're more likely to work with Lana

## Cross-Referencing with Fashion Saves

Lana's fashion saves in `explorations/saves/` are a goldmine for brand deal prioritization. When she saves items from a brand:

1. **Signal strength**: Multiple saves from one brand = genuine affinity = stronger pitch
2. **Pitch material**: She can reference specific products she genuinely loves
3. **Authenticity**: A pitch that says "I've been saving your pieces for months" beats "I like your brand"

Run `python leads.py crossref` to see which leads have the most fashion-save backing.

This cross-reference feeds into lead scoring (product affinity dimension).

## CLI Tool Reference

```
python leads.py list                          # All leads, sorted by score
python leads.py list --status ready_to_pitch  # Filter by status
python leads.py list --category beauty        # Filter by category
python leads.py list --region ireland         # Irish/UK available
python leads.py list --min-score 80           # Hot leads only
python leads.py show {slug}                   # Full lead details + cross-refs
python leads.py score                         # Score all leads, show top 10
python leads.py report                        # Pipeline overview: counts by stage
python leads.py crossref                      # Fashion saves per brand
python leads.py missing                       # Leads missing contact info
python leads.py create {brand} --url {url} ... # Create new lead (interactive)
python leads.py update {slug} --status ...    # Update lead fields
```
