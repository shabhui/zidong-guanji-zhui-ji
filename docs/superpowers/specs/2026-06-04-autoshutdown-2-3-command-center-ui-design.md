# AutoShutdownQt 2.3 Command Center UI Design

## Goal

AutoShutdownQt 2.3 should make the existing QML app feel like a professional single-page command center while preserving the 2.2 stability posture, dry-run safety model, and E5E8/neon glass identity.

## Scope

### In scope

- Rework the main QML layout into a clearer single-page command center.
- Keep the current E5E8/neon glass visual base, but reduce noise inside information-heavy areas.
- Add a top safety/status strip for dry-run/live mode, current action, tray availability, and queue count.
- Add compact command cards for next task, active triggers, and scheduler/queue health.
- Improve the visual hierarchy of quick task creation, task queue, trigger controls, and recent activity/logs.
- Add lightweight UI feedback states: clearer badges, disabled/active states, empty queue copy, and safer live-mode copy.
- Preserve current controller APIs unless a small QML-facing computed text property is necessary for readable cards.
- Update static QML regression tests to protect the new visible text, component usage, and default-window fit.
- Update README/release notes/package identity for 2.3.

### Out of scope

- New scheduling behavior.
- Task editing, searching, filtering, duplication, or drag-and-drop.
- New tray behavior beyond showing the existing state more clearly.
- New installer, code signing, automatic updates, or startup integration.
- Large page/navigation redesign with tabs or side navigation.
- Replacing the current visual identity with a minimal utility theme.

## Design Direction

Use a single scrollable command center page. The page should read from top to bottom as:

1. Current safety and runtime state.
2. Important scheduler summary.
3. Fast task creation.
4. Queue and trigger details.
5. Recent activity.

The visual identity stays neon/glass, but the dense content areas should prioritize contrast and alignment over decoration. Decorative glow belongs on outer cards, section headers, and primary buttons. Queue rows and logs should use calmer surfaces, consistent spacing, and readable badges.

## Layout

### Top safety strip

The top strip should be visible near the top of the main scroll area and summarize:

- Dry-run enabled vs live mode.
- Current selected power action.
- Tray availability / close-to-tray expectation.
- Number of queued tasks.

Dry-run should look safe and calm. Live mode should be visually stronger and include concise warning copy.

### Command cards

Add three compact cards below the top strip:

- **Next task**: show the next queued task or an empty-state message.
- **Active triggers**: show process/network trigger state from existing controller state/copy.
- **Queue health**: show queue count and scheduler pause/running state when available from existing data.

If QML cannot derive a summary cleanly from existing properties, add small controller properties instead of duplicating complex logic in QML.

### Quick create and existing controls

Keep existing countdown, fixed-time, task template, process trigger, and network trigger controls. Reposition them into clearer sections with shorter headings and consistent card spacing. Do not remove existing user-facing capabilities.

### Task queue dashboard

The queue section should look like a dashboard table/list:

- Clear empty state when no tasks exist.
- Consistent status badges.
- Next run and repeat information remain visible.
- Existing enable/disable/delete actions stay accessible.
- Avoid adding edit/search/filter controls in 2.3.

### Recent activity

The log area should be framed as recent activity:

- Keep export/clear actions.
- Improve heading and helper copy.
- Use existing log text; do not introduce a new log data model.

## Architecture

Keep the 2.2 module boundaries:

- `controller.py` remains the Python/QML bridge.
- `task_scheduler.py` remains responsible for scheduling and queue state.
- `tray_service.py` remains responsible for tray integration.
- `Main.qml` and existing QML components own the visual restructure.

Prefer QML-only layout changes. Add Python properties only when needed for stable, testable summary text that would otherwise be duplicated or brittle in QML.

## Safety and behavior

- No UI path may bypass dry-run safeguards.
- Live-mode warning and confirmation behavior remain unchanged.
- Existing task queue, process trigger, network trigger, tray, and release packaging behavior must continue passing v2.2 tests.
- v2.3 UI copy should make it easier to understand whether the app is safe, hidden-to-tray capable, and actively monitoring triggers.

## Testing Strategy

- Keep the full unittest suite passing with `python -m unittest discover AutoShutdownQt/tests -v`.
- Add or update QML static regression tests for:
  - Command center/safety strip copy.
  - Command cards for next task, active triggers, and queue health.
  - Queue dashboard empty-state/status copy.
  - Recent activity heading/copy.
  - Continued use of NeonButton/NeonCard style components.
  - Default window height accessibility.
- Add controller tests only if new summary properties are introduced.
- Add release packaging tests for 2.3 identity, README, and release notes.

## Release Experience

AutoShutdownQt 2.3 should be documented as a UI polish release:

- Package identity moves to `2.3`.
- Add `AutoShutdownQt-2.3.spec` if release packaging keeps version-specific specs.
- Release notes should say 2.3 improves command-center readability and safety visibility without changing scheduling semantics.
- Release checklist should include dry-run, command center visibility, queue dashboard, recent activity, tray status copy, and no real power actions during validation.
