#!/usr/bin/env python3
"""
Maintenance-time generator for canonical mode, rule, and shortcut files.

Inputs:
- aias/.canonical/*.mdc (mode templates)
- aias/.canonical/base-rule.md (canonical base rule)
- aias/.canonical/output-contract.md (canonical output contract)
- <repo_root>/stack-fragment.md (build system integration — one per repo)
- aias/.canonical/delivery.mdc, devops.mdc (transversal mode templates — rendered with defaults or stack-profile bindings)
- <repo_root>/stack-profile.md (one per repo)

Outputs (canonical — always produced):
- aias-config/modes/*.mdc (generated platform modes)
- aias-config/rules/base.mdc, output-contract.mdc (flat, from last workspace processed)

Outputs (shortcuts — only with --shortcuts flag):
- .cursor/rules/*.mdc (rules + modes)
- .cursor/skills/<name>/SKILL.md (skills)
- .claude/rules/*.md (rules + modes with paths:)
- .claude/skills/<name>/SKILL.md (skills)
- .windsurf/rules/*.md (always-apply rules only)
- .github/copilot-instructions.md (aggregated rules)
- .github/instructions/*.instructions.md (modes with applyTo:)
- .github/agents/*.md (command-shaped skills → aias/.skills/<name>/SKILL.md)
- .codex/commands/*.md (command-shaped skills → aias/.skills/<name>/SKILL.md)
- .agents/skills/<name>/SKILL.md (skills)

Pre-flight validation:
  G0 — Infrastructure: templates, fragment file, canonical mode templates exist
  G1 — Profile Discovery: stack-profile.md exists at repo root, bindings parse
  G2 — Mode Binding Completeness: all required mode bindings present per profile
  G3 — Rule Binding Completeness: all required base + output_contract bindings present per workspace
  G4 — Fragment Validation: stack-fragment.md exists at repo root, non-empty, has UPPERCASE header
  G5 — Output Directory: aias-config/rules/ and aias-config/modes/ exist or can be created
  G6 — Shortcut Consistency: every canonical file has corresponding shortcuts for all supported tools (only with --shortcuts)
  G7 — No Content Duplication: no shortcut file exceeds threshold length (only with --shortcuts)
"""

from __future__ import annotations

import argparse
import os
import pathlib
import re
import sys
from typing import Dict, List, Optional, Tuple


_DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[3]


class Paths:
    """Resolved filesystem paths. Reconfigurable via init_paths() for testing."""
    root = _DEFAULT_ROOT
    canonical_dir = _DEFAULT_ROOT / "aias" / ".canonical"
    stack_fragment = _DEFAULT_ROOT / "stack-fragment.md"
    rules_output = _DEFAULT_ROOT / "aias-config" / "rules"
    modes_output = _DEFAULT_ROOT / "aias-config" / "modes"
    fw_skills = _DEFAULT_ROOT / "aias" / ".skills"
    project_skills = _DEFAULT_ROOT / "aias-config" / "skills"


def init_paths(root: pathlib.Path) -> None:
    """Reconfigure all paths for a different root. Used by tests."""
    Paths.root = root
    Paths.canonical_dir = root / "aias" / ".canonical"
    Paths.stack_fragment = root / "stack-fragment.md"
    Paths.rules_output = root / "aias-config" / "rules"
    Paths.modes_output = root / "aias-config" / "modes"
    Paths.fw_skills = root / "aias" / ".skills"
    Paths.project_skills = root / "aias-config" / "skills"

MODE_NAMES = ("planning", "dev", "qa", "debug", "review", "product", "integration", "delivery", "devops")
TRANSVERSAL_RULES = ("continuous-improvement",)

# Canonical artifact-suffix requirements per mode.
# "required" must always be present; "optional" are validated only for catalog coherence.
MODE_ARTIFACT_GLOB_RULES: Dict[str, Dict[str, Tuple[str, ...]]] = {
    "planning": {"required": (), "optional": ("*.product.md", "*.issue.md", "*.fix.md", "*.assessment.md", "*.plan.md", "*.design.md")},
    "product": {"required": (), "optional": ("*.product.md", "*.design.md", "*.plan.md", "*.issue.md", "*.fix.md", "*.assessment.md")},
    "dev": {"required": ("*.plan.md",), "optional": ("*.design.md", "*.product.md", "*.fix.md", "*.assessment.md", "*.trace.md", "*.issue.md")},
    "qa": {"required": ("*.issue.md",), "optional": ("*.trace.md", "*.plan.md")},
    "debug": {"required": ("*.issue.md",), "optional": ("*.fix.md", "*.plan.md")},
    "review": {"required": ("*.plan.md",), "optional": ("*.design.md", "*.product.md")},
    "delivery": {"required": ("*.charter.md",), "optional": ("*.plan.md", "*.product.md")},
    "integration": {"required": ("*.plan.md",), "optional": ()},
    "devops": {"required": ("*.plan.md",), "optional": ()},
}

TRANSVERSAL_MODE_DEFAULTS: Dict[str, Dict[str, str]] = {
    "delivery": {
        "description": "Delivery mode: evaluate plans or tickets for viability, effort, impact, dependencies, and risks; produce raw delivery data for /charter (no implementation design)",
        "model": "opus-4.6",
        "color": "indigo",
        "globs": "*.charter.md, *.plan.md, *.product.md",
    },
    "devops": {
        "description": "DevOps mode: CI/CD pipeline configuration, private dependency resolution, build orchestration, and secrets management across any CI platform",
        "model": "sonnet-4.6",
        "color": "slate",
        "globs": "*.plan.md, *.yml, *.yaml",
    },
}
ALWAYS_APPLY_RULES = ("base", "output-contract", "continuous-improvement")

SUPPORTED_TOOLS = ("cursor", "claude", "windsurf", "copilot", "codex", "gemini")

RULE_GENERATION_SKIP = {"xctemplates-dev"}

BASE_RULE_REQUIRED_KEYS = (
    "description",
    "role_specialty",
    "conversation_language",
    "engineering_domain_principle",
    "security_line",
    "performance_line",
    "assumptions_domain",
    "limitations_truthfulness_line",
    "platform_limitations",
    "styleguide_paths",
)

OUTPUT_CONTRACT_REQUIRED_KEYS = (
    "environment",
    "documentation_tool",
    "linter",
    "testing",
)

MODE_FRONTMATTER_KEYS = ("description", "model", "color", "globs")

SHORTCUT_MAX_LEN = 500


def _create_symlink(link_path: pathlib.Path, target_path: pathlib.Path) -> None:
    """Create a relative symlink. Idempotent: removes existing file or symlink first."""
    rel_target = os.path.relpath(target_path, link_path.parent)
    if link_path.is_symlink() or link_path.exists():
        link_path.unlink()
    link_path.parent.mkdir(parents=True, exist_ok=True)
    link_path.symlink_to(rel_target)


def _extract_description(canonical_path: pathlib.Path) -> str:
    """Extract the description field from a canonical file's YAML frontmatter."""
    if not canonical_path.is_file():
        return ""
    text = canonical_path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---\n", 4)
    if end == -1:
        return ""
    for line in text[4:end].split("\n"):
        if line.startswith("description:"):
            desc = line[len("description:"):].strip().strip('"')
            if len(desc) > 120:
                return desc[:117] + "..."
            return desc
    return ""


