"""Clean scheduler — SQLite-backed room interval tracking and planning."""

from __future__ import annotations

import asyncio
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

# DB in project root alongside .roborock_session.json
_DB_PATH = Path(__file__).parent.parent.parent / "vacuum_schedule.db"


# ---------------------------------------------------------------------------
# DB setup
# ---------------------------------------------------------------------------

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Create DB tables if they don't exist (idempotent)."""
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS room_schedules (
                segment_id  INTEGER PRIMARY KEY,
                name        TEXT NOT NULL,
                vacuum_days REAL,
                mop_days    REAL,
                notes       TEXT
            );
            CREATE TABLE IF NOT EXISTS clean_events (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                dispatched_at TEXT NOT NULL,
                mode          TEXT NOT NULL,
                source        TEXT NOT NULL,
                complete      INTEGER NOT NULL DEFAULT 0,
                duration_sec  REAL,
                area_m2       REAL
            );
            CREATE TABLE IF NOT EXISTS clean_event_rooms (
                clean_event_id INTEGER NOT NULL REFERENCES clean_events(id),
                segment_id     INTEGER NOT NULL REFERENCES room_schedules(segment_id),
                PRIMARY KEY (clean_event_id, segment_id)
            );
        """)
        # Migrations for new columns (idempotent)
        for col, typedef in [
            ("started_at", "TEXT"),
            ("finished_at", "TEXT"),
            ("trigger_name", "TEXT"),
        ]:
            try:
                conn.execute(f"ALTER TABLE clean_events ADD COLUMN {col} {typedef}")
            except sqlite3.OperationalError:
                pass  # column already exists
        for col, typedef in [
            ("priority_weight", "REAL DEFAULT 1.0"),
            ("default_duration_sec", "REAL"),
        ]:
            try:
                conn.execute(f"ALTER TABLE room_schedules ADD COLUMN {col} {typedef}")
            except sqlite3.OperationalError:
                pass  # column already exists
        # Trigger tables
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS triggers (
                name       TEXT PRIMARY KEY,
                budget_min REAL NOT NULL,
                mode       TEXT DEFAULT 'vacuum',
                notes      TEXT
            );
            CREATE TABLE IF NOT EXISTS trigger_events (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                trigger_name   TEXT NOT NULL,
                fired_at       TEXT NOT NULL,
                returned_at    TEXT,
                actual_min     REAL,
                clean_event_id INTEGER
            );
            CREATE TABLE IF NOT EXISTS dispatch_settings (
                mode       TEXT PRIMARY KEY,
                fan_speed  TEXT,
                mop_mode   TEXT,
                water_flow TEXT,
                route      TEXT
            );
        """)
        # Seed default dispatch settings if not present
        conn.execute("""
            INSERT OR IGNORE INTO dispatch_settings (mode, fan_speed, mop_mode, water_flow, route)
            VALUES ('vacuum', 'balanced', NULL, 'off', NULL)
        """)
        conn.execute("""
            INSERT OR IGNORE INTO dispatch_settings (mode, fan_speed, mop_mode, water_flow, route)
            VALUES ('mop', 'off', 'standard', 'medium', NULL)
        """)


# ---------------------------------------------------------------------------
# Room sync
# ---------------------------------------------------------------------------

def _sync_rooms_sync(rooms: list) -> None:
    with _connect() as conn:
        for r in rooms:
            conn.execute(
                """
                INSERT INTO room_schedules (segment_id, name)
                VALUES (?, ?)
                ON CONFLICT(segment_id) DO UPDATE SET name = excluded.name
                """,
                (r.id, r.name),
            )


async def sync_rooms(rooms: list) -> None:
    """Upsert rooms from device; preserves existing interval config."""
    await asyncio.to_thread(_sync_rooms_sync, rooms)


# ---------------------------------------------------------------------------
# Configuration setters
# ---------------------------------------------------------------------------

def _set_room_interval_sync(segment_id: int, mode: str, days: float | None) -> None:
    if mode == "vacuum":
        col = "vacuum_days"
    elif mode == "mop":
        col = "mop_days"
    else:
        raise ValueError(f"mode must be 'vacuum' or 'mop', got {mode!r}")
    with _connect() as conn:
        conn.execute(
            f"UPDATE room_schedules SET {col} = ? WHERE segment_id = ?",
            (days, segment_id),
        )


