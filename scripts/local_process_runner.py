#!/usr/bin/env python3
"""Own one worker child and expose durable file-based stop/exit control."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--command-json", required=True)
    args = parser.parse_args()
    run_dir = Path(args.run_dir).resolve()
    command = json.loads(args.command_json)
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    with (run_dir / "stdout.log").open("ab") as stdout, (run_dir / "stderr.log").open("ab") as stderr:
        child = subprocess.Popen(command, cwd=json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))["worktree"], stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, creationflags=flags, start_new_session=os.name != "nt")
        (run_dir / "child.json").write_text(json.dumps({"pid": child.pid}) + "\n", encoding="utf-8")
        while child.poll() is None:
            if (run_dir / "stop.request").exists():
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(child.pid), "/T", "/F"], capture_output=True, check=False)
                    if child.poll() is None:
                        child.kill()
                else:
                    try:
                        os.killpg(child.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                break
            time.sleep(0.1)
        try:
            code = child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            code = child.wait(timeout=5)
    (run_dir / "exit.json").write_text(json.dumps({"returncode": code, "exited_at": datetime.now(timezone.utc).isoformat()}) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
