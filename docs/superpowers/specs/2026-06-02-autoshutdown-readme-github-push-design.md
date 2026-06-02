# AutoShutdownQt 2.0 README and Branch Push Design

Date: 2026-06-02
Branch: v2-e5e8-reference-ui

## Goal

Make the GitHub branch readable and shareable by adding a root README for AutoShutdownQt 2.0, then push the current branch to `origin` without creating a GitHub Release.

## Chosen Scope

- Add `README.md` at the repository root.
- Document AutoShutdownQt 2.0 features, dry-run safety, source run/test commands, and local packaging commands.
- Mention the generated local artifact path `dist/AutoShutdownQt-2.0.zip` but keep `dist/` ignored and out of git.
- Push the current branch `v2-e5e8-reference-ui` to GitHub.
- Do not create a `v2.0` tag or GitHub Release in this pass.

## README Structure

- Title and one-line description.
- Feature list for v2.0 e5e8.
- Safety notes explaining dry-run default and live power actions.
- Requirements: Python 3.12, PySide6, optional PyInstaller for packaging.
- Run from source command.
- Test command.
- Package command and output paths.
- Repository hygiene notes: build outputs, zip artifacts, pycache, and screenshots are not committed.
- Current branch/publishing note.

## GitHub Publishing Behavior

Commit only documentation/design files. Keep these out of the commit:

- `dist/`
- `build/`
- `AutoShutdownQt/current-render.png`
- `AutoShutdownQt/e5e8b88f-7acc-4be7-930f-952ad1670984.png`
- `__pycache__/`

Push command:

```bash
git push origin v2-e5e8-reference-ui
```

## Acceptance Criteria

- `README.md` exists at repository root and explains AutoShutdownQt 2.0 clearly.
- README includes safety warning that dry-run is enabled by default.
- README includes `python AutoShutdownQt/main.py`, `python -m unittest discover AutoShutdownQt/tests -v`, and `python AutoShutdownQt/package_release.py`.
- Git status before commit shows screenshots still untracked and build outputs ignored.
- Commit is created for README/spec only.
- Branch `v2-e5e8-reference-ui` is pushed to `origin`.
