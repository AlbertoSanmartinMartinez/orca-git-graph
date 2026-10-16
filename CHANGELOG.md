# Changelog

## Unreleased

- Read the workspace state from `profile-state.db`, the SQLite store of Orca 1.4.224. The sync process opens it read-only. Profiles that store the state in `orca-data.json` continue to work.
- The installer prefers `profile-state.db` when a profile has both state files.

## 0.1.0 — 2026-09-15

Initial public release.

- Git commit graph in Orca's right sidebar.
- Automatic local workspace and worktree switching.
- Branch/tag filters, search, HEAD navigation, and commit/file details.
- Standard-library Python installer with explicit profile selection and process locking.
- English documentation, fictional interactive demo, and machine-readable documentation index.
- Core Git/parser/installation tests and sandboxed browser tests.

Desktop target: Orca 1.4.185 on macOS. Remote workspaces are not supported; Windows/Linux desktop integration remains experimental.
