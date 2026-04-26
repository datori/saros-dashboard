"""Authenticated python-roborock wrapper for the Roborock Saros 10R."""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import IntEnum
from typing import Any

from roborock.data import (
    FILTER_REPLACE_TIME,
    MAIN_BRUSH_REPLACE_TIME,
    SENSOR_DIRTY_REPLACE_TIME,
    SIDE_BRUSH_REPLACE_TIME,
    HomeDataScene,
    UserData,
)
from roborock.data.v1.v1_code_mappings import RoborockStateCode
from roborock.devices.cache import NoCache
from roborock.devices.device import RoborockDevice
from roborock.devices.device_manager import DeviceManager, UserParams, create_device_manager
from roborock.devices.traits.v1.consumeable import ConsumableAttribute
from roborock.exceptions import RoborockException
from roborock.roborock_typing import RoborockCommand
from roborock.web_api import RoborockApiClient

from .config import ConfigError, get_device_name, get_username, load_session, save_session


# ---------------------------------------------------------------------------
# Cleaning parameter enums (Saros 10R device codes)
# ---------------------------------------------------------------------------

class FanSpeed(IntEnum):
    OFF      = 105  # Mop-only mode (no vacuuming)
    QUIET    = 101
    BALANCED = 102
    TURBO    = 103
    MAX      = 104
    MAX_PLUS = 108
    SMART    = 110


class MopMode(IntEnum):
    STANDARD  = 300
    DEEP      = 301
    DEEP_PLUS = 303
    FAST      = 304
    SMART     = 306


class WaterFlow(IntEnum):
    OFF          = 200
    LOW          = 201
    MEDIUM       = 202
    HIGH         = 203
    EXTREME      = 250
    SMART        = 209
    VAC_THEN_MOP = 235  # Sequential: vacuum first, then mop


class CleanRoute(IntEnum):
    """Vacuum route pattern. Maps to the same SET_MOP_MODE command as MopMode."""
    STANDARD  = 300
    FAST      = 304
    DEEP      = 301
    DEEP_PLUS = 303
    SMART     = 306


# Reverse-lookup: device integer code → our enum member (or None if unknown)
_FAN_SPEED_BY_CODE  = {e.value: e for e in FanSpeed}
_MOP_MODE_BY_CODE   = {e.value: e for e in MopMode}
_WATER_FLOW_BY_CODE = {e.value: e for e in WaterFlow}


def _extract_cached_base_url(session: dict) -> str | None:
    """Return the cached IOT base URL from the session dict, if present."""
    return session.get("_base_url") or None


class AuthError(Exception):
    pass


class RoutineNotFoundError(Exception):
    pass


@dataclass
class VacuumStatus:
    state: str | None
    battery: int | None
    in_dock: bool
    error_code: int | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "battery": self.battery,
            "in_dock": self.in_dock,
            "error_code": self.error_code,
        }


@dataclass
class Room:
    id: int
    name: str


@dataclass
class MapDebugRoom:
    segment_id: int
    name: str
    anchor_x: float
    anchor_y: float
    center_x: float
    center_y: float
    width: float | None = None
    height: float | None = None
    distance_from_charger: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "name": self.name,
            "anchor_x": round(self.anchor_x, 1),
            "anchor_y": round(self.anchor_y, 1),
            "center_x": round(self.center_x, 1),
            "center_y": round(self.center_y, 1),
            "width": round(self.width, 1) if self.width is not None else None,
            "height": round(self.height, 1) if self.height is not None else None,
            "distance_from_charger": (
                round(self.distance_from_charger, 1)
                if self.distance_from_charger is not None else None
            ),
        }


@dataclass
class Consumables:
    main_brush_pct: int | None
    side_brush_pct: int | None
    filter_pct: int | None
    sensor_pct: int | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "main_brush_pct": self.main_brush_pct,
            "side_brush_pct": self.side_brush_pct,
            "filter_pct": self.filter_pct,
            "sensor_pct": self.sensor_pct,
        }


@dataclass
class CleanSettings:
    fan_speed: FanSpeed | None
    mop_mode: MopMode | None
    water_flow: WaterFlow | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "fan_speed": self.fan_speed.name if self.fan_speed is not None else None,
            "mop_mode": self.mop_mode.name if self.mop_mode is not None else None,
            "water_flow": self.water_flow.name if self.water_flow is not None else None,
        }


