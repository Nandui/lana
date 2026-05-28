# Lana Mem0 Codex Switch Report

Date: 2026-05-25

## User correction

Fernando clarified that Venice.ai is temporary for NSFW content and must not be Lana's Mem0/memory brain.

Required direction:

```text
Lana Mem0 extraction/summarization brain: Codex/GPT-5.4
Venice.ai: temporary NSFW content provider only
```

## Changes made

### `lana_memory.py`

Changed Lana's memory write path so `add()` now:

1. asks Hermes Codex/GPT-5.4 to extract durable memory facts;
2. writes extracted facts into Mem0/ChromaDB with `infer=False`;
3. avoids Mem0's internal LLM extraction path for normal writes;
4. falls back to `memory/fallback_memories.jsonl` if Codex/GPT-5.4 is temporarily unavailable.

Important constants:

```python
CODEX_PROVIDER = "openai-codex"
CODEX_MODEL = "gpt-5.4"
```

The active script no longer contains Venice API URLs or `grok-4-20` for Mem0.

### `lana_realness_common.py`

Changed dream/consolidation synthesis helper to call:

```bash
hermes chat --provider openai-codex -m gpt-5.4 -t safe -Q
```

instead of using Lana's profile model or Venice.

### Profile memory / prefill docs

Updated:

- `/Users/fernandoserina/.hermes/profiles/lana/memories/MEMORY.md`
- `/Users/fernandoserina/.hermes/profiles/lana/memory_prefill.md`
- `/Users/fernandoserina/lana_memory/refresh_prefill.py`

They now say Lana's memory extraction uses Codex/GPT-5.4 and that Venice is not Lana's Mem0 brain.

## Verification

### Static/code verification

Passed:

```bash
python -m py_compile lana_memory.py lana_realness_common.py dream_cycle.py consolidate_memory.py refresh_prefill.py
```

Active files checked:

- `lana_memory.py`
- `lana_realness_common.py`
- `refresh_prefill.py`
- Lana profile `memory_prefill.md`
- Lana profile `memories/MEMORY.md`

Results:

- no `api.venice.ai` in active Mem0 files
- no `grok-4-20` in active Mem0 files
- Codex/GPT-5.4 appears in active memory files
- `openai-codex` appears in active code paths

### Runtime profile verification

Lana's profile can see the corrected automatic context without tools:

```text
LANA_PHASE1_AUTOMATIC_CONTEXT states that the Phase 1 realness system at /Users/fernandoserina/lana_memory/ includes Mem0+ChromaDB and Codex/GPT-5.4 memory extraction with fallback JSONL memory and verified scripts, while Venice is temporary for NSFW content and is not Lana's Mem0 memory brain.
```

### Mem0 add/search behavior

A temporary test memory was added. Because Codex/GPT-5.4 is currently quota-limited, the write used fallback JSONL as designed.

Observed error:

```text
HTTP 429: The usage limit has been reached
```

Expected behavior occurred:

- no Venice call was used
- fallback JSONL saved the memory
- search found the fallback memory
- temporary test marker was removed afterward

## Current caveat

Codex/GPT-5.4 is currently returning a usage-limit 429 from Hermes CLI. Until that quota clears, memory writes that need extraction will be preserved in fallback JSONL with reason:

```text
codex_gpt54_extraction_unavailable
```

Once Codex quota is available again, `lana_memory.py add` should extract with Codex/GPT-5.4 and store extracted facts into Mem0/ChromaDB directly.

## Final status

Venice has been removed from Lana's Mem0 memory brain.

The intended memory brain is now Codex/GPT-5.4, with fallback JSONL protection during Codex quota outages.
