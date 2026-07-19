"""Loop Engineer home directory and path resolution.

Layout (all platforms: ~/.loop-engineer):

  app/                 updatable tool runtime (git clone; loop update)
  bin/                 loop CLI shim
  data/                ALL global memory/data - nothing else lives loose at the top level
    registry/          workspace registry for local products
    memories/          global product memory (when not using a local folder)
    state.db           global session store
    skills/            global user skills
    secrets.env        user secrets, if any (never commit)
    plan/main_plan.md, ...    global product state files

Local product folders mirror this under <product-folder>/.loop-engineer/ -
see workspace_resolver.py.
"""

from __future__ import annotations

import os
from pathlib import Path


def loop_home() -> Path:
    for key in ("LOOP_ENGINEER_HOME", "LOOP_HOME"):
        raw = os.environ.get(key, "").strip()
        if raw:
            return Path(raw).expanduser().resolve()
    return (Path.home() / ".loop-engineer").resolve()


def app_path() -> Path:
    return loop_home() / "app"


def runtime_path() -> Path:
    return app_path()


def bin_path() -> Path:
    return loop_home() / "bin"


def data_home() -> Path:
    """Directory holding ALL global memory/data - sibling of app/, never mixed with it."""
    return loop_home() / "data"


def registry_path() -> Path:
    return data_home() / "registry" / "workspaces.json"


def global_data_home() -> Path:
    """Directory holding global product memory and state."""
    return data_home()


def ensure_loop_home() -> Path:
    home = loop_home()
    for rel in ("app", "bin", "data", "data/registry"):
        (home / rel).mkdir(parents=True, exist_ok=True)
    return home


def describe_layout() -> str:
    home = loop_home()
    return (
        f"Loop home: {home}\n"
        f"  app/                     # updatable tool runtime\n"
        f"  bin/loop                 # CLI entry point\n"
        f"  data/                    # ALL global memory/data (nothing else lives loose here)\n"
        f"    registry/              #   registered local product folders\n"
        f"    memories/              #   global MEMORY.md, USER.md, SOUL.md\n"
        f"    state.db               #   global session search\n"
        f"    skills/                #   global procedural skills\n"
        f"    secrets.env            #   user secrets, if any (chmod 600)\n"
        f"    plan/                  #   product plan: main_plan.md + step plans\n"
        f"  <product-dir>/.loop-engineer/  # local memory when working inside a product folder\n"
    )
