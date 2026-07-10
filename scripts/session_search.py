#!/usr/bin/env python3
"""Search past Loop Engineering OS sessions stored in workspace state.db."""

from __future__ import annotations

import argparse

from memory_paths import state_db
from session_store import recent_sessions, search_sessions
from workspace_utils import resolve_workspace


def main() -> int:
    parser = argparse.ArgumentParser(description="Search past sessions (SQLite FTS5).")
    parser.add_argument("--workspace", default=None, help="Product workspace path.")
    parser.add_argument("--query", "-q", default=None, help="FTS5 search query.")
    parser.add_argument("--recent", type=int, default=10, help="Show recent sessions when no query.")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    db_path = state_db(workspace)

    if args.query:
        results = search_sessions(db_path, args.query, limit=args.recent)
        if not results:
            print(f"No matches in {db_path}")
            return 0
        for row in results:
            print(f"[{row['created_at']}] {row['command'] or 'session'} — {row['title']}")
            excerpt = row["body"][:240].replace("\n", " ")
            print(f"  {excerpt}")
        return 0

    results = recent_sessions(db_path, limit=args.recent)
    if not results:
        print(f"No sessions in {db_path}")
        return 0
    for row in results:
        print(f"[{row['created_at']}] {row['command'] or 'session'} — {row['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
