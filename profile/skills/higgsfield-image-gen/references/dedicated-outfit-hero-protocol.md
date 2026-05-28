# Dedicated Outfit Hero Protocol (from session where clothing kept drifting despite prompts)

## Trigger
User says "the clothing is not the same", "you used a random picture that was not part of your references", or "picture one is fantastic but the other 2..." 

## Exact Steps (embed in every short-sequence task)
1. When user approves an image as "fantastic", "YESS OH YES", or "great body and composition", **immediately** curl it to `/Users/fernandoserina/.hermes/profiles/lana/home/lana-identity-references/INVALID_ARCHIVED_lana_pyjamas_hero_reference.png` (or outfit-specific name). Do not use generated "master hero" files that are not saved into the official references folder.
2. Run `vision_analyze` on the new hero with the prompt "Extract verbatim exact outfit description for use as hero reference... Provide the exact phrase to use in prompts like 'the exact soft pink velour pajama set with...'".
3. Add the verbatim phrase to every subsequent prompt: "exactly matching the girl and the exact [verbatim phrase from analysis] in the hero reference photo, identical outfit with no changes whatsoever as if photos taken only 2-3 minutes apart".
4. **Always** lead with this hero as the **FIRST --image flag**, followed by primary face (lana_ref_01), body (ref_02), and bust (ref_04) references. Never rely on text prompt alone or "random" recent generations.
5. When user asks "What do you need from me?", answer honestly: "Please send or confirm the definitive hero shot of the exact outfit. I'll save it, analyze it for the verbatim description, and use it as the lead reference in every generation so clothing stays identical."

## Why this is required
Without a dedicated, analyzed hero for the exact outfit from the "fantastic" image, the model changes fabric, button state, fit, color tone, or details between shots. This was the root cause of the repeated "clothing is not the same" feedback. Using only the official primary references (ref_01 face first) + dedicated hero stops the back and forth.

## Example Verbatim Phrase (from golden hour pink velour session)
"the exact soft pink velour pajama set with a long-sleeved button-up top made of plush velvety fabric that has a slightly mottled/tie-dye effect in varying shades of soft pink and light pink, white piping along the collar and button placket, left chest pocket, the top three buttons completely unbuttoned creating deep plunging cleavage with visible inner curves of breasts and upper torso, the velour fabric hugging her body tightly across the bust and ribcage while the sleeves are slightly looser, matching soft pink velour pajama pants"

Save this file and link it from the main SKILL.md. Update after every new outfit approval. This is now part of the non-negotiable consistency protocol.