# Short-Sequence Prompt Templates & Validation (higgsfield-image-gen)

## Hero Reference Technique (learned May 2026)
When user approves an outfit:
1. Download the best generation: `curl -o INVALID_ARCHIVED_lana_pyjamas_hero_reference.png <cloudfront_url>`
2. Use it as the FIRST --image flag in all subsequent calls in the sequence.
3. Extract exact details via vision_analyze (fabric, prints, fit, colors) and quote them verbatim in every prompt.

## Successful Base Prompt Skeleton (copy-paste & modify pose only)
"real casual outstretched-arm iPhone selfie in 4:5 portrait ratio, authentic imperfect amateur shot taken by the girl herself on a bright Monday morning at 9am, exactly matching the girl and the exact pyjama set in the hero reference photo, identical outfit with no changes whatsoever as if photos taken only 2-3 minutes apart, pastel rainbow tie-dye velour pajama set (mint lavender pink blue), oversized hoodie with large purple-haired anime girl print (crescent moon, pink heart), matching tight shorts with print on thigh, bright consistent Irish morning daylight from window, same cosy bedroom, [SPECIFIC POSE AND EXPRESSION HERE], natural messy hair, real unposed candid moment with slight imperfections, precise consistency to hero reference and face locks, soft natural lighting"

## Validation Questions for vision_analyze (use on every output)
- "Describe the girl's exact outfit, pyjamas details (print, fabric, colors, fit), room, lighting, pose, and overall realism. Is this a candid amateur iPhone selfie with outstretched arm or does it look polished/influencer-staged? Does the outfit match the hero reference exactly with no changes?"
- Compare across the set: "Does this look like it was taken 2-3 minutes after the previous image in the sequence (same clothing state, lighting, hair)?"

## What Worked
- Leading with hero reference + repeated exact outfit description eliminated variation.
- nano_banana_flash was noticeably faster for 3-image batches.
- Adding "unposed candid moment with slight imperfections, not polished or professional composition" improved amateur feel.
- Always checking TZ='Europe/Dublin' date before prompting.
- Updating LANA_VISUAL_IDENTITY.md after each round prevents regression.

## Pitfall Examples from Session
- Initial generations used different velour sets (rainbow Sailor-Moon vs light-blue anime t-shirt) because no hero reference was used.
- Prompts that were too vague on "anime pyjamas" triggered model invention.
- Images that passed basic generation but failed vision_analyze on "amateur iPhone" test were rejected by user.

Save new successful generations as additional hero references. Update this file when new outfit templates survive validation.