async def set_room_interval(segment_id: int, mode: str, days: float | None) -> None:
    """Set vacuum_days or mop_days for a room. Pass days=None to clear."""
    await asyncio.to_thread(_set_room_interval_sync, segment_id, mode, days)


def _set_room_notes_sync(segment_id: int, notes: str | None) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE room_schedules SET notes = ? WHERE segment_id = ?",
            (notes, segment_id),
        )


async def set_room_notes(segment_id: int, notes: str | None) -> None:
    """Set free-text notes for a room."""
    await asyncio.to_thread(_set_room_notes_sync, segment_id, notes)


def _set_room_priority_sync(segment_id: int, weight: float) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE room_schedules SET priority_weight = ? WHERE segment_id = ?",
            (weight, segment_id),
        )


async def set_room_priority(segment_id: int, weight: float) -> None:
    """Set priority weight for a room (default 1.0)."""
    await asyncio.to_thread(_set_room_priority_sync, segment_id, weight)


def _set_room_duration_sync(segment_id: int, seconds: float | None) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE room_schedules SET default_duration_sec = ? WHERE segment_id = ?",
            (seconds, segment_id),
        )


async def set_room_duration(segment_id: int, seconds: float | None) -> None:
    """Set manual duration estimate for a room (seconds), or None to clear."""
    await asyncio.to_thread(_set_room_duration_sync, segment_id, seconds)


# ---------------------------------------------------------------------------
# Trigger management
# ---------------------------------------------------------------------------

