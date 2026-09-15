import copy
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from orca_git_graph.app import empty_repo, render_html, watcher_lock
from orca_git_graph.git_data import collect
from orca_git_graph.workspace import discover_state, resolve_workspace, WorkspaceError


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.path = str(Path(tempfile.gettempdir()) / "feature worktree")
        self.state = {"repos": [{"id": "repo", "kind": "git"}], "workspaceSession": {
            "activeWorktreeId": "repo::" + self.path, "activeWorkspaceKey": "worktree:stale::/stale"}}

    def test_active_id_overrides_stale_workspace_key(self):
        self.assertEqual(resolve_workspace(self.state)["path"], self.path)

    def test_worktree_switch_in_same_repository(self):
        path = str(Path(tempfile.gettempdir()) / "another worktree")
        self.state["workspaceSession"]["activeWorktreeId"] = "repo::" + path
        self.assertEqual(resolve_workspace(self.state)["path"], path)

    def test_deselection_does_not_restore_stale_workspace(self):
        self.state["workspaceSession"]["activeWorktreeId"] = None
        self.assertNotIn("path", resolve_workspace(self.state))

    def test_remote_does_not_read_a_matching_local_path(self):
        self.state["workspaceSession"]["activeWorkspaceExecutionHostId"] = "ssh:example"
        self.assertNotIn("path", resolve_workspace(self.state))

    def test_folder(self):
        self.state["workspaceSession"]["activeWorktreeId"] = "folder:notes"
        self.state["folderWorkspaces"] = [{"id": "notes", "path": self.path}]
        self.assertEqual(resolve_workspace(self.state)["path"], self.path)

    def test_removed_repo(self):
        self.state["repos"] = []
        self.assertNotIn("path", resolve_workspace(self.state))

    def test_multiple_profiles_require_explicit_choice(self):
        with tempfile.TemporaryDirectory() as root:
            for name in ("personal", "work"):
                path = Path(root) / "profiles" / name / "orca-data.json"
                path.parent.mkdir(parents=True)
                path.write_text("{}")
            with patch.dict(os.environ, {"ORCA_USER_DATA_PATH": root}):
                with self.assertRaises(WorkspaceError):
                    discover_state()
                self.assertEqual(discover_state(profile="work").parent.name, "work")


class GitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Example Developer")
        self.git("config", "user.email", "developer@example.com")
        self.commit("Initial commit", "base.txt")

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.check_output(["git", "-c", "core.hooksPath=" + str(self.path / "no-hooks"),
                                        "-C", str(self.path), *args], stderr=subprocess.DEVNULL).decode().strip()

    def commit(self, message, name):
        (self.path / name).write_text(message, encoding="utf-8")
        self.git("add", "--", name)
        self.git("commit", "-m", message)
        return self.git("rev-parse", "HEAD")

    def test_merge_tags_files_and_multiline_message(self):
        self.git("checkout", "-b", "feature/search")
        feature = self.commit("Add search\n\nA message with <script> and a separator \x1f.", "space name.txt")
        self.git("tag", "-a", "v0.1.0", "-m", "Example release")
        self.git("checkout", "main")
        self.commit("Add docs", "guide.md")
        self.git("merge", "--no-ff", "feature/search", "-m", "Merge search")
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")
        repo = collect(self.path)
        lookup = {c["hash"]: c for c in repo["commits"]}
        self.assertEqual(len(lookup[repo["head"]]["parents"]), 2)
        self.assertIn("separator \x1f", lookup[feature]["message"])
        self.assertIn({"status": "A", "path": "space name.txt"}, lookup[feature]["files"])
        self.assertIn({"name": "feature/search", "type": "branch"}, lookup[feature]["refs"])
        self.assertIn({"name": "v0.1.0", "type": "tag"}, lookup[feature]["refs"])
        self.assertIn({"name": "origin/main", "type": "remote"}, lookup[repo["head"]]["refs"])

    @unittest.skipIf(os.name == "nt", "Windows does not support newline filenames")
    def test_newline_and_hash_shaped_filenames(self):
        name = "line\nbreak.txt"
        sha = self.commit("Add an unusual path", name)
        self.commit("Add a hash-shaped filename", sha)
        commits = collect(self.path)["commits"]
        self.assertIn({"status": "A", "path": sha}, commits[0]["files"])
        self.assertIn({"status": "A", "path": name}, commits[1]["files"])

    def test_detached_unreferenced_head_is_included(self):
        self.git("checkout", "--detach")
        sha = self.commit("Detached change", "detached.txt")
        repo = collect(self.path)
        self.assertEqual(repo["head"], sha)
        self.assertTrue(any(c["hash"] == sha for c in repo["commits"]))
        self.assertEqual(repo["branch"], "Detached HEAD")

    def test_ambient_git_dir_does_not_redirect_collection(self):
        with patch.dict(os.environ, {"GIT_DIR": "/nonexistent"}):
            self.assertEqual(collect(self.path)["name"], self.path.name)

    def test_html_script_termination_is_escaped(self):
        repo = collect(self.path)
        repo["commits"][0]["subject"] = "</script><script>window.bad=true</script>"
        page = render_html(repo)
        self.assertNotIn("</script><script>window.bad", page)
        self.assertIn("\\u003c/script>", page)

    def test_collection_does_not_change_git_state(self):
        before = self.git("status", "--porcelain"), self.git("show-ref"), self.git("rev-parse", "HEAD")
        collect(self.path)
        after = self.git("status", "--porcelain"), self.git("show-ref"), self.git("rev-parse", "HEAD")
        self.assertEqual(before, after)


class InstallationTests(unittest.TestCase):
    def test_clean_install_and_build_outside_checkout(self):
        import install
        with tempfile.TemporaryDirectory() as root:
            dest = Path(root) / "runtime with spaces"
            state = Path(root) / "orca-data.json"
            state.write_text('{"workspaceSession": {"activeWorktreeId": null}}')
            self.assertEqual(install.main(["--no-start", "--install-dir", str(dest), "--orca-state", str(state)]), 0)
            result = subprocess.run([os.sys.executable, str(dest / "run.py"), "build"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Select a Git workspace", (dest / "plugin/panel.html").read_text())
            with watcher_lock(dest / ".watcher.lock"):
                duplicate = subprocess.run([os.sys.executable, str(dest / "run.py"), "watch"], capture_output=True, text=True)
                self.assertNotEqual(duplicate.returncode, 0)
                self.assertIn("already running", duplicate.stderr)

if __name__ == "__main__":
    unittest.main()
