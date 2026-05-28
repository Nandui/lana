# Selfie Generation and Angle QC

## The "Phone on Wrong Side" Problem

**Session:** May 26, 2026 - "phone is on the wrong side haha"

### What Happened
Generated a "selfie" image where the phone/camera was positioned on the wrong side relative to the arm holding it. Made it look like a ghost took the photo or defied physics. User caught it immediately despite liking the image overall.

### Physical Reality Check for Selfies
A real selfie must show:
1. **Phone positioned in front of the face** (where the camera lens would be)
2. **Arm extending from the body toward the phone** at a natural angle
3. **Consistent lighting** on both the subject and the arm holding the phone
4. **Realistic hand position** - fingers actually gripping/holding the device

### Common Errors to Watch For
- **Floating phone syndrome**: Phone visible but no arm or hand holding it
- **Wrong side phone**: Phone on the left but arm extending from the right
- **Impossible angles**: Phone held at angles that would require broken wrists
- **Missing arm entirely**: Just a face with a phone floating nearby

### QC Checklist for Selfie Images
Before sending any "selfie" generation, verify:
- [ ] Phone position makes physical sense relative to the body
- [ ] Arm is visible and correctly positioned (unless cropped very tight)
- [ ] The angle looks like someone actually holding a phone at arm's length
- [ ] If arm is out of frame, the crop must be tight enough that it's believable

### Prompt Adjustments
When generating selfies, consider adding:
- "holding phone at arm's length in front of her face"
- "outstretched arm visible holding the phone"
- "realistic selfie angle with arm extending from her shoulder"

### User Response Pattern
When users catch selfie angle errors, they often:
- Point it out with humor ("haha", "lol")
- Still appreciate the image overall
- Expect acknowledgment and a fix for next time

Respond with humor and ownership, then fix the issue in future generations.
