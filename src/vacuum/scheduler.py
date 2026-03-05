"""Clean scheduler — SQLite-backed room interval tracking and planning."""

from __future__ import annotations

import asyncio
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
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
    vacuum_overdue_ratio: float | None  # None = no interval; float('inf') = never cleaned
    mop_overdue_ratio: float | None
    notes: str | None

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
            "vacuum_overdue_ratio": _ratio(self.vacuum_overdue_ratio),
            "mop_overdue_ratio": _ratio(self.mop_overdue_ratio),
            "notes": self.notes,
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
    return days_since / interval_days


def _get_last_cleaned(
    conn: sqlite3.Connection, segment_id: int, mode: str
) -> str | None:
    """Get most recent dispatched_at for a room in the given mode."""
    row = conn.execute(
        """
        SELECT e.dispatched_at
        FROM clean_events e
        JOIN clean_event_rooms cer ON cer.clean_event_id = e.id
        WHERE cer.segment_id = ?
          AND (e.mode = ? OR e.mode = 'both')
        ORDER BY e.dispatched_at DESC
        LIMIT 1
        """,
        (segment_id, mode),
    ).fetchone()
    return row[0] if row else None


def _get_schedule_sync() -> list[RoomSchedule]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT segment_id, name, vacuum_days, mop_days, notes FROM room_schedules ORDER BY name"
        ).fetchall()
        result = []
        for row in rows:
            sid = row["segment_id"]
            last_vacuumed = _get_last_cleaned(conn, sid, "vacuum")
            last_mopped = _get_last_cleaned(conn, sid, "mop")
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
                    vacuum_overdue_ratio=vacuum_ratio,
                    mop_overdue_ratio=mop_ratio,
                    notes=row["notes"],
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
# Duration estimation
# ---------------------------------------------------------------------------

def _estimate_duration_sync(segment_ids: list[int]) -> float | None:
    if not segment_ids:
        return None
    sorted_ids = sorted(segment_ids)
    n = len(sorted_ids)
    placeholders = ",".join("?" * n)

    with _connect() as conn:
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
    overdue = _get_overdue_rooms_sync(mode)

    if not overdue:
        return PlanResult(
            selected=[], deferred=[], estimated_total_sec=None,
            notes=["No rooms are overdue."],
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
