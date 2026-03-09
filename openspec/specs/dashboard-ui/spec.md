## REMOVED Requirements

### Requirement: Rooms panel
**Reason**: The Rooms panel displays a raw list of room segment IDs and names, which is not useful for daily operation. Room data is still fetched internally for the Clean Rooms checkbox list.
**Migration**: No migration needed. The `GET /api/rooms` endpoint remains; only the UI panel is removed. The `_rooms` JS global is still populated by `loadCleanRooms()`.
