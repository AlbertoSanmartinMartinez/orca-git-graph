# Architecture and compatibility

Orca Git Graph combines a standard-library Python sync process with an Orca plugin panel. The panel is a standalone HTML document using JavaScript and SVG. It has no network client, external scripts, plugin worker, or requested Orca API capabilities.

## Data flow

1. Read the configured profile's `orca-data.json`.
2. Resolve `workspaceSession.activeWorktreeId` to the exact selected local worktree path.
3. Read Git commits, references, HEAD, upstream divergence, and changed-file names with argument-based subprocess calls.
4. Escape commit metadata before embedding it in a self-contained HTML document.
5. Atomically replace the runtime's `plugin/panel.html`.
6. Orca's Development plugin watcher reloads the sandboxed iframe.

`activeWorktreeId` takes precedence over `activeWorkspaceKey`. During development with Orca 1.4.185, the latter could retain a previous workspace after navigation. If `activeWorktreeId` explicitly becomes null, the graph clears; it does not silently fall back to an old project.

## Modules

| File | Responsibility |
| --- | --- |
| `install.py` | Locate Orca state, copy an isolated runtime, print registration steps, optionally open a sync terminal |
| `orca_git_graph/workspace.py` | Platform paths, explicit profile selection, selected-workspace resolution |
| `orca_git_graph/git_data.py` | Read-only Git commands and NUL-delimited parsing |
| `orca_git_graph/app.py` | Polling, process lock, escaping, atomic HTML generation, diagnostics |
| `orca_git_graph/panel.html` | SVG lane layout, commit table, search, branch filter, details |
| `plugin/orca-plugin.json` | Right-sidebar panel contribution |
| `tests/test_core.py` | Real temporary Git histories, selection edge cases, isolated installation |

## Compatibility contract

The initial desktop target is Orca 1.4.185 on macOS. The plugin manifest requires `>=1.4.185`, but that is a minimum version gate, not a guarantee that every later Orca build is compatible. Both the plugin API and the persisted selection format are experimental/version-dependent.

Linux and Windows have filesystem and process-lock implementations and automated core checks. Their Orca desktop registration, profile layout, and live-reload behavior are not yet end-to-end validated. Remote/SSH/cloud workspaces are intentionally unsupported.

When adapting a new Orca version, test actual left-sidebar switching in addition to parser unit tests. Update `workspace.py` if Orca's persisted selection contract changes. Do not modify Orca's signed app bundle or bypass its plugin review UI.

## Performance and behavior

Selection is polled every 0.75 seconds. Git fingerprints are checked every 10 seconds and immediately after selection changes. The HTML is only rewritten when selection or Git state changes. The process does not fetch remote updates; remote branch labels reflect locally available Git refs.

The default history window is 400 commits, including detached HEAD. Branch filtering follows ancestors only within that loaded window. The renderer preserves graph context during search by dimming nonmatching rows rather than removing them.

Changed-file lists are capped at 200 entries per commit. Rename detection is disabled, and merge commits can lack a file list. Refreshes replace the entire document, resetting filters and scroll position. These are deliberate first-release limitations, not full parity with the VS Code Git Graph extension.

## Local data boundaries

Runtime HTML contains metadata from the selected repository, including commit messages, names/emails, hashes, and file paths. Keep the runtime directory private. The installer places it outside the source checkout; generated data and local config are excluded from the public package.

The sync process reads Orca's state JSON to select a workspace. It does not print or export the whole state document, read runtime authentication tokens, or call Orca's internal RPC endpoints. The optional installer terminal launch uses the public Orca CLI.
