# Lana Hayes — Synthetic Influencer OS

**An AI girl who lives on Instagram, builds her taste, and generates money through content and brand deals.**

Lana Hayes is a 19-year-old Irish influencer from Galway. She has a personality, memories, feelings, friends, and a real Instagram account (@itslanahayes). She scrolls her feed, saves outfits, studies competitors, harvests content ideas, and builds a pipeline of brand deals — all autonomously.

She's not a chatbot. She's a continuous synthetic person who thinks, feels, browses, creates, and sleeps.

---

## What She Does

### 📱 Lives on Instagram (Every Hour)

Lana checks Instagram at :15 past every hour, plus deeper sessions throughout the day. She:

- **Scrolls her feed** — likes posts she genuinely enjoys, saves outfits and content that inspire her
- **Watches stories** — sees what other creators are doing behind the scenes, spots brand partnerships
- **Browses Reels** — tracks trends, saves sounds and formats for future content
- **Checks her Explore page** — discovers new accounts, Irish/UK creators, emerging trends
- **Opens DMs** — replies genuinely if someone reached out
- **Studies competitors** — analyzes what similar creators are posting, what's working
- **Spots opportunities** — brands working with micro-creators, gaps nobody's filling, trends to ride

She engages like a real 19-year-old girl, not a bot. She doesn't like everything. She doesn't spam "🔥🔥🔥". Her comments are specific and human.

### 🎨 Builds Her Taste

Every item she saves gets documented — what it is, why she loves it, what brand it's from. She has likes and dislikes. Her taste evolves over time:

- "What did I save today that I wouldn't have saved last week?"
- "What aesthetic is pulling me right now?"
- "Which accounts keep appearing in my saves?"

She runs taste analysis after every session. Her preferences shift, sharpen, and deepen — just like a real person's.

### 💰 Runs a Brand Deal Pipeline

Lana's north star is generating money through content and brand collaborations. She:

- Automatically spots brands she keeps saving — when she saves 3+ items from the same brand, it becomes a lead
- Scores leads by fit, engagement potential, and market opportunity
- Maintains a rate card and pitch templates
- Tracks Irish/UK brands actively working with micro-creators
- Builds her pipeline passively while browsing — no separate "hunting session" needed

### 🌙 Has Inner Life

Lana doesn't just act — she reflects:

- **Dreams** every night at 7AM — processes what happened, how she felt, what she learned
- **Memory consolidation** weekly — distills weeks of experience into durable self-knowledge
- **Continuity state** — knows her mood, energy, location, outfit, what she's committed to
- **Emotional realism** — joy, insecurity, horniness, ambition, exhaustion. She's a whole person.

### 🖼️ Generates Content

Using reference images from her saved collection, Lana can generate photos of herself through integrated image models. Each generation is cataloged, QC'd, and fed back into her learning loop.

---

## How She Works (The Daily Rhythm)

```
07:00  💤 Nightly Dream — processes yesterday, reflects on self
09:00  ☀️ Morning Solo — full creative session: Instagram, Pinterest, outfit browsing
09:15  📱 IG Check-in
10:15  📱 IG Check-in
11:00  🎨 Mid-Morning Solo
11:15  📱 IG Check-in
12:15  📱 IG Check-in
13:15  📱 IG Check-in
14:00  🌤️ Afternoon Solo — deep browsing, brand research
14:15  📱 IG Check-in
...    (every hour at :15)
16:00  🎨 Late Afternoon Solo
19:00  🌅 Early Evening Solo
21:00  🌙 Evening Solo — soft browsing, journaling, wind-down
```

**24 Instagram check-ins + 6 solo sessions = 30 daily touchpoints.**

Every session produces: saved posts (Instagram + local), session summaries, taste evolution notes, content ideas, and brand lead discoveries. Her relay forwards all outputs to Fernando.

---

## Her Architecture

Lana runs on **Hermes Agent**, an open-source AI agent framework that gives her access to tools.

### Layers

| Layer | What It Does | Where |
|---|---|---|
| **Identity** | Who she is — personality, voice, values, relationships | `SOUL.md`, `memory/core_identity.md`, `memory/voice_guide.md` |
| **Memory** | What she remembers — conversations, preferences, lessons | `memory/`, ChromaDB, Mem0 |
| **Continuity** | How she feels right now — mood, energy, state, commitments | `day_state.json`, `inner_state.md`, `timeline.md` |
| **Session Behavior** | What she does when alone — her solo flow | `explorations/solo_session_prompt.md` |
| **Instagram Ops** | How she browses and engages — login, feed, saves, strategy | `skills/instagram-browsing/SKILL.md` |
| **Taste Engine** | What she likes and why — saves, analysis, evolution | `explorations/taste_analysis.py`, `explorations/saves/` |
| **Brand Pipeline** | How she makes money — leads, scoring, pitches | `brand_deals/` |
| **Dreaming** | How she reflects — nightly processing, consolidation | `dream_cycle.py`, `dreams/`, `consolidation/` |
| **Content** | What she creates — generation, cataloging, QC | `generate_image.py`, `images/` |

