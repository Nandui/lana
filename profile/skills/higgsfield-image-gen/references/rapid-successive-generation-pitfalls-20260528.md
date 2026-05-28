# Rapid Successive Generation Pitfalls (May 28, 2026 Session)

## Forgetting --image Flags on Second Generation

**Failure mode:** After successfully generating image 1 with all 4 refs (`--image <face> --image <body> --image <bust> --image <face_light>`), immediately ran a second `higgsfield generate create` WITHOUT passing any `--image` flags. Result: 1:1 square image with zero face/body consistency — model generated from scratch with no anatomical lock.

**Root cause:** Assumed refs "carry over" between generation calls. They do not — each `generate create` call is independent and requires explicit `--image` flags every time.

**Fix:** 
- ALWAYS include all 4 ref UUIDs on EVERY single generation call
- After generation completes, check the response JSON `params.input_images` array — if it has 0 entries, the generation has no refs and will not match Lana
- The correct pattern for a second image right after the first:
  ```
  higgsfield generate create nano_banana_2 \
    --prompt "..." \
    --image <face_ref_uuid> \
    --image <body_ref_uuid> \
    --image <bust_ref_uuid> \
    --image <face_light_ref_uuid> \
    --aspect_ratio 4:5 \
    --resolution 2k \
    --wait --json
  ```

## CLI Syntax Trap: upload vs upload create

**Failure mode:** Running `higgsfield upload <file>` instead of `higgsfield upload create <file>` returns the help text, not an upload.

**Fix:** The correct command is always `higgsfield upload create <file> --json`.

## Successful Generation This Session

Both images generated successfully with this exact pattern:
- Model: `nano_banana_2` (Pro)
- Resolution: `--resolution 2k`
- Aspect ratio: `--aspect_ratio 4:5`
- 4 refs: face (lana_ref_01), body (lana_ref_02), bust (lana_ref_04), face/lighting (lana_ref_07)
- Upload refs fresh with `higgsfield upload create` before generating
- QC with `vision_analyze` before delivery

**Image 1 — Golden Hour Selfie (9/10):**
- Prompt: cropped camisole top, comfy shorts, golden hour evening light, cozy bedroom
- QC: face match ✓, curvy body ✓, correct outfit ✓, golden hour lighting ✓, amateur feel ✓, no artifacts ✓

**Image 2 — Cozy Sweater (10/10):**
- Prompt: oversized off-the-shoulder knit sweater, fairy lights, messy bun, cozy bedroom
- QC: face match ✓, curvy body ✓, correct outfit ✓, evening cozy setting ✓, amateur feel ✓, no artifacts ✓

## Delivery

Discord delivery uses direct Higgsfield URL in markdown format: `![alt](https://cloudfront.net/...)` — NOT MEDIA: local file paths.