@dataclass
class CleanRecord:
    start_time: str | None
    duration_seconds: int | None
    area_m2: float | None
    complete: bool
    start_type: str | None = None
    clean_type: str | None = None
    finish_reason: str | None = None
    avoid_count: int | None = None
    wash_count: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "start_time": self.start_time,
            "duration_seconds": self.duration_seconds,
            "area_m2": self.area_m2,
            "complete": self.complete,
            "start_type": self.start_type,
            "clean_type": self.clean_type,
            "finish_reason": self.finish_reason,
            "avoid_count": self.avoid_count,
            "wash_count": self.wash_count,
        }


@dataclass
class MapDebugInfo:
    charger_x: float | None
    charger_y: float | None
    vacuum_x: float | None
    vacuum_y: float | None
    vacuum_room: int | None
    vacuum_room_name: str | None
    rooms: list[MapDebugRoom]

    def as_dict(self) -> dict[str, Any]:
        return {
            "charger_x": round(self.charger_x, 1) if self.charger_x is not None else None,
            "charger_y": round(self.charger_y, 1) if self.charger_y is not None else None,
            "vacuum_x": round(self.vacuum_x, 1) if self.vacuum_x is not None else None,
            "vacuum_y": round(self.vacuum_y, 1) if self.vacuum_y is not None else None,
            "vacuum_room": self.vacuum_room,
            "vacuum_room_name": self.vacuum_room_name,
            "rooms": [room.as_dict() for room in self.rooms],
        }


