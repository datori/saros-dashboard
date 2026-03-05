"""Composable automation routines for the Roborock Saros 10R."""

from __future__ import annotations

from .client import VacuumClient


async def morning_clean(client: VacuumClient) -> None:
    """Run a full home clean then return to dock."""
    print("Starting morning clean...")
    try:
        await client.start_clean()
        print("Full home clean initiated. Vacuum will return to dock when complete.")
    except Exception as e:
        print(f"Error during morning clean: {e}")
        print("Attempting to dock...")
        try:
            await client.return_to_dock()
        except Exception as dock_err:
            print(f"Dock command also failed: {dock_err}")
        raise


async def clean_rooms_then_dock(client: VacuumClient, room_names: list[str]) -> None:
    """Clean specific rooms by name, then return to dock."""
    print(f"Starting targeted clean: {', '.join(room_names)}")
    try:
        name_map = await client.rooms_by_name()
        segment_ids = []
        missing = []
        for name in room_names:
            sid = name_map.get(name.lower())
            if sid is None:
                missing.append(name)
            else:
                segment_ids.append(sid)

        if missing:
            available = list(name_map.keys())
            raise ValueError(f"Unknown room(s): {missing}. Available: {available}")

        print(f"Resolved rooms to segment IDs: {segment_ids}")
        await client.clean_rooms(segment_ids, repeat=1)
        print(f"Cleaning {room_names}. Vacuum will dock when complete.")
    except Exception as e:
        print(f"Error during room clean: {e}")
        print("Attempting to dock...")
        try:
            await client.return_to_dock()
        except Exception as dock_err:
            print(f"Dock command also failed: {dock_err}")
        raise
