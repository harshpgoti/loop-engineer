#!/usr/bin/env python3
"""Background loop for the persistent local execution supervisor."""

from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone
from pathlib import Path

from execution_runtime import ExecutionRuntime
from execution_supervisor import _write


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--workspace", required=True); parser.add_argument("--generation", type=int, required=True); parser.add_argument("--token", required=True)
    args = parser.parse_args(); workspace = Path(args.workspace).resolve(); root = workspace / "workers"; runtime = ExecutionRuntime(workspace)
    while True:
        stop = root / "supervisor.stop"
        if stop.exists() and f"token={args.token}" in stop.read_text(encoding="utf-8", errors="ignore"):
            break
        try:
            result = runtime.supervisor_tick()
            payload = {"generation": args.generation, "token": args.token, "heartbeat_at": datetime.now(timezone.utc).isoformat(), "last_tick": result}
        except Exception as exc:
            payload = {"generation": args.generation, "token": args.token, "heartbeat_at": datetime.now(timezone.utc).isoformat(), "error": str(exc)[:500]}
        _write(root / "supervisor-heartbeat.json", payload)
        policy = runtime._quota_policy()
        time.sleep(max(1, int(policy["poll_seconds"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
