"""Authenticated python-roborock wrapper for the Roborock Saros 10R."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from roborock.data import HomeDataScene, UserData
from roborock.data.v1.v1_code_mappings import RoborockStateCode
from roborock.devices.cache import NoCache
from roborock.devices.device import RoborockDevice
from roborock.devices.device_manager import DeviceManager, UserParams, create_device_manager
from roborock.exceptions import RoborockException
from roborock.roborock_typing import RoborockCommand
from roborock.web_api import RoborockApiClient

from .config import ConfigError, get_device_name, get_username, load_session, save_session


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

    async def start_clean(self) -> None:
        v1 = await self._v1()
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

    # -------------------------------------------------------------------------
    # Room and zone cleaning
    # -------------------------------------------------------------------------

    async def clean_rooms(self, segment_ids: list[int], repeat: int = 1) -> None:
        """Clean specific rooms by segment ID."""
        v1 = await self._v1()
        params = [{"segments": segment_ids, "repeat": repeat, "clean_order_mode": 0}]
        await v1.command.send(RoborockCommand.APP_SEGMENT_CLEAN, params)

    async def clean_zones(self, zones: list[tuple[int, int, int, int]], repeat: int = 1) -> None:
        """Clean rectangular zones. Each zone is (x1, y1, x2, y2)."""
        v1 = await self._v1()
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
