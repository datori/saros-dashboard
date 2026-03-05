## Context

The Roborock Saros 10R is a 2025 flagship vacuum with cloud-dependent control. The `python-roborock` library (v3.14+) provides an async Python interface to the Roborock cloud API covering device discovery, status polling, room/zone cleaning, and map retrieval. The Saros 10R's local API uses an unimplemented protocol — all control must go via cloud.

This is a greenfield Python project. No existing codebase to migrate.

## Goals / Non-Goals

**Goals:**
- Thin, authenticated client wrapper around `python-roborock` for the Saros 10R
- MCP server exposing vacuum tools consumable by Claude or other AI assistants
- CLI for direct terminal-based vacuum control and routine execution
- Composable routines module for multi-step automation sequences
- Simple credential management via env vars / `.env` file

**Non-Goals:**
- Local API support (blocked by unimplemented Saros 10R protocol)
- Web UI or dashboard
- Multi-user or multi-home support
- Home Assistant integration (separate concern)
- Scheduling daemon / cron replacement (routines are invoked, not scheduled)

## Decisions

### 1. python-roborock as sole API layer
**Decision**: Wrap `python-roborock` directly rather than calling Roborock cloud APIs raw.
**Rationale**: The library handles authentication token exchange, protocol versioning, device discovery, and async communication. Rebuilding this is unnecessary and fragile.
**Alternative considered**: Direct HTTP calls to Roborock cloud — rejected due to undocumented/changing API surface.

### 2. Async throughout, sync CLI shim at the edge
**Decision**: Core client and routines are fully async (`asyncio`). CLI uses `asyncio.run()` at command entry points.
**Rationale**: `python-roborock` is async-native. Forcing sync would require thread executors and complicate MCP server integration.
**Alternative considered**: `anyio` — unnecessary complexity for single-backend use.

### 3. MCP server built with official Python MCP SDK
**Decision**: Use the `mcp` Python package (Anthropic's official SDK) to build the server.
**Rationale**: Correct protocol compliance, type-safe tool definitions, maintained by Anthropic.
**Alternative considered**: Forking `jaxx2104/roborock-mcp-server` — that project uses Deno/TypeScript and has Saros 10R gaps; building fresh in Python keeps the stack unified.

### 4. CLI built with Typer
**Decision**: Use `typer` for CLI construction.
**Rationale**: Type-annotated, generates help text automatically, async-friendly, pairs well with Python 3.10+.
**Alternative considered**: `click` — more verbose; `argparse` — too low-level.

### 5. Config via env vars + optional `.env` file
**Decision**: Credentials (`ROBOROCK_USERNAME`, `ROBOROCK_PASSWORD`) loaded from environment, with `python-dotenv` for `.env` support.
**Rationale**: Simple, 12-factor compatible, no secrets in config files committed to repo.
**No alternative seriously considered** — standard pattern.

### 7. IOT base URL cached in session file
**Decision**: After first authentication, cache the resolved IOT base URL (e.g. `https://usiot.roborock.com`) as `_base_url` inside `.roborock_session.json`. Subsequent commands pass this directly to `RoborockApiClient(base_url=...)` and `UserParams(base_url=...)`.
**Rationale**: Without caching, every CLI command triggers a `POST /api/v1/getUrlByEmail` network call to discover the regional server. This adds ~0.5s latency and consumes a rate-limited slot (Roborock enforces 3 req/min, 10 req/hour for this endpoint). The URL is stable — it only changes if the account migrates regions, which is extremely rare.
**Alternative considered**: Storing separately in a `~/.vacuum_cache` file — rejected in favour of keeping a single session file for simplicity.
**Trade-off**: If the URL ever changes, deleting `.roborock_session.json` and re-running `vacuum login` will rediscover and re-cache it.

### 6. Project layout: flat `src/vacuum/` package
```
vacuum/
├── src/vacuum/
│   ├── __init__.py
│   ├── client.py        # python-roborock wrapper
│   ├── mcp_server.py    # MCP server definition
│   ├── cli.py           # Typer CLI
│   ├── routines.py      # Composable automation routines
│   └── config.py        # Credential + device config
├── .env.example
├── pyproject.toml
└── README.md
```

## Risks / Trade-offs

- **Roborock cloud API changes** → Mitigation: pin `python-roborock` version; monitor library releases
- **Saros 10R feature gaps in python-roborock** (e.g., mop intensity issue #579) → Mitigation: file upstream issues; work around with raw command dispatch where needed
- **Cloud dependency** → No mitigation available; local API requires community reverse-engineering effort not yet complete
- **Auth token expiry** → Mitigation: session token lasts weeks-to-months; `vacuum login` re-authenticates and refreshes `.roborock_session.json`
- **Cached base URL staleness** → Mitigation: rare in practice; deleting `.roborock_session.json` forces re-discovery on next `vacuum login`
- **Rate limiting on `_get_iot_login_info`** → Mitigation: base URL caching eliminates this call on every command after first run

## Open Questions

- Should routines be defined in code or in a config file for easier user editing?

## Discovered Facts (Post-Setup)

- **Rooms**: Bedroom (1), Closet (2), Bathroom (3), Kitchen (4), Living room (5), Study (6), Hall (7)
- **App routines**: Kitchen
- **Account region**: US — IOT base URL `https://usiot.roborock.com`
- **Auth method**: Email code login required (password login returns error 2012 for iCloud accounts)