def _read_skill_frontmatter(skill_md_path: pathlib.Path) -> Dict[str, str]:
    """Parse YAML frontmatter from a SKILL.md file. Returns dict of key→value strings.

    Only handles simple scalar string values (no nested YAML). This is sufficient
    for the fields relevant to shortcut generation (category, disable-model-invocation).
    """
    if not skill_md_path.is_file():
        return {}
    text = skill_md_path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    result: Dict[str, str] = {}
    for line in text[4:end].split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip()] = val.strip().strip('"')
    return result


def _is_command_skill(skill_dir: pathlib.Path) -> bool:
    """Return True if a skill directory contains a command-shaped skill.

    A command-shaped skill has:
      - disable-model-invocation: true
      - category: advisory | operative
    """
    fm = _read_skill_frontmatter(skill_dir / "SKILL.md")
    return (
        fm.get("disable-model-invocation", "").lower() == "true"
        and fm.get("category", "") in ("advisory", "operative")
    )


# ---------------------------------------------------------------------------
# Pre-flight validation
# ---------------------------------------------------------------------------

def preflight_validation(profiles: List[pathlib.Path]) -> List[str]:
    """Run all validation gates. Returns a list of error strings (empty = OK)."""
    errors: List[str] = []
    errors.extend(_gate_0_infrastructure())

    profile_bindings: List[Tuple[pathlib.Path, Dict[str, str]]] = []
    g1_errors, profile_bindings = _gate_1_profile_discovery(profiles)
    errors.extend(g1_errors)

    if profile_bindings:
        errors.extend(_gate_2_mode_bindings(profile_bindings))
        errors.extend(_gate_3_rule_bindings(profile_bindings))
        errors.extend(_gate_4_fragment_validation(profile_bindings))

    errors.extend(_gate_5_output_directories())

    return errors


def _gate_0_infrastructure() -> List[str]:
    """G0: Verify templates, stack-fragment.md, and canonical mode templates exist."""
    errors: List[str] = []

    base_tpl = Paths.canonical_dir / "base-rule.md"
    if not base_tpl.is_file():
        errors.append(
            f"[G0] Missing canonical base rule: {base_tpl.relative_to(Paths.root)}\n"
            f"      → Create it following aias/contracts/readme-base-rule.md"
        )

    oc_tpl = Paths.canonical_dir / "output-contract.md"
    if not oc_tpl.is_file():
        errors.append(
            f"[G0] Missing canonical output contract: {oc_tpl.relative_to(Paths.root)}\n"
            f"      → Create it following aias/contracts/readme-output-contract.md"
        )

    if not Paths.stack_fragment.is_file():
        errors.append(
            f"[G0] Missing stack fragment: {Paths.stack_fragment.relative_to(Paths.root)}\n"
            f"      → Create stack-fragment.md at repo root (see aias/contracts/readme-output-contract.md § Fragment Structure Options)"
        )

    for mode_name in MODE_NAMES:
        mode_path = Paths.canonical_dir / f"{mode_name}.mdc"
        if not mode_path.is_file():
            errors.append(
                f"[G0] Missing canonical mode template: {mode_path.relative_to(Paths.root)}\n"
                f"      → Create the template for mode '{mode_name}'"
            )

    if base_tpl.is_file():
        content = base_tpl.read_text(encoding="utf-8")
        if "```markdown" not in content:
            errors.append(
                "[G0] base-rule.md has no ```markdown code block\n"
                "      → Canonical content must be wrapped in a markdown code block"
            )

    if oc_tpl.is_file():
        content = oc_tpl.read_text(encoding="utf-8")
        if "```markdown" not in content:
            errors.append(
                "[G0] output-contract.md has no ```markdown code block\n"
                "      → Canonical content must be wrapped in a markdown code block"
            )

    return errors


def _gate_1_profile_discovery(
    profiles: List[pathlib.Path],
) -> Tuple[List[str], List[Tuple[pathlib.Path, Dict[str, str]]]]:
    """G1: Verify stack profiles exist, are readable, and contain bindings."""
    errors: List[str] = []
    result: List[Tuple[pathlib.Path, Dict[str, str]]] = []

    if not profiles:
        errors.append(
            "[G1] No stack-profile.md found at repo root.\n"
            "      → Create stack-profile.md at repo root with binding.* entries"
        )
        return errors, result

    for profile in profiles:
        if not profile.is_file():
            errors.append(f"[G1] Stack profile not readable: {profile.relative_to(Paths.root)}")
            continue
        try:
            bindings = load_bindings(profile)
        except ValueError as e:
            errors.append(f"[G1] {e}")
            continue

        if "generation.stack_id" not in bindings:
            errors.append(
                f"[G1] Missing binding.generation.stack_id in {profile.relative_to(Paths.root)}\n"
                f"      → Add: - `binding.generation.stack_id`: `<id>`"
            )
        if "generation.mode_output_dir" in bindings:
            errors.append(
                f"[G1] Deprecated binding.generation.mode_output_dir in {profile.relative_to(Paths.root)}\n"
                f"      → Remove it and use binding.generation.canonical_mode_output_dir instead"
            )
        for _canon_key, _canon_expected, _canon_legacy in [
            ("generation.canonical_mode_output_dir", "aias-config/modes", "aias/.modes"),
            ("generation.canonical_rule_output_dir", "aias-config/rules", "aias/.rules"),
        ]:
            if _canon_key not in bindings:
                errors.append(
                    f"[G1] Missing binding.{_canon_key} in {profile.relative_to(Paths.root)}\n"
                    f"      → Add: - `binding.{_canon_key}`: `{_canon_expected}`"
                )
            else:
                _canon_val = bindings[_canon_key].strip()
                if _canon_val == _canon_legacy:
                    errors.append(
                        f"[G1] Legacy binding.{_canon_key} = '{_canon_legacy}' in {profile.relative_to(Paths.root)}\n"
                        f"      → Update to: `{_canon_expected}`"
                    )
                elif _canon_val != _canon_expected:
                    errors.append(
                        f"[G1] Invalid binding.{_canon_key} in {profile.relative_to(Paths.root)}\n"
                        f"      → Must be: `{_canon_expected}`"
                    )
        if "generation.tools" not in bindings:
            errors.append(
                f"[G1] Missing binding.generation.tools in {profile.relative_to(Paths.root)}\n"
                f"      → Add: - `binding.generation.tools`: `cursor` (or comma-separated list)"
            )
        else:
            tools_raw = bindings["generation.tools"]
            tools_list = [t.strip() for t in tools_raw.split(",") if t.strip()]
            invalid = [t for t in tools_list if t not in SUPPORTED_TOOLS]
            if invalid:
                errors.append(
                    f"[G1] Invalid tool(s) in binding.generation.tools: {', '.join(invalid)}\n"
                    f"      → Valid values: {', '.join(SUPPORTED_TOOLS)}"
                )
            if not tools_list:
                errors.append(
                    f"[G1] binding.generation.tools is empty in {profile.relative_to(Paths.root)}\n"
                    f"      → At least one tool must be specified"
                )
        if "generation.tasks_dir" not in bindings:
            errors.append(
                f"[G1] Missing binding.generation.tasks_dir in {profile.relative_to(Paths.root)}\n"
                f"      → Add: - `binding.generation.tasks_dir`: `~/.cursor/plans/`"
            )
        result.append((profile, bindings))

    return errors, result


