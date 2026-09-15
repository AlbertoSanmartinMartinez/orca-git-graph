# Security and privacy

The plugin manifest requests no Orca API capabilities and has no worker entry point. A separate, user-started Python process reads the configured Orca state document and selected local Git repository. It uses read-only Git commands and writes a private HTML snapshot in its own installation directory.

There is no telemetry, external network endpoint, public server, or automatic Git fetch/push. Runtime HTML contains repository metadata such as author names/emails, commit messages, hashes, and changed-file paths. Do not publish that directory or attach unredacted snapshots to issues.

The public demo and screenshot are generated from fictional Git history. The installer does not patch Orca, change security settings, grant plugin consent, or install an operating-system startup service.

## Reporting

Use GitHub's **Security → Report a vulnerability** for a confidential report when private vulnerability reporting is enabled. For a non-sensitive issue, use the bug-report template. Never put secrets or private repository contents in a public issue.

Version 0.1.x is the initial supported release line. Orca desktop integration is experimental and was validated with Orca 1.4.185 on macOS.