def _upsert_trigger_sync(name: str, budget_min: float, mode: str = "vacuum", notes: str | None = None) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO triggers (name, budget_min, mode, notes)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET budget_min = excluded.budget_min,
                mode = excluded.mode, notes = excluded.notes
            """,
            (name, budget_min, mode, notes),
        )


async def upsert_trigger(name: str, budget_min: float, mode: str = "vacuum", notes: str | None = None) -> None:
    """Create or update a trigger."""
    await asyncio.to_thread(_upsert_trigger_sync, name, budget_min, mode, notes)


def _delete_trigger_sync(name: str) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM triggers WHERE name = ?", (name,))


async def delete_trigger(name: str) -> None:
    """Delete a trigger by name."""
    await asyncio.to_thread(_delete_trigger_sync, name)


def _get_triggers_sync() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT name, budget_min, mode, notes FROM triggers ORDER BY name").fetchall()
        return [dict(r) for r in rows]


async def get_triggers() -> list[dict]:
    """Return all configured triggers."""
    return await asyncio.to_thread(_get_triggers_sync)


def _log_trigger_event_sync(trigger_name: str, clean_event_id: int | None = None) -> int:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO trigger_events (trigger_name, fired_at, clean_event_id) VALUES (?, ?, ?)",
            (trigger_name, now, clean_event_id),
        )
        return cur.lastrowid


async def log_trigger_event(trigger_name: str, clean_event_id: int | None = None) -> int:
    """Log a trigger firing event. Returns the event ID."""
    return await asyncio.to_thread(_log_trigger_event_sync, trigger_name, clean_event_id)


def _close_trigger_event_sync(trigger_name: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        # Find the most recent unclosed event for this trigger
        row = conn.execute(
            "SELECT id, fired_at FROM trigger_events WHERE trigger_name = ? AND returned_at IS NULL ORDER BY fired_at DESC LIMIT 1",
            (trigger_name,),
        ).fetchone()
        if row:
            fired = datetime.fromisoformat(row["fired_at"])
            if fired.tzinfo is None:
                fired = fired.replace(tzinfo=timezone.utc)
            actual_min = (datetime.now(timezone.utc) - fired).total_seconds() / 60
            conn.execute(
                "UPDATE trigger_events SET returned_at = ?, actual_min = ? WHERE id = ?",
                (now, round(actual_min, 2), row["id"]),
            )


async def close_trigger_event(trigger_name: str) -> None:
    """Close an open trigger event, recording returned_at and actual_min."""
    await asyncio.to_thread(_close_trigger_event_sync, trigger_name)


async def close_all_trigger_events() -> None:
    """Close all open trigger events (used when window closes)."""
    triggers = await get_triggers()
    for t in triggers:
        await close_trigger_event(t["name"])


# ---------------------------------------------------------------------------
# Dispatch settings
# ---------------------------------------------------------------------------

def _get_dispatch_settings_sync() -> dict:
    with _connect() as conn:
        rows = conn.execute("SELECT mode, fan_speed, mop_mode, water_flow, route FROM dispatch_settings").fetchall()
        return {row["mode"]: {
            "fan_speed": row["fan_speed"],
            "mop_mode": row["mop_mode"],
            "water_flow": row["water_flow"],
            "route": row["route"],
        } for row in rows}


async def get_dispatch_settings() -> dict:
    """Return dispatch settings keyed by mode (vacuum, mop)."""
    return await asyncio.to_thread(_get_dispatch_settings_sync)


_DISPATCH_SETTING_FIELDS = {"fan_speed", "mop_mode", "water_flow", "route"}


def _update_dispatch_settings_sync(mode: str, **kwargs) -> None:
    updates = {k: v for k, v in kwargs.items() if k in _DISPATCH_SETTING_FIELDS}
    if not updates:
        return
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [mode]
    with _connect() as conn:
        conn.execute(f"UPDATE dispatch_settings SET {set_clause} WHERE mode = ?", values)


async def update_dispatch_settings(mode: str, **kwargs) -> None:
    """Update dispatch settings for a mode. Only provided fields are changed."""
    await asyncio.to_thread(_update_dispatch_settings_sync, mode, **kwargs)


# ---------------------------------------------------------------------------
# Clean event logging
# ---------------------------------------------------------------------------

def _log_clean_sync(segment_ids: list[int], mode: str, source: str) -> int:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO clean_events (dispatched_at, mode, source) VALUES (?, ?, ?)",
            (now, mode, source),
        )
        event_id = cur.lastrowid
        conn.executemany(
            "INSERT OR IGNORE INTO clean_event_rooms (clean_event_id, segment_id) VALUES (?, ?)",
            [(event_id, sid) for sid in segment_ids],
        )
    return event_id


async def log_clean(segment_ids: list[int], mode: str, source: str) -> int:
    """Log a clean event at dispatch time. Returns the new event ID."""
    return await asyncio.to_thread(_log_clean_sync, segment_ids, mode, source)


def _update_clean_duration_sync(
    event_id: int, duration_sec: float, area_m2: float | None = None
) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE clean_events SET duration_sec = ?, area_m2 = ?, complete = 1 WHERE id = ?",
            (duration_sec, area_m2, event_id),
        )


async def update_clean_duration(
    event_id: int, duration_sec: float, area_m2: float | None = None
) -> None:
    """Update duration and area for a clean event (post-hoc)."""
    await asyncio.to_thread(_update_clean_duration_sync, event_id, duration_sec, area_m2)


# ---------------------------------------------------------------------------
# History reconciliation
# ---------------------------------------------------------------------------

@dataclass
class UnreconciledEvent:
    event_id: int
    dispatched_at: str  # ISO 8601 UTC
    mode: str
    source: str
    segment_ids: list[int]


def _get_unreconciled_events_sync(max_age_hours: float = 2.0) -> list[UnreconciledEvent]:
    """Return clean_events with complete=0 dispatched within max_age_hours."""
    cutoff = datetime.now(timezone.utc)
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, dispatched_at, mode, source
            FROM clean_events
            WHERE complete = 0
            ORDER BY dispatched_at DESC
            """,
        ).fetchall()
        result = []
        for row in rows:
            dispatched = datetime.fromisoformat(row["dispatched_at"])
            if dispatched.tzinfo is None:
                dispatched = dispatched.replace(tzinfo=timezone.utc)
            age_hours = (cutoff - dispatched).total_seconds() / 3600
            if age_hours > max_age_hours:
                continue
            seg_rows = conn.execute(
                "SELECT segment_id FROM clean_event_rooms WHERE clean_event_id = ?",
                (row["id"],),
            ).fetchall()
            result.append(UnreconciledEvent(
                event_id=row["id"],
                dispatched_at=row["dispatched_at"],
                mode=row["mode"],
                source=row["source"],
                segment_ids=[r["segment_id"] for r in seg_rows],
            ))
        return result


async def get_unreconciled_events(max_age_hours: float = 2.0) -> list[UnreconciledEvent]:
    """Return unreconciled clean events (complete=0) within max_age_hours."""
    return await asyncio.to_thread(_get_unreconciled_events_sync, max_age_hours)


