#!/usr/bin/env python3
"""Inspect and validate Loop's capability registry and install profiles."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


class CapabilityRegistry:
    def __init__(self, root: Path, registry_data: dict[str, Any], profile_data: dict[str, Any]) -> None:
        self.root = root
        self.registry_data = registry_data
        self.profile_data = profile_data
        self.capabilities = {item["id"]: item for item in registry_data.get("capabilities", [])}
        self.profiles = {item["id"]: item for item in profile_data.get("profiles", [])}
        self.command_owners = self._owners("commands")
        self.skill_owners = self._owners("skills")

    @classmethod
    def load(cls, root: Path = ROOT) -> "CapabilityRegistry":
        registry = json.loads((root / "manifests" / "capabilities.json").read_text(encoding="utf-8"))
        profiles = json.loads((root / "manifests" / "install_profiles.json").read_text(encoding="utf-8"))
        return cls(root, registry, profiles)

    def _owners(self, field: str) -> dict[str, str]:
        owners: dict[str, str] = {}
        for capability in self.registry_data.get("capabilities", []):
            for name in capability.get(field, []):
                owners.setdefault(name, capability["id"])
        return owners

    def _closure(self, requested: list[str]) -> list[str]:
        resolved: set[str] = set()
        resolving: set[str] = set()

        def visit(name: str) -> None:
            if name in resolved or name in resolving or name not in self.capabilities:
                return
            resolving.add(name)
            for dependency in self.capabilities[name].get("requires", []):
                visit(dependency)
            resolving.remove(name)
            resolved.add(name)

        for name in requested:
            visit(name)
        return [name for name in self.capabilities if name in resolved]

    def validate(self) -> list[str]:
        errors: list[str] = []
        capability_ids = [item.get("id") for item in self.registry_data.get("capabilities", [])]
        for duplicate in sorted(name for name, count in Counter(capability_ids).items() if count > 1):
            errors.append(f"capability has multiple definitions: {duplicate}")

        supported = set(self.registry_data.get("supported_harnesses", []))
        for field, directory, suffix in (("commands", "commands", ".md"), ("skills", "skills", None)):
            names: list[str] = []
            for capability in self.registry_data.get("capabilities", []):
                names.extend(capability.get(field, []))
                unknown = set(capability.get("harnesses", [])) - supported
                if unknown:
                    errors.append(f"{capability['id']} declares unsupported harnesses: {', '.join(sorted(unknown))}")
                for dependency in capability.get("requires", []):
                    if dependency not in self.capabilities:
                        errors.append(f"{capability['id']} requires unknown capability: {dependency}")
            duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
            for duplicate in duplicates:
                errors.append(f"{field[:-1]} has multiple owners: {duplicate}")
            base = self.root / directory
            actual = ({path.stem for path in base.glob(f"*{suffix}")} if suffix else
                      {path.name for path in base.iterdir() if path.is_dir()})
            declared = set(names)
            for missing in sorted(actual - declared):
                errors.append(f"{field[:-1]} has no owner: {missing}")
            for stale in sorted(declared - actual):
                errors.append(f"registered {field[:-1]} does not exist: {stale}")

        visiting: set[str] = set()
        visited: set[str] = set()

        def detect(name: str, trail: list[str]) -> None:
            if name in visiting:
                errors.append(f"dependency cycle: {' -> '.join(trail + [name])}")
                return
            if name in visited or name not in self.capabilities:
                return
            visiting.add(name)
            for dependency in self.capabilities[name].get("requires", []):
                detect(dependency, trail + [name])
            visiting.remove(name)
            visited.add(name)

        for name in self.capabilities:
            detect(name, [])

        for profile in self.profile_data.get("profiles", []):
            unknown = set(profile.get("capabilities", [])) - set(self.capabilities)
            if unknown:
                errors.append(f"profile {profile['id']} contains unknown capabilities: {', '.join(sorted(unknown))}")
                continue
            plan = self.plan(profile["id"])
            if plan["context_cost"] > plan["context_budget"]:
                errors.append(f"profile {profile['id']} exceeds context budget: {plan['context_cost']} > {plan['context_budget']}")
        try:
            from skill_audit import SkillAudit, load_policy

            errors.extend(
                f"{finding['rule_id']} {finding['location']}: {finding['evidence']}"
                for finding in SkillAudit(self.root, load_policy(self.root)).validate()
            )
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"skill contracts could not be audited: {exc}")
        try:
            from agent_registry import validate as validate_agents

            errors.extend(f"agent registry: {error}" for error in validate_agents(self.root))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"agent registry could not be audited: {exc}")
        return errors

    def plan(self, profile_name: str) -> dict[str, Any]:
        if profile_name not in self.profiles:
            raise KeyError(f"unknown profile: {profile_name}")
        profile = self.profiles[profile_name]
        capabilities = self._closure(profile["capabilities"])
        return {
            "profile": profile_name,
            "capabilities": capabilities,
            "commands": sorted(name for name, owner in self.command_owners.items() if owner in capabilities),
            "skills": sorted(name for name, owner in self.skill_owners.items() if owner in capabilities),
            "context_cost": sum(self.capabilities[name]["context_cost"] for name in capabilities),
            "context_budget": profile["context_budget"],
        }

    def explain(self, name: str) -> dict[str, Any]:
        capability_id = name if name in self.capabilities else self.command_owners.get(name) or self.skill_owners.get(name)
        if not capability_id:
            raise KeyError(f"unknown capability, command, or skill: {name}")
        capability = dict(self.capabilities[capability_id])
        if name in self.skill_owners:
            try:
                from skill_audit import load_policy

                capability["selected_skill"] = name
                capability["skill_class"] = load_policy(self.root).get("assignments", {}).get(name)
            except (OSError, ValueError):
                pass
        capability["selected_by_profiles"] = [
            profile for profile in self.profiles if capability_id in self.plan(profile)["capabilities"]
        ]
        return capability

    def render_map(self) -> str:
        lines = [
            "# Capability Map",
            "",
            "Rendered from `manifests/capabilities.json`.",
            "",
            "| Capability | Requires | Commands | Skills | Cost |",
            "|---|---|---|---|---:|",
        ]
        for item in self.capabilities.values():
            lines.append(
                "| {id} | {requires} | {commands} | {skills} | {context_cost} |".format(
                    id=item["id"],
                    requires=", ".join(item["requires"]) or "—",
                    commands=", ".join(item["commands"]) or "—",
                    skills=", ".join(item["skills"]) or "—",
                    context_cost=item["context_cost"],
                )
            )
        return "\n".join(lines) + "\n"


def _print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("list", help="List registered capabilities.")
    explain = sub.add_parser("explain", help="Explain a capability, command, or skill.")
    explain.add_argument("name")
    plan = sub.add_parser("plan", help="Resolve an install profile and its dependencies.")
    plan.add_argument("profile")
    sub.add_parser("map", help="Render the command and skill ownership map.")
    sub.add_parser("doctor", help="Validate ownership, dependencies, harnesses, and budgets.")
    sub.add_parser("agents", help="List governed canonical agent roles.")
    args = parser.parse_args(argv)
    registry = CapabilityRegistry.load()
    try:
        if args.action == "list":
            _print_json([{"id": item["id"], "summary": item["summary"]} for item in registry.capabilities.values()])
        elif args.action == "explain":
            _print_json(registry.explain(args.name))
        elif args.action == "plan":
            _print_json(registry.plan(args.profile))
        elif args.action == "map":
            print(registry.render_map(), end="")
        elif args.action == "agents":
            from agent_registry import load as load_agents

            _print_json(load_agents(ROOT)["roles"])
        else:
            errors = registry.validate()
            if errors:
                for error in errors:
                    print(f"ERROR: {error}")
                return 1
            print(f"Capability registry OK: {len(registry.capabilities)} capabilities, {len(registry.command_owners)} commands, {len(registry.skill_owners)} skills, {len(registry.profiles)} profiles.")
    except KeyError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
