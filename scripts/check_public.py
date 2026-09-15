"""Check the release tree for local snapshots, private paths, and untranslated UI."""
import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
try:
    paths = [root / p for p in subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z']).decode().split('\0') if p]
except subprocess.CalledProcessError:
    paths = list(root.rglob('*'))
if not paths:
    paths = list(root.rglob('*'))
failures = []
for path in paths:
    if not path.is_file() or '.git' in path.parts or '__pycache__' in path.parts:
        continue
    if path.suffix.lower() in ('.png', '.jpg', '.zip', '.pyc'):
        continue
    text = path.read_text(encoding='utf-8')
    relative = path.relative_to(root).as_posix()
    # Match real home directories and credential-shaped strings, not placeholder examples.
    forbidden = [r"/Users/[A-Za-z0-9_.-]+/", r"/home/[A-Za-z0-9_.-]+/",
                 r"gh[o,p]_" + r"[A-Za-z0-9]{20,}"]
    if any(re.search(pattern, text) for pattern in forbidden):
        failures.append(relative + ': private path/project or token-like content')
    if re.search('[\uac00-\ud7a3]', text):
        failures.append(relative + ': non-English Korean text')
    if relative == 'plugin/panel.html' and 'const DATA=' in text:
        failures.append(relative + ': generated runtime history must not be committed')
if failures:
    raise SystemExit('\n'.join(failures))
print('Public source checks passed.')
