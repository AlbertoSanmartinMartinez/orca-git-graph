"""Generate plain-text documentation mirrors from their canonical Markdown sources."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
readme = (root / "README.md").read_text(encoding="utf-8")
# Resolve repository-relative links for the Markdown page hosted at the site root.
readme = readme.replace('](docs/', '](').replace('(docs/assets/', '(assets/')
for name in ('AGENTS.md', 'CONTRIBUTING.md', 'SECURITY.md', 'CHANGELOG.md', 'LICENSE'):
    readme = readme.replace('](' + name + ')', '](https://github.com/pty0220/orca-git-graph/blob/main/' + name + ')')
(root / "docs/index.md").write_text(readme, encoding="utf-8")
(root / "docs/llms.txt").write_text((root / "llms.txt").read_text(encoding="utf-8"), encoding="utf-8")
parts = [readme] + [(root / "docs" / name).read_text(encoding="utf-8") for name in
                     ('installation.md', 'architecture.md', 'troubleshooting.md', 'faq.md')]
(root / "docs/llms-full.txt").write_text('\n\n---\n\n'.join(parts), encoding="utf-8")
