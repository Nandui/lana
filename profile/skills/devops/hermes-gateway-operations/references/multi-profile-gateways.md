# Multi-Profile Gateway Setup

## Current Profiles

| Profile | Path | Discord Bot | Gateway Service |
|---------|------|-------------|-----------------|
| lana | `~/.hermes/profiles/lana/` | Lana Hayes#6922 | `ai.hermes.gateway-lana` |
| default | `~/.hermes/` | Ella#1856 | `ai.hermes.gateway` |

## LaunchAgent Plists

```
~/Library/LaunchAgents/ai.hermes.gateway-lana.plist
~/Library/LaunchAgents/ai.hermes.gateway.plist
```

## Starting Both Gateways

```bash
# Start lana gateway
hermes --profile lana gateway start

# Start default gateway
hermes profile use default
hermes gateway start

# Or use launchctl directly
launchctl start ai.hermes.gateway
launchctl start ai.hermes.gateway-lana
```

## Verifying Both Are Running

```bash
# Check both processes
ps aux | grep "gateway run" | grep -v grep

# Check launchctl status
launchctl list | grep hermes

# Check lana Discord connection
tail -5 ~/.hermes/profiles/lana/logs/gateway.log | grep "Connected as"
# Expected: Connected as Lana Hayes#6922

# Check default Discord connection
tail -5 ~/.hermes/logs/gateway.log | grep "Connected as"
# Expected: Connected as Ella#1856
```

## Notes

- Both gateways can run simultaneously without conflicts
- Each has its own session storage, logs, and config
- The `hermes profile use` command only affects the CLI session, not the running gateway
- To restart a specific gateway, use `hermes --profile <name> gateway restart`
