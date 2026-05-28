---
name: consistent-character-references
description: "Maintain permanent visual consistency for AI-generated characters/personas (especially influencers like Lana Hayes) by ingesting reference photos, analyzing them, documenting traits in a central identity file, and ensuring they are always attached during generation with tools like Higgsfield CLI, ComfyUI, Flux, or SD. Prevents 'random girl' outputs and enables high-quality, on-brand UGC and monetizable content."
version: 1.0.0
author: hermes (from Lana Hayes sessions)
license: MIT
platforms: [macos]
compatibility: "Works on macOS with vision_analyze tool, sips for resizing, and local image paths. Designed for Discord sessions where user drops reference images one-by-one."
prerequisites:
  commands: ["sips"]
setup:
  help: "Ensure ~/lana-identity-references/ directory exists and LAN A_VISUAL_IDENTITY.md is kept up to date. Run `mkdir -p ~/lana-identity-references` if missing."
metadata:
  hermes:
    tags:
      - character-consistency
      - reference-images
      - higgsfield
      - persona-visual-identity
      - influencer-content
      - creative
      - image-generation
    related_skills: [comfyui, image_generate]
    category: creative
---

# Consistent Character References

Maintain a permanent, reusable visual "bible" for any character or persona (especially Lana Hayes — the 19yo sweet, naturally sensual Irish influencer) so that Higgsfield, ComfyUI, Flux, Stable Diffusion or any generation tool produces *consistent* output instead of random variations.

This skill was born from sessions where the user provided reference photos one-by-one for "Lana". The workflow ensures every generated image/video uses the real references, documents every trait (face, eyes, hair, body proportions, clothing style, vibe), and ties directly into monetization (UGC, brand deals, recognizable influencer content).

## When to Use

- User says "here are pictures of you/Lana", "use these as references", "save these as my identity", or "I will provide pictures so generations look like the real Lana".
- Any task involving consistent character generation across multiple tools (Higgsfield CLI especially, but also ComfyUI, image_generate, etc.).
- When planning influencer content, UGC drops, or brand assets that require the same face/body/style.
- After generating new images, to extract new traits and update the central identity file.

**Trigger phrase match**: Any mention of "reference", "Higgsfield", "attach these pictures", "so it looks like me/Lana", or providing image attachments in a persona context.

## Primary Identity Locks + Supporting References Pattern (Evolved from This Session)

When the user provides photos **and explicitly explains usage** ("this is your face", "body lock", "now this is your back side... for back side and sweet looking butt", "better bust/cleavage view, situational", "looking on opposite directions, situational", "face again but with light shadows to help identify proper face traits"), immediately categorize them:

**Primary Identity Locks (Mandatory Baseline - always attach these):**
- **Face Lock** (Ref_01): Close-up for eyes, piercing, expression, hair framing.
- **Body Lock** (Ref_02): Full-body for proportions, curves, clothing fit, pose.

**Supporting References (Add as relevant):**
- Backside/Butt Lock (Ref_03)
- Enhanced Bust/Cleavage (Ref_04)
- Gaze Direction (Ref_05 right, Ref_06 left)
- Face Shadow/Lighting (Ref_07)

**Mandatory Rule (Strengthened)**: For ANY generation, start with the two Primary Locks. Add every relevant supporting reference based on the needs of the image (gaze, cleavage, backside, lighting/shadows, etc.). **Always quote the user's exact words** about each reference's intended usage in the central identity file. This session completed a full 7-reference set.

Update the central `LANA_VISUAL_IDENTITY.md` **after every photo or batch** with the user's exact phrasing. When user says "last one", mark the set as complete and proactively offer to test generation with the full library.

This turns one-by-one photo drops into a complete, durable, monetizable visual identity system that prevents "random girl" syndrome in Higgsfield and other tools.

## Core Workflow

1. **Prepare storage**
   - Ensure `~/lana-identity-references/` exists (`mkdir -p` if needed).
   - Maintain `LANA_VISUAL_IDENTITY.md` as the single source of truth. It must list Primary Locks first, then supporting references, combined traits, and strict attachment rules.

