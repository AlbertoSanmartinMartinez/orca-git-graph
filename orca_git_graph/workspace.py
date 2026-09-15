"""Isolate the experimental Orca 1.4.185 state-file integration here."""
import json
import os
import sys
from pathlib import Path


class WorkspaceError(RuntimeError):
    pass


def data_root():
    override = os.environ.get("ORCA_USER_DATA_PATH")
    if override:
        return Path(override).expanduser()
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/orca"
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming")) / "orca"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "orca"


def discover_state(explicit=None, profile=None):
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.is_file():
            raise WorkspaceError("The supplied Orca state file does not exist.")
        return path
    root = data_root()
    if profile:
        if Path(profile).name != profile or profile in (".", ".."):
            raise WorkspaceError("Profile must be a directory name, not a path.")
        return discover_state(root / "profiles" / profile / "orca-data.json")
    candidates = list((root / "profiles").glob("*/orca-data.json"))
    if (root / "orca-data.json").is_file():
        candidates.append(root / "orca-data.json")
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise WorkspaceError("Orca state was not found. Open Orca, or pass --orca-state PATH.")
    raise WorkspaceError("Multiple Orca profiles found. Choose --profile NAME or --orca-state PATH.")


def resolve_workspace(state):
    session = state.get("workspaceSession") or {}
    host = session.get("activeWorkspaceExecutionHostId")
    if host and host != "local":
        return {"error": "Remote workspaces are not supported in this release.", "key": host}
    # Orca runtime uses activeWorktreeId. activeWorkspaceKey may be stale after navigation.
    active = session.get("activeWorktreeId")
    if "activeWorktreeId" not in session:
        active = session.get("activeWorkspaceKey")
    if not isinstance(active, str) or not active:
        return {"error": "Select a Git workspace in Orca's left sidebar.", "key": None}
    key = active
    if active.startswith("worktree:"):
        active = active[len("worktree:"):]
    if active.startswith("folder:"):
        folder_id = active[len("folder:"):]
        folder = next((f for f in state.get("folderWorkspaces", []) if f.get("id") == folder_id), None)
        path = folder.get("path") if folder else None
    elif "::" in active:
        repo_id, path = active.split("::", 1)
        repo = next((r for r in state.get("repos", []) if r.get("id") == repo_id), None)
        if not repo or repo.get("kind", "git") not in ("git", "folder", "local"):
            return {"error": "The selected local repository is unavailable.", "key": key}
    else:
        path = None
    if not isinstance(path, str) or not Path(path).is_absolute():
        return {"error": "The selected workspace has no local folder.", "key": key}
    return {"path": path, "key": key}


def read_selection(state_path):
    try:
        with Path(state_path).open(encoding="utf-8") as source:
            # Bound malformed or unexpected files. Never print or copy the state document.
            raw = source.read(16 * 1024 * 1024 + 1)
        if len(raw) > 16 * 1024 * 1024:
            raise ValueError("State document is too large")
        return resolve_workspace(json.loads(raw))
    except (OSError, ValueError, AttributeError, TypeError):
        return {"error": "Cannot read Orca's current workspace. Check the state-file setting.", "key": None}