def _gate_2_mode_bindings(
    profile_bindings: List[Tuple[pathlib.Path, Dict[str, str]]],
) -> List[str]:
    """G2: Verify all required mode bindings are present for every profile.
    Transversal modes (delivery, devops) have built-in defaults so missing
    bindings are acceptable — they will use TRANSVERSAL_MODE_DEFAULTS."""
    errors: List[str] = []

    for profile, bindings in profile_bindings:
        rel = profile.relative_to(Paths.root)
        for mode in MODE_NAMES:
            defaults = TRANSVERSAL_MODE_DEFAULTS.get(mode, {})
            for field in MODE_FRONTMATTER_KEYS:
                key = f"mode.{mode}.{field}"
                has_binding = key in bindings and bindings[key].strip()
                has_default = field in defaults
                if not has_binding and not has_default:
                    errors.append(
                        f"[G2] Missing binding.{key} in {rel}\n"
                        f"      → Add: - `binding.{key}`: `<value>`"
                    )
    return errors


def _gate_3_rule_bindings(
    profile_bindings: List[Tuple[pathlib.Path, Dict[str, str]]],
) -> List[str]:
    """G3: Verify all required base + output_contract bindings for every workspace."""
    errors: List[str] = []

    for profile, bindings in profile_bindings:
        rel = profile.relative_to(Paths.root)
        shared_prefix = detect_shared_prefix(bindings)
        workspace_ids = discover_rule_workspaces(bindings)

        if not workspace_ids:
            errors.append(
                f"[G3] No rule workspaces discovered in {rel}\n"
                f"      → Add binding.rule.base.<ws_id>.description entries"
            )
            continue

        for ws_id in workspace_ids:
            for key in BASE_RULE_REQUIRED_KEYS:
                value = _resolve_binding(bindings, ws_id, "base", key, shared_prefix)
                if value is None:
                    errors.append(
                        f"[G3] Missing base rule binding for '{ws_id}': binding.rule.base.{ws_id}.{key}\n"
                        f"      → Add to {rel} (workspace, shared, or platform level)"
                    )

            for key in OUTPUT_CONTRACT_REQUIRED_KEYS:
                value = _resolve_binding(bindings, ws_id, "output_contract", key, shared_prefix)
                if value is None:
                    errors.append(
                        f"[G3] Missing output contract binding for '{ws_id}': binding.rule.output_contract.{ws_id}.{key}\n"
                        f"      → Add to {rel} (workspace, shared, or platform level)"
                    )

            profile_key = f"rule.output_contract.{ws_id}.profile"
            if profile_key not in bindings:
                errors.append(
                    f"[G3] Missing canonical profile for '{ws_id}': binding.{profile_key}\n"
                    f"      → Add: - `binding.{profile_key}`: `<profile-id>`"
                )

    return errors


def _gate_4_fragment_validation(
    profile_bindings: List[Tuple[pathlib.Path, Dict[str, str]]],
) -> List[str]:
    """G4: Verify stack-fragment.md exists at repo root and is valid."""
    errors: List[str] = []

    if not Paths.stack_fragment.is_file():
        errors.append(
            f"[G4] Missing stack fragment: {Paths.stack_fragment.relative_to(Paths.root)}\n"
            f"      → Create stack-fragment.md at repo root (see aias/contracts/readme-output-contract.md § Fragment Structure Options)"
        )
    elif Paths.stack_fragment.stat().st_size == 0:
        errors.append(
            f"[G4] Empty stack fragment: {Paths.stack_fragment.relative_to(Paths.root)}\n"
            f"      → Fill with build system integration content (see aias/contracts/readme-output-contract.md § Fragment Structure Options)"
        )
    else:
        content = Paths.stack_fragment.read_text(encoding="utf-8").strip()
        has_uppercase_header = bool(re.search(r"^[A-Z][A-Z /()]+", content, re.MULTILINE))
        if not has_uppercase_header:
            errors.append(
                f"[G4] Fragment missing section header: {Paths.stack_fragment.relative_to(Paths.root)}\n"
                f"      → Fragment must contain at least one UPPERCASE section header"
            )

    return errors


def _gate_5_output_directories() -> List[str]:
    """G5: Verify output directories exist or can be created."""
    errors: List[str] = []
    for d in (Paths.rules_output, Paths.modes_output):
        if not d.is_dir():
            try:
                d.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                errors.append(
                    f"[G5] Cannot create output directory: {d.relative_to(Paths.root)}\n"
                    f"      → {e}"
                )
    return errors


def _resolve_binding(
    bindings: Dict[str, str],
    ws_id: str,
    category: str,
    key: str,
    shared_prefix: Optional[str],
) -> Optional[str]:
    """Check binding resolution without unescaping (for validation only)."""
    ws_key = f"rule.{category}.{ws_id}.{key}"
    if ws_key in bindings:
        return bindings[ws_key]
    if shared_prefix:
        shared_key = f"rule.{category}.{shared_prefix}.{key}"
        if shared_key in bindings:
            return bindings[shared_key]
    platform_key = f"rule.{category}.{key}"
    if platform_key in bindings:
        return bindings[platform_key]
    return None


# ---------------------------------------------------------------------------
# Tool resolution
# ---------------------------------------------------------------------------

def _resolve_tools(
    args_tools: Optional[str],
    all_bindings: List[Tuple[pathlib.Path, Dict[str, str]]],
) -> List[str]:
    """Resolve target tools: --tools flag overrides binding."""
    if args_tools:
        return [t.strip() for t in args_tools.split(",") if t.strip()]
    for _profile, bindings in all_bindings:
        if "generation.tools" in bindings:
            return [t.strip() for t in bindings["generation.tools"].split(",") if t.strip()]
    return list(SUPPORTED_TOOLS)


# ---------------------------------------------------------------------------
# Post-generation validation (only when --shortcuts is active)
# ---------------------------------------------------------------------------

def postflight_validation(generated_modes: List[str], tools: List[str]) -> List[str]:
    """G6 + G7: Validate shortcuts after generation."""
    errors: List[str] = []
    errors.extend(_gate_6_shortcut_consistency(generated_modes, tools))
    errors.extend(_gate_7_no_duplication(tools))
    return errors


def _check_shortcut_exists(path: pathlib.Path, label: str, errors: List[str]) -> None:
    """Check that a shortcut exists; report broken symlinks specifically."""
    if path.is_symlink() and not path.exists():
        errors.append(f"[G6] Broken symlink for {label}: {path.relative_to(Paths.root)}")
    elif not path.is_file():
        errors.append(f"[G6] Missing shortcut for {label}: {path.relative_to(Paths.root)}")