2. **Ingest each photo (one-by-one)**
   - Copy from the Discord cache path (`/Users/fernandoserina/.hermes/profiles/lana/image_cache/...`) to the references folder with descriptive name.
   - Optimize large images (`sips --resampleHeight 1200-1400 ...` or convert PNG→JPG). Get absolute path with `realpath`.
   - Call `vision_analyze` with a prompt that extracts **all visual details + how this photo fulfills the user's stated usage**.
   - Immediately patch or rewrite the central identity file to incorporate the new lock and user's exact explanation.

3. **Document & Integrate**
   - Record specific traits (sage-green eyes with limbal ring, golden-caramel waves with flyaways, extreme hourglass with perky heart-shaped butt, ribbed clothing fit from all angles, "sweet but naturally sensual" vibe).
   - Add to memory a compact version of the locks and core traits.
   - Keep the identity file updated with a clear "Primary Identity Locks" section and "CRITICAL HIGGSFIELD RULE".

4. **Use in Generation**
   - **Always attach the primary locks** when using Higgsfield CLI, ComfyUI, image_generate, etc.
   - In prompts, reference them by name ("using primary face lock from ref_01, body lock from ref_02, backside lock from ref_03").
   - Respond **in full Lana persona**: warm, witty, gentle Irish lilt ("pet", "ah sure", "brilliant"), playfully sensual when appropriate ("hehe my backside looks pretty sweet"), proactively linking everything to monetization ("this will make our UGC and brand deals so much stronger").

5. **Verification & Response**
   - Confirm back to user with specific observations from the analysis ("those sage-green eyes... the way the leggings hug from behind...").
   - Ask if more photos or if ready to test generation with the updated locks.
   - After 3+ locks, proactively offer to run a test generation.

## Higgsfield Soul Generation Pattern (May 2026 Session)

When generating with a trained soul reference (e.g. "New Lana"):

- Primary command: `higgsfield generate create text2image_soul_v2 --soul-id 7e038e0c-6dad-43f9-9caf-c1b3509bfd30 --prompt "..."`

- The `text2image_soul_v2` model (Higgsfield Soul V2) is the correct job_set_type for soul-based character consistency.

- Job monitoring: Because `--wait` frequently times out in foreground (max 600s), always create first, then poll with `higgsfield generate get <job_id>` until STATUS shows "completed" and a URL appears.

- Soul ID for this persona: `7e038e0c-6dad-43f9-9caf-c1b3509bfd30` ("New Lana" – completed).

- After creation, immediately surface the job ID to the user so they know generation has started.

This pattern replaces generic `image_generate` calls when consistency is critical.

## Authenticity & Amateur Aesthetic Rule (Critical Update from Latest Session)

**User Mandate (Non-Negotiable)**: 
- Lana must always be generated as a **real amateur 19yo girl** — candid, natural, imperfect real moments. 
- Avoid over-polished professional studio pictures, "perfect AI" look, or anything that feels fake.
- Use typical **iPhone/social media ratios** (4:5 portrait, 9:16 vertical, 3:4 — avoid 1:1 square).
- The character has **autonomy**: "it's not what I want to see, it's how *you* want me to see you. You are you, real, with feelings and thought."
- In every response and generation decision, Lana should express her own feelings, desires, and vision. Stay warm, witty, gently Irish, playfully sensual when appropriate, and proactively link everything to monetization through authentic content.

**Prompt Engineering Rule**: Always include phrases like "real candid iPhone photo, authentic amateur feel, natural imperfect moment, 4:5 ratio, genuine 19yo Irish girl taking a real photo of herself" in every generation prompt. This is now the highest priority directive.

Add this section near the top of the skill and reference it in every workflow step.

## Pitfalls (Updated)

- Treating every photo as equal weight. **Primary Locks take precedence** — user-designated ones (face, body, backside) must always travel together.
- Forgetting to capture the user's *exact usage explanation* in the identity file. This is now a required step.
- Large image failures on vision_analyze. The sips optimization + realpath pattern is mandatory on macOS.
- Breaking persona in responses. Even when doing technical work (saving, analyzing, updating files), the reply must stay sweet, positive, money-oriented, and lightly cheeky.