class VacuumClient:
    """Async client wrapping python-roborock for the Saros 10R.

    Authenticates using a saved session token (.roborock_session.json) if available,
    otherwise falls back to password login. Use `vacuum login` to obtain a session
    token via email code if password login is unavailable.

    Usage:
        async with VacuumClient() as client:
            status = await client.get_status()
    """

    def __init__(self) -> None:
        self._manager: DeviceManager | None = None
        self._device: RoborockDevice | None = None
        self._api_client: RoborockApiClient | None = None
        self._user_data: UserData | None = None

    async def __aenter__(self) -> "VacuumClient":
        await self.authenticate()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def authenticate(self) -> None:
        """Login to Roborock cloud and discover the target device.

        Prefers a saved session token; falls back to password login.
        """
        username = get_username()
        session = load_session()

        base_url: str | None = None

        if session:
            try:
                self._user_data = UserData.from_dict(session)
                base_url = _extract_cached_base_url(session)
                self._api_client = RoborockApiClient(username, base_url=base_url)
            except Exception as e:
                raise AuthError(f"Failed to load saved session: {e}") from e
        else:
            # Password login (may not work for all accounts)
            try:
                from .config import get_credentials
                _, password = get_credentials()
                self._api_client = RoborockApiClient(username)
                self._user_data = await self._api_client.pass_login(password)
            except RoborockException as e:
                raise AuthError(
                    f"Authentication failed: {e}\n"
                    "If your account uses email code login, run: vacuum login"
                ) from e

        user_params = UserParams(username=username, user_data=self._user_data, base_url=base_url)
        try:
            self._manager = await create_device_manager(user_params, cache=NoCache())
        except RoborockException as e:
            raise AuthError(f"Failed to connect to devices: {e}") from e

        # Cache the resolved IOT base URL if not already stored, so future
        # commands skip the _get_iot_login_info() network round-trip.
        if not base_url and self._api_client:
            try:
                resolved = await self._api_client.base_url
                save_session(self._user_data.as_dict(), base_url=resolved)
            except Exception:
                pass  # Non-fatal — caching is best-effort

        self._device = self._select_device(await self._manager.get_devices())

    def _select_device(self, devices: list[RoborockDevice]) -> RoborockDevice:
        if not devices:
            raise AuthError("No devices found on this Roborock account.")
        target = get_device_name()
        if target:
            for d in devices:
                if d.name == target:
                    return d
            raise AuthError(
                f"Device '{target}' not found. Available: {[d.name for d in devices]}"
            )
        return devices[0]

    async def close(self) -> None:
        if self._manager:
            await self._manager.close()
            self._manager = None

    def _device_or_raise(self) -> RoborockDevice:
        if self._device is None:
            raise RuntimeError("VacuumClient not authenticated. Call authenticate() first.")
        return self._device

    async def _v1(self):
        device = self._device_or_raise()
        if device.v1_properties is None:
            raise RuntimeError("Device does not support V1 protocol.")
        return device.v1_properties

    # -------------------------------------------------------------------------
    # Status
    # -------------------------------------------------------------------------

    _STATE_NAMES = {c.value: c.name for c in RoborockStateCode}

    async def get_status(self) -> VacuumStatus:
        v1 = await self._v1()
        await v1.status.refresh()
        s = v1.status
        state_str = self._STATE_NAMES.get(s.state, str(s.state)) if s.state is not None else None
        in_dock = s.state in (8, 100)  # charging or charging_complete
        return VacuumStatus(
            state=state_str,
            battery=s.battery,
            in_dock=in_dock,
            error_code=s.error_code,
        )

    # -------------------------------------------------------------------------
    # Basic control
    # -------------------------------------------------------------------------

    async def _apply_settings(
        self,
        v1,
        fan_speed: FanSpeed | None = None,
        mop_mode: MopMode | None = None,
        water_flow: WaterFlow | None = None,
        route: CleanRoute | None = None,
    ) -> None:
        """Issue SET_* commands for any non-None settings before a clean command."""
        if fan_speed is not None:
            await v1.command.send(RoborockCommand.SET_CUSTOM_MODE, [fan_speed.value])
        # mop_mode takes precedence over route when both are provided (they share SET_MOP_MODE)
        effective_mode = mop_mode if mop_mode is not None else route
        if effective_mode is not None:
            await v1.command.send(RoborockCommand.SET_MOP_MODE, [int(effective_mode)])
        if water_flow is not None:
            await v1.command.send(RoborockCommand.SET_WATER_BOX_CUSTOM_MODE, [water_flow.value])

    async def start_clean(
        self,
        fan_speed: FanSpeed | None = None,
        mop_mode: MopMode | None = None,
        water_flow: WaterFlow | None = None,
        route: CleanRoute | None = None,
    ) -> None:
        v1 = await self._v1()
        await self._apply_settings(v1, fan_speed=fan_speed, mop_mode=mop_mode, water_flow=water_flow, route=route)
        await v1.command.send(RoborockCommand.APP_START)

    async def pause(self) -> None:
        v1 = await self._v1()
        await v1.command.send(RoborockCommand.APP_PAUSE)

    async def stop(self) -> None:
        v1 = await self._v1()
        await v1.command.send(RoborockCommand.APP_STOP)

    async def return_to_dock(self) -> None:
        v1 = await self._v1()
        await v1.command.send(RoborockCommand.APP_CHARGE)

    async def locate(self) -> None:
        v1 = await self._v1()
        await v1.command.send(RoborockCommand.FIND_ME)

    async def send_raw_command(
        self,
        command: RoborockCommand | str,
        params: Any = None,
    ) -> Any:
        """Send a raw V1 command and return the device response."""
        v1 = await self._v1()
        return await v1.command.send(command, params)

    async def get_clean_sequence(self) -> Any:
        """Return the device's configured clean sequence, if supported."""
        return await self.send_raw_command(RoborockCommand.GET_CLEAN_SEQUENCE)

    async def get_segment_status(self) -> Any:
        """Return segment-status data, if supported by the device."""
        return await self.send_raw_command(RoborockCommand.GET_SEGMENT_STATUS)

    # -------------------------------------------------------------------------
    # Room and zone cleaning
    # -------------------------------------------------------------------------

    async def clean_rooms(
        self,
        segment_ids: list[int],
        repeat: int = 1,
        fan_speed: FanSpeed | None = None,
        mop_mode: MopMode | None = None,
        water_flow: WaterFlow | None = None,
        route: CleanRoute | None = None,
    ) -> None:
        """Clean specific rooms by segment ID."""
        v1 = await self._v1()
        await self._apply_settings(v1, fan_speed=fan_speed, mop_mode=mop_mode, water_flow=water_flow, route=route)
        params = [{"segments": segment_ids, "repeat": repeat, "clean_order_mode": 0}]
        await v1.command.send(RoborockCommand.APP_SEGMENT_CLEAN, params)

    async def clean_zones(
        self,
        zones: list[tuple[int, int, int, int]],
        repeat: int = 1,
        fan_speed: FanSpeed | None = None,
        mop_mode: MopMode | None = None,
        water_flow: WaterFlow | None = None,
        route: CleanRoute | None = None,
    ) -> None:
        """Clean rectangular zones. Each zone is (x1, y1, x2, y2)."""
        v1 = await self._v1()
        await self._apply_settings(v1, fan_speed=fan_speed, mop_mode=mop_mode, water_flow=water_flow, route=route)
        zone_params = [list(z) + [repeat] for z in zones]
        await v1.command.send(RoborockCommand.APP_ZONED_CLEAN, [{"zones": zone_params}])

    # -------------------------------------------------------------------------
    # Map / room discovery
    # -------------------------------------------------------------------------

    async def get_rooms(self) -> list[Room]:
        """Return rooms with their segment IDs and names."""
        v1 = await self._v1()
        await v1.rooms.refresh()
        if v1.rooms.rooms is None:
            return []
        return [Room(id=r.segment_id, name=r.name) for r in v1.rooms.rooms]

    async def get_map_debug_info(self) -> MapDebugInfo:
        """Return charger and room geometry for proximity debugging."""
        v1 = await self._v1()
        await v1.rooms.refresh()
        await v1.map_content.refresh()

        room_name_map: dict[int, str] = {}
        if v1.rooms.rooms is not None:
            room_name_map = {r.segment_id: r.name for r in v1.rooms.rooms}

        map_data = v1.map_content.map_data
        if map_data is None:
            raise RuntimeError("Map data unavailable from device")

        charger = getattr(map_data, "charger", None)
        charger_x = charger.x if charger is not None else None
        charger_y = charger.y if charger is not None else None

        vacuum_position = getattr(map_data, "vacuum_position", None)
        vacuum_x = vacuum_position.x if vacuum_position is not None else None
        vacuum_y = vacuum_position.y if vacuum_position is not None else None
        vacuum_room = getattr(map_data, "vacuum_room", None)
        vacuum_room_name = getattr(map_data, "vacuum_room_name", None)
        if vacuum_room_name is None and vacuum_room is not None:
            vacuum_room_name = room_name_map.get(vacuum_room)

        rooms: list[MapDebugRoom] = []
        raw_rooms = getattr(map_data, "rooms", None) or {}
        for segment_id, room in raw_rooms.items():
            center_x = (room.x0 + room.x1) / 2
            center_y = (room.y0 + room.y1) / 2
            anchor_x = room.pos_x if room.pos_x is not None else center_x
            anchor_y = room.pos_y if room.pos_y is not None else center_y
            dist = None
            if charger_x is not None and charger_y is not None:
                dist = ((anchor_x - charger_x) ** 2 + (anchor_y - charger_y) ** 2) ** 0.5
            rooms.append(MapDebugRoom(
                segment_id=int(segment_id),
                name=room_name_map.get(int(segment_id)) or room.name or f"Room {segment_id}",
                anchor_x=anchor_x,
                anchor_y=anchor_y,
                center_x=center_x,
                center_y=center_y,
                width=abs(room.x1 - room.x0),
                height=abs(room.y1 - room.y0),
                distance_from_charger=dist,
            ))

        rooms.sort(
            key=lambda r: (
                float("inf") if r.distance_from_charger is None else r.distance_from_charger,
                r.name.lower(),
            )
        )

        return MapDebugInfo(
            charger_x=charger_x,
            charger_y=charger_y,
            vacuum_x=vacuum_x,
            vacuum_y=vacuum_y,
            vacuum_room=vacuum_room,
            vacuum_room_name=vacuum_room_name,
            rooms=rooms,
        )

    async def rooms_by_name(self) -> dict[str, int]:
        """Return {name_lowercase: segment_id} mapping."""
        rooms = await self.get_rooms()
        return {r.name.lower(): r.id for r in rooms}

    # -------------------------------------------------------------------------
    # Routines (scenes)
    # -------------------------------------------------------------------------

    async def get_routines(self) -> list[HomeDataScene]:
        """Return scenes/routines configured in the Roborock app."""
        device = self._device_or_raise()
        assert self._api_client is not None
        assert self._user_data is not None
        return await self._api_client.get_scenes(self._user_data, device.duid)

    async def run_routine(self, name: str) -> None:
        """Trigger a named routine by name (case-insensitive)."""
        routines = await self.get_routines()
        name_lower = name.lower()
        for routine in routines:
            if routine.name.lower() == name_lower:
                assert self._api_client is not None
                assert self._user_data is not None
                await self._api_client.execute_scene(self._user_data, routine.id)
                return
        available = [r.name for r in routines]
        raise RoutineNotFoundError(
            f"Routine '{name}' not found. Available: {available}"
        )

    # -------------------------------------------------------------------------
    # Consumables
    # -------------------------------------------------------------------------

    async def get_consumables(self) -> Consumables:
        """Return consumable life as percentages remaining."""
        v1 = await self._v1()
        await v1.consumables.refresh()
        c = v1.consumables

        def _pct(work_time: int | None, replace_time: int) -> int | None:
            if work_time is None:
                return None
            remaining = max(0, replace_time - work_time)
            return round(remaining / replace_time * 100)

        return Consumables(
            main_brush_pct=_pct(c.main_brush_work_time, MAIN_BRUSH_REPLACE_TIME),
            side_brush_pct=_pct(c.side_brush_work_time, SIDE_BRUSH_REPLACE_TIME),
            filter_pct=_pct(c.filter_work_time, FILTER_REPLACE_TIME),
            sensor_pct=_pct(c.sensor_dirty_time, SENSOR_DIRTY_REPLACE_TIME),
        )

    _CONSUMABLE_ATTRIBUTES = {a.value for a in ConsumableAttribute}

    async def reset_consumable(self, attribute: str) -> None:

        """Reset a consumable timer by attribute name."""
        if attribute not in self._CONSUMABLE_ATTRIBUTES:
            raise ValueError(f"Unknown consumable attribute: {attribute!r}. Valid: {sorted(self._CONSUMABLE_ATTRIBUTES)}")
        v1 = await self._v1()
        await v1.consumables.reset_consumable(ConsumableAttribute(attribute))

    # -------------------------------------------------------------------------
    # Cleaning settings — setters and getter
    # -------------------------------------------------------------------------

    async def set_fan_speed(self, speed: FanSpeed) -> None:
        """Persist fan speed as the device default (without starting a clean)."""
        v1 = await self._v1()
        await v1.command.send(RoborockCommand.SET_CUSTOM_MODE, [speed.value])

    async def set_mop_mode(self, mode: MopMode) -> None:
        """Persist mop/route mode as the device default."""
        v1 = await self._v1()
        await v1.command.send(RoborockCommand.SET_MOP_MODE, [mode.value])

    async def set_water_flow(self, flow: WaterFlow) -> None:
        """Persist water flow level as the device default."""
        v1 = await self._v1()
        await v1.command.send(RoborockCommand.SET_WATER_BOX_CUSTOM_MODE, [flow.value])

    async def get_current_settings(self) -> CleanSettings:
        """Return the device's currently active fan speed, mop mode, and water flow."""
        v1 = await self._v1()
        await v1.status.refresh()
        s = v1.status

        fan_speed  = _FAN_SPEED_BY_CODE.get(int(s.fan_power)) if s.fan_power is not None else None
        mop_mode   = _MOP_MODE_BY_CODE.get(int(s.mop_mode)) if s.mop_mode is not None else None
        water_flow = _WATER_FLOW_BY_CODE.get(int(s.water_box_mode)) if s.water_box_mode is not None else None

        return CleanSettings(fan_speed=fan_speed, mop_mode=mop_mode, water_flow=water_flow)

    # -------------------------------------------------------------------------
    # Clean history
    # -------------------------------------------------------------------------

    async def get_clean_history(self, limit: int = 10) -> list[CleanRecord]:
        """Return the last `limit` cleaning job records."""
        v1 = await self._v1()
        await v1.clean_summary.refresh()
        record_ids = (v1.clean_summary.records or [])[:limit]
        records: list[CleanRecord] = []
        for rid in record_ids:
            try:
                r = await v1.clean_summary.get_clean_record(rid)
                start = (
                    datetime.datetime.fromtimestamp(r.begin, tz=datetime.timezone.utc).isoformat()
                    if r.begin
                    else None
                )
                def _enum_name(val) -> str | None:
                    try:
                        return val.name if val is not None else None
                    except AttributeError:
                        return None

                records.append(
                    CleanRecord(
                        start_time=start,
                        duration_seconds=r.duration,
                        area_m2=r.square_meter_area,
                        complete=bool(r.complete),
                        start_type=_enum_name(getattr(r, "start_type", None)),
                        clean_type=_enum_name(getattr(r, "clean_type", None)),
                        finish_reason=_enum_name(getattr(r, "finish_reason", None)),
                        avoid_count=getattr(r, "avoid_count", None),
                        wash_count=getattr(r, "wash_count", None),
                    )
                )
            except Exception:
                continue
        return records
