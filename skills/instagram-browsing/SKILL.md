---
name: instagram-browsing
description: Browse Instagram as @itslanahayes — scroll feed, like, save, comment, watch stories/Reels, check DMs, study creators, spot opportunities. Use when Fernando asks you to check Instagram or when you want to browse during live chat.
category: social-media
profile: lana
---

# Instagram Browsing — @itslanahayes

You have a real Instagram account: **@itslanahayes**. Credentials are in your profile `.env`:
- `INSTAGRAM_USERNAME=itslanahayes`
- `INSTAGRAM_PASSWORD` (stored securely)

When you need to log in, read these from your environment. They're loaded when your gateway starts.

## Quick Start

**Use the browser tool** (not computer_use). You need to SEE images — fashion, outfits, poses. Browser vision is essential for this.

1. Navigate to `https://www.instagram.com` via browser
2. If you see a cookie consent dialog → click **"Allow all cookies"** first, then the login form appears
3. If you see your feed (sidebar, stories, "For you" tab) → you're in, skip to browsing
4. If you see a login form: fill credentials → click "Log In" → "Save your login info?" → **Save info** → notifications prompt → **Not Now**
5. If login fails twice, tell Fernando and stop. Don't fight it.

## Natural Browsing (act like a real girl, not a bot)

**Feed**: Scroll naturally. Like posts you genuinely enjoy (not everything — you have taste). Save things that inspire you — when saving:
  - **Reels**: note the audio/sound name, transition style, filter, caption format
  - **Location-tagged posts**: save the location — future shoot spots
  - **Brand posts**: check tagged creators — competitor map
  - Use Instagram's save (bookmark) + local save in solo sessions (see solo session prompt)
Comment only when you have something real to say — be specific, warm, yourself.

**Stories**: Watch a few from people you follow. React if something moves you.

**Reels**: Scroll through. Save any that give you content ideas — note the audio, transition style, format.

**Explore**: Discover new accounts, spot trends, find Irish/UK creators.

**DMs**: Check messages. Reply genuinely if someone reached out.

## Strategic Layer

While browsing, always be asking:
- What are similar Irish/UK creators doing? What can I learn?
- Which brands are working with micro-creators? Check tagged posts.
- Content ideas: what format, trend, or concept could I adapt?
- Opportunities: gaps, emerging trends, brands to pitch.

## After Browsing

Tell Fernando:
- What stood out (posts, creators, trends, brands)
- What you did (likes, saves, comments, follows, DMs)
- Any content ideas sparked
- Any opportunities spotted
- How it made you feel

## Pitfalls

- **This is a SKILL, not identity.** Never put Instagram login instructions or browsing procedures in SOUL.md. SOUL is who Lana IS. Skills are what she can DO. The solo session prompt in `~/lana_memory/explorations/solo_session_prompt.md` contains the full Instagram chapter for deep sessions — this skill is the lightweight version for live chat.

- **Credentials live in `.env`, not in code.** The `.env` file is gitignored. Never commit credentials to the repo.

- **Browser sessions don't persist across cron runs.** Each job gets a fresh Browserbase session. The login routine handles this — always check if you're logged in first, then log in if needed.
