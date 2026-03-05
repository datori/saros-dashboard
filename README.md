# vacuum

CLI and MCP server for controlling a Roborock Saros 10R via the `python-roborock` cloud API.

## Setup

```bash
pip install -e .
cp .env.example .env
# Edit .env with your Roborock credentials
```

## CLI Usage

```bash
vacuum status                        # Show current state, battery, dock status
vacuum clean                         # Start a full home clean
vacuum stop                          # Stop cleaning
vacuum pause                         # Pause in place
vacuum dock                          # Return to dock
vacuum locate                        # Play locator sound
vacuum map                           # Show rooms and segment IDs
vacuum rooms "Kitchen" "Office"      # Clean specific rooms
vacuum rooms "Kitchen" --repeat 2    # Clean a room twice
vacuum routine --list                # List available routines
vacuum routine "morning-clean"       # Run a named routine
```

## MCP Server

```bash
vacuum-mcp
```

Configure in your MCP client (e.g. Claude Desktop `claude_desktop_config.json`):

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

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `vacuum_status` | Get current state, battery, dock status |
| `start_cleaning` | Start a full home clean |
| `stop_cleaning` | Stop cleaning |
| `pause_cleaning` | Pause in place |
| `return_to_dock` | Return to charging dock |
| `locate_vacuum` | Play locator sound |
| `get_map` | Get room names and segment IDs |
| `room_clean` | Clean specific rooms by name |
| `zone_clean` | Clean rectangular zones by coordinates |
| `run_routine` | Trigger a named routine from the Roborock app |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ROBOROCK_USERNAME` | Yes | Roborock account email |
| `ROBOROCK_PASSWORD` | Yes | Roborock account password |
| `ROBOROCK_DEVICE_NAME` | No | Device name to target (defaults to first device) |

## Notes

- The Saros 10R uses a new local protocol not yet supported — all commands go via cloud API
- Routines are defined in the Roborock app; use `vacuum routine --list` to enumerate them
- Run `vacuum map` once after setup to discover your room segment IDs