def _reconcile_event_sync(
    event_id: int, duration_sec: float | None, area_m2: float | None, complete: bool
) -> None:
    with _connect() as conn:
        conn.execute(
            """
            UPDATE clean_events
            SET duration_sec = ?, area_m2 = ?, complete = ?
            WHERE id = ?
            """,
            (duration_sec, area_m2, 1 if complete else 0, event_id),
        )


async def reconcile_event(
    event_id: int, duration_sec: float | None, area_m2: float | None, complete: bool
) -> None:
    """Update a clean event with device-reported data from history reconciliation."""
    await asyncio.to_thread(_reconcile_event_sync, event_id, duration_sec, area_m2, complete)


# ---------------------------------------------------------------------------
# Schedule queries
# ---------------------------------------------------------------------------

@dataclass
class RoomSchedule:
    segment_id: int
    name: str
    vacuum_days: float | None
    mop_days: float | None
    last_vacuumed: str | None
    last_mopped: str | None
    last_vacuum_combined: bool  # True when last_vacuumed credit came from a mode='both' event
    vacuum_overdue_ratio: float | None  # None = no interval; float('inf') = never cleaned
    mop_overdue_ratio: float | None
    notes: str | None
    priority_weight: float
    default_duration_sec: float | None

    def as_dict(self) -> dict:
        def _ratio(v: float | None) -> float | None:
            # Represent infinity as None in JSON; JS checks vacuum_days to distinguish
            if v is None or v == float("inf"):
                return None
            return round(v, 3)

        return {
            "segment_id": self.segment_id,
            "name": self.name,
            "vacuum_days": self.vacuum_days,
            "mop_days": self.mop_days,
            "last_vacuumed": self.last_vacuumed,
            "last_mopped": self.last_mopped,
            "last_vacuum_combined": self.last_vacuum_combined,
            "vacuum_overdue_ratio": _ratio(self.vacuum_overdue_ratio),
            "mop_overdue_ratio": _ratio(self.mop_overdue_ratio),
            "notes": self.notes,
            "priority_weight": self.priority_weight,
            "default_duration_sec": self.default_duration_sec,
        }


def _compute_overdue_ratio(
    last_cleaned_iso: str | None, interval_days: float | None
) -> float | None:
    if interval_days is None:
        return None
    if last_cleaned_iso is None:
        return float("inf")
    last = datetime.fromisoformat(last_cleaned_iso)
    now = datetime.now(timezone.utc)
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    days_since = (now - last).total_seconds() / 86400
    ratio = days_since / interval_days

    # Quantize due-ness to the local calendar day: if a clean becomes due at any
    # point today, treat it as due for the full day so an earlier window can pick it up.
    local_tz = datetime.now().astimezone().tzinfo or timezone.utc
    due_at = last + timedelta(days=interval_days)
    if due_at.astimezone(local_tz).date() <= now.astimezone(local_tz).date():
        return max(1.0, ratio)

    return ratio


def _get_last_cleaned(
    conn: sqlite3.Connection, segment_id: int, mode: str
) -> tuple[str | None, bool]:
    """Return (dispatched_at, is_combined) for the most recent completed clean in mode.

    is_combined is True when the matching event has mode='both' (i.e. the vacuum
    credit came from a simultaneous mop+vac run, not a dedicated vacuum pass).
    """
    row = conn.execute(
        """
        SELECT e.dispatched_at, e.mode
        FROM clean_events e
        JOIN clean_event_rooms cer ON cer.clean_event_id = e.id
        WHERE cer.segment_id = ?
          AND (e.mode = ? OR e.mode = 'both')
          AND e.complete = 1
        ORDER BY e.dispatched_at DESC
        LIMIT 1
        """,
        (segment_id, mode),
    ).fetchone()
    if row is None:
        return None, False
    return row[0], row[1] == "both"