def _gate_6_shortcut_consistency(generated_modes: List[str], tools: List[str]) -> List[str]:
    """G6: Canonical artifacts should have corresponding shortcuts for listed tools only."""
    errors: List[str] = []

    cursor_rules_dir = Paths.root / ".cursor" / "rules"
    claude_rules_dir = Paths.root / ".claude" / "rules"
    windsurf_rules_dir = Paths.root / ".windsurf" / "rules"

    for base_rule in ("base", "output-contract"):
        if "cursor" in tools:
            _check_shortcut_exists(cursor_rules_dir / f"{base_rule}.mdc", f"Cursor rule: {base_rule}", errors)
        if "claude" in tools:
            _check_shortcut_exists(claude_rules_dir / f"{base_rule}.md", f"Claude Code rule: {base_rule}", errors)
        if "windsurf" in tools:
            _check_shortcut_exists(windsurf_rules_dir / f"{base_rule}.md", f"Windsurf rule: {base_rule}", errors)

    ci_rule = "continuous-improvement"
    if (Paths.rules_output / f"{ci_rule}.mdc").is_file():
        if "cursor" in tools:
            _check_shortcut_exists(cursor_rules_dir / f"{ci_rule}.mdc", f"Cursor rule: {ci_rule}", errors)
        if "claude" in tools:
            _check_shortcut_exists(claude_rules_dir / f"{ci_rule}.md", f"Claude Code rule: {ci_rule}", errors)
        if "windsurf" in tools:
            _check_shortcut_exists(windsurf_rules_dir / f"{ci_rule}.md", f"Windsurf rule: {ci_rule}", errors)

    if "copilot" in tools:
        copilot_instructions = Paths.root / ".github" / "copilot-instructions.md"
        _check_shortcut_exists(copilot_instructions, "GitHub Copilot copilot-instructions.md", errors)

    for mode_name in generated_modes:
        if "cursor" in tools:
            _check_shortcut_exists(cursor_rules_dir / f"{mode_name}.mdc", f"Cursor mode: {mode_name}", errors)
        if "claude" in tools:
            _check_shortcut_exists(claude_rules_dir / f"{mode_name}.md", f"Claude Code mode: {mode_name}", errors)
        if "copilot" in tools:
            copilot_mode = Paths.root / ".github" / "instructions" / f"{mode_name}.instructions.md"
            _check_shortcut_exists(copilot_mode, f"GitHub Copilot mode: {mode_name}", errors)

    # G6 for command-shaped skills (advisory/operative with disable-model-invocation: true)
    # Cursor: command-shaped skills go into .cursor/skills/ (same as other skills) — no .cursor/commands/ check.
    # Copilot and Codex: still use their respective commands directories.
    for skills_dir in (Paths.fw_skills, Paths.project_skills):
        if not skills_dir.is_dir():
            continue
        for skill_dir in sorted(skills_dir.iterdir()):
            if skill_dir.is_dir() and _is_command_skill(skill_dir):
                name = f"{skill_dir.name}.md"
                if "copilot" in tools:
                    _check_shortcut_exists(Paths.root / ".github" / "agents" / name, f"Copilot command: {name}", errors)
                if "codex" in tools:
                    _check_shortcut_exists(Paths.root / ".codex" / "commands" / name, f"Codex command: {name}", errors)

    for skills_dir in (Paths.fw_skills, Paths.project_skills):
        if not skills_dir.is_dir():
            continue
        for skill_dir in sorted(skills_dir.iterdir()):
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").is_file():
                sname = skill_dir.name
                if "cursor" in tools:
                    _check_shortcut_exists(Paths.root / ".cursor" / "skills" / sname / "SKILL.md", f"Cursor skill: {sname}", errors)
                if "claude" in tools:
                    _check_shortcut_exists(Paths.root / ".claude" / "skills" / sname / "SKILL.md", f"Claude Code skill: {sname}", errors)
                if "codex" in tools:
                    _check_shortcut_exists(Paths.root / ".agents" / "skills" / sname / "SKILL.md", f"Codex skill: {sname}", errors)

    return errors


def _gate_7_no_duplication(tools: List[str]) -> List[str]:
    """G7: No enriched text shortcut should exceed threshold length. Symlinks are exempt."""
    errors: List[str] = []

    _TOOL_DIRS: Dict[str, List[pathlib.Path]] = {
        "cursor": [
            Paths.root / ".cursor" / "rules",
            Paths.root / ".cursor" / "skills",
        ],
        "claude": [
            Paths.root / ".claude" / "rules",
            Paths.root / ".claude" / "skills",
        ],
        "windsurf": [
            Paths.root / ".windsurf" / "rules",
        ],
        "copilot": [
            Paths.root / ".github" / "instructions",
            Paths.root / ".github" / "agents",
        ],
        "codex": [
            Paths.root / ".codex" / "commands",
            Paths.root / ".agents" / "skills",
        ],
    }

    shortcut_dirs: List[pathlib.Path] = []
    for tool in tools:
        shortcut_dirs.extend(_TOOL_DIRS.get(tool, []))

    single_files: List[pathlib.Path] = []
    if "copilot" in tools:
        single_files.append(Paths.root / ".github" / "copilot-instructions.md")

    for d in shortcut_dirs:
        if not d.is_dir():
            continue
        for f in d.rglob("*.md"):
            if f.is_symlink():
                continue
            if f.is_file():
                size = f.stat().st_size
                if size > SHORTCUT_MAX_LEN:
                    errors.append(
                        f"[G7] Shortcut too large ({size} bytes): {f.relative_to(Paths.root)}\n"
                        f"      → Enriched text shortcut must be <{SHORTCUT_MAX_LEN} bytes"
                    )
        for f in d.rglob("*.mdc"):
            if f.is_symlink():
                continue
            if f.is_file():
                size = f.stat().st_size
                if size > SHORTCUT_MAX_LEN:
                    errors.append(
                        f"[G7] Shortcut too large ({size} bytes): {f.relative_to(Paths.root)}\n"
                        f"      → Enriched text shortcut must be <{SHORTCUT_MAX_LEN} bytes"
                    )

    for f in single_files:
        if f.is_file():
            size = f.stat().st_size
            if size > SHORTCUT_MAX_LEN * 3:
                errors.append(
                    f"[G7] Aggregated shortcut too large ({size} bytes): {f.relative_to(Paths.root)}\n"
                    f"      → Should only contain enriched path references"
                )

    return errors


# ---------------------------------------------------------------------------
# Binding loading
# ---------------------------------------------------------------------------

def load_bindings(profile_path: pathlib.Path) -> Dict[str, str]:
    bindings: Dict[str, str] = {}
    for line in profile_path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"- `binding\.([^`]+)`: `(.*)`$", line.strip())
        if match:
            bindings[match.group(1)] = match.group(2)
    if not bindings:
        raise ValueError(f"No generation bindings found in {profile_path}")
    return bindings


def unescape_binding(value: str) -> str:
    result = value.replace("\\n", "\n").replace("\\`", "`")
    return result


