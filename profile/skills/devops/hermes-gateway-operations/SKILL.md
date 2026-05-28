---
name: hermes-gateway-operations
description: "Start, stop, verify, and troubleshoot Hermes Gateway — platform connections, presence issues, launchctl quirks, and common fixes."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [gateway, discord, troubleshooting, launchctl, platform, operations]
    related_skills: [hermes-agent, systematic-debugging]
---

# Hermes Gateway Operations

## Overview

The Hermes Gateway runs messaging platform adapters (Discord, Telegram, Slack, etc.) plus the cron scheduler and kanban dispatcher. This skill covers starting, verifying, and troubleshooting the gateway — especially platform-specific issues that aren't obvious from CLI output.

Use this skill when:
- Starting or restarting the gateway
- Gateway shows "started" but platform appears offline or unresponsive
- Verifying actual gateway state vs launchctl/systemd reports
- Discord bot shows offline despite gateway logs showing "Connected"
- Platform adapter not receiving or sending messages

## Starting / Restarting

```bash
hermes gateway start      # Start the service
hermes gateway restart    # Stop + start
hermes gateway status     # Check status
hermes gateway stop       # Stop
```

## Verifying Actual State (Critical)

**launchctl/systemd status can be misleading.** The `LastExitStatus` may show a stale exit code from a previous run, not the current state. Always verify with:

```bash
# Check if the process is actually running
ps aux | grep "gateway run" | grep -v grep

# Check the logs for recent activity
tail -30 ~/.hermes/profiles/<profile>/logs/gateway.log
```

A gateway that logs "Connected as <bot>" and "Press Ctrl+C to stop" is running, regardless of what launchctl reports.

## Platform-Specific Issues

### Discord Bot Shows Offline

**Root cause:** The Discord adapter doesn't call `change_presence()` in its `on_ready()` handler. Discord.py bots appear offline without an explicit presence set.

**Fix:** Patch `plugins/platforms/discord/adapter.py` in the `on_ready()` handler:

```python
@self._client.event
async def on_ready():
    logger.info("[%s] Connected as %s", adapter_self.name, adapter_self._client.user)

    # Set bot presence to show as online
    await adapter_self._client.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(type=discord.ActivityType.listening, name="you")
    )

    # ... rest of on_ready
```

**After patching:** Restart the gateway (`hermes gateway restart`).

**Location:** `~/.hermes/hermes-agent/plugins/platforms/discord/adapter.py` — the `on_ready` event handler inside the `connect()` method (around line 750).

### Discord: Gateway Logs Connected But Bot Not Responding

Check:
1. `DISCORD_ALLOWED_USERS` or `DISCORD_ALLOWED_GUILDS` may be filtering messages
2. Bot might be DM-only — check if it's in the right server/channel
3. Look for "inbound message" lines in gateway.log to confirm messages arrive

### Gateway Dies on macOS After SSH Logout

Enable linger:
```bash
sudo loginctl enable-linger $USER
```

### Gateway Keeps Restarting (Crash Loop)

Check error log:
```bash
tail -50 ~/.hermes/profiles/<profile>/logs/gateway.error.log
```

Common causes:
- Missing API keys (check `.env`)
- Model provider errors
- Invalid config values

## Gateway Logs Location

```
~/.hermes/profiles/<profile>/logs/gateway.log       # Info+ (normal operation)
~/.hermes/profiles/<profile>/logs/gateway.error.log  # Warnings+ (errors, issues)
```

## Pitfalls

- **launchctl "LastExitStatus" is stale** — it shows the exit code of the LAST run, not the current state. Always verify with `ps aux` and log inspection.
- **Gateway "start" returning success doesn't mean it's running** — launchctl may accept the start command but the process could fail immediately. Check logs.
- **Discord bot needs explicit presence** — unlike some other platforms, Discord bots don't show as online by default. The adapter must call `change_presence()`.
- **Opus codec warning is harmless** — "Opus codec not found — voice channel playback disabled" just means voice features are unavailable. The gateway still works for text.
- **memory_prefill.md warning is harmless** — "Failed to load prefill messages" with JSON parse error means the file is empty or malformed. Not critical.

## Multi-Profile Gateway Management

Multiple profiles can run gateways simultaneously (e.g., lana + default), each with its own Discord bot or other platforms.

### Switching Profiles and Starting Gateways

```bash
# Switch to a profile
hermes profile use <profile>

# Start gateway for current profile
hermes gateway start

# Or start a specific profile's gateway directly
hermes --profile <profile> gateway start
```

### Checking Which Gateways Are Running

```bash
# List all hermes processes
ps aux | grep "hermes" | grep -v grep

# Check launchctl status for all services
launchctl list | grep hermes

# Verify each gateway's Discord connection
tail -5 ~/.hermes/profiles/lana/logs/gateway.log | grep "Connected as"
tail -5 ~/.hermes/logs/gateway.log | grep "Connected as"
```

### Common Multi-Profile Pitfalls

- **Confusing which profile's gateway is running** — Each profile has its own launchd service (`ai.hermes.gateway-<profile>.plist`). Check the plist name or logs to confirm which bot is connected.
- **Gateway start may silently fail** — If another gateway is already using the same port (for API server adapters), the new one may fail. Check error logs.
- **Different Discord bots per profile** — Each profile's Discord bot has its own token and shows as a separate user in servers.

## Verification

After starting/restarting:
1. Check process exists: `ps aux | grep "gateway run" | grep -v grep`
2. Check logs show connection: `tail -10 ~/.hermes/profiles/<profile>/logs/gateway.log | grep -i "connected"`
3. Send a test message from the platform and verify response in logs
4. For Discord: verify bot shows online in the server member list
5. For multi-profile: verify each profile's bot shows online independently