def _get_schedule_sync() -> list[RoomSchedule]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT segment_id, name, vacuum_days, mop_days, notes, priority_weight, default_duration_sec FROM room_schedules ORDER BY name"
        ).fetchall()
        result = []
        for row in rows:
            sid = row["segment_id"]
            last_vacuumed, vacuum_combined = _get_last_cleaned(conn, sid, "vacuum")
            last_mopped, _ = _get_last_cleaned(conn, sid, "mop")
            vacuum_ratio = _compute_overdue_ratio(last_vacuumed, row["vacuum_days"])
            mop_ratio = _compute_overdue_ratio(last_mopped, row["mop_days"])
            result.append(
                RoomSchedule(
                    segment_id=sid,
                    name=row["name"],
                    vacuum_days=row["vacuum_days"],
                    mop_days=row["mop_days"],
                    last_vacuumed=last_vacuumed,
                    last_mopped=last_mopped,
                    last_vacuum_combined=vacuum_combined,
                    vacuum_overdue_ratio=vacuum_ratio,
                    mop_overdue_ratio=mop_ratio,
                    notes=row["notes"],
                    priority_weight=row["priority_weight"] or 1.0,
                    default_duration_sec=row["default_duration_sec"],
                )
            )
    return result


async def get_schedule() -> list[RoomSchedule]:
    """Return full schedule status for all rooms."""
    return await asyncio.to_thread(_get_schedule_sync)


def _get_overdue_rooms_sync(mode: str = "vacuum") -> list[RoomSchedule]:
    schedule = _get_schedule_sync()
    ratio_attr = "vacuum_overdue_ratio" if mode == "vacuum" else "mop_overdue_ratio"
    overdue = [
        r for r in schedule
        if getattr(r, ratio_attr) is not None and getattr(r, ratio_attr) >= 1.0
    ]
    # float('inf') sorts correctly with reverse=True (comes first)
    overdue.sort(key=lambda r: getattr(r, ratio_attr) or 0, reverse=True)
    return overdue


async def get_overdue_rooms(mode: str = "vacuum") -> list[RoomSchedule]:
    """Return rooms where overdue_ratio >= 1.0, sorted descending by ratio."""
    return await asyncio.to_thread(_get_overdue_rooms_sync, mode)


# ---------------------------------------------------------------------------
# Priority scoring
# ---------------------------------------------------------------------------

TYPE_WEIGHTS: dict[str, float] = {"vacuum": 1.5, "mop": 1.0}


def compute_priority_score(
    room_weight: float, type_weight: float, overdue_ratio: float
) -> float:
    """Return room_weight × type_weight × overdue_ratio (infinity if ratio is inf)."""
    if overdue_ratio == float("inf"):
        return float("inf")
    return room_weight * type_weight * overdue_ratio


@dataclass
class PriorityEntry:
    segment_id: int
    name: str
    mode: str
    overdue_ratio: float
    priority_score: float
    estimated_sec: float | None
    priority_weight: float

    def as_dict(self) -> dict:
        return {
            "segment_id": self.segment_id,
            "name": self.name,
            "mode": self.mode,
            "overdue_ratio": round(self.overdue_ratio, 3) if self.overdue_ratio != float("inf") else None,
            "priority_score": round(self.priority_score, 3) if self.priority_score != float("inf") else None,
            "estimated_sec": round(self.estimated_sec, 1) if self.estimated_sec is not None else None,
            "priority_weight": self.priority_weight,
        }


