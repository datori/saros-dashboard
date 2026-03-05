## Context

The vacuum system currently dispatches cleans but has no memory of when rooms were last cleaned or how often they should be. This design adds a local scheduling layer that enables overdue-based prioritization and time-budget planning for AI-assisted cleaning sessions.

All device interaction already goes through `VacuumClient`. The scheduler is a separate concern — it tracks intent and history, not device state. Both the dashboard (FastAPI) and the MCP server (stdio) need access to the same scheduling data.

## Goals / Non-Goals

**Goals:**
- Track last-cleaned per room × mode ("vacuum" | "both")
- Store per-room intervals (vacuum_days, mop_days)
- Log clean events at dispatch time (no completion tracking in v1)
- Compute overdue ratio: `days_since_last / interval_days`
- Estimate run duration for a given room set using historical data
- Plan optimal room selection given a time budget
- Expose schedule state and controls via MCP tools and dashboard panel

**Non-Goals:**
- Completion tracking / reconciling with device history (v2 concern)
- Cron / automated trigger execution (scheduling state is read by AI, not executed by a daemon)
- Historical bootstrap from device API (start fresh)
- Zone-level scheduling (rooms only)

## Decisions

### SQLite over JSON file

**Decision**: Use SQLite (`vacuum_schedule.db` in project root) as the single source of truth.

**Rationale**: Both the dashboard process and MCP server process need read/write access concurrently. SQLite's WAL mode handles this cleanly. JSON would require a lock file and custom merge logic. Querying "when was room X last mopped" is trivial SQL but painful in JSON. The stdlib `sqlite3` module (no extra deps) suffices; wrap blocking calls in `asyncio.to_thread()` to stay async-friendly.

**Alternative considered**: `aiosqlite` — adds a dependency but cleaner async API. Rejected: for this scale (7 rooms, single user), `asyncio.to_thread(sqlite3...)` is sufficient.

### Schema: normalized junction table

**Decision**: Use a `clean_event_rooms` junction table rather than a JSON array in `clean_events`.

```sql
room_schedules (segment_id PK, name, vacuum_days, mop_days, notes)
clean_events   (id PK, dispatched_at, mode, source, complete, duration_sec, area_m2)
clean_event_rooms (clean_event_id FK, segment_id FK)
```

**Rationale**: "When was room 4 last mopped?" is a simple JOIN, not a `json_each()` scan. The normalized form is cleaner for the queries that matter.

### Dispatched = cleaned (v1)

**Decision**: Record the clean event at dispatch time. No completion polling or reconciliation.

**Rationale**: If a run fails, the room will show as overdue sooner and get priority next cycle — self-correcting behavior. Completion tracking requires polling device state or reconciling against device history, which adds significant complexity for uncertain benefit in v1.

### Mode detection at dispatch time

**Decision**: Determine mode from `water_flow` parameter at dispatch time.
- `water_flow = OFF` or `water_flow = None` (default when not specified) → `"vacuum"`
- `water_flow` any non-OFF value → `"both"` (vacuum + mop)

**Rationale**: The Saros 10R always vacuums. The only question is whether it also mopped, which is directly controlled by water_flow. No heuristics needed.

### Run-time estimation: three-tier fallback

**Decision**: Estimate clean duration using this priority order:
1. **Exact match**: If we have ≥2 historical events with the same sorted `segment_ids`, use their average `duration_sec`.
2. **Per-room decomposition**: Average duration of single-room events for each room; sum + fixed overhead (300s ≈ 5 min for dock return and travel).
3. **Area-based prior**: `total_area_m2 × 150 sec/m²` + 300s overhead. Area must come from past events; if unknown, return `None`.

**Rationale**: Exact match is most accurate. Single-room decomposition is composable. Area-based is a reasonable fallback as data accumulates.

### Planning: greedy time-budget selection

**Decision**: Sort rooms by overdue ratio descending (rooms never cleaned → ∞ ratio), then greedily add rooms until adding the next would exceed the time budget.

**Rationale**: With ≤7 rooms, even optimal subset enumeration (2^7 = 128) is trivial, but greedy is predictable and explainable to the user ("I picked the most overdue rooms that fit"). We can upgrade to optimal later.

### DB location: project root

**Decision**: `vacuum_schedule.db` in the project root alongside `.roborock_session.json`.

**Rationale**: Consistent with the existing session file convention. Simple, no XDG overhead.

## Risks / Trade-offs

- **Stale room names**: `room_schedules.name` is populated from the device at first sync. If rooms are renamed in the app, names drift. Mitigation: `sync_rooms()` refreshes names from the device on demand and at dashboard startup.
- **No completion signal**: A failed clean counts as "cleaned." Mitigation: self-correcting — overdue ratio rises faster if rooms aren't actually being cleaned.
- **Duration estimates start empty**: First few runs produce no estimates. Mitigation: area-based prior gives a rough estimate until per-room data accumulates.
- **Concurrent writes (dashboard + MCP)**: SQLite WAL handles this, but write contention is theoretically possible. Mitigation: writes are rare (only on dispatch); risk is negligible at this scale.

## Open Questions

- Should `plan_clean` return a recommendation only, or also accept `auto_dispatch=True` to trigger the clean automatically? (Start with recommendation only; AI calls dispatch separately.)
- Should rooms with no schedule set (`vacuum_days = NULL`) appear in the overdue list? (No — only rooms with an interval configured are considered for scheduling.)
