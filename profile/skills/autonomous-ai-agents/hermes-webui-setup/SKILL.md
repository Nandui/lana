---
name: hermes-webui-setup
description: Install, configure, and manage Hermes WebUI — the browser-based interface for Hermes Agent. Covers initial setup, daemon lifecycle, remote access, auth, and troubleshooting.
category: autonomous-ai-agents
---

# Hermes WebUI Setup & Management

Hermes WebUI is a lightweight, dark-themed web app that gives you browser/phone access to Hermes Agent with full CLI parity. No build step, no framework — just Python and vanilla JS.

**Repo:** https://github.com/nesquena/hermes-webui

## Triggers

- User wants to install, set up, or get Hermes WebUI running
- User wants local or remote browser access to Hermes Agent
- User asks about WebUI daemon management (start/stop/restart/logs)
- User asks about WebUI auth, password, or remote security

## Initial Installation

### 1. Clone at the desired version tag

```bash
git clone https://github.com/nesquena/hermes-webui.git hermes-webui
cd hermes-webui
git checkout v<VERSION>   # e.g., v0.51.157
```

Always install from a specific release tag, not `master`, so the version is pinned. Find the latest tag at https://github.com/nesquena/hermes-webui/releases.

### 2. Run bootstrap (foreground test)

```bash
python3 bootstrap.py
```

This starts the WebUI **in the foreground on 127.0.0.1:8787**. Use this only to verify the install works — kill it (Ctrl+C or `pkill -f bootstrap.py`) before proceeding to daemon mode.

### 3. Create `.env` for remote access + auth

Create `.env` in the repo root with at minimum:

```bash
HERMES_WEBUI_HOST=0.0.0.0
HERMES_WEBUI_PORT=8787
HERMES_WEBUI_PASSWORD=<secure-password>
```

**Important:** When creating `.env` via the agent, use `cat > file << 'EOF'` (terminal heredoc) rather than `write_file` — the `.env` read guard may mask secrets in `write_file`, leading to truncated passwords. Verify with `wc -l` after writing.

| Env var | Purpose |
|---|---|
| `HERMES_WEBUI_HOST` | Bind address. `0.0.0.0` for remote access, `127.0.0.1` for local only |
| `HERMES_WEBUI_PORT` | Port (default 8787) |
| `HERMES_WEBUI_PASSWORD` | Enables cookie-based auth on all endpoints. **Without this, the WebUI is open to anyone who can reach the port.** |

Additional optional env vars (see README for full list): `HERMES_WEBUI_STATE_DIR`, `HERMES_WEBUI_SKIP_ONBOARDING`, `HERMES_WEBUI_CHAT_BACKEND`, `HERMES_WEBUI_GATEWAY_BASE_URL`.

The `ctl.sh` script auto-loads `.env` from the repo root, preserving any already-set env vars (env takes precedence over `.env`).

### 4. Start as daemon with ctl.sh

```bash
cd ~/hermes-webui
./ctl.sh start
```

This runs bootstrap in background/no-browser mode. PID is written to `~/.hermes/webui.pid`, logs to `~/.hermes/webui.log`.

## Daemon Management

All commands from the repo root:

| Command | What it does |
|---|---|
| `./ctl.sh start` | Start background daemon |
| `./ctl.sh stop` | Stop the daemon |
| `./ctl.sh restart` | Stop then start |
| `./ctl.sh status` | PID, uptime, bound host:port, log path, health (`ok`/`error`), session count, active streams |
| `./ctl.sh logs` | Tail last 100 lines of `~/.hermes/webui.log` |
| `./ctl.sh logs --lines 200` | Tail N lines |

Override env vars inline: `HERMES_WEBUI_HOST=0.0.0.0 ./ctl.sh restart`

## Auth Model

- **No `HERMES_WEBUI_PASSWORD` set:** WebUI is open — anyone who can reach the port has full access.
- **`HERMES_WEBUI_PASSWORD` set:** All API endpoints require a session cookie. User logs in once in the browser; the cookie persists. Changing the env var requires restart.

The password can also be changed from within the WebUI (Settings → System → Password), but the env var takes precedence — if `HERMES_WEBUI_PASSWORD` is set, the in-UI password field is locked (disabled with a banner).

## Remote Access Patterns

The WebUI binds to whatever `HERMES_WEBUI_HOST` specifies. For access outside the local network:

1. **Tailscale** (easiest): Install Tailscale on the host, then access via `http://<tailscale-ip>:8787`
2. **SSH tunnel:** `ssh -L 8787:localhost:8787 user@host` from the client
3. **Reverse proxy:** nginx/Caddy in front with TLS termination
4. **Port forwarding:** Router-level — only if you understand the security implications

## Verifying Success

```bash
# Daemon health
./ctl.sh status
# Expected: "● hermes-webui — running" with "Health: ok"

# Browser access
curl -s http://localhost:8787/ | head -5
# Should return the WebUI HTML
```

## Pitfalls

- **Bootstrap foreground trap:** `python3 bootstrap.py` binds to `127.0.0.1` only and runs in the foreground. Don't mistake it for a working daemon. Use `ctl.sh start` for persistent daemon + remote binding.
- **`.env` not auto-created:** You must create `.env` manually. `ctl.sh` loads it but doesn't generate one.
- **Password write truncation:** When the agent uses `write_file` to create `.env`, the secret-bearing file read guard may cause truncated content. Prefer terminal heredoc (`cat > file << 'EOF'`) for `.env` creation, then verify line count with `wc -l`.
- **Env var precedence:** Already-exported env vars override `.env` values. If `HERMES_WEBUI_HOST=127.0.0.1` is already in the environment, setting `HERMES_WEBUI_HOST=0.0.0.0` in `.env` won't take effect — either `unset` the var first or pass it inline: `HERMES_WEBUI_HOST=0.0.0.0 ./ctl.sh restart`.
- **No Tailscale CLI on macOS:** `tailscale ip -4` may not be available even when Tailscale is running. Use `ifconfig utun0 | grep "inet "` to find the Tailscale IP instead.
