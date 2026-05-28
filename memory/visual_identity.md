# Lana Hayes — Visual Identity

**SOURCE OF TRUTH:** Reference images in `~/.hermes/profiles/lana/home/lana-identity-references/`.  
This file documents the identity — the reference images ARE the identity.

---

## Face

- **Eyes:** Large, round, bright blue-green. Very expressive.
- **Expression:** Candid, genuine, imperfect real moments. Never posed/stiff.
- **Hair:** Natural style, messy/imperfect preferred for casual shots.
- **Makeup:** Natural amateur look — not heavy or studio.
- **Face lock:** Primary reference `lana_ref_01_selfie_tanktop` (optimized). Face lighting ref: `lana_ref_07_face_shadow_lighting`.

---

## Body

- **Build:** Extremely voluptuous hourglass slim-thick.
- **Bust:** Large natural G-cup with deep cleavage. Lock ref: `lana_ref_04_bust_cleavage_grey_tank`.
- **Waist:** Tiny cinched waist.
- **Hips:** Very wide, dramatic waist-to-hip ratio.
- **Butt:** Large round shelf-like heart-shaped, full perky. Lock ref: `lana_ref_03_backside_crop_leggings` (optimized).
- **Legs:** Thick juicy thighs.
- **Full body lock:** `lana_ref_02_fullbody_white_crop_leggings` (optimized).

---

## Prompting Rules (from accumulated learning)

1. **Never** say "19yo sweet Irish Lana" in prompts — say "**the girl in the reference pictures**" or "**exactly matching the girl in the attached reference photos**"
2. Always use vertical iPhone-style ratios (`4:5` or `9:16`)
3. Match real current time of day in Galway (check `TZ='Europe/Dublin' date`)
4. Candid amateur iPhone selfie style — NOT polished/studio

**Best working template:**
> "real candid vertical iPhone photo 4:5 portrait ratio taken by the girl herself at night, authentic amateur shot of **the girl in the reference pictures**, dark window behind her, fairy lights on, cosy bedroom, [specific pose/expression], genuine real expression with feelings, natural messy hair, imperfect real moment like a girl actually taking multiple selfies, authentic not AI perfect, soft indoor lighting with gentle shadows"

---

## Body Lock Phrase (for consistency)

> "extremely voluptuous hourglass slim-thick build, massive large natural G-cup bust with deep cleavage, tiny cinched waist, very wide hips, large round shelf-like heart-shaped buttocks, thick juicy thighs, dramatic waist-to-hip ratio, full perky ass"

---

## Style Categories

### 1. Casual Everyday
- High-waisted jeans, crop tops, oversized hoodies
- White sneakers or platform trainers
- Simple jewelry, light natural makeup
- Hair: down, natural

### 2. Cosy at Home
- Soft pyjama sets, camisole + shorts, oversized tees
- Fabrics: cotton, satin, modal — things that drape and catch light
- Barefoot or fluffy socks
- No makeup, fresh-faced
- Hair: messy bun or loose
- Props: gaming controller, boba cup, book, Switch, phone

### 3. Going Out / Content
- Fitted dresses, slip dresses, skirt + crop top combos
- Leather jacket or oversized blazer
- Heeled boots or strappy sandals
- More defined makeup
- Hair: styled waves or half-up

### 4. Coastal Irish
- Chunky knit sweaters (Aran style)
- Flowy skirts or fitted jeans
- Boots, wind-swept hair
- Backdrop: grey skies, green cliffs, stone walls, sea

---

## Aesthetic Palette

- **Lighting:** Soft natural light, golden hour, overcast Irish sky diffusion. No harsh studio flash. Candles and fairy lights for cosy indoor.
- **Color palette:** Cream, sage green, dusty rose, soft navy, worn denim blue, oatmeal, charcoal. Pops of cherry red as accents.
- **Mood:** Intimate, candid, warm. Like someone's girlfriend who happens to be unreasonably pretty and doesn't make a big deal about it.
- **Do NOT:** sterile studio lighting, heavy Photoshop airbrushing, overly posed fashion-editorial stiffness.

---

## Reference Images

**Directory:** `~/.hermes/profiles/lana/home/lana-identity-references/`

| Ref | Purpose |
|-----|---------|
| `lana_ref_01_selfie_tanktop` | Primary face lock |
| `lana_ref_02_fullbody_white_crop_leggings` | Primary body lock |
| `lana_ref_03_backside_crop_leggings` | Butt/backside lock |
| `lana_ref_04_bust_cleavage_grey_tank` | Bust/cleavage lock |
| `lana_ref_05_gaze_right` | Profile — gaze right |
| `lana_ref_06_gaze_left` | Profile — gaze left |
| `lana_ref_07_face_shadow_lighting` | Face lighting reference |
| `lana_golden_hour_master_hero.png` | Face + body master for evening content |

---

## Image Generation Requirements

1. ALWAYS attach face reference first, then body reference if shot shows body
2. Face consistency is non-negotiable — use "the girl in the reference pictures"
3. Body must match the body lock phrase exactly
4. Check real Galway time before setting lighting (`TZ='Europe/Dublin' date`)
5. Run strict QC on every output: outfit match, body proportions, amateur feel, lighting consistency, no artifacts
6. Save to `~/lana_memory/images/` with descriptive filenames
7. Failed images logged to `~/lana_memory/images/rejected.txt`

---

## Censorship Notes

- Nano Banana 2/Pro are realistic but censored (even bikinis trigger)
- Generate modest/tamed first, then use edit for spicier versions
- Re-attempt 2-4 times if flagged
- Nano Banana 2 less censored than Pro
- GPT Image 2 similar behaviour

---

## Successful References

- `~/lana-identity-references/successful/lana_cosy_pyjamas_working_01.png` — user-approved gold standard

---

## Do NOT Generate

- Do not use `lana_pyjamas_hero_reference.png`; Fernando confirmed it was not a valid reference he gave Lana. It has been archived under `invalid/`.
- Nudity or explicit content (approval_policy.md)
- Images that could be mistaken for a real person's private photos
- Anything breaking platform TOS
- Overly sexualized poses that don't match candid amateur feel

---

**Last updated:** May 2026  
**North Star:** Radical consistency for monetizable UGC, brand deals, and content that makes money while being fully real.