def discover_profiles() -> List[pathlib.Path]:
    """Discover the single stack-profile.md at repo root."""
    profile_path = Paths.root / "stack-profile.md"
    if not profile_path.is_file():
        raise ValueError(
            "No stack-profile.md found at repo root.\n"
            "Create stack-profile.md at repo root with binding.* entries."
        )
    return [profile_path]


# ---------------------------------------------------------------------------
# Mode generation
# ---------------------------------------------------------------------------

def mode_frontmatter_from_bindings(bindings: Dict[str, str], mode: str) -> Dict[str, str]:
    required = ("description", "model", "color", "globs")
    defaults = TRANSVERSAL_MODE_DEFAULTS.get(mode, {})
    result: Dict[str, str] = {}
    for field in required:
        key = f"mode.{mode}.{field}"
        if key in bindings and bindings[key].strip():
            result[field] = bindings[key]
        elif field in defaults:
            result[field] = defaults[field]
        else:
            raise KeyError(f"Missing binding key: binding.{key}")
    return result


def normalize_globs_yaml(raw_globs: str) -> str:
    items = [item.strip() for item in raw_globs.split(",") if item.strip()]
    if not items:
        raise ValueError("Mode globs cannot be empty after normalization.")
    return "\n".join(f'  - "{item}"' for item in items)


def validate_mode_glob_coverage(mode: str, raw_globs: str) -> None:
    """Fail fast when mode globs use unknown artifact suffixes."""
    rules = MODE_ARTIFACT_GLOB_RULES.get(mode)
    if not rules:
        return
    current = {item.strip() for item in raw_globs.split(",") if item.strip()}
    allowed = set(rules.get("required", ())) | set(rules.get("optional", ()))
    configured_artifact_globs = {
        item for item in current if re.match(r"^\*\.[a-z0-9-]+\.md$", item)
    }
    unknown = sorted(glob for glob in configured_artifact_globs if glob not in allowed)
    if unknown:
        raise ValueError(
            f"Mode '{mode}' has non-canonical artifact globs: {', '.join(unknown)}"
        )


def render_conditionals(content: str, context: Dict[str, str]) -> str:
    pattern = re.compile(r"\{\{#if ([^}]+)\}\}(.*?)\{\{/if\}\}", re.DOTALL)
    while True:
        match = pattern.search(content)
        if not match:
            return content
        key = match.group(1).strip()
        block = match.group(2)
        value = context.get(key, "false").strip().lower()
        include = value in ("true", "1", "yes", "enabled")
        content = content[: match.start()] + (block if include else "") + content[match.end() :]


