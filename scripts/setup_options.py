"""Shared setup helpers for local vs global product memory layout."""

from __future__ import annotations

from pathlib import Path

from loop_home import ensure_loop_home, global_data_home, loop_home
from workspace_resolver import LOCAL_DATA_DIRNAME, is_global_data_home, local_data_dir

MEMORY_MODES = ("local", "global")


def global_workspace_path(_name: str = "global") -> Path:
    ensure_loop_home()
    return global_data_home()


def infer_memory_mode(workspace: Path, explicit: str | None = None) -> str:
    if explicit in MEMORY_MODES:
        return explicit
    if is_global_data_home(workspace):
        return "global"
    return "local"


def _to_local_data_dir(product_folder: Path) -> Path:
    """Append .loop-engineer/ unless the path already points at one."""
    if product_folder.name == LOCAL_DATA_DIRNAME:
        return product_folder
    return local_data_dir(product_folder)


def resolve_workspace_path(
    *,
    memory_mode: str,
    workspace: str | None,
    name: str,
    root: Path,
    cwd: Path | None = None,
) -> Path:
    if memory_mode == "global":
        return global_workspace_path(name)

    if workspace:
        path = Path(workspace)
        if not path.is_absolute():
            path = root / workspace
        return _to_local_data_dir(path.resolve())

    if cwd is not None:
        return _to_local_data_dir(cwd.resolve())

    return _to_local_data_dir((root / "../product").resolve())


def describe_memory_mode(memory_mode: str, workspace: Path) -> str:
    if memory_mode == "global":
        return (
            f"Global memory: product state lives in `{workspace}` "
            f"(memories/, state.db, plan/main_plan.md, ...). Default when no local folder is detected."
        )
    return (
        f"Local memory: product state lives in `{workspace}` — a hidden "
        f"`.loop-engineer/` folder inside your product folder, kept out of your "
        f"product code. Loop auto-detects it when you return and run /plan or /loop-engine."
    )


def print_memory_mode_menu() -> None:
    print("Choose where to store product memory (plan, MEMORY.md, state.db, ...):")
    print("  1) local  — in your product development folder (recommended for multiple products)")
    print("  2) global — in ~/.loop-engineer/ (default; used when no local data is present)")
    print("")


def parse_interactive_mode(choice: str) -> str:
    normalized = choice.strip().lower()
    if normalized in {"1", "local", "l", "product"}:
        return "local"
    if normalized in {"2", "global", "g", ""}:
        return "global"
    raise ValueError(f"Invalid memory mode choice: {choice!r}")
