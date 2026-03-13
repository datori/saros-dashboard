## MODIFIED Requirements

### Requirement: Fire trigger
The system SHALL open a cleaning window when a trigger is fired, passing the trigger's mode to the window.

#### Scenario: Fire trigger with no active window
- **WHEN** trigger "gym" (budget=20min, mode="vacuum") is fired and no window is active
- **THEN** the window end time SHALL be set to `now + 20 minutes` and `_window_mode` SHALL be set to `"vacuum"`

#### Scenario: Fire trigger extends existing window
- **WHEN** a window is active ending at 2:15pm and trigger "leaving" (budget=60min, mode="mop") is fired at 2:05pm
- **THEN** the window end time SHALL be updated to `max(2:15pm, 3:05pm)` and `_window_mode` SHALL be set to `"mop"`

#### Scenario: Fire trigger with shorter budget than active window
- **WHEN** a window is active ending at 3:00pm and trigger "shower" (budget=15min) is fired at 2:50pm
- **THEN** the window end time SHALL be max(3:00pm, 3:05pm) = 3:05pm and `_window_mode` SHALL be updated to the new trigger's mode

#### Scenario: Fire trigger while vacuum is already cleaning
- **WHEN** a trigger is fired and the vacuum is currently cleaning
- **THEN** the window SHALL be opened/extended (with mode updated) but no new dispatch SHALL occur until the current clean completes

## ADDED Requirements

### Requirement: "both" trigger mode
The system SHALL support `mode="both"` on triggers, causing auto-dispatch to select mop-overdue rooms and apply combined vacuum+mop settings.

#### Scenario: Create trigger with both mode
- **WHEN** a trigger is created with `mode="both"`
- **THEN** it SHALL be stored in the `triggers` table and returned in the trigger list

#### Scenario: Trigger UI shows both option
- **WHEN** the trigger create/edit modal is opened
- **THEN** the mode dropdown SHALL include "Both (vac+mop)" as a selectable option alongside "Vacuum" and "Mop"
