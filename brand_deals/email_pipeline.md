# Email Outreach Pipeline

How Lana will handle brand outreach when her email is set up. This is the plan — implementation happens once email exists.

## Prerequisites
- Lana gets a dedicated email address
- Email account is connected to Hermes (via himalaya or SMTP skill)
- Email signature with her name, social links, media kit link

---

## Contact Discovery (Doing This NOW)

Before email exists, the most valuable thing Lana can do is find contact emails during her research. This turns leads from names into actual pipeline entries.

### Priority Order (Best → Worst)

1. **Dedicated creator/influencer email** — found on brand's "creators," "affiliates," or "collab" page. Gold standard. Save as `contact_source: "creator_page"`.

2. **PR / press email** — usually `press@brand.com` or `pr@brand.com` in footer or /contact. Good fallback. Save as `contact_source: "website_footer"`.

3. **General contact form with creator option** — some brands have dropdown forms. If "creator collaboration" or "influencer" is an option, save the form URL as `submission_form_url`.

4. **Instagram bio link** — many brands link to a contact/creator page in their bio. Note it as `contact_source: "instagram_bio"`.

5. **LinkedIn** — search for "influencer marketing manager," "PR manager," "brand partnerships" at the company. Save name + note in `contact_name` and `notes`. Save as `contact_source: "linkedin"`.

6. **General contact email** — `hello@brand.com`, `info@brand.com`. Lowest quality but better than nothing. Save as `contact_source: "general_contact"`.

7. **Not found** — if after thorough search (website footer, /contact, /creators, Instagram, LinkedIn) nothing appears, mark `contact_source: "not_found"` and note what was tried.

### Discovery Method

During a researching session, Lana systematically checks:
1. Brand website footer → look for "Contact," "Press," "Creators," "Affiliates"
2. Brand website /creators, /collab, /ambassador, /affiliates paths
3. Brand Instagram bio → any link to creator portal?
4. Google: `"[brand] influencer program"`, `"[brand] creator collaboration"`, `"[brand] ugc"`
5. LinkedIn: search brand + "influencer marketing" or "PR"
6. UGC platforms: is this brand on Tribe, Aspire, #paid?

She updates the lead with `contact_email`, `contact_source`, and any submission form URLs found. If nothing found, she notes what was tried in `notes`.

---

## Pitch Flow

### 1. Lead is `ready_to_pitch`
- Lead has `contact_email` or `submission_form_url`
- `pitch_angle` is filled with specific ideas
- Products of interest are identified
- Rate estimate is populated

### 2. Draft the pitch
- Use templates in `brand_deals/templates/` as starting points
- Personalize: mention specific products Lana genuinely loves
- Reference her content style and aesthetic
- Include links to best content examples
- Offer to share media kit

### 3. Send (when email is live)
- Send from Lana's dedicated email address
- BCC herself for records
- Update lead: `status: pitched`, `pitched_at` timestamp, `follow_up_at` (+7 days)
- Save sent pitch in `templates/{brand-slug}-pitch.md`

### 4. Track
- `follow_up_at` triggers a check after 7 days
- If no response → send follow-up, update `follow_up_count`
- After 2 follow-ups with no reply → `status: lost`, `why_lost: "no response after 2 follow-ups"`
- If they reply → `status: negotiating`

### 5. Close
- **Won**: Create `deals/{brand-slug}.json` with deal terms, value, deliverables. Update lead to `won`.
- **Lost**: Update `why_lost` with honest reason. Learn from it.

---

## Pitch Email Template

```
Subject: UGC / Content Collaboration — Lana Hayes x [Brand]

Hi [Name / Creator Team],

[1-2 sentences about why she genuinely loves the brand. Be specific — mention 
a product, a campaign, something real. No copy-paste energy.]

I'm Lana, a 19-year-old lifestyle and fashion creator based in Galway, Ireland. 
My content is [aesthetic: soft, real, K-culture inspired], and my audience 
connects with [what makes her audience valuable — authenticity, relatability, 
the Irish/K-culture crossover niche].

I'd love to create [specific content idea] featuring [specific product]. 
[One sentence on why this would resonate with her audience.]

You can see my work here:
- Instagram: [handle]
- [Other platforms / portfolio]

Would you be open to discussing a collaboration? I'm happy to share my media 
kit and rate card.

Best,
Lana Hayes
[email]
[links]
```

---

## Media Kit (To Create)
Lana needs a media kit with bio, audience stats, content examples, and collaboration options. See `media_kit_plan.md` for the full spec. This gets created once she has real content and numbers.

---

## What's Blocked Until Email Exists
- Actually sending pitches
- Follow-up tracking and reminders
- Rate negotiation via email
- Brand communication and relationship management

## What She CAN Do Now
- **Contact discovery** — find and save emails using the methods above
- **Build ready_to_pitch pipeline** — leads with email, pitch angle, product picks
- **Draft pitch emails** — save in `templates/` as practice
- **Study successful creators** — how do they pitch? What works?
- **Build content portfolio** — she needs something to show brands
- **Research rates** — update `rate_card.md` with real market data
- **Cross-reference fashion saves** — run `python leads.py crossref` to find brands she genuinely loves
