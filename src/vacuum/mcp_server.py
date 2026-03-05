"""MCP server exposing Roborock Saros 10R control tools."""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import VacuumClient
from . import scheduler

_client: VacuumClient | None = None


@asynccontextmanager
async def _lifespan(mcp: FastMCP):
    global _client
    scheduler.init_db()
    _client = VacuumClient()
    await _client.authenticate()
    rooms = await _client.get_rooms()
    await scheduler.sync_rooms(rooms)
    try:
        yield {}
    finally:
        if _client:
            await _client.close()
            _client = None


mcp = FastMCP("vacuum", lifespan=_lifespan)


def _client_or_raise() -> VacuumClient:
    if _client is None:
        raise RuntimeError("Client not initialized")
    return _client


@mcp.tool()
async def vacuum_status() -> dict:
    """Get current vacuum state, battery level, and dock status."""
    client = _client_or_raise()
    s = await client.get_status()
    return s.as_dict()


@mcp.tool()
async def start_cleaning() -> dict:
    """Start a full home clean."""
    client = _client_or_raise()
    await client.start_clean()
    return {"result": "Cleaning started."}


@mcp.tool()
async def stop_cleaning() -> dict:
    """Stop the current cleaning session."""
    client = _client_or_raise()
    await client.stop()
    return {"result": "Stopped."}


@mcp.tool()
async def pause_cleaning() -> dict:
    """Pause cleaning in place without returning to dock."""
    client = _client_or_raise()
    await client.pause()
    return {"result": "Paused."}


@mcp.tool()
async def return_to_dock() -> dict:
    """Stop cleaning and return the vacuum to its charging dock."""
    client = _client_or_raise()
    await client.return_to_dock()
    return {"result": "Returning to dock."}


@mcp.tool()
async def locate_vacuum() -> dict:
    """Play a sound on the vacuum to help locate it."""
    client = _client_or_raise()
    await client.locate()
    return {"result": "Locator sound played."}


@mcp.tool()
async def get_map() -> dict:
    """Get room names and segment IDs from the vacuum's map."""
    client = _client_or_raise()
    rooms = await client.get_rooms()
    return {"rooms": [{"id": r.id, "name": r.name} for r in rooms]}


@mcp.tool()
async def room_clean(rooms: list[str], repeat: int = 1) -> dict:
    """Clean specific rooms by name.

    Args:
        rooms: List of room names to clean (e.g. ["Kitchen", "Office"]).
        repeat: Number of times to clean each room (default: 1).
    """
    client = _client_or_raise()
    name_map = await client.rooms_by_name()
    segment_ids = []
    missing = []
    for rname in rooms:
        sid = name_map.get(rname.lower())
        if sid is None:
            missing.append(rname)
        else:
            segment_ids.append(sid)
    if missing:
        available = list(name_map.keys())
        raise ValueError(f"Unknown room(s): {missing}. Available: {available}")
    await client.clean_rooms(segment_ids, repeat=repeat)
    return {"result": f"Cleaning {rooms} (repeat={repeat})."}


@mcp.tool()
async def zone_clean(zones: list[list[int]], repeat: int = 1) -> dict:
    """Clean rectangular zones defined by coordinates.

    Args:
        zones: List of rectangles, each as [x1, y1, x2, y2].
        repeat: Times to clean each zone (default: 1).
    """
    client = _client_or_raise()
    zone_tuples = [tuple(z) for z in zones]
    await client.clean_zones(zone_tuples, repeat=repeat)
    return {"result": f"Cleaning {len(zones)} zone(s)."}


@mcp.tool()
async def run_routine(name: str) -> dict:
    """Trigger a named routine configured in the Roborock app.

    Args:
        name: Name of the routine to run.
    """
    client = _client_or_raise()
    await client.run_routine(name)
    return {"result": f"Routine '{name}' started."}


@mcp.tool()
async def get_cleaning_schedule() -> dict:
    """Get the full cleaning schedule status for all rooms, including last cleaned times, overdue ratios, and configured intervals."""
    rows = await scheduler.get_schedule()
    return {"schedule": [r.as_dict() for r in rows]}


@mcp.tool()
async def get_overdue_rooms(mode: str = "vacuum") -> dict:
    """List rooms that are past their cleaning interval.

    Args:
        mode: 'vacuum' or 'mop' (default: 'vacuum').
    """
    rows = await scheduler.get_overdue_rooms(mode)
    if not rows:
        return {"overdue": [], "message": f"No {mode} rooms are currently overdue."}
    return {"overdue": [r.as_dict() for r in rows]}


@mcp.tool()
async def set_room_interval(room: str, mode: str, days: float | None) -> dict:
    """Set or clear a room's cleaning interval.

    Args:
        room: Room name (e.g. 'Kitchen').
        mode: 'vacuum' or 'mop'.
        days: Interval in days (e.g. 3.0), or null to clear.
    """
    client = _client_or_raise()
    name_map = await client.rooms_by_name()
    segment_id = name_map.get(room.lower())
    if segment_id is None:
        available = sorted(name_map.keys())
        raise ValueError(f"Unknown room '{room}'. Available: {available}")
    await scheduler.set_room_interval(segment_id, mode, days)
    action = f"set to {days} days" if days is not None else "cleared"
    return {"result": f"{room} {mode} interval {action}."}


@mcp.tool()
async def plan_clean(max_minutes: float | None = None, mode: str = "vacuum") -> dict:
    """Recommend rooms to clean given an optional time budget.

    Args:
        max_minutes: Time budget in minutes. If omitted, returns all overdue rooms.
        mode: 'vacuum' or 'mop' (default: 'vacuum').
    """
    result = await scheduler.plan_clean(max_minutes, mode)
    return result.as_dict()


@mcp.tool()
async def set_room_notes(room: str, notes: str | None) -> dict:
    """Attach or clear free-text notes for a room's schedule entry.

    Args:
        room: Room name (e.g. 'Bedroom').
        notes: Notes text, or null to clear.
    """
    client = _client_or_raise()
    name_map = await client.rooms_by_name()
    segment_id = name_map.get(room.lower())
    if segment_id is None:
        available = sorted(name_map.keys())
        raise ValueError(f"Unknown room '{room}'. Available: {available}")
    await scheduler.set_room_notes(segment_id, notes)
    return {"result": f"Notes for '{room}' updated."}


def main():
    mcp.run(transport="stdio")
