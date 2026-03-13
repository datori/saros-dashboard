# saros-dashboard

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

CLI, MCP server, and web dashboard for the **Roborock Saros 10R** robot vacuum, built on top of [`python-roborock`](https://github.com/Python-roborock/python-roborock). Control cleaning, monitor status, manage schedules, and query history — all from the terminal, your browser, or an AI assistant.

> **Cloud API only.** The Saros 10R uses a newer local protocol not yet supported by `python-roborock`. All commands are relayed through Roborock's cloud MQTT broker (`usiot.roborock.com:8883`), even when the device is on the same LAN. See [Connectivity](#connectivity) for details.

---

## Features

- **CLI** (`vacuum`) — status, start/stop/pause/dock, room selection, routines, consumables, history
- **Web dashboard** (`vacuum-dashboard`) — full-featured browser UI with scheduling, clean history, consumable gauges, and per-room cleaning intervals
- **MCP server** (`vacuum-mcp`) — exposes vacuum tools to AI assistants via the [Model Context Protocol](https://modelcontextprotocol.io) (works with Claude Desktop)
- **Scheduling** — SQLite-backed per-room cleaning intervals with overdue detection and priority scoring
- **Clean history** — paginated history with duration, area, and completion status
- **Consumables** — percentage-remaining gauges for main brush, side brush, filter, and sensor

---

## Requirements

- Python 3.11+
- A Roborock account (the same login used in the Roborock app)
- A Roborock Saros 10R (other Roborock devices may work but are untested)
- Internet access (cloud API)

---

## Setup

**1. Install**

```bash
git clone https://github.com/yourusername/saros-dashboard
cd saros-dashboard
pip install -e .
```

**2. Configure credentials**

```bash
cp .env.example .env
# Edit .env and fill in your Roborock username and password
```

`.env` contents:
```
ROBOROCK_USERNAME=your@email.com
ROBOROCK_PASSWORD=yourpassword
ROBOROCK_DEVICE_NAME=           # optional — defaults to first device found
```

**3. Authenticate**

```bash
vacuum login        # use this if password login doesn't work (triggers email code flow)
```

After first login, the session token is cached at `.roborock_session.json`. Subsequent runs skip the login round-trip.

---

## Usage

### CLI

```bash
vacuum status                        # Current state, battery, dock status
vacuum clean                         # Start a full home clean
vacuum stop                          # Stop cleaning
vacuum pause                         # Pause in place
vacuum dock                          # Return to dock
vacuum locate                        # Play locator sound
vacuum map                           # Show rooms and segment IDs
vacuum rooms "Kitchen" "Living room" # Clean specific rooms
vacuum rooms "Kitchen" --repeat 2   # Clean a room twice
vacuum routine --list                # List available routines
vacuum routine "morning-clean"       # Run a named routine
vacuum history                       # Recent clean history
vacuum consumables                   # Brush / filter / sensor wear
```

### Web dashboard

```bash
vacuum-dashboard                     # Start on default port 8080
vacuum-dashboard --port 8181         # Use a different port
```

Then open `http://<your-lan-ip>:<port>` in your browser. The dashboard auto-refreshes every 30 seconds and works as an iOS "Add to Home Screen" PWA.

### MCP server (Claude Desktop)

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "vacuum": {
      "command": "vacuum-mcp",
      "env": {
        "ROBOROCK_USERNAME": "your@email.com",
        "ROBOROCK_PASSWORD": "yourpassword"
      }
    }
  }
}
```

Available MCP tools: `vacuum_status`, `start_cleaning`, `stop_cleaning`, `pause_cleaning`, `return_to_dock`, `locate_vacuum`, `get_map`, `room_clean`, `zone_clean`, `run_routine`, `get_cleaning_schedule`, `get_overdue_rooms`, `set_room_interval`, `plan_clean`, `set_room_notes`

---

## Connectivity

All commands travel:

```
Your client (CLI / browser / AI)
    ↓
FastAPI / Typer / MCP handler
    ↓
python-roborock  (persistent MQTT connection)
    ↓
Roborock Cloud MQTT  (usiot.roborock.com:8883, TCP/TLS)
    ↓
Saros 10R device
```

There is **no local path** — the device is on the same LAN but uses a newer local protocol version not yet supported by `python-roborock` (tracked in [home-assistant/core#152136](https://github.com/home-assistant/core/issues/152136)). This means:

- Commands require an internet connection
- Latency is cloud round-trip (~1–3s typical)
- Occasional timeouts occur during cloud maintenance windows
- The dashboard auto-reconnects after MQTT session drops

---

## Project structure

```
src/vacuum/
  cli.py          # `vacuum` CLI (Typer)
  mcp_server.py   # `vacuum-mcp` MCP server
  dashboard.py    # `vacuum-dashboard` FastAPI web app
  client.py       # VacuumClient — all device logic
  scheduler.py    # SQLite-backed cleaning scheduler
  config.py       # Credentials and session management
```

See [`CLAUDE.md`](CLAUDE.md) for a detailed developer reference (API docs, gotchas, architecture notes).

---

## Contributing

1. Fork the repo and create a feature branch
2. Install in editable mode: `pip install -e .`
3. Make your changes — see `CLAUDE.md` for the full API reference
4. Open a pull request

Bug reports and feature requests are welcome via GitHub Issues.

---

## License

MIT — see [LICENSE](LICENSE).
