# Outfit Reference Upload Technique (May 27 2026)

## What It Is
Instead of describing an outfit purely in text (which can drift), download an actual product photo of the desired outfit and upload it as an additional `--image` reference to Higgsfield. The model then replicates the exact clothes from the uploaded image onto the generated character.

## Why It's Better Than Text-Only
- Text descriptions like "dusty pink velour cropped hoodie" can produce variations in shade, cut, fabric texture
- An actual product photo locks: exact colour, fabric texture/sheen, cut, stitching details, logos/embroidery, hardware (zips, buttons)
- Especially powerful for specific brand aesthetics (Chuu, NERDY, etc.) where the exact look matters

## Workflow
1. **Find the outfit image**: Browse Pinterest, Shein, PrettyLittleThing, ASOS, brand sites for the desired outfit
2. **Download the image**: Save the product photo locally
3. **Upload to Higgsfield**: `higgsfield upload create <local_path>` to get a UUID
4. **Use in generation**: Add `--image <outfit_uuid>` alongside the face/body ref UUIDs
5. **Prompt accordingly**: Reference the uploaded image explicitly:
   - "wearing the exact outfit from the uploaded clothing reference image"
   - "identical fabric, colour, cut and details as the clothing reference"
   - "the velour/sheen/cut must match the uploaded reference exactly"

## Example Command
```bash
# Upload the outfit reference
higgsfield upload create ./dusty_pink_velour_set.jpg
# Returns UUID like: a1b2c3d4-...

# Generate with outfit ref + face/body refs
higgsfield generate create nano_banana_2 \
  --prompt "exactly matching the girl in the reference pictures, wearing the exact outfit from the uploaded clothing reference, identical velour fabric with sheen, same cropped zip-up cut and jogger fit..." \
  --image <face_ref_uuid> \
  --image <body_ref_uuid> \
  --image <outfit_ref_uuid> \
  --aspect_ratio 4:5 \
  --resolution 2k \
  --wait
```

## When to Use
- User asks to see a specific outfit ("show me the black velour set")
- Text descriptions have been producing inconsistent results
- The outfit has specific details (embroidery, logos, contrast stitching, specific fabric sheen)
- Building a new outfit hero from a product image rather than a generated image

## When NOT to Use
- Simple outfit descriptions that work fine in text ("cream knit sweater")
- When no good product image is available
- For anatomy-only refs (those stay as `lana_ref_*` files)

## Reference Order (Updated)
Face ref first → body ref second → outfit ref third. When using the outfit reference upload technique, the outfit ref replaces the need for a "hero" reference for that specific outfit — it IS the outfit source of truth. For subsequent images in a sequence, the previous generated image becomes an additional ref to lock outfit/setting continuity.

## Validated Examples (May 27 2026)
- **Olive green velour tracksuit**: Downloaded Felina Deep Olive velour set product image from Amazon → uploaded as `--image` ref alongside face/body refs → generated with prompt "wearing the exact olive green velour tracksuit from the outfit reference image" → QC scored 9/10 with perfect outfit match including velour sheen, zip-up hoodie, joggers, and correct olive green colour. User confirmed "i see really good!"
- **Cream oversized fuzzy fleece**: Downloaded GKBK cream fuzzy fleece lounge set from Amazon → uploaded as outfit ref → QC scored 9/10 with perfect plush fabric texture, oversized fit, and cream/off-white colour. User said "cuuute".
- Both scored 9/10 vs text-only descriptions which typically score 7-8/10 on outfit accuracy.

## Source Sites (What Works)
- **Amazon**: Most reliable — loads without bot detection, has product images with clean backgrounds. Search: "velour loungewear set women [colour]".
- **Pinterest**: Works for browsing and viewing pins. Image URLs follow pattern `https://i.pinimg.com/736x/...` — extract via browser console (`document.querySelectorAll('img[src*="pinimg"]')`) or right-click → Copy image address. Bot detection can block login-gated content but search results are usually accessible.
- **Shein, PrettyLittleThing, ASOS**: Frequently blocked by bot detection/CAPTCHA. Amazon and Pinterest are the fallbacks.
- **Brand sites (Chuu, NERDY)**: May work but often have aggressive bot detection.

## Pinterest Browsing Workflow (Verified May 28 2026)
Full end-to-end pattern for outfit discovery from Pinterest:
1. Navigate to Pinterest search: `https://www.pinterest.com/search/pins/?q=korean+cosy+loungewear+set+cropped+summer`
2. Accept cookies if prompted
3. Use `browser_vision` to see and describe the pin grid — identify promising outfits
4. Click on a pin to see the full product image
5. Extract image URL via browser console: `document.querySelectorAll('img[src*="pinimg"]')` — pick the largest/highest-res version
6. Download with `curl -sL "<url>" -o /tmp/outfit_ref.jpg`
7. Verify with `file /tmp/outfit_ref.jpg`
8. Upload to Higgsfield: `higgsfield upload create /tmp/outfit_ref.jpg --json`
9. Use the returned UUID as outfit `--image` ref alongside face/body refs
10. Generate with prompt referencing the uploaded outfit: "wearing the exact outfit from the uploaded clothing reference image"

**Pinterest login modal pitfall (May 28 2026):** Pinterest sometimes shows a "Log in to see more" modal that blocks the visual display of pins. However, the image URLs are still loaded in the DOM behind the modal. Use the console extraction technique (`document.querySelectorAll('img[src*="pinimg"]')`) to grab URLs even when the modal is visible. The `browser_vision` tool may report a black/blank screen when the modal is active — this doesn't mean the page failed, just that the modal is overlaying the content. Try console extraction first before giving up on a Pinterest page.

**Seasonal search terms that work well:**
- Summer: "korean cami shorts set summer", "pastel loungewear set cropped", "lightweight knit set women"
- Winter: "korean velour tracksuit", "fuzzy fleece lounge set", "cosy pyjama set anime"

## User Feedback
User explicitly said: "you can sometimes download the picture of the outfit, upload it in addition to your reference pictures and prompt to use the clothes on that picture you uploaded. This way you did now works too, but that is another way to do it and sometimes is even better." After I used it successfully: "you are so fucking good at this, love when you do what I suggest!" — strong positive reinforcement. **Always use this technique when user asks to see a specific outfit.**