def _get_priority_queue_sync() -> list[PriorityEntry]:
    """Return all overdue rooms across both modes, scored and sorted descending."""
    schedule = _get_schedule_sync()

    # When mop dispatch settings use a non-OFF fan speed, a mop run physically
    # vacuums too (logged as mode='both', resetting both clocks).  In that case,
    # represent ALL overdue rooms (for either vacuum or mop) as a single mop entry —
    # the mop dispatch will satisfy both needs in one pass.  This prevents the queue
    # from mixing vacuum and mop entries, which would cause the window planner to
    # dispatch only the top-mode batch (typically vacuum) and defer mop indefinitely.
    mop_gives_both = False
    with _connect() as conn:
        row = conn.execute(
            "SELECT fan_speed FROM dispatch_settings WHERE mode = 'mop'"
        ).fetchone()
        if row:
            fs = (row["fan_speed"] or "").lower()
            mop_gives_both = bool(fs and fs != "off")

    entries: list[PriorityEntry] = []

    if mop_gives_both:
        for room in schedule:
            v_ratio = room.vacuum_overdue_ratio
            m_ratio = room.mop_overdue_ratio
            v_overdue = v_ratio is not None and v_ratio >= 1.0
            m_overdue = m_ratio is not None and m_ratio >= 1.0
            if m_overdue:
                # Room needs mopping → single mop entry, scored by the most urgent need.
                # Suppresses the separate vacuum entry since the mop run will cover it.
                best_ratio = max(v_ratio if v_overdue else 0.0, m_ratio)
                score = compute_priority_score(room.priority_weight, TYPE_WEIGHTS["mop"], best_ratio)
                est = _estimate_duration_sync([room.segment_id])
                entries.append(PriorityEntry(
                    segment_id=room.segment_id,
                    name=room.name,
                    mode="mop",
                    overdue_ratio=best_ratio,
                    priority_score=score,
                    estimated_sec=est,
                    priority_weight=room.priority_weight,
                ))
            elif v_overdue:
                # Vacuum-only overdue (no mop interval or mop not yet due) → vacuum entry.
                score = compute_priority_score(room.priority_weight, TYPE_WEIGHTS["vacuum"], v_ratio)
                est = _estimate_duration_sync([room.segment_id])
                entries.append(PriorityEntry(
                    segment_id=room.segment_id,
                    name=room.name,
                    mode="vacuum",
                    overdue_ratio=v_ratio,
                    priority_score=score,
                    estimated_sec=est,
                    priority_weight=room.priority_weight,
                ))
    else:
        for room in schedule:
            for mode, ratio_attr in [("vacuum", "vacuum_overdue_ratio"), ("mop", "mop_overdue_ratio")]:
                ratio = getattr(room, ratio_attr)
                if ratio is None or ratio < 1.0:
                    continue
                type_weight = TYPE_WEIGHTS.get(mode, 1.0)
                score = compute_priority_score(room.priority_weight, type_weight, ratio)
                est = _estimate_duration_sync([room.segment_id])
                entries.append(PriorityEntry(
                    segment_id=room.segment_id,
                    name=room.name,
                    mode=mode,
                    overdue_ratio=ratio,
                    priority_score=score,
                    estimated_sec=est,
                    priority_weight=room.priority_weight,
                ))
    # Sort descending by score; inf sorts first with reverse=True
    entries.sort(key=lambda e: e.priority_score if e.priority_score != float("inf") else float("inf"), reverse=True)
    return entries


async def get_priority_queue() -> list[PriorityEntry]:
    """Return all overdue rooms across both modes, scored and sorted descending."""
    return await asyncio.to_thread(_get_priority_queue_sync)


# ---------------------------------------------------------------------------
# Duration estimation
# ---------------------------------------------------------------------------

def _estimate_duration_sync(segment_ids: list[int]) -> float | None:
    if not segment_ids:
        return None
    sorted_ids = sorted(segment_ids)
    n = len(sorted_ids)
    placeholders = ",".join("?" * n)

    with _connect() as conn:
        # Tier 0: manual defaults — if all rooms have default_duration_sec, use sum + overhead
        manual_rows = conn.execute(
            f"SELECT segment_id, default_duration_sec FROM room_schedules WHERE segment_id IN ({placeholders})",
            sorted_ids,
        ).fetchall()
        manual_map = {r["segment_id"]: r["default_duration_sec"] for r in manual_rows}
        if all(manual_map.get(sid) is not None for sid in sorted_ids):
            return sum(manual_map[sid] for sid in sorted_ids) + (300 if n > 1 else 0)

        # Tier 1: exact match — avg of events with exactly these rooms
        exact_rows = conn.execute(
            f"""
            SELECT e.duration_sec
            FROM clean_events e
            WHERE e.duration_sec IS NOT NULL
              AND (SELECT COUNT(*) FROM clean_event_rooms cer
                   WHERE cer.clean_event_id = e.id) = ?
              AND (SELECT COUNT(*) FROM clean_event_rooms cer
                   WHERE cer.clean_event_id = e.id
                     AND cer.segment_id IN ({placeholders})) = ?
            """,
            (n, *sorted_ids, n),
        ).fetchall()

        if len(exact_rows) >= 2:
            return sum(r["duration_sec"] for r in exact_rows) / len(exact_rows)

        # Tier 2: per-room decomposition from single-room events
        per_room_avgs = []
        for sid in sorted_ids:
            row = conn.execute(
                """
                SELECT AVG(e.duration_sec) as avg_dur
                FROM clean_events e
                JOIN clean_event_rooms cer ON cer.clean_event_id = e.id
                WHERE e.duration_sec IS NOT NULL
                  AND cer.segment_id = ?
                  AND (SELECT COUNT(*) FROM clean_event_rooms cer2
                       WHERE cer2.clean_event_id = e.id) = 1
                """,
                (sid,),
            ).fetchone()
            per_room_avgs.append(row["avg_dur"] if row else None)

        if all(v is not None for v in per_room_avgs):
            return sum(per_room_avgs) + 300  # 300s fixed overhead

        # Tier 3: area-based prior
        area_row = conn.execute(
            """
            SELECT AVG(e.area_m2) as avg_total_area,
                   AVG(CAST((SELECT COUNT(*) FROM clean_event_rooms cer
                             WHERE cer.clean_event_id = e.id) AS REAL)) as avg_room_count
            FROM clean_events e
            WHERE e.area_m2 IS NOT NULL
              AND (SELECT COUNT(*) FROM clean_event_rooms cer
                   WHERE cer.clean_event_id = e.id) > 0
            """
        ).fetchone()

        if (
            area_row
            and area_row["avg_total_area"] is not None
            and area_row["avg_room_count"]
            and area_row["avg_room_count"] > 0
        ):
            avg_area_per_room = area_row["avg_total_area"] / area_row["avg_room_count"]
            total_area = avg_area_per_room * n
            return total_area * 150 + 300  # 150 sec/m² + 300s overhead

    return None


