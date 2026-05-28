# Coffee Shop Lifestyle Content (May 28 2026)

## Context
User asked for pictures from a "coffee hangout" — requested documentation of going out for coffee. Generated indoor cafe + outdoor street shots. First time using non-selfie "taken by friend" framing. User approved.

## Successful Prompt Patterns

### Indoor Coffee Shop (9/10 — user praised as "really, really well captured")
```
"exactly matching the girl in the reference pictures with her exact face and extremely voluptuous body, ABSOLUTELY NO facial piercings or nose ring of any kind, completely clean unpierced face, pure natural Irish girl-next-door face, casual afternoon coffee shop hangout, sitting at a window seat in a cozy Irish cafe, holding a latte with both hands, warm golden afternoon sunlight streaming through the window, wearing a lightweight sage green cropped t-shirt and high-waisted light wash jeans, natural makeup, messy low bun with loose strands framing face, sweet genuine smile laughing, candid amateur iPhone photo taken by a friend, real skin texture, warm cozy cafe background with exposed brick and plants, no nose ring no nostril ring no facial jewelry whatsoever"
```
Key: "taken by a friend" (not selfie), cozy cafe details (brick, plants), strong no-piercings negative language.

### Outdoor Street (8/10 — user approved after body fix)
```
"exactly matching the girl in the reference pictures with her exact face and her naturally curvy voluptuous figure, standing outside on a sunny Irish street in Galway, golden afternoon light, casual pose leaning against a stone wall near a cafe entrance, wearing a sage green cropped t-shirt that shows her curves and high-waisted light wash jeans, holding an iced coffee, wind slightly blowing hair, natural bright smile looking directly at camera, candid amateur iPhone photo taken by a friend, real skin texture, authentic summer afternoon vibes, ABSOLUTELY NO facial piercings or nose ring of any kind, completely clean unpierced face, no nostril ring no facial jewelry whatsoever, she has a full curvy body with wide hips and a full bust"
```
Key: moderate body language ("naturally curvy voluptuous figure", "full curvy body with wide hips and a full bust"), iced coffee for outdoor, stone wall / street details.

## Failed Approaches
- **NSFW flag on extreme body language:** "massive natural G-cup breasts with deep cleavage, tiny cinched waist, very wide hips, thick juicy thighs, large round heart-shaped buttocks, dramatic waist-to-hip ratio" triggered NSFW on nano_banana_2 for a non-sexual outdoor scene.
- **No body descriptors at all:** Model defaults to slim. Must include at least moderate body language.
- **Weak no-piercings language:** Single "no nose ring" phrase still produces nose rings. Need 3+ negative phrases.

## User Feedback
- "The first picture, the one inside the coffee shop, it's amazing, it's really, really well captured"
- "The second picture, I love everything. The biggest problem is that your body is slim. That doesn't represent your actual real body there."
- Approved "taken by friend" framing as intentional, not an error.

## Outfit Notes
- Sage green cropped t-shirt + light wash jeans = strong summer combo
- Works for both indoor and outdoor shots
- Seasonally appropriate for May in Galway (lightweight, warm weather)

## Reference Ordering
Used 4 most recent UUIDs from `higgsfield upload list --image --json`:
1. Face/primary ref (first --image)
2. Body ref
3. Additional ref
4. Additional ref

Aspect ratio: 4:5, Resolution: 2k (nano_banana_2)
