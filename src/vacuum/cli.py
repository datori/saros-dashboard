"""Command-line interface for Roborock Saros 10R control."""

from __future__ import annotations

import asyncio
import sys
from typing import Annotated

import typer

from .client import (
    AuthError,
    CleanRoute,
    ConfigError,
    FanSpeed,
    MopMode,
    RoutineNotFoundError,
    VacuumClient,
    WaterFlow,
)
from .config import get_username, save_session

# ---------------------------------------------------------------------------
# Settings option helpers
# ---------------------------------------------------------------------------

_FAN_SPEED_CHOICES  = [e.name for e in FanSpeed]
_MOP_MODE_CHOICES   = [e.name for e in MopMode]
_WATER_FLOW_CHOICES = [e.name for e in WaterFlow]
_ROUTE_CHOICES      = [e.name for e in CleanRoute]


def _parse_fan_speed(value: str | None) -> FanSpeed | None:
    if value is None:
        return None
    v = value.upper()
    if v not in {e.name for e in FanSpeed}:
        _err(f"Invalid --fan-speed '{value}'. Valid values: {', '.join(_FAN_SPEED_CHOICES)}")
    return FanSpeed[v]


def _parse_mop_mode(value: str | None) -> MopMode | None:
    if value is None:
        return None
    v = value.upper()
    if v not in {e.name for e in MopMode}:
        _err(f"Invalid --mop-mode '{value}'. Valid values: {', '.join(_MOP_MODE_CHOICES)}")
    return MopMode[v]


def _parse_water_flow(value: str | None) -> WaterFlow | None:
    if value is None:
        return None
    v = value.upper()
    if v not in {e.name for e in WaterFlow}:
        _err(f"Invalid --water-flow '{value}'. Valid values: {', '.join(_WATER_FLOW_CHOICES)}")
    return WaterFlow[v]


def _parse_route(value: str | None) -> CleanRoute | None:
    if value is None:
        return None
    v = value.upper()
    if v not in {e.name for e in CleanRoute}:
        _err(f"Invalid --route '{value}'. Valid values: {', '.join(_ROUTE_CHOICES)}")
    return CleanRoute[v]

app = typer.Typer(
    name="vacuum",
    help="Control your Roborock Saros 10R from the command line.",
    no_args_is_help=True,
)


def _err(msg: str) -> None:
    typer.echo(msg, err=True)
    raise typer.Exit(1)


def _run(coro):
    """Run an async coroutine from a sync CLI command."""
    return asyncio.run(coro)


async def _with_client(coro_fn):
    """Authenticate and run coro_fn(client), handling common errors."""
    try:
        async with VacuumClient() as client:
            return await coro_fn(client)
    except (ConfigError, AuthError) as e:
        _err(str(e))
    except RoutineNotFoundError as e:
        _err(str(e))
    except Exception as e:
        _err(f"Error: {e}")


@app.command()
def status():
    """Show current vacuum state, battery level, and dock status."""

    async def _run_status(client: VacuumClient):
        s = await client.get_status()
        typer.echo(f"State:      {s.state or 'unknown'}")
        typer.echo(f"Battery:    {s.battery}%")
        typer.echo(f"In dock:    {s.in_dock}")
        if s.error_code:
            typer.echo(f"Error code: {s.error_code}")

    _run(_with_client(_run_status))


@app.command()
def clean(
    fan_speed:  Annotated[str | None, typer.Option("--fan-speed",  help=f"Fan speed: {', '.join(_FAN_SPEED_CHOICES)}")] = None,
    mop_mode:   Annotated[str | None, typer.Option("--mop-mode",   help=f"Mop mode: {', '.join(_MOP_MODE_CHOICES)}")] = None,
    water_flow: Annotated[str | None, typer.Option("--water-flow", help=f"Water flow: {', '.join(_WATER_FLOW_CHOICES)}")] = None,
    route:      Annotated[str | None, typer.Option("--route",      help=f"Route: {', '.join(_ROUTE_CHOICES)}")] = None,
):
    """Start a full home clean."""

    async def _go(client: VacuumClient):
        await client.start_clean(
            fan_speed=_parse_fan_speed(fan_speed),
            mop_mode=_parse_mop_mode(mop_mode),
            water_flow=_parse_water_flow(water_flow),
            route=_parse_route(route),
        )
        typer.echo("Cleaning started.")

    _run(_with_client(_go))


@app.command()
def stop():
    """Stop cleaning."""

    async def _go(client: VacuumClient):
        await client.stop()
        typer.echo("Stopped.")

    _run(_with_client(_go))


@app.command()
def pause():
    """Pause cleaning in place."""

    async def _go(client: VacuumClient):
        await client.pause()
        typer.echo("Paused.")

    _run(_with_client(_go))


@app.command()
def dock():
    """Return to charging dock."""

    async def _go(client: VacuumClient):
        await client.return_to_dock()
        typer.echo("Returning to dock.")

    _run(_with_client(_go))


@app.command()
def locate():
    """Play locator sound to find the vacuum."""

    async def _go(client: VacuumClient):
        await client.locate()
        typer.echo("Locator sound played.")

    _run(_with_client(_go))


