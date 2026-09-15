"""Generate a public demo from a temporary, entirely fictional Git repository."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from orca_git_graph.app import render_html
from orca_git_graph.git_data import collect


def build():
    with tempfile.TemporaryDirectory() as directory:
        repo = Path(directory)
        counter = 0
        def git(*args):
            return subprocess.check_output(['git', '-c', 'core.hooksPath=' + str(repo / 'no-hooks'), '-C', str(repo), *args], stderr=subprocess.DEVNULL)
        def commit(message, file):
            nonlocal counter
            counter += 1
            (repo / file).write_text(message + '\n', encoding='utf-8')
            git('add', '--', file)
            date = '2026-09-{:02d}T12:00:00+00:00'.format(counter)
            env = dict(os.environ, GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
            subprocess.check_call(['git', '-c', 'core.hooksPath=' + str(repo / 'no-hooks'), '-C', str(repo), 'commit', '-m', message], env=env, stdout=subprocess.DEVNULL)
        git('init', '-b', 'main')
        git('config', 'user.name', 'Alex Example')
        git('config', 'user.email', 'alex@example.com')
        commit('Initialize the example application', 'README.md')
        git('checkout', '-b', 'feature/search')
        commit('Add commit search and keyboard navigation', 'search.js')
        commit('Highlight matching authors and commit hashes', 'highlight.js')
        git('checkout', 'main')
        commit('Document the one-time plugin setup', 'installation.md')
        git('checkout', '-b', 'fix/worktree-switching')
        commit('Follow the exact active Git worktree', 'workspace.py')
        git('checkout', 'main')
        git('merge', '--no-ff', 'feature/search', '-m', 'Merge branch feature/search')
        git('tag', '-a', 'v0.1.0', '-m', 'Example release')
        commit('Show branches, tags, and author details', 'graph.js')
        git('update-ref', 'refs/remotes/origin/main', 'HEAD')
        git('checkout', '-b', 'feature/sidebar')
        commit('Keep Git history beside the conversation', 'panel.html')
        data = collect(repo)
        # The fixture must not contain the temporary directory or a developer identity.
        data.update(path='/example/acme-app', name='acme-app')
        for i, c in enumerate(data['commits']):
            c['at'] = c['ct'] = 1789473600 - i * 86400
        page = render_html(data, generated='2026-09-15T12:00:00+00:00')
        page = page.replace('Follows your workspace', 'Fictional interactive demo')
        (ROOT / 'docs/demo.html').write_text(page, encoding='utf-8')
        print('Built fictional demo ({} commits).'.format(len(data['commits'])))

if __name__ == '__main__':
    build()
