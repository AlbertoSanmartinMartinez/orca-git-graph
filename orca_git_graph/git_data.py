"""Read-only Git history collection. No shell commands, fetches, or repository writes."""
import os
import re
import subprocess
from pathlib import Path


class GitError(RuntimeError):
    pass


def git(path, *args):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    # Ambient Git overrides can point a process at a different repository.
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"):
        env.pop(key, None)
    try:
        result = subprocess.run(
            ["git", "--no-pager", "-C", str(path), *args], env=env,
            capture_output=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise GitError(str(error)) from error
    if result.returncode:
        raise GitError(result.stderr.decode("utf-8", "replace").strip())
    return result.stdout.decode("utf-8", "replace")


def fingerprint(path):
    return (git(path, "rev-parse", "--verify", "HEAD"),
            git(path, "symbolic-ref", "--quiet", "--short", "HEAD") if git(path, "branch", "--show-current").strip() else "",
            git(path, "for-each-ref", "--format=%(refname) %(objectname)"))


def read_commits(path, limit):
    # NUL-delimited fields preserve multiline messages and literal separator characters.
    fields = ["%H", "%P", "%an", "%ae", "%at", "%ct", "%s", "%B"]
    raw = git(path, "log", "--all", "HEAD", "--topo-order", "--no-show-signature",
              "--max-count=" + str(limit), "--format=" + "%x00".join(fields) + "%x00")
    tokens = raw.split("\0")
    commits = []
    for i in range(0, len(tokens) - 7, 8):
        sha, parents, author, email, authored, committed, subject, body = tokens[i:i+8]
        commits.append(dict(hash=sha.strip(), parents=parents.split(), an=author, ae=email,
                            at=int(authored), ct=int(committed), subject=subject,
                            message=body.strip(), refs=[], files=[]))
    # File records have a distinct empty-token + hash + empty-token header.
    # Rename detection is disabled for predictable cost on large repositories.
    raw = git(path, "log", "--all", "HEAD", "--topo-order", "--no-show-signature",
              "--max-count=" + str(limit), "--format=%x00%H%x00", "--name-status", "--no-renames", "-z")
    tokens = raw.split("\0")
    lookup = {c["hash"]: c for c in commits}
    i, current = 0, None
    while i < len(tokens):
        if tokens[i] == "" and i+2 < len(tokens) and tokens[i+1] in lookup and tokens[i+2] == "":
            current = lookup[tokens[i+1]]
            i += 3
        elif current is not None and re.fullmatch(r"[ACDMTUXB]", tokens[i].strip("\n")) and i+1 < len(tokens):
            if len(current["files"]) < 200:
                current["files"].append({"status": tokens[i].strip("\n"), "path": tokens[i+1]})
            else:
                current["filesTruncated"] = True
            i += 2
        else:
            i += 1
    return commits


def collect(path, limit=400):
    head = git(path, "rev-parse", "--verify", "HEAD").strip()
    commits = read_commits(path, limit)
    lookup = {c["hash"]: c for c in commits}
    branch = git(path, "branch", "--show-current").strip() or "Detached HEAD"
    refs = []
    for line in git(path, "for-each-ref", "--format=%(refname)%09%(objectname)%09%(*objectname)").splitlines():
        full, sha, peeled = line.split("\t")
        prefix = next((p for p in ("refs/heads/", "refs/remotes/", "refs/tags/") if full.startswith(p)), "refs/")
        name = full[len(prefix):]
        kind = {"refs/heads/": "branch", "refs/remotes/": "remote", "refs/tags/": "tag"}.get(prefix, "branch")
        target = peeled or sha
        refs.append({"name": name, "hash": target})
        if target in lookup:
            lookup[target]["refs"].append({"name": name, "type": "head" if kind == "branch" and name == branch else kind})
    if branch == "Detached HEAD" and head in lookup:
        lookup[head]["refs"].insert(0, {"name": "detached", "type": "head"})
    try:
        upstream = git(path, "rev-parse", "--abbrev-ref", "@{upstream}").strip()
        ahead, behind = map(int, git(path, "rev-list", "--left-right", "--count", "HEAD...@{upstream}").split())
    except GitError:
        upstream, ahead, behind = None, 0, 0
    return dict(path=str(path), name=Path(path).name, commits=commits, head=head,
                branch=branch, refs=refs, upstream=upstream, ahead=ahead, behind=behind)