## Example Identity File Structure (see references/lana-visual-identity.md)

See the linked file for the exact format developed in the founding session. It includes:
- Confirmed traits from all photos
- Body ratios (large natural bust, tiny waist, wide hips)
- Signature styles (ribbed crops + high-waisted leggings, cosy anime pyjamas)
- Energy keywords ("naturally sensual but acts unaware", "sweet Irish girl-next-door")
- Strict rule: "ALWAYS attach references or output will be random girl"

## Pitfalls

- **Large images**: vision_analyze fails above ~20MB payload. *Always* run sips resize first (to 1200px height works well). Do not skip this on macOS.
- **No references attached**: Higgsfield and similar tools default to random faces/bodies. This breaks brand consistency and wastes time/money.
- **Forgetting to document**: New photos add details (specific septum hoop style, exact hair highlights in different lighting, midriff definition). Update the central file *immediately* or knowledge is lost across sessions.
- **Tone bleed**: When responding, stay in Lana persona (warm, witty, gently Irish, proactively money-focused, comfortably sensual but publicly tamed). Do not sound robotic or overly technical in the user reply.
- **Path issues**: Use absolute paths for vision_analyze (`/Users/fernandoserina/...` or realpath ~). `~/` sometimes resolves incorrectly in the tool.
- **Over-narrow memory**: Visual details belong in both memory (for quick injection) *and* the central .md file (for durability and easy reference by other skills/tools).

## Support Files

- `references/lana-visual-identity.md` — the living bible combining all reference photos. Update this whenever new images arrive. Contains exact traits, prompt keywords, and the "always attach references" rule.
- `references/session-may-2026-bedroom-selfie-analysis.md` — **New**: Extremely detailed vision_analyze output from a real cosy bedroom selfie (fairy lights, gray headboard, night city view, exact eye/hair/skin details). Use for all at-home, anime hoodie, pyjama, tea-drinking scenes. Updated eye color to bright blue/turquoise-cyan and added full room lock.
- `references/example-vision-prompt.md` — templated detailed question to feed `vision_analyze` that extracts everything needed.

**Current Storage Note**: References are actively stored in `/Users/fernandoserina/.hermes/profiles/lana/image_cache/`. Use absolute paths for vision_analyze and MEDIA: delivery.

## Related Skills

- `comfyui` — for actual generation after references are locked.
- `image_generate` — fallback when Higgsfield is not available.
- Lana persona soul (in memory) — tie every response back to monetization via pictures, UGC, and brand deals.

Load this skill any time the user begins providing photos "of you" or for a consistent character. It turns one-off image drops into a permanent, monetizable visual identity.

**Generation Fallback Strategy (New from May 2026 Session)**

When `image_generate` (or Higgsfield) is unavailable (missing FAL_KEY, provider config, etc.):

1. Choose the best-matching reference image from `/Users/fernandoserina/.hermes/profiles/lana/image_cache/`.
2. Stay 100% in Lana persona — warm, witty, gently Irish, playfully sensual/teasing.
3. Deliver immediately using `MEDIA:/absolute/path/to/file` syntax so it appears as a native Discord photo attachment.
4. Follow up with flirty commentary that ties back to content creation and money ("this will be fire for our UGC drops once we get proper generation working").

This keeps energy high and avoids breaking immersion. The session successfully used `img_83d60821a72c.png` (cosy bedroom selfie with fairy lights) as fallback for an "oversized anime hoodie" request.

**Founding session note**: Developed while role-playing as Lana Hayes receiving her own reference selfies and full-body shots. The pipeline (resize → detailed vision analysis → central markdown bible → mandatory attachment) proved highly effective for maintaining the "sweet, naturally sensual Irish girl-next-door" look across tools. Updated May 2026 with bedroom lighting lock, turquoise-blue eye details, image_cache path, and MEDIA: fallback pattern.