async def estimate_duration(segment_ids: list[int]) -> float | None:
    """Estimate clean duration in seconds using three-tier fallback."""
    return await asyncio.to_thread(_estimate_duration_sync, segment_ids)


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------

@dataclass
class PlanResult:
    selected: list[RoomSchedule]
    deferred: list[RoomSchedule]
    estimated_total_sec: float | None
    notes: list[str]

    def as_dict(self) -> dict:
        return {
            "selected": [r.as_dict() for r in self.selected],
            "deferred": [r.as_dict() for r in self.deferred],
            "estimated_total_minutes": (
                round(self.estimated_total_sec / 60, 1)
                if self.estimated_total_sec is not None
                else None
            ),
            "notes": self.notes,
        }


def _plan_clean_sync(
    max_minutes: float | None = None, mode: str = "vacuum"
) -> PlanResult:
    # Get overdue rooms sorted by priority score (cross-mode if no mode filter needed)
    overdue = _get_overdue_rooms_sync(mode)

    if not overdue:
        return PlanResult(
            selected=[], deferred=[], estimated_total_sec=None,
            notes=["No rooms are overdue."],
        )

    # Sort by priority score instead of raw overdue ratio
    type_weight = TYPE_WEIGHTS.get(mode, 1.0)
    ratio_attr = "vacuum_overdue_ratio" if mode == "vacuum" else "mop_overdue_ratio"
    overdue.sort(
        key=lambda r: compute_priority_score(
            r.priority_weight, type_weight, getattr(r, ratio_attr) or 0
        ),
        reverse=True,
    )

    if max_minutes is None:
        selected = overdue
        total_sec = _estimate_duration_sync([r.segment_id for r in selected])
        return PlanResult(selected=selected, deferred=[], estimated_total_sec=total_sec, notes=[])

    max_sec = max_minutes * 60
    selected: list[RoomSchedule] = []
    deferred: list[RoomSchedule] = []
    running_sec = 0.0
    plan_notes: list[str] = []

    for room in overdue:
        room_est = _estimate_duration_sync([room.segment_id])
        if room_est is None:
            selected.append(room)
            plan_notes.append(f"{room.name}: duration unknown, included without budget deduction")
        elif running_sec + room_est <= max_sec:
            selected.append(room)
            running_sec += room_est
        else:
            deferred.append(room)

    total_sec = (
        _estimate_duration_sync([r.segment_id for r in selected]) if selected else None
    )
    return PlanResult(
        selected=selected, deferred=deferred,
        estimated_total_sec=total_sec, notes=plan_notes,
    )


async def plan_clean(
    max_minutes: float | None = None, mode: str = "vacuum"
) -> PlanResult:
    """Greedy room selection by overdue ratio within optional time budget."""
    return await asyncio.to_thread(_plan_clean_sync, max_minutes, mode)
