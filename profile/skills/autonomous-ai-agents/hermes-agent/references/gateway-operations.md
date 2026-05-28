# Gateway Operations & Troubleshooting

## Starting/Restarting the Gateway

```bash
hermes gateway start      # Start as background service
hermes gateway restart    # Stop + start (kills running agents — approval required)
hermes gateway stop       # Stop the service
hermes gateway status     # Show launchd service definition
```

## Verifying Gateway Is Actually Running

**Pitfall:** After `hermes gateway restart`, `launchctl list` can show stale exit status (e.g. the previous -15 termination code) and the old PID even though the gateway has restarted with a new PID. Do NOT trust `launchctl list` as the sole indicator.

**Correct verification sequence:**

1. Check the logs (ground truth):
   ```bash
   tail -30 ~/.hermes/profiles/<profile>/logs/gateway.log
   ```
   Look for: "Gateway running with N platform(s)", "✓ discord connected", "Press Ctrl+C to stop"

2. Confirm the process is alive:
   ```bash
   ps aux | grep "gateway run" | grep -v grep
   ```
   Should show the python process with `--profile <name> gateway run --replace`

3. Only then trust `launchctl list` — but cross-reference against steps 1-2.

## Log Locations

- Main log: `~/.hermes/profiles/<profile>/logs/gateway.log`
- Error log: `~/.hermes/profiles/<profile>/logs/gateway.error.log`
- Quick check: `grep -i "failed\|error" ~/.hermes/logs/gateway.log | tail -20`

## Common Issues

### Gateway shows "started" but launchctl shows old exit status
- This is the stale-launchd-status pitfall — use logs + ps aux to verify
- The restart actually worked; launchd metadata just hasn't refreshed

### Gateway keeps terminating immediately (exit status -15)
- Check logs for the specific shutdown reason
- SIGTERM under `under_systemd=yes parent_pid=1` = systemd/launchd sent the signal
- May indicate resource issues or conflicting instances

### Gateway connected but messages not received
- Verify platform adapter connected: look for "✓ discord connected" (or other platform) in logs
- Check channel directory: "Channel directory built: N target(s)"
- Confirm bot permissions on the platform (e.g. Discord Message Content Intent)

### Stale sessions after gateway restart
- Gateway logs "Previous gateway exited cleanly — skipping session suspension" when restart is clean
- If it says sessions were suspended, they'll resume automatically

## Platform-Specific Notes

### Discord
- Requires Message Content Intent enabled in Bot → Privileged Gateway Intents
- Voice playback requires opus codec (warning logged if missing, but doesn't block text)
- Slash commands auto-synced on startup

### Multiple Profiles
- Each profile runs its own gateway service: `ai.hermes.gateway-<profile>`
- Plist at: `~/Library/LaunchAgents/ai.hermes.gateway-<profile>.plist`
- Services are independent — starting one doesn't affect others
