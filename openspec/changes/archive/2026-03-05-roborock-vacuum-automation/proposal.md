## Why

Controlling a Roborock Saros 10R programmatically requires either the official app or fragile third-party integrations. Building custom CLI and MCP tools on top of `python-roborock` gives us direct, scriptable control over cleaning routines, room selection, schedules, and status — tailored to our specific use patterns without depending on Home Assistant or third-party MCP servers.

## What Changes

- New Python project scaffolded (`saros-dashboard`)
- Custom CLI (`vacuum`) for running commands, routines, and schedules from the terminal
- Custom MCP server exposing vacuum control as tools for AI assistant use
- Configuration layer for credentials and device selection
- Automation routines module for composing multi-step cleaning sequences

## Capabilities

### New Capabilities

- `vacuum-client`: Authenticated python-roborock client wrapper; handles cloud API login, device discovery, and command dispatch for the Saros 10R
- `mcp-server`: MCP server exposing vacuum tools (status, start, stop, pause, dock, locate, room-clean, zone-clean, get-map, run-routine)
- `cli`: Command-line interface for all vacuum operations and routine execution
- `routines`: Composable automation routines (e.g., clean kitchen then dock, scheduled full-clean, targeted spot clean)
- `config`: Credential and device configuration management (env vars + optional config file)

### Modified Capabilities

_(none — greenfield project)_

## Impact

- **Dependencies**: `python-roborock`, `mcp` (Python SDK), `click` or `typer` for CLI, `python-dotenv` for config
- **External APIs**: Roborock cloud API (cloud-only; Saros 10R local API uses unimplemented protocol)
- **Auth**: Roborock username + password via env vars or config file
- **Network**: Requires internet access to Roborock cloud; local network access not required