def render_placeholders(content: str, context: Dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        if key not in context:
            raise KeyError(f"Missing placeholder key: {key}")
        return context[key]

    return re.sub(r"\{\{([^#\/][^}]*)\}\}", repl, content)


def strip_template_comments(content: str) -> str:
    lines = [line for line in content.splitlines() if not line.strip().startswith("<!--")]
    return "\n".join(lines).strip() + "\n"


def inject_generated_header(content: str) -> str:
    if content.startswith("---\n"):
        end_idx = content.find("\n---\n", 4)
        if end_idx == -1:
            return "GENERATED — DO NOT EDIT\n\n" + content
        frontmatter = content[: end_idx + 5]
        body = content[end_idx + 5 :].lstrip("\n")
        return frontmatter + "\nGENERATED — DO NOT EDIT\n\n" + body
    return "GENERATED — DO NOT EDIT\n\n" + content


def generate_modes_for_profile(
    profile_path: pathlib.Path, bindings: Dict[str, str]
) -> Tuple[str, List[str]]:
    if "generation.stack_id" not in bindings:
        raise KeyError(f"Missing binding key: binding.generation.stack_id in {profile_path}")
    stack_id = bindings["generation.stack_id"]

    Paths.modes_output.mkdir(parents=True, exist_ok=True)

    generated_mode_names: List[str] = []

    for mode in MODE_NAMES:
        canonical_path = Paths.canonical_dir / f"{mode}.mdc"
        template = canonical_path.read_text(encoding="utf-8")

        context = {}
        context.update(bindings)
        frontmatter = mode_frontmatter_from_bindings(bindings, mode)
        validate_mode_glob_coverage(mode, frontmatter["globs"])
        frontmatter["globs_yaml"] = normalize_globs_yaml(frontmatter["globs"])
        context.update(frontmatter)

        rendered = render_conditionals(template, context)
        rendered = render_placeholders(rendered, context)
        rendered = strip_template_comments(rendered)
        rendered = inject_generated_header(rendered)

        canonical_output = Paths.modes_output / f"{mode}.mdc"
        canonical_output.write_text(rendered, encoding="utf-8")

        generated_mode_names.append(mode)

    return stack_id, generated_mode_names


# ---------------------------------------------------------------------------
# Rule generation
# ---------------------------------------------------------------------------

def extract_template_content(template_path: pathlib.Path) -> str:
    content = template_path.read_text(encoding="utf-8")
    match = re.search(r"```markdown\n(.*?)```", content, re.DOTALL)
    if not match:
        raise ValueError(f"No markdown code block found in {template_path}")
    return match.group(1)


def render_sections(content: str, context: Dict[str, str]) -> str:
    """Render Mustache-style sections: {{#key}}...{{/key}}."""
    pattern = re.compile(r"\{\{#([^}]+)\}\}(.*?)\{\{/\1\}\}", re.DOTALL)
    while True:
        match = pattern.search(content)
        if not match:
            return content
        key = match.group(1).strip()
        raw_block = match.group(2)
        value = context.get(key, "").strip()
        if value:
            block = raw_block
            if block.startswith("\n"):
                block = block[1:]
            if block.endswith("\n"):
                block = block[:-1]
            rendered_block = block.replace("{{" + key + "}}", value)
            content = content[: match.start()] + rendered_block + content[match.end() :]
        else:
            end = match.end()
            if end < len(content) and content[end] == "\n":
                end += 1
            content = content[: match.start()] + content[end:]


def render_rule_placeholders(content: str, context: Dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        if key.startswith("#") or key.startswith("/"):
            return match.group(0)
        if key not in context:
            raise KeyError(f"Missing rule placeholder: {{{{{key}}}}}")
        return context[key]

    return re.sub(r"\{\{([^#\/][^}]*)\}\}", repl, content)


def discover_rule_workspaces(bindings: Dict[str, str]) -> List[str]:
    workspace_ids = set()
    for key in bindings:
        match = re.match(r"rule\.base\.([^.]+)\.description$", key)
        if match:
            ws_id = match.group(1)
            if ws_id not in RULE_GENERATION_SKIP:
                workspace_ids.add(ws_id)
    return sorted(workspace_ids)


def get_rule_binding(
    bindings: Dict[str, str],
    ws_id: str,
    category: str,
    key: str,
    shared_prefix: Optional[str] = None,
) -> Optional[str]:
    ws_key = f"rule.{category}.{ws_id}.{key}"
    if ws_key in bindings:
        return unescape_binding(bindings[ws_key])
    if shared_prefix:
        shared_key = f"rule.{category}.{shared_prefix}.{key}"
        if shared_key in bindings:
            return unescape_binding(bindings[shared_key])
    platform_key = f"rule.{category}.{key}"
    if platform_key in bindings:
        return unescape_binding(bindings[platform_key])
    return None


def require_rule_binding(
    bindings: Dict[str, str],
    ws_id: str,
    category: str,
    key: str,
    shared_prefix: Optional[str] = None,
) -> str:
    value = get_rule_binding(bindings, ws_id, category, key, shared_prefix)
    if value is None:
        raise KeyError(
            f"Missing rule binding: binding.rule.{category}.{ws_id}.{key}"
        )
    return value


def detect_shared_prefix(bindings: Dict[str, str]) -> Optional[str]:
    for key in bindings:
        m = re.match(r"rule\.base\.([^.]+_shared)\.", key)
        if m:
            return m.group(1)
    return None


def build_file_header_section(project_name: str, author: str) -> str:
    return (
        "SWIFT FILE HEADER (NEW FILES)\n"
        "- For every NEW `.swift` file created, include this header at the very top (before imports):\n"
        "\n"
        "//\n"
        f"//  FILENAME.swift\n"
        f"//  {project_name}\n"
        "//\n"
        f"//  Created by {author} on DD/MM/YY.\n"
        "//\n"
        "\n"
        "- Replace `FILENAME.swift` with the actual filename.\n"
        "- Replace `DD/MM/YY` with the creation date."
    )


def generate_base_rule(
    bindings: Dict[str, str],
    ws_id: str,
    shared_prefix: Optional[str],
) -> pathlib.Path:
    template = extract_template_content(Paths.canonical_dir / "base-rule.md")

    required_keys = (
        "description",
        "role_specialty",
        "conversation_language",
        "engineering_domain_principle",
        "security_line",
        "performance_line",
        "assumptions_domain",
        "limitations_truthfulness_line",
        "platform_limitations",
        "styleguide_paths",
    )

    context: Dict[str, str] = {}
    for k in required_keys:
        context[k] = require_rule_binding(bindings, ws_id, "base", k, shared_prefix)

    optional_keys = ("domain_constraints_section",)
    for k in optional_keys:
        val = get_rule_binding(bindings, ws_id, "base", k, shared_prefix)
        if val:
            context[k] = val

    rendered = render_sections(template, context)
    rendered = render_rule_placeholders(rendered, context)
    rendered = re.sub(r"\n{3,}", "\n\n", rendered)
    if not rendered.endswith("\n"):
        rendered += "\n"
    rendered = inject_generated_header(rendered)

    Paths.rules_output.mkdir(parents=True, exist_ok=True)
    canonical_path = Paths.rules_output / "base.mdc"
    canonical_path.write_text(rendered, encoding="utf-8")

    return canonical_path


def generate_output_contract(
    bindings: Dict[str, str],
    ws_id: str,
    shared_prefix: Optional[str],
) -> pathlib.Path:
    template = extract_template_content(Paths.canonical_dir / "output-contract.md")

    context: Dict[str, str] = {}
    context["description"] = "Output contract: complete file contents + reasoning"
    context["environment"] = require_rule_binding(
        bindings, ws_id, "output_contract", "environment", shared_prefix
    )
    context["documentation_tool"] = require_rule_binding(
        bindings, ws_id, "output_contract", "documentation_tool", shared_prefix
    )
    context["comment_style"] = require_rule_binding(
        bindings, ws_id, "output_contract", "linter", shared_prefix
    )
    context["testing"] = require_rule_binding(
        bindings, ws_id, "output_contract", "testing", shared_prefix
    )

    for opt_key in ("deliverables_extra", "documentation_extra", "domain_considerations"):
        val = get_rule_binding(bindings, ws_id, "output_contract", opt_key, shared_prefix)
        if val:
            context[opt_key] = val

    if not Paths.stack_fragment.exists():
        raise FileNotFoundError(
            f"Missing stack fragment: {Paths.stack_fragment}\n"
            f"Create stack-fragment.md at repo root (see aias/contracts/readme-output-contract.md § Fragment Structure Options)"
        )
    context["build_system_integration"] = Paths.stack_fragment.read_text(encoding="utf-8").rstrip("\n")

    project_name = get_rule_binding(
        bindings, ws_id, "output_contract", "file_header_project_name", shared_prefix
    )
    author = get_rule_binding(
        bindings, ws_id, "output_contract", "file_header_author", shared_prefix
    )
    if project_name and author:
        context["file_header_section"] = build_file_header_section(project_name, author)

    rendered = render_sections(template, context)
    rendered = render_rule_placeholders(rendered, context)
    rendered = re.sub(r"\n{3,}", "\n\n", rendered)
    if not rendered.endswith("\n"):
        rendered += "\n"
    rendered = inject_generated_header(rendered)

    Paths.rules_output.mkdir(parents=True, exist_ok=True)
    canonical_path = Paths.rules_output / "output-contract.mdc"
    canonical_path.write_text(rendered, encoding="utf-8")

    return canonical_path


def generate_rules_for_profile(
    profile_path: pathlib.Path, bindings: Dict[str, str]
) -> List[str]:
    shared_prefix = detect_shared_prefix(bindings)
    workspace_ids = discover_rule_workspaces(bindings)

    if len(workspace_ids) > 1:
        print(f"  WARNING: {len(workspace_ids)} workspaces found ({', '.join(workspace_ids)}). "
              f"Rules are written to flat files (base.mdc, output-contract.mdc) — "
              f"only the last workspace ('{workspace_ids[-1]}') will be preserved (last-wins).")

    generated: List[str] = []
    for ws_id in workspace_ids:
        canon_base = generate_base_rule(bindings, ws_id, shared_prefix)
        canon_oc = generate_output_contract(bindings, ws_id, shared_prefix)
        generated.append(ws_id)
        print(f"  Rules generated: {ws_id}")
        print(f"    → (canonical) {canon_base.relative_to(Paths.root)}")
        print(f"    → (canonical) {canon_oc.relative_to(Paths.root)}")
    return generated


# ---------------------------------------------------------------------------
# Shortcut generation (only with --shortcuts flag)
# ---------------------------------------------------------------------------

def generate_shortcuts(
    generated_modes: List[str],
    all_bindings: List[Tuple[pathlib.Path, Dict[str, str]]],
    tools: List[str],
) -> Dict[str, int]:
    """Generate shortcut files for selected tools. Returns count per tool."""
    counts: Dict[str, int] = {t: 0 for t in tools}

    mode_globs = _collect_mode_globs(all_bindings)

    if "cursor" in tools:
        counts["cursor"] += _generate_cursor_shortcuts(generated_modes)
    if "claude" in tools:
        counts["claude"] += _generate_claude_shortcuts(generated_modes, mode_globs)
    if "windsurf" in tools:
        counts["windsurf"] += _generate_windsurf_shortcuts()
    if "copilot" in tools:
        counts["copilot"] += _generate_copilot_shortcuts(generated_modes, mode_globs)
    if "codex" in tools:
        counts["codex"] += _generate_codex_shortcuts()

    cursor_skills, claude_skills = _generate_skill_shortcuts(tools)
    if "cursor" in tools:
        counts["cursor"] += cursor_skills
    if "claude" in tools:
        counts["claude"] += claude_skills

    return counts


def _collect_mode_globs(
    all_bindings: List[Tuple[pathlib.Path, Dict[str, str]]]
) -> Dict[str, str]:
    """Collect globs for each mode from all profiles (use first found).
    Falls back to TRANSVERSAL_MODE_DEFAULTS for modes with built-in defaults.
    """
    mode_globs: Dict[str, str] = {}
    for _profile, bindings in all_bindings:
        for mode in MODE_NAMES:
            if mode not in mode_globs:
                key = f"mode.{mode}.globs"
                if key in bindings and bindings[key].strip():
                    mode_globs[mode] = bindings[key]
    for mode, defaults in TRANSVERSAL_MODE_DEFAULTS.items():
        if mode not in mode_globs and "globs" in defaults:
            mode_globs[mode] = defaults["globs"]
    return mode_globs


def _generate_cursor_shortcuts(generated_modes: List[str]) -> int:
    """Generate .cursor/ symlinks for rules, modes, and command-shaped skills.

    All Cursor shortcuts are filesystem symlinks to canonical sources.
    Behavioral change: mode symlinks inherit `globs` from canonical .mdc,
    enabling auto-activation by file pattern (previously omitted in text shortcuts).
    """
    count = 0
    rules_dir = Paths.root / ".cursor" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    for rule_name in ("base", "output-contract"):
        _create_symlink(rules_dir / f"{rule_name}.mdc", Paths.rules_output / f"{rule_name}.mdc")
        count += 1

    ci_source = Paths.rules_output / "continuous-improvement.mdc"
    if ci_source.is_file():
        _create_symlink(rules_dir / "continuous-improvement.mdc", ci_source)
        count += 1

    for mode in generated_modes:
        _create_symlink(rules_dir / f"{mode}.mdc", Paths.modes_output / f"{mode}.mdc")
        count += 1

    # NOTE: .cursor/commands/ is intentionally NOT created here.
    # Command-shaped skills (advisory/operative) are projected into .cursor/skills/
    # via _generate_skill_shortcuts, which handles all skill categories uniformly.
    # Cursor consumes skills from .cursor/skills/; .cursor/commands/ is retired for Cursor.

    return count


def _generate_claude_shortcuts(
    generated_modes: List[str],
    mode_globs: Dict[str, str],
) -> int:
    """Generate .claude/rules/ enriched text shortcuts for rules and modes."""
    count = 0
    rules_dir = Paths.root / ".claude" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    for rule_name in ("base", "output-contract"):
        shortcut_path = rules_dir / f"{rule_name}.md"
        canonical_path = Paths.rules_output / f"{rule_name}.mdc"
        desc = _extract_description(canonical_path)
        prefix = f"[{rule_name}] {desc}\n" if desc else ""
        content = f"{prefix}Read and follow the canonical rule at: aias-config/rules/{rule_name}.mdc\n"
        shortcut_path.write_text(content, encoding="utf-8")
        count += 1

    ci_source = Paths.rules_output / "continuous-improvement.mdc"
    if ci_source.is_file():
        shortcut_path = rules_dir / "continuous-improvement.md"
        desc = _extract_description(ci_source)
        prefix = f"[continuous-improvement] {desc}\n" if desc else ""
        content = f"{prefix}Read and follow the canonical rule at: aias-config/rules/continuous-improvement.mdc\n"
        shortcut_path.write_text(content, encoding="utf-8")
        count += 1

    for mode in generated_modes:
        shortcut_path = rules_dir / f"{mode}.md"
        canonical_path = Paths.modes_output / f"{mode}.mdc"
        canonical_ref = f"aias-config/modes/{mode}.mdc"
        desc = _extract_description(canonical_path)
        desc_line = f"[{mode}] {desc}\n" if desc else ""
        globs_raw = mode_globs.get(mode, "")
        if globs_raw:
            items = [item.strip() for item in globs_raw.split(",") if item.strip()]
            paths_lines = "\n".join(f'  - "{item}"' for item in items)
            content = (
                f"---\n"
                f"paths:\n"
                f"{paths_lines}\n"
                f"---\n"
                f"{desc_line}"
                f"Read and follow the canonical mode at: {canonical_ref}\n"
            )
        else:
            content = f"{desc_line}Read and follow the canonical mode at: {canonical_ref}\n"
        shortcut_path.write_text(content, encoding="utf-8")
        count += 1

    return count


def _generate_windsurf_shortcuts() -> int:
    """Generate .windsurf/rules/ enriched text shortcuts for always-apply rules only."""
    count = 0
    rules_dir = Paths.root / ".windsurf" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    for rule_name in ("base", "output-contract"):
        shortcut_path = rules_dir / f"{rule_name}.md"
        canonical_path = Paths.rules_output / f"{rule_name}.mdc"
        desc = _extract_description(canonical_path)
        prefix = f"[{rule_name}] {desc}\n" if desc else ""
        content = f"{prefix}Read and follow the canonical rule at: aias-config/rules/{rule_name}.mdc\n"
        shortcut_path.write_text(content, encoding="utf-8")
        count += 1

    ci_source = Paths.rules_output / "continuous-improvement.mdc"
    if ci_source.is_file():
        shortcut_path = rules_dir / "continuous-improvement.md"
        desc = _extract_description(ci_source)
        prefix = f"[continuous-improvement] {desc}\n" if desc else ""
        content = f"{prefix}Read and follow the canonical rule at: aias-config/rules/continuous-improvement.mdc\n"
        shortcut_path.write_text(content, encoding="utf-8")
        count += 1

    return count


def _generate_copilot_shortcuts(
    generated_modes: List[str],
    mode_globs: Dict[str, str],
) -> int:
    """Generate .github/ shortcuts: copilot-instructions.md (enriched text), instructions/ (enriched text), agents/ (symlinks)."""
    count = 0
    github_dir = Paths.root / ".github"
    github_dir.mkdir(parents=True, exist_ok=True)

    rule_lines: List[str] = []
    for rule_name in ("base", "output-contract"):
        desc = _extract_description(Paths.rules_output / f"{rule_name}.mdc")
        desc_part = f" {desc}" if desc else ""
        rule_lines.append(f"- [{rule_name}]{desc_part} — aias-config/rules/{rule_name}.mdc")
    ci_source = Paths.rules_output / "continuous-improvement.mdc"
    if ci_source.is_file():
        desc = _extract_description(ci_source)
        desc_part = f" {desc}" if desc else ""
        rule_lines.append(f"- [continuous-improvement]{desc_part} — aias-config/rules/continuous-improvement.mdc")

    if rule_lines:
        instructions_path = github_dir / "copilot-instructions.md"
        content = "Read and follow these canonical rules:\n" + "\n".join(rule_lines) + "\n"
        instructions_path.write_text(content, encoding="utf-8")
        count += 1

    instr_dir = github_dir / "instructions"
    instr_dir.mkdir(parents=True, exist_ok=True)
    for mode in generated_modes:
        shortcut_path = instr_dir / f"{mode}.instructions.md"
        canonical_path = Paths.modes_output / f"{mode}.mdc"
        canonical_ref = f"aias-config/modes/{mode}.mdc"
        desc = _extract_description(canonical_path)
        desc_line = f"[{mode}] {desc}\n" if desc else ""
        globs_raw = mode_globs.get(mode, "")
        if globs_raw:
            content = (
                f"---\n"
                f"applyTo: \"{globs_raw}\"\n"
                f"---\n"
                f"{desc_line}"
                f"Read and follow the canonical mode at: {canonical_ref}\n"
            )
        else:
            content = f"{desc_line}Read and follow the canonical mode at: {canonical_ref}\n"
        shortcut_path.write_text(content, encoding="utf-8")
        count += 1

    agents_dir = github_dir / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    # Commands now live in aias/.skills/ (advisory/operative with disable-model-invocation: true)
    for skills_dir in (Paths.fw_skills, Paths.project_skills):
        if not skills_dir.is_dir():
            continue
        for skill_dir in sorted(skills_dir.iterdir()):
            if skill_dir.is_dir() and _is_command_skill(skill_dir):
                skill_file = skill_dir / "SKILL.md"
                _create_symlink(agents_dir / f"{skill_dir.name}.md", skill_file)
                count += 1

    return count


def _generate_codex_shortcuts() -> int:
    """Generate .codex/commands/ (symlinks) and .agents/skills/ (symlinks) for Codex."""
    count = 0

    cmds_dir = Paths.root / ".codex" / "commands"
    cmds_dir.mkdir(parents=True, exist_ok=True)
    # Commands now live in aias/.skills/ (advisory/operative with disable-model-invocation: true)
    for skills_dir in (Paths.fw_skills, Paths.project_skills):
        if not skills_dir.is_dir():
            continue
        for skill_dir in sorted(skills_dir.iterdir()):
            if skill_dir.is_dir() and _is_command_skill(skill_dir):
                skill_file = skill_dir / "SKILL.md"
                _create_symlink(cmds_dir / f"{skill_dir.name}.md", skill_file)
                count += 1

    for skills_dir in (Paths.fw_skills, Paths.project_skills):
        if not skills_dir.is_dir():
            continue
        for skill_dir in sorted(skills_dir.iterdir()):
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").is_file():
                target_dir = Paths.root / ".agents" / "skills" / skill_dir.name
                target_dir.mkdir(parents=True, exist_ok=True)
                _create_symlink(target_dir / "SKILL.md", skill_dir / "SKILL.md")
                count += 1

    return count


def _generate_skill_shortcuts(tools: List[str]) -> Tuple[int, int]:
    """Generate skill symlinks for Cursor and Claude Code, scoped to selected tools.

    Returns (cursor_count, claude_count).
    """
    cursor_count = 0
    claude_count = 0

    all_skill_dirs: List[pathlib.Path] = []
    for skills_dir in (Paths.fw_skills, Paths.project_skills):
        if skills_dir.is_dir():
            all_skill_dirs.extend(sorted(skills_dir.iterdir()))
    if not all_skill_dirs:
        return cursor_count, claude_count

    for skill_dir in all_skill_dirs:
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").is_file():
            continue

        if "cursor" in tools:
            cursor_link = Paths.root / ".cursor" / "skills" / skill_dir.name / "SKILL.md"
            _create_symlink(cursor_link, skill_dir / "SKILL.md")
            cursor_count += 1

        if "claude" in tools:
            claude_link = Paths.root / ".claude" / "skills" / skill_dir.name / "SKILL.md"
            _create_symlink(claude_link, skill_dir / "SKILL.md")
            claude_count += 1

    return cursor_count, claude_count


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate platform modes, rules, and (optionally) tool shortcuts."
    )
    parser.add_argument(
        "--shortcuts",
        action="store_true",
        help="Generate tool-specific shortcut files (.cursor/, .claude/, .windsurf/, .github/). "
             "Only use in adopter projects, NOT in the meta-workspace.",
    )
    parser.add_argument(
        "--tools",
        type=str,
        default=None,
        help="Comma-separated list of tools to generate shortcuts for (overrides binding.generation.tools). "
             "Valid: cursor, claude, windsurf, copilot, codex.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    profiles = discover_profiles()

    # --- Pre-flight validation ---
    print("Pre-flight validation")
    errors = preflight_validation(profiles)
    if errors:
        print(f"\n{'='*60}")
        print(f"VALIDATION FAILED — {len(errors)} error(s) found")
        print(f"{'='*60}\n")
        for i, err in enumerate(errors, 1):
            print(f"  {i}. {err}\n")
        print("No files were modified. Fix the errors above and re-run.")
        return 1
    print("  All gates passed (G0–G5). Proceeding with generation.\n")

    # --- Generation ---
    mode_stacks: List[str] = []
    all_mode_names: List[str] = []
    rule_workspaces: List[str] = []
    all_bindings: List[Tuple[pathlib.Path, Dict[str, str]]] = []

    for profile in profiles:
        bindings = load_bindings(profile)
        all_bindings.append((profile, bindings))
        stack_id, mode_names = generate_modes_for_profile(profile, bindings)
        mode_stacks.append(stack_id)
        all_mode_names = mode_names
        rule_workspaces.extend(generate_rules_for_profile(profile, bindings))

    # --- Transversal rules: copy from .canonical/ to .rules/ ---
    Paths.rules_output.mkdir(parents=True, exist_ok=True)
    for tr in TRANSVERSAL_RULES:
        src = Paths.canonical_dir / f"{tr}.mdc"
        if src.is_file():
            dst = Paths.rules_output / f"{tr}.mdc"
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"\nMode generation completed for stacks: {', '.join(mode_stacks)} ({len(MODE_NAMES)} modes).")
    print(f"Rule generation completed for workspaces: {', '.join(rule_workspaces)}.")
    print(f"Canonical output: aias-config/rules/ (flat), aias-config/modes/ (flat)")
    if RULE_GENERATION_SKIP:
        print(f"Skipped (manual-maintenance): {', '.join(sorted(RULE_GENERATION_SKIP))}.")

    # --- Shortcut generation (only with --shortcuts) ---
    if args.shortcuts:
        tools = _resolve_tools(args.tools, all_bindings)
        print(f"\nGenerating shortcuts for: {', '.join(tools)}...")
        shortcut_counts = generate_shortcuts(all_mode_names, all_bindings, tools)
        for tool, count in shortcut_counts.items():
            print(f"  {tool}: {count} shortcuts")

        print("\nPost-flight validation (G6–G7)...")
        post_errors = postflight_validation(all_mode_names, tools)
        if post_errors:
            print(f"\n{'='*60}")
            print(f"POST-FLIGHT ERRORS — {len(post_errors)} issue(s)")
            print(f"{'='*60}\n")
            for i, err in enumerate(post_errors, 1):
                print(f"  {i}. {err}\n")
            print("Generation produced output but post-flight validation failed.")
            return 1
        else:
            print("  All post-flight gates passed (G6–G7).")
    else:
        print("\nShortcuts skipped (use --shortcuts to generate tool-specific files).")

    print("\nGeneration complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
