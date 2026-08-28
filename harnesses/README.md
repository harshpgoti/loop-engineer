# Coding harness adapters

Each JSON file describes only what differs between coding-agent harnesses: global
skill locations, optional project locations, command namespaces, invocation syntax,
trust, hooks, and permissions. Canonical Loop behavior remains in the globally
installed app's `commands/`, `skills/`, and `scripts/` directories.

`scripts/harness_adapters.py` validates and loads these files. The skill installer
derives its destinations from that registry; do not add another harness table.

