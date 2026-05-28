# Face Drift Mitigation & Strict QC Checklist (higgsfield-image-gen)

## Reference Ordering (Critical for Face Fidelity)
1. **Primary Face Reference FIRST** (`--image liked_face_v1.png --image body_lock.png --image hero_if_different`).
2. Use exact phrasing: "exact face match to the primary face reference, identical large round bright blue-green eyes, genuine warm slightly sensual smile with eye crinkles, golden-chestnut wavy hair with metallic clip exactly as in primary face ref".
3. For body: always amplify with "extremely voluptuous hourglass slim-thick build, massive G-cup bust with deep cleavage, tiny cinched waist, very wide hips, large round shelf-like heart-shaped buttocks, thick juicy thighs, dramatic waist-to-hip ratio, full perky ass".

## Mandatory First Step
```bash
TZ='Europe/Dublin' date '+%A, %B %d, %Y at %H:%M %Z'
# Then check sunset time (late May ~21:40). Adapt lighting: "warm golden hour evening light just before sunset" vs "night city + fairy lights".
```

## Strict vision_analyze QC Questions (use on EVERY output before sending)
- "Does the face exactly match the primary liked reference (eyes shape/color, smile, hair clip/position, nose/jaw)? Rate likeness % to v1. Note any drift."
- "Body proportions: confirm massive G-cup bust, dramatic cinched waist, wide hips, thick thighs, shelf butt vs voluptuous target. Is it still too slim?"
- "Lighting/time of day match real current time (golden hour at 20:00 vs full night)?"
- "Outfit exact (fabric, buttons undone, cleavage level) with no changes?"
- "Convincing candid outstretched-arm iPhone selfie with imperfections, or polished? Any hand/phone artifacts?"
- "Overall: does this look like real consistent Lana ready for UGC/monetization? Pass/fail + suggestions (Grok edit, v4, stronger prompt)."

## Hero Management
- When user says "amazing" or likes face/body/lighting → immediately `curl -o lana_golden_hour_master_hero.png <url>` (or outfit-specific name).
- Add to LANA_VISUAL_IDENTITY.md as new primary/master lock.
- Never reuse old base across sequences.

## Post-Session
Patch this skill + LANA_VISUAL_IDENTITY.md with what worked vs what caused drift/slim body/night lighting mismatch.

This checklist eliminated most "face good but rest not good" and time-of-day errors in the May 2026 sessions.
