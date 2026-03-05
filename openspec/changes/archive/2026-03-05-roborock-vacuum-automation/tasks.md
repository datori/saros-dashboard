## 1. Project Scaffolding

- [x] 1.1 Create `pyproject.toml` with dependencies: `python-roborock`, `mcp`, `typer`, `python-dotenv`
- [x] 1.2 Create `src/vacuum/__init__.py` package init
- [x] 1.3 Create `.env.example` with `ROBOROCK_USERNAME`, `ROBOROCK_PASSWORD`, `ROBOROCK_DEVICE_NAME`
- [x] 1.4 Create `README.md` with setup instructions and usage examples

## 2. Config Module

- [x] 2.1 Implement `src/vacuum/config.py` — load credentials from env / `.env`, raise `ConfigError` if missing
- [x] 2.2 Add optional `ROBOROCK_DEVICE_NAME` support with default-to-first-device fallback

## 3. Vacuum Client

- [x] 3.1 Implement `src/vacuum/client.py` — async `VacuumClient` class wrapping `python-roborock`
- [x] 3.2 Add `authenticate()` — cloud login and device discovery using config credentials
- [x] 3.3 Add `get_status()` — return state, battery, dock status, error code
- [x] 3.4 Add `start_clean()`, `pause()`, `stop()`, `return_to_dock()` basic control methods
- [x] 3.5 Add `clean_rooms(segment_ids, repeat)` — room cleaning by segment ID
- [x] 3.6 Add `clean_zones(zones, repeat)` — zone cleaning by coordinate rectangles
- [x] 3.7 Add `get_rooms()` — return list of `{id, name}` dicts from map data
- [x] 3.8 Add `locate()` — trigger locator sound
- [x] 3.9 Add `get_routines()` and `run_routine(name)` — enumerate and trigger app-defined routines
- [x] 3.10 Add `AuthError`, `ConfigError`, `RoutineNotFoundError` custom exceptions

## 4. CLI

- [x] 4.1 Implement `src/vacuum/cli.py` — Typer app with `vacuum` entry point registered in `pyproject.toml`
- [x] 4.2 Add `vacuum status` subcommand — pretty-print vacuum state
- [x] 4.3 Add `vacuum clean` subcommand — start full clean
- [x] 4.4 Add `vacuum stop`, `vacuum pause`, `vacuum dock` subcommands
- [x] 4.5 Add `vacuum rooms <name>... [--repeat N]` subcommand — resolve names to IDs, clean
- [x] 4.6 Add `vacuum locate` subcommand
- [x] 4.7 Add `vacuum map` subcommand — print room name/ID table
- [x] 4.8 Add `vacuum routine <name>` with `--list` flag
- [x] 4.9 Ensure all commands print errors to stderr and exit with code 1 on failure

## 5. MCP Server

- [x] 5.1 Implement `src/vacuum/mcp_server.py` — MCP server using Python `mcp` SDK
- [x] 5.2 Add `vacuum_status` tool
- [x] 5.3 Add `start_cleaning`, `stop_cleaning`, `pause_cleaning`, `return_to_dock` tools
- [x] 5.4 Add `locate_vacuum` tool
- [x] 5.5 Add `room_clean` tool — accept room names, resolve to segment IDs
- [x] 5.6 Add `zone_clean` tool — accept coordinate list
- [x] 5.7 Add `get_map` tool — return room names and segment IDs
- [x] 5.8 Add `run_routine` tool — accept routine name, execute
- [x] 5.9 Wrap all tool handlers in try/except, return error content blocks on failure
- [x] 5.10 Add MCP server entry point in `pyproject.toml` (e.g., `vacuum-mcp`)

## 6. Routines Module

- [x] 6.1 Implement `src/vacuum/routines.py` — async routine functions using `VacuumClient`
- [x] 6.2 Add `morning_clean(client)` — full clean then dock
- [x] 6.3 Add `clean_rooms_then_dock(client, room_names)` — targeted rooms then dock
- [x] 6.4 Add step logging (print) throughout all routines
- [x] 6.5 Add error handling — catch, log, attempt dock, re-raise

## 7. Verification

- [x] 7.1 Install package locally (`pip install -e .`) and verify `vacuum --help` works
- [x] 7.2 Run `vacuum status` against live Roborock account and verify output
- [x] 7.3 Run `vacuum map` and record actual room segment IDs for the home
- [x] 7.4 Test `vacuum rooms` with at least one real room name
- [x] 7.5 Start MCP server and verify tools are listed by an MCP client
- [x] 7.6 Test `run_routine` with an app-defined routine name
