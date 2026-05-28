# Discord Bot Offline Fix — Adapter Patch

## Problem
Discord bot shows offline in server member list despite gateway logs showing "Connected as <bot>".

## Root Cause
The Discord adapter (`plugins/platforms/discord/adapter.py`) doesn't call `change_presence()` in its `on_ready()` event handler. Discord.py bots appear offline by default without an explicit presence set.

## Patch

**File:** `~/.hermes/hermes-agent/plugins/platforms/discord/adapter.py`

**Location:** Inside `connect()` method, in the `on_ready()` event handler (around line 750).

**Before:**
```python
@self._client.event
async def on_ready():
    logger.info("[%s] Connected as %s", adapter_self.name, adapter_self._client.user)

    # Resolve any usernames in the allowed list to numeric IDs
    await adapter_self._resolve_allowed_usernames()
    adapter_self._ready_event.set()
```

**After:**
```python
@self._client.event
async def on_ready():
    logger.info("[%s] Connected as %s", adapter_self.name, adapter_self._client.user)

    # Set bot presence to show as online
    await adapter_self._client.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(type=discord.ActivityType.listening, name="you")
    )

    # Resolve any usernames in the allowed list to numeric IDs
    await adapter_self._resolve_allowed_usernames()
    adapter_self._ready_event.set()
```

## After Patching
Restart the gateway: `hermes gateway restart`

## Activity Customization
Change the activity type and name as desired:
- `discord.ActivityType.listening` — "Listening to you"
- `discord.ActivityType.playing` — "Playing a game"
- `discord.ActivityType.watching` — "Watching something"
- `discord.ActivityType.competing` — "Competing in something"
- `activity=None` — no activity, just online status

## Notes
- LSP warnings about `change_presence` being "not a known attribute of None" are false positives — `self._client` is definitely connected when `on_ready` fires.
- This patch persists across gateway restarts since it's in the source code.
- If hermes-agent is updated, this patch may need to be re-applied.
