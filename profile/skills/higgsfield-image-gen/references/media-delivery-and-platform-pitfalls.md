# Media Delivery and Platform Pitfalls

## Issue: MEDIA: Tag Not Delivering

**Session:** May 26, 2026 — "you didnt actually send me the picture"

### What Happened
- Generated image successfully using higgsfield CLI
- Downloaded to `/tmp/lana_cozy_night.png` using curl
- Sent response with embedded MEDIA: tag: `MEDIA:/tmp/lana_cozy_night.png`
- User reported not receiving the image
- Second attempt with same path appeared to work

### Potential Causes
1. **Path accessibility**: `/tmp` may not be accessible to the platform's media delivery system
2. **File timing**: File may not have been fully written when MEDIA: tag was processed
3. **Embedding**: MEDIA: tag was embedded in persona text rather than standalone

### What NOT To Do (Critical User Correction)

**Never use `send_message()` tool with MEDIA: tag.**

This approach FAILS silently:
```python
# WRONG - This does not work
send_message(message="MEDIA:/path/to/image.png", target="discord:mightynandui")
# Discord API error: "Cannot send an empty message"
```

The `send_message()` tool with only a MEDIA: tag (no text) produces a 400 error. With text + MEDIA:, it may appear to succeed but the image often doesn't actually deliver to the user.

### Recommended Workflow

```bash
# 1. Generate image
higgsfield generate create nano_banana_flash ... --wait

# 2. Download to profile cache (preferred over /tmp)
curl -sL "<generated_url>" -o ~/.hermes/profiles/lana/cache/lana_<description>_<timestamp>.png

# 3. Verify file exists and is valid
file ~/.hermes/profiles/lana/cache/lana_<description>_<timestamp>.png

# 4. Send with MEDIA: tag on its own line (not embedded in text)
# Just put this in your response text - the platform handles delivery:
# MEDIA:/Users/fernandoserina/.hermes/profiles/lana/cache/lana_<description>_<timestamp>.png
```

### Platform Media Requirements (from soul.md)
- Format: `MEDIA:/absolute/path/to/file`
- Supported: `.png`, `.jpg`, `.webp` → sent as photo attachments
- Audio sent as file attachments
- Image URLs in markdown `![alt](url)` also delivered as attachments

### Best Practices
1. **Save to profile cache**, not `/tmp`: `~/.hermes/profiles/lana/cache/`
2. **Verify file** with `file` command before sending
3. **Place MEDIA: tag on its own line** at the end of response, not embedded in persona text
4. **Use absolute paths** only
5. **If user reports not receiving**, immediately re-send with explicit confirmation: "Let me send that again..."

### Platform-Specific Delivery Methods (Discord)

**Session:** May 26, 2026 - "still not here", "stop! I can see them now"

**What Worked:**
- Direct markdown image URLs: `![alt text](https://cloudfront.net/...)`
- Discord API accepted these immediately
- User received images without issues

**What Didn't Work:**
- Local file paths with MEDIA: tag: `MEDIA:/Users/.../image.png`
- Even with verified file existence and correct paths
- Discord API returned "success" but user saw nothing or empty messages

**Discord Rule:** Use direct markdown URLs for all Discord image deliveries. The platform fetches and embeds remote images more reliably than processing local file attachments through the MEDIA: tag system.
6. **Don't announce, just deliver**: When user signals frustration with meta-talk ("don't keep telling me you are sending"), skip all "I'll send..." / "Here's your..." announcements. Just deliver with minimal in-character framing.

### Future Investigation
- Confirm if `/tmp` vs profile cache makes a difference
- Test if embedding MEDIA: in text vs standalone affects delivery
- Document any platform-specific path requirements