@app.command()
def map():
    """Show room names and segment IDs."""

    async def _go(client: VacuumClient):
        rooms = await client.get_rooms()
        if not rooms:
            typer.echo("No rooms found. Make sure your map is saved in the Roborock app.")
            return
        typer.echo(f"{'ID':<6} {'Name'}")
        typer.echo("-" * 30)
        for r in rooms:
            typer.echo(f"{r.id:<6} {r.name}")

    _run(_with_client(_go))


@app.command()
def rooms(
    names:      Annotated[list[str], typer.Argument(help="Room name(s) to clean")],
    repeat:     Annotated[int,       typer.Option("--repeat", "-r",     help="Times to clean each room")] = 1,
    fan_speed:  Annotated[str | None, typer.Option("--fan-speed",  help=f"Fan speed: {', '.join(_FAN_SPEED_CHOICES)}")] = None,
    mop_mode:   Annotated[str | None, typer.Option("--mop-mode",   help=f"Mop mode: {', '.join(_MOP_MODE_CHOICES)}")] = None,
    water_flow: Annotated[str | None, typer.Option("--water-flow", help=f"Water flow: {', '.join(_WATER_FLOW_CHOICES)}")] = None,
    route:      Annotated[str | None, typer.Option("--route",      help=f"Route: {', '.join(_ROUTE_CHOICES)}")] = None,
):
    """Clean one or more rooms by name."""

    async def _go(client: VacuumClient):
        name_map = await client.rooms_by_name()
        segment_ids = []
        missing = []
        for name in names:
            sid = name_map.get(name.lower())
            if sid is None:
                missing.append(name)
            else:
                segment_ids.append(sid)
        if missing:
            available = list(name_map.keys())
            _err(f"Unknown room(s): {missing}. Available: {available}")
        await client.clean_rooms(
            segment_ids, repeat=repeat,
            fan_speed=_parse_fan_speed(fan_speed),
            mop_mode=_parse_mop_mode(mop_mode),
            water_flow=_parse_water_flow(water_flow),
            route=_parse_route(route),
        )
        typer.echo(f"Cleaning: {', '.join(names)} (repeat={repeat})")

    _run(_with_client(_go))


@app.command()
def routine(
    name: Annotated[str | None, typer.Argument(help="Routine name to run")] = None,
    list_: Annotated[bool, typer.Option("--list", "-l", help="List available routines")] = False,
):
    """Run a named routine or list available routines."""

    async def _go(client: VacuumClient):
        if list_ or name is None:
            routines = await client.get_routines()
            if not routines:
                typer.echo("No routines found. Create routines in the Roborock app.")
                return
            typer.echo("Available routines:")
            for r in routines:
                typer.echo(f"  {r.name}")
            return
        await client.run_routine(name)
        typer.echo(f"Routine '{name}' started.")

    _run(_with_client(_go))


@app.command()
def settings(
    fan_speed:  Annotated[str | None, typer.Option("--fan-speed",  help=f"Set fan speed: {', '.join(_FAN_SPEED_CHOICES)}")] = None,
    mop_mode:   Annotated[str | None, typer.Option("--mop-mode",   help=f"Set mop mode: {', '.join(_MOP_MODE_CHOICES)}")] = None,
    water_flow: Annotated[str | None, typer.Option("--water-flow", help=f"Set water flow: {', '.join(_WATER_FLOW_CHOICES)}")] = None,
):
    """View or update device cleaning settings. With no flags, prints current settings."""

    async def _go(client: VacuumClient):
        fs = _parse_fan_speed(fan_speed)
        mm = _parse_mop_mode(mop_mode)
        wf = _parse_water_flow(water_flow)

        if fs is None and mm is None and wf is None:
            s = await client.get_current_settings()
            typer.echo(f"Fan speed:  {s.fan_speed.name if s.fan_speed else '(unknown)'}")
            typer.echo(f"Mop mode:   {s.mop_mode.name if s.mop_mode else '(unknown)'}")
            typer.echo(f"Water flow: {s.water_flow.name if s.water_flow else '(unknown)'}")
            return

        if fs is not None:
            await client.set_fan_speed(fs)
            typer.echo(f"Fan speed set to {fs.name}.")
        if mm is not None:
            await client.set_mop_mode(mm)
            typer.echo(f"Mop mode set to {mm.name}.")
        if wf is not None:
            await client.set_water_flow(wf)
            typer.echo(f"Water flow set to {wf.name}.")

    _run(_with_client(_go))


@app.command()
def login():
    """Authenticate via email code (use when password login fails)."""
    import asyncio
    from roborock.web_api import RoborockApiClient

    async def _go():
        try:
            username = get_username()
        except ConfigError as e:
            _err(str(e))
            return
        client = RoborockApiClient(username)
        typer.echo(f"Sending login code to {username}...")
        await client.request_code_v4()
        code = typer.prompt("Enter the code from your email")
        user_data = await client.code_login_v4(code.strip())
        # Resolve and cache the IOT base URL so future commands skip the
        # _get_iot_login_info() network round-trip.
        base_url = await client.base_url
        save_session(user_data.as_dict(), base_url=base_url)
        typer.echo("Login successful. Session saved.")

    asyncio.run(_go())
