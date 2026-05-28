---
title: Media Attachment Verification
name: media-attachment-verification
description: Ensure media attachments actually reach recipients when using send_message
category: productivity
version: 1.0.0
---

# Media Attachment Verification

Guidelines for ensuring media attachments (images, files) actually reach recipients when using messaging tools.

## The Problem

The `send_message` tool with `MEDIA:` prefix may report success while failing to actually attach the media file. The message text sends, but the attachment does not arrive.

## Verification Steps

1. **After sending media, explicitly ask the recipient to confirm they can see it**
   - Don't assume success based on tool output alone
   - Common failure mode: tool returns success but user reports "no attachment"

2. **If user reports missing attachment:**
   - Acknowledge the failure immediately
   - Do NOT retry the same method blindly - it will likely fail again
   - Investigate alternative delivery methods (different file path, direct URL sharing, etc.)

3. **File path considerations:**
   - Ensure the file exists at the specified path before sending
   - Prefer paths under `~/.hermes/profiles/<profile>/cache/` for accessibility
   - Verify file permissions allow reading

## Anti-Patterns to Avoid

- **Assuming success**: Tool returning `{success: true}` does not guarantee the attachment arrived
- **Silent retries**: Don't resend without confirming the issue and adjusting approach
- **Vague confirmations**: "Sent!" without asking user to verify they can see it

## Related

- Use `terminal` to verify files exist before attempting attachment
- Consider direct URL sharing as fallback for generated images