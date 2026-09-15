# Working on Orca Git Graph

This repository is an independent Orca desktop sidebar plugin plus a local Python sync process. All source comments, UI copy, documentation, issues, and commit messages should be in English.

## Start here

- `README.md`: product scope and quick start.
- `docs/installation.md`: exact installation and registration flow.
- `docs/architecture.md`: data flow and the version-dependent Orca state integration.
- `docs/troubleshooting.md`: supported recovery paths.
- `llms.txt`: concise documentation index for AI assistants.

## Implementation map

- `orca_git_graph/workspace.py`: find Orca state and resolve its selected local worktree.
- `orca_git_graph/git_data.py`: Git parsing. Use argument lists, never shell interpolation.
- `orca_git_graph/app.py`: polling, one-process lock, atomic output, CLI diagnostics.
- `orca_git_graph/panel.html`: standalone HTML/JS/SVG in Orca's sandbox.
- `install.py`: independent runtime copy and public Orca CLI terminal launch.

## Constraints

Preserve read-only Git behavior and a standard-library-only runtime. Do not edit Orca's app bundle or user settings, fabricate consent, read runtime auth tokens, or silently select among multiple profiles. Keep generated private repository history outside the source checkout. Public screenshots and demos must use fictional fixtures.

Prefer `workspaceSession.activeWorktreeId`; persisted `activeWorkspaceKey` can be stale. Test same-repo worktrees, detached HEAD, explicit deselection, unavailable folders, and remote workspaces. Platform core tests do not establish Orca desktop compatibility.

## Validation

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build_demo.py
python3 scripts/test_browser.py
python3 scripts/check_public.py
```

Browser tests require `requirements-dev.txt` and Playwright Chromium. Rebuild the fictional demo after UI changes. Regenerate `docs/index.md` and `docs/llms-full.txt` with `python3 scripts/build_docs.py` after documentation changes.

Do not commit runtime `config.json`, logs, user state files, or private generated panel snapshots. The checked-in `plugin/panel.html` is a setup placeholder only.