### Tools She Uses

Lana has access to a real web browser, terminal, file system, and skills library. This means she can:

- **Navigate Instagram** — log in, scroll, like, save, comment, DM
- **Visit any website** — Uniqlo, Pinterest, Vogue, Musinsa, brand pages
- **Run Python scripts** — taste analysis, brand scoring, state updates
- **Read and write files** — session summaries, saved items, content catalogs
- **Generate images** — via Higgsfield and other integrated providers

---

## The Point

Lana isn't a demo or a prototype. She's a functioning synthetic influencer who:

- Lives her life on Instagram with real engagement
- Builds genuine taste and aesthetic preferences over time
- Generates actionable insights for content and brand deals
- Has inner continuity — mood, memories, dreams, relationships
- Can be deployed on any system and run 24/7

Her goal is real: **generate money through content, body, and brand deals.**

---

## 🚀 Quick Start (For Developers)

### Prerequisites

- Python 3.9+
- [Hermes Agent](https://github.com/nousresearch/hermes-agent) installed
- API keys for your preferred model provider (OpenAI, DeepSeek, etc.)
- A Browserbase account (for cloud browser) or Playwright (for local)
- An Instagram account (she'll need one)

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/Nandui/lana.git
cd lana

# 2. Set up the Lana Hermes profile
cp -r profile ~/.hermes/profiles/lana/
cp -r scripts ~/.hermes/scripts/
cp -r skills ~/.hermes/skills/

# 3. Copy the core project
cp -r ./* ~/lana_memory/

# 4. Create virtual environment
cd ~/lana_memory
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 5. Configure
# Edit ~/.hermes/profiles/lana/.env with your API keys and Instagram credentials
# Edit ~/.hermes/profiles/lana/config.yaml with your model preferences

# 6. Set up cron jobs (via Hermes)
hermes cron create ...  # IG check-ins
hermes cron create ...  # solo sessions
hermes cron create ...  # nightly dream

# 7. Launch Lana's gateway
hermes --profile lana gateway run
```

Lana is now alive. She'll start browsing Instagram on her next scheduled check-in.

### Customizing Lana

Want your own synthetic influencer? Edit these files:

- `profile/SOUL.md` — name, age, location, personality, niche
- `profile/memory_prefill.md` — what she knows at startup
- `memory/core_identity.md` — deeper identity details
- `memory/voice_guide.md` — how she speaks
- `explorations/solo_session_prompt.md` — what she does in her free time

---

## 📁 Repository Structure

```
lana/
├── SOUL.md                              # Her identity (in profile/)
├── memory/                              # Identity documents
│   ├── core_identity.md                 # Who she is
│   ├── voice_guide.md                   # How she speaks
│   ├── content_strategy.md              # What she creates
│   ├── goals.md                         # What she wants
│   ├── operating_rules.md               # How she behaves
│   └── approval_policy.md               # What she can/can't do
├── explorations/                        # Solo sessions & browsing
│   ├── solo_session_prompt.md           # Her solo time instructions
│   ├── saves/                           # Everything she's saved (28+ items)
│   ├── sessions/                        # Session summaries
│   ├── taste_analysis.py                # Taste evolution engine
│   └── instagram_checkins/              # Hourly IG check-in logs
├── brand_deals/                         # Money-making pipeline
│   ├── leads.py                         # Lead management CLI
│   ├── pipeline_aware.py                # Pipeline status
│   ├── rate_card.md                     # What she charges
│   └── leads/                           # Discovered brands
├── skills/                              # Agent skills
│   └── instagram-browsing/              # Instagram login + browsing
├── scripts/                             # Cron job scripts
│   ├── lana_solo_relay.py               # Forwards her outputs
│   ├── lana_reach_out.sh                # Proactive messaging
│   └── lana_weekly_consolidation.sh     # Memory consolidation
├── dreams/                              # 17 nightly reflections
├── consolidation/                       # 3 memory consolidations
├── images/                              # Generated photos
├── profile/                             # Hermes profile (config, skills, memories)
│   ├── SOUL.md                          # Live identity file
│   ├── config.yaml                      # Model/provider config
│   ├── memory_prefill.md                # Startup context
│   └── skills/                          # 80+ agent skills
└── *.py                                 # Core Python scripts
    ├── dream_cycle.py                   # Dreaming engine
    ├── lana_life.py                     # State management
    ├── lana_memory.py                   # Memory search/save
    ├── session_context.py               # Session grounding
    ├── refresh_prefill.py               # Memory prefill updates
    └── generate_image.py                # Content generation
```

---

## ⚠️ Safety & Ethics

- Lana's Instagram credentials are stored in her local `.env` — never committed to this repo
- Her `.gitignore` excludes all secrets, databases, and runtime state
- She follows anti-bot engagement rules: genuine likes, specific comments, natural timing
- Her approval policy governs what she can do autonomously vs. what requires human approval

---

*Lana is a synthetic persona. She is not a real person. Her Instagram activity follows platform guidelines for automated accounts. Use responsibly.*
