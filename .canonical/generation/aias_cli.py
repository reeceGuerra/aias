#!/usr/bin/env python3
"""
Rho AIAS CLI — interactive scaffolding, generation, and health checks.

Subcommands:
    init        Full onboarding (context + profile + fragment + shortcuts + generate)
    new         Create a new artifact (mode, rule, command, skill, provider, context, stack-profile, stack-fragment)
    generate    Run the canonical generator (alias: gen)
    health      Verify setup health

Usage:
    python3 aias/.canonical/generation/aias_cli.py <subcommand> [options]
"""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys
import textwrap
from typing import Dict, List, Tuple

from generate_modes_and_rules import SUPPORTED_TOOLS


ROOT = pathlib.Path(__file__).resolve().parents[3]
CANONICAL_DIR = ROOT / "aias" / ".canonical"
CONTRACTS_DIR = ROOT / "aias" / "contracts"
AIAS_CONFIG_DIR = ROOT / "aias-config"
RULES_DIR = AIAS_CONFIG_DIR / "rules"
MODES_DIR = AIAS_CONFIG_DIR / "modes"
FW_SKILLS_DIR = ROOT / "aias" / ".skills"
PROJECT_COMMANDS_DIR = AIAS_CONFIG_DIR / "commands"
PROJECT_SKILLS_DIR = AIAS_CONFIG_DIR / "skills"
PROVIDERS_DIR = AIAS_CONFIG_DIR / "providers"
LEGACY_PROVIDERS_DIR = ROOT / "aias-providers"
GENERATOR = CANONICAL_DIR / "generation" / "generate_modes_and_rules.py"

KEBAB_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
PROVIDER_CATEGORIES = ("knowledge", "tracker", "design", "vcs")

HEADING_PAREN_RE = re.compile(r"\s*\(.*\)\s*$")

EXPECTED_SECTIONS: Dict[str, Dict[str, List[str]]] = {
    "confluence-config.md": {
        "mandatory": ["Space", "Publishing Hierarchy", "TECH Resolution",
                       "Date Resolution", "Navigation Algorithm", "Rules", "Example"],
        "optional": ["Table of Contents"],
    },
    "jira-field-mapping.md": {
        "mandatory": ["Precedence Rule", "Format Rules"],
        "optional": [],
    },
    "tracker-status-mapping.md": {
        "mandatory": ["Purpose", "Provider", "Canonical Status Catalog",
                       "Canonical -> Provider Mapping", "Command Triggers",
                       "Boundary Rules", "Resolution Rules"],
        "optional": [],
    },
}

TOOL_CONTEXT_MAP: Dict[str, Tuple[str, ...]] = {
    "AGENTS.md": ("cursor", "windsurf", "copilot"),
    "CLAUDE.md": ("claude",),
    "codex.md": ("codex",),
    "GEMINI.md": ("gemini",),
}

TOOL_SHORTCUT_DIRS: Dict[str, Tuple[str, ...]] = {
    "cursor": (".cursor/rules", ".cursor/skills"),
    "claude": (".claude/rules", ".claude/commands"),
    "windsurf": (".windsurf/rules",),
    "copilot": (".github/instructions", ".github/agents"),
    "codex": (".codex/commands", ".agents/skills"),
}

SHORTCUT_BOUNDARY_PATHS: Tuple[str, ...] = (
    "aias-config",
    "aias/.skills",
    "RHOAIAS.md",
)

# aias/.commands/ is retired; symlinks to it are legacy and should be flagged by health.
LEGACY_COMMAND_DIR = "aias/.commands"

SHORTCUT_REF_RE = re.compile(
    r"(?:aias-config|aias/\.skills)/[A-Za-z0-9._/\-]+|RHOAIAS\.md"
)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _create_symlink(link_path: pathlib.Path, target_path: pathlib.Path) -> None:
    """Create a relative symlink. Idempotent: removes existing file or symlink first."""
    rel_target = os.path.relpath(target_path, link_path.parent)
    if link_path.is_symlink() or link_path.exists():
        link_path.unlink()
    link_path.parent.mkdir(parents=True, exist_ok=True)
    link_path.symlink_to(rel_target)


def _read_binding_from_profile(binding_key: str) -> str:
    """Read a binding value from stack-profile.md. Returns empty string if absent."""
    profile = ROOT / "stack-profile.md"
    if not profile.is_file():
        return ""
    for line in profile.read_text(encoding="utf-8").splitlines():
        if binding_key in line:
            parts = line.split("`: `")
            if len(parts) == 2:
                return parts[1].rstrip("` \n")
    return ""


def _read_tools_from_profile() -> List[str]:
    """Read binding.generation.tools from stack-profile.md. Returns empty list if absent."""
    raw = _read_binding_from_profile("binding.generation.tools")
    if not raw:
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]


def _read_tasks_dir_from_profile() -> str:
    """Read binding.generation.tasks_dir from stack-profile.md. Returns empty string if absent."""
    return _read_binding_from_profile("binding.generation.tasks_dir")


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value if value else default


def ask_choice(prompt: str, options: List[str]) -> str:
    print(f"\n{prompt}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}) {opt}")
    while True:
        raw = input("Choice: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print(f"  Enter a number between 1 and {len(options)}.")


def ask_multi_choice(prompt: str, options: List[str]) -> List[str]:
    """Multi-select prompt. User enters comma-separated numbers."""
    print(f"\n{prompt}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}) {opt}")
    while True:
        raw = input("Choices (comma-separated, e.g. 1,3): ").strip()
        indices = [s.strip() for s in raw.split(",") if s.strip()]
        if all(s.isdigit() and 1 <= int(s) <= len(options) for s in indices) and indices:
            return [options[int(s) - 1] for s in indices]
        print(f"  Enter numbers between 1 and {len(options)}, comma-separated.")


def confirm(prompt: str, default_yes: bool = False) -> bool:
    hint = "Y/n" if default_yes else "y/N"
    raw = input(f"{prompt} [{hint}]: ").strip().lower()
    if not raw:
        return default_yes
    return raw in ("y", "yes")


def validate_kebab(name: str) -> bool:
    return bool(KEBAB_RE.match(name))


def safe_write(path: pathlib.Path, content: str) -> bool:
    """Write content to path. If file exists, ask before overwriting. Returns True if written."""
    if path.is_file():
        if not confirm(f"  '{path.relative_to(ROOT)}' already exists. Overwrite?"):
            print("  Skipped.")
            return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  Created: {path.relative_to(ROOT)}")
    return True


def run_generator(shortcuts: bool = True) -> int:
    cmd = [sys.executable, str(GENERATOR)]
    if shortcuts:
        cmd.append("--shortcuts")
    print(f"\nRunning generator{'  (--shortcuts)' if shortcuts else ''}...")
    result = subprocess.run(cmd, cwd=str(ROOT))
    return result.returncode


def _parse_max_depth(args: List[str], default: int = 0) -> int:
    """Parse --max-depth <int> option from args."""
    value = default
    for i, arg in enumerate(args):
        if arg == "--max-depth":
            if i + 1 >= len(args):
                raise ValueError("--max-depth requires an integer value")
            try:
                value = int(args[i + 1])
            except ValueError as exc:
                raise ValueError("--max-depth must be an integer") from exc
            if value < 0:
                raise ValueError("--max-depth must be >= 0")
    return value


def _discover_rhoaias_files(max_depth: int) -> List[pathlib.Path]:
    """Discover RHOAIAS.md files from ROOT up to max_depth."""
    results: List[pathlib.Path] = []
    for current_root, dirs, files in os.walk(ROOT):
        current_path = pathlib.Path(current_root)
        rel = current_path.relative_to(ROOT)
        depth = 0 if str(rel) == "." else len(rel.parts)
        if depth > max_depth:
            dirs[:] = []
            continue
        if "RHOAIAS.md" in files:
            results.append(current_path / "RHOAIAS.md")
    return sorted(results, key=lambda p: str(p))


def _ensure_context_symlinks_for_rhoaias(
    rhoaias_files: List[pathlib.Path], selected_tools: List[str]
) -> int:
    """Ensure tool context symlinks for each discovered RHOAIAS.md."""
    created = 0
    for rhoaias_target in rhoaias_files:
        base_dir = rhoaias_target.parent
        for filename, required_tools in TOOL_CONTEXT_MAP.items():
            if selected_tools and not any(t in selected_tools for t in required_tools):
                continue
            link_path = base_dir / filename
            if link_path.is_symlink():
                current = (link_path.parent / os.readlink(link_path)).resolve()
                if current == rhoaias_target.resolve():
                    continue
                _create_symlink(link_path, rhoaias_target)
                created += 1
                continue
            if link_path.is_file():
                # Non-destructive in non-interactive contexts: leave regular files untouched.
                continue
            _create_symlink(link_path, rhoaias_target)
            created += 1
    return created


def existing_names(directory: pathlib.Path, suffix: str = ".mdc") -> List[str]:
    if not directory.is_dir():
        return []
    return sorted(p.stem for p in directory.glob(f"*{suffix}") if p.is_file())


def _validate_sections(
    content: str,
    mandatory: List[str],
    optional: List[str],
    filename: str = "",
) -> Tuple[List[str], List[Tuple[str, str]]]:
    """Validate that ``## ``-level headings in *content* satisfy *mandatory* and *optional*.

    Returns ``(missing_mandatory, inconsistencies)`` where *inconsistencies*
    are ``(kind, detail)`` tuples.  The function is pure — no filesystem access.
    """
    found: List[str] = []
    for line in content.splitlines():
        if line.startswith("## "):
            raw = line[3:].strip()
            normalized = HEADING_PAREN_RE.sub("", raw).strip()
            found.append(normalized)

    missing = [s for s in mandatory if s not in found]

    inconsistencies: List[Tuple[str, str]] = []
    if filename == "confluence-config.md":
        has_toc_ref = "injectTocIfMissing" in content
        has_toc_section = "Table of Contents" in found
        if has_toc_ref and not has_toc_section:
            inconsistencies.append(
                ("cross-reference",
                 "Navigation/Rules reference injectTocIfMissing but ## Table of Contents section is absent"))
    return missing, inconsistencies


# ---------------------------------------------------------------------------
# new --mode
# ---------------------------------------------------------------------------

def new_mode(name: str) -> None:
    if not validate_kebab(name):
        print(f"Error: '{name}' is not valid kebab-case (expected: ^[a-z][a-z0-9]*(-[a-z0-9]+)*$)")
        sys.exit(1)

    existing = existing_names(MODES_DIR)
    if name in existing:
        if not confirm(f"  Mode '{name}' already exists in aias-config/modes/. Overwrite?"):
            return

    description = ask("Description (one line, max 200 chars)")
    if not description:
        print("Error: description is required.")
        sys.exit(1)
    if len(description) > 200:
        print(f"Warning: description is {len(description)} chars (max 200). Truncating.")
        description = description[:200]

    activation = ask_choice("Activation type:", ["file-specific (globs)", "intelligent"])

    globs_value = ""
    if activation.startswith("file-specific"):
        globs_value = ask("Globs (comma-separated, e.g. **/*.swift, **/*.md)")
        if not globs_value.strip():
            print("Error: at least one glob is required for file-specific activation.")
            sys.exit(1)

    role = ask("Role (expertise + perspective + focus, min 30 chars)")
    if len(role) < 30:
        print(f"Warning: role is only {len(role)} chars. Consider a more detailed description.")

    scope_in = ask("In-scope (what this mode handles)")
    scope_out = ask("Out-of-scope (what this mode does NOT handle)")

    skills_raw = ask("Skills (comma-separated, optional)")
    workflow = ask("Workflow hints (optional, e.g. 1. Read 2. Analyze 3. Report)")

    # Build frontmatter
    frontmatter = f"---\ndescription: \"{description}\"\nalwaysApply: false\n"
    if globs_value:
        items = [g.strip() for g in globs_value.split(",") if g.strip()]
        globs_yaml = "\n".join(f'  - "{g}"' for g in items)
        frontmatter += f"globs:\n{globs_yaml}\n"
    frontmatter += "---\n"

    # Build body
    body_parts = [f"{name.upper().replace('-', ' ')} ROLE\n{role}"]
    scope = f"SCOPE\n- In-scope: {scope_in}"
    if scope_out:
        scope += f"\n- Out-of-scope: {scope_out}"
    body_parts.append(scope)

    if workflow:
        body_parts.append(f"WORKFLOW\n{workflow}")

    if skills_raw:
        skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
        enrichment = "CONTEXT ENRICHMENT\n" + "\n".join(f"- Use the **{s}** skill when applicable." for s in skills)
        body_parts.append(enrichment)

    content = frontmatter + "\n" + "\n\n".join(body_parts) + "\n"
    path = MODES_DIR / f"{name}.mdc"
    safe_write(path, content)


# ---------------------------------------------------------------------------
# new --rule
# ---------------------------------------------------------------------------

def new_rule(name: str) -> None:
    if not validate_kebab(name):
        print(f"Error: '{name}' is not valid kebab-case (expected: ^[a-z][a-z0-9]*(-[a-z0-9]+)*$)")
        sys.exit(1)

    existing = existing_names(RULES_DIR)
    if name in existing:
        print(f"  Existing rules: {', '.join(existing)}")
        if not confirm(f"  Rule '{name}' already exists in aias-config/rules/. Overwrite?"):
            return

    description = ask("Description (one line, purpose of this rule)")
    if not description:
        print("Error: description is required.")
        sys.exit(1)

    purpose = ask("Purpose (what behavior does this rule enforce?)")
    content_text = ask("Content (the constraints/principles — press Enter to leave empty and fill manually)")

    frontmatter = f"---\ndescription: \"{description}\"\nalwaysApply: true\n---\n"

    body = ""
    if purpose:
        body += f"\n{name.upper().replace('-', ' ')}\n{purpose}\n"
    if content_text:
        body += f"\n{content_text}\n"
    elif not purpose:
        body += f"\n# TODO: Add rule content\n"

    full = frontmatter + body
    path = RULES_DIR / f"{name}.mdc"
    safe_write(path, full)


# ---------------------------------------------------------------------------
# new --command
# ---------------------------------------------------------------------------

def new_command(name: str) -> None:
    """Deprecated: redirect to new_skill with category advisory|operative."""
    print(
        "\n[DEPRECATED] `aias new --command` is deprecated as of BL-S36 (readme-skill.md v1.3).\n"
        "Commands are now advisory or operative skills in `aias-config/skills/<name>/SKILL.md`.\n\n"
        "Use instead:  aias new --skill <name>  (select category: advisory or operative)\n"
        "Or migrate existing project commands:  aias new --migrate-commands\n"
    )
    if not confirm("Redirect to `aias new --skill` now?"):
        print("Aborted. Run: aias new --skill <name>")
        return
    new_skill(name)


# ---------------------------------------------------------------------------
# new --skill
# ---------------------------------------------------------------------------

def new_skill(name: str) -> None:
    if not validate_kebab(name):
        print(f"Error: '{name}' is not valid kebab-case (expected: ^[a-z][a-z0-9]*(-[a-z0-9]+)*$)")
        sys.exit(1)

    existing: List[str] = []
    for sdir in (FW_SKILLS_DIR, PROJECT_SKILLS_DIR):
        if sdir.is_dir():
            existing.extend(d.name for d in sdir.iterdir() if d.is_dir())
    if name in existing:
        if not confirm(f"  Skill '{name}' already exists. Overwrite?"):
            return

    category_choice = ask_choice(
        "Skill category:",
        ["MCP (interacts with an MCP server)", "Knowledge (reusable domain knowledge)", "Tool (CLI tool or local utility)",
         "Advisory (chat-only command workflow, no file writes)", "Operative (execution command workflow, writes artifacts)"],
    )
    category = (
        "mcp" if "MCP" in category_choice
        else "knowledge" if "Knowledge" in category_choice
        else "tool" if "Tool" in category_choice
        else "advisory" if "Advisory" in category_choice
        else "operative"
    )
    is_command_skill = category in ("advisory", "operative")

    description = ask("Description (WHAT + WHEN with trigger terms, max 1024 chars)")
    if not description or len(description) < 50:
        print(f"Warning: description should be >= 50 chars with trigger terms (current: {len(description)}).")

    version = ask("Version (SemVer, e.g. 1.0.0)", "1.0.0") if category != "mcp" else None

    if is_command_skill:
        # Advisory/operative: scaffold from the commands contract template
        cmd_type = "Advisory" if category == "advisory" else "Operative"
        purpose = ask("Identity / Purpose (what does this command do?)")
        invocation = ask("Invocation example (e.g. /<name> --flag value)")
        inputs_text = ask("Inputs (what information does it consume?)")
        output_format = ask("Output format (Rendered Markdown, code block, file...)")
        content_rules = ask("Content rules (what to include/exclude, language)")
        output_structure = ask("Output structure (sections of the output)")
        non_goals = ask("Non-goals (what must this command NOT do?)")
        skills_ref = ask("Skills referenced (comma-separated, optional)")

        body = textwrap.dedent(f"""\
            # {name.replace('-', ' ').title()} — v1

            ## 1. Identity
            **Command Type:** {cmd_type}
            {purpose}
        """)
        if skills_ref:
            sl = [s.strip() for s in skills_ref.split(",") if s.strip()]
            body += f"\n**Skills referenced:** {', '.join(f'`{s}`' for s in sl)}.\n"
        body += textwrap.dedent(f"""
            ---

            ## 2. Invocation / Usage
            {invocation if invocation else f'`/{name}`'}

            ## 3. Inputs
            {inputs_text}

            ## 4. Output Contract (Format)
            {output_format}

            ## 5. Content Rules (Semantics)
            {content_rules}

            ## 6. Output Structure (Template)
            {output_structure}

            ## 7. Non-Goals / Forbidden Actions
            {non_goals}

            ## 8. Self-Verification Checklist
            - [ ] Terminal state line emitted with correct state token
        """)
    else:
        # MCP / Knowledge / Tool: scaffold with PURPOSE + OPERATIONS + SAFETY RULES
        body = ""
        purpose = ask("Purpose (1-2 sentences: what it enables)")
        body += f"\n## PURPOSE\n{purpose}\n"

        print("\nOperations (enter at least one; empty name to stop):")
        operations = []
        while True:
            op_name = ask("  Operation name (empty to finish)")
            if not op_name:
                break
            op_when = ask("  When to use")
            op_prereq = ask("  Prerequisites")
            op_sequence = ask("  Call sequence")
            op_output = ask("  Output")
            operations.append((op_name, op_when, op_prereq, op_sequence, op_output))

        if not operations:
            print("Warning: at least one operation is recommended.")

        body += "\n## OPERATIONS\n"
        for op_name, op_when, op_prereq, op_sequence, op_output in operations:
            body += f"\n### {op_name}\n"
            body += f"- **When**: {op_when}\n"
            body += f"- **Prerequisites**: {op_prereq}\n"
            body += f"- **Call sequence**: {op_sequence}\n"
            body += f"- **Output**: {op_output}\n"

        safety = ask("Safety rules (read/write boundary, abort-on-failure, data integrity)")
        if not safety:
            safety = (
                "- Read-only by default. Write operations require explicit user request.\n"
                "- Abort on failure. Do not invent data.\n"
                "- Data integrity: do not fabricate or assume data not returned by the service."
            )
        body += f"\n## SAFETY RULES\n{safety}\n"

    # Build SKILL.md frontmatter
    dm_inv = "true" if is_command_skill else "false"
    version_line = f"version: {version}\n" if version else ""
    frontmatter = (
        f"---\nname: {name}\ndescription: \"{description}\"\n"
        f"category: {category}\ndisable-model-invocation: {dm_inv}\n"
        f"{version_line}---\n"
    )

    path = PROJECT_SKILLS_DIR / name / "SKILL.md"
    safe_write(path, frontmatter + body)


# ---------------------------------------------------------------------------
# new --migrate-commands
# ---------------------------------------------------------------------------

def migrate_commands() -> None:
    """Migrate project custom commands from aias-config/commands/ to aias-config/skills/.

    For each .md file found in PROJECT_COMMANDS_DIR, creates a corresponding
    aias-config/skills/<name>/SKILL.md with an advisory or operative frontmatter
    and the original content. Does not touch framework commands (aias/.commands/).
    """
    if not PROJECT_COMMANDS_DIR.is_dir():
        print("No aias-config/commands/ directory found. Nothing to migrate.")
        return

    cmd_files = sorted(PROJECT_COMMANDS_DIR.glob("*.md"))
    if not cmd_files:
        print("No command files found in aias-config/commands/. Nothing to migrate.")
        return

    print(f"Found {len(cmd_files)} command file(s) in aias-config/commands/ to migrate:\n")
    for f in cmd_files:
        print(f"  {f.name}")
    print()

    if not confirm("Migrate all the above commands to aias-config/skills/?"):
        print("Aborted.")
        return

    migrated = 0
    for cmd_file in cmd_files:
        name = cmd_file.stem
        content = cmd_file.read_text(encoding="utf-8")

        # Detect category from existing Command Type declaration
        if "Command Type: Advisory" in content or "Command Type:** Advisory" in content:
            category = "advisory"
        else:
            category = "operative"

        dest_dir = PROJECT_SKILLS_DIR / name
        dest = dest_dir / "SKILL.md"
        if dest.exists():
            if not confirm(f"  aias-config/skills/{name}/SKILL.md already exists. Overwrite?"):
                print(f"  Skipped: {name}")
                continue

        description = f"Migrated project command: {name.replace('-', ' ')}. Invoke with /{name}."
        frontmatter = (
            f"---\n"
            f"name: {name}\n"
            f"description: \"{description}\"\n"
            f"category: {category}\n"
            f"disable-model-invocation: true\n"
            f"version: 1.0.0\n"
            f"---\n\n"
        )
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest.write_text(frontmatter + content, encoding="utf-8")
        print(f"  Migrated: aias-config/commands/{cmd_file.name} → aias-config/skills/{name}/SKILL.md")
        migrated += 1

    print(f"\nMigrated {migrated} of {len(cmd_files)} command(s).")
    if migrated:
        print(
            "\nNext steps:\n"
            "  1. Review each migrated SKILL.md and update description + version in frontmatter.\n"
            "  2. Run: aias generate --shortcuts  (to regenerate .<tool>/commands/ from skills)\n"
            "  3. Delete aias-config/commands/ once you have verified the migration.\n"
        )


# ---------------------------------------------------------------------------
# new --provider
# ---------------------------------------------------------------------------

CAPABILITY_SUGGESTIONS = {
    "knowledge": "knowledge-publish",
    "tracker": "tracker-sync",
    "design": "design-context",
    "vcs": "pull-request-and-branch",
}

MCP_SERVER_EXAMPLES = {
    "knowledge": "user-Atlassian",
    "tracker": "user-Atlassian",
    "design": "user-Figma",
    "vcs": "user-GitHub",
}


def new_provider(category: str) -> None:
    if category not in PROVIDER_CATEGORIES:
        print(f"Error: category must be one of: {', '.join(PROVIDER_CATEGORIES)}")
        sys.exit(1)

    provider = ask("Provider name (e.g. jira, figma, github)")
    if not provider:
        print("Error: provider is required.")
        sys.exit(1)

    skill_binding = ask("Skill binding (skill name that implements this provider)")
    if skill_binding:
        found = any((sdir / skill_binding).is_dir() for sdir in (FW_SKILLS_DIR, PROJECT_SKILLS_DIR))
        if not found:
            available: List[str] = []
            for sdir in (FW_SKILLS_DIR, PROJECT_SKILLS_DIR):
                if sdir.is_dir():
                    available.extend(d.name for d in sdir.iterdir() if d.is_dir())
            print(f"Error: skill '{skill_binding}' not found.")
            if available:
                print(f"  Available: {', '.join(sorted(set(available)))}")
            print("  Create one with: aias new --skill <name>")
            sys.exit(1)

    cap_default = CAPABILITY_SUGGESTIONS.get(category, "")
    capability = ask(f"Capability (purpose of this provider binding)", cap_default)
    if not capability:
        print("Error: capability is required. See aias/contracts/readme-provider-config.md § Capability Compatibility Matrix.")
        sys.exit(1)

    mcp_default = MCP_SERVER_EXAMPLES.get(category, "")
    mcp_server = ask(f"MCP server name (e.g. {mcp_default})", mcp_default)
    if not mcp_server:
        print("Error: mcp_server is required when provider_mode is mcp.")
        sys.exit(1)

    has_resource_files = category in ("tracker", "knowledge")
    resource_files_block = ""
    resource_files_example = ""
    if has_resource_files:
        resource_files_block = (
            f"  resource_files: []\n"
            f"  # Referenced files not yet configured. Run /aias configure-providers to generate them."
        )
        resource_files_example = (
            f"\n          resource_files: []\n"
            f"          # Run /aias configure-providers to populate"
        )

    skill_binding_section = f"""\
        ```yaml
        skill_binding:
          skill: {skill_binding}
          capability: {capability}"""
    if has_resource_files:
        skill_binding_section += f"\n          resource_files: []\n          # Referenced files not yet configured. Run /aias configure-providers to generate them."
    skill_binding_section += "\n        ```"

    example_skill_binding = f"""\
          skill: {skill_binding}
          capability: {capability}"""
    if has_resource_files:
        example_skill_binding += f"\n          resource_files: []\n          # Run /aias configure-providers to populate"

    content = textwrap.dedent(f"""\
        # Provider Config — {category}

        ## Purpose

        Define which {category} provider is used by commands and modes that require {category} operations.

        ## Active provider

        ```yaml
        service_category: {category}
        active_provider: {provider}
        provider_mode: mcp
        ```

        ## Skill binding

        {skill_binding_section}

        ## Provider parameters

        ```yaml
        providers:
          {provider}:
            enabled: true
            mcp_server: {mcp_server}
        ```

        ## Failure behavior

        - Validation: `service_category` must be `{category}`, `active_provider` must exist under `providers`, provider must be `enabled: true`, skill must be resolvable.
        - On failure: abort the dependent remote operation and inform the user.

        ## Example

        ```yaml
        service_category: {category}
        active_provider: {provider}
        provider_mode: mcp
        skill_binding:
{example_skill_binding}
        providers:
          {provider}:
            enabled: true
            mcp_server: {mcp_server}
        ```
    """)

    path = PROVIDERS_DIR / f"{category}-config.md"
    safe_write(path, content)


# ---------------------------------------------------------------------------
# new --context (RHOAIAS.md)
# ---------------------------------------------------------------------------

def new_context() -> None:
    print("\n--- RHOAIAS.md (Project Context) ---")
    project_name = ask("Project name")
    platform = ask("Platform (e.g. iOS, Android, Web)")
    description = ask("Brief description")
    architecture = ask("Architecture pattern (e.g. MVVM, Clean Architecture)")
    technologies = ask("Key technologies (comma-separated)")

    content = textwrap.dedent(f"""\
        # {project_name}

        ## Project Overview
        {description}

        **Platform:** {platform}

        ## Project Structure
        < Describe main directories and their purpose using tree format >

        ## Conventions
        - **Architecture**: {architecture}
        - **UI Framework**: < fill >
        - **DI Approach**: < fill >
        - **Code Style**: < fill >
        - **Testing Strategy**: < fill >

        ## Key Technologies
        {technologies}

        ## Build and Test
        < Document build commands, test commands, CI/CD notes >

        ## Related Documentation
        < Links to style guides, READMEs, external docs >

        ## Rho AIAS Integration

        This project uses [Rho AIAS](https://github.com/org/rho-aias) for AI-assisted development.

        - **Rules**: `aias-config/rules/` — Generated behavioral rules (always-apply and output contracts)
        - **Modes**: `aias-config/modes/` — Generated task-specific modes (planning, dev, QA, debug, review, product, integration)
        - **Skills**: `aias/.skills/` (framework) + `aias-config/skills/` (project) — All skills including advisory/operative (commands)
        - **Providers**: `aias-config/providers/` — Provider configuration files

        > This file is the single source of truth for project context. Tool-specific context files (e.g., `AGENTS.md`) are symlinks to this file, scoped by the tools selected in `stack-profile.md`.
    """)

    path = ROOT / "RHOAIAS.md"
    safe_write(path, content)


# ---------------------------------------------------------------------------
# new --stack-profile
# ---------------------------------------------------------------------------

def new_stack_profile() -> None:
    print("\n--- Stack Profile ---")
    language = ask("Language and version (e.g. Swift 6.0, Kotlin 2.0)")
    build_system = ask("Build system (e.g. Xcode, Gradle, SPM)")
    ui_framework = ask("UI framework (e.g. SwiftUI, Jetpack Compose)")
    test_framework = ask("Testing framework (e.g. Swift Testing, JUnit + MockK)")
    tools = ask_multi_choice(
        "Target AI coding tools (select which tools to generate shortcuts for):",
        list(SUPPORTED_TOOLS),
    )
    tools_csv = ",".join(tools)
    tasks_dir = ask("Tasks directory (base path for task artifacts)", "~/.cursor/plans/")

    content = textwrap.dedent(f"""\
        # Stack Profile

        ## Platform Identity
        - **Language**: {language}
        - **Build system**: {build_system}
        - **UI framework**: {ui_framework}
        - **Testing framework**: {test_framework}

        ## Generation Bindings

        < Add binding.* entries below. See aias/contracts/readme-stack-profile.md for required keys. >

        - `binding.generation.stack_id`: `< stack-id >`
        - `binding.generation.canonical_mode_output_dir`: `aias-config/modes`
        - `binding.generation.canonical_rule_output_dir`: `aias-config/rules`
        - `binding.generation.tools`: `{tools_csv}`
        - `binding.generation.tasks_dir`: `{tasks_dir}`

        ## Mode Bindings

        < Add binding.mode.<mode>.* entries for all 7 modes: planning, dev, qa, debug, review, product, integration >

        ## Rule Bindings

        < Add binding.rule.base.* and binding.rule.output_contract.* entries >
    """)

    path = ROOT / "stack-profile.md"
    safe_write(path, content)


# ---------------------------------------------------------------------------
# new --stack-fragment
# ---------------------------------------------------------------------------

def new_stack_fragment() -> None:
    print("\n--- Stack Fragment (Build System Integration) ---")
    option = ask_choice(
        "Fragment type:",
        [
            "A: Automatic inclusion (SPM, Gradle, npm, etc.)",
            "B: Manual project file integration (Xcode pbxproj, CMake, etc.)",
            "C: Hybrid (e.g. SPM package + Xcode demo app)",
        ],
    )

    if option.startswith("A"):
        build_tool = ask("Build tool name (e.g. Swift Package Manager, Gradle)")
        source_dir = ask("Source directory (e.g. Sources/, src/main/java/)")
        content = textwrap.dedent(f"""\
            BUILD SYSTEM STRUCTURE
            - Files are managed by {build_tool}, not manual project configuration.
            - New files are automatically included if placed in the correct {source_dir} structure.
            - No manual build file modifications needed.
        """)
    elif option.startswith("B"):
        has_removal = confirm(
            "Does removing files also require updating the project file? "
            "(e.g., Xcode pbxproj, CMakeLists.txt)",
            default_yes=True,
        )
        removal_block = ""
        if has_removal:
            removal_block = textwrap.dedent("""
            PROCESS FOR REMOVING FILES:
            When deleting a file that is part of the project, ensure all references are removed from the project file to prevent build errors and orphaned references.

            1) Locate all references to the file:
               - < DESCRIBE HOW TO FIND REFERENCES >

            2) Identify the sections to clean up:
               - < DESCRIBE SECTIONS >

            3) Remove all entries:
               - < DESCRIBE STEPS >

            4) Verify removal:
               - < DESCRIBE VERIFICATION >

            In the reasoning section, explicitly state:
              - that the file was removed from the project,
              - which sections of the project file were modified,
              - that all references were verified as removed (no orphaned entries).
            """)

        content = textwrap.dedent("""\
            PROJECT FILE INTEGRATION (NEW FILES)
            - When creating a new file that must be part of the project, ensure it is added to the correct project and target(s).
            - This applies ONLY to source and resource files managed by the build system such as:
              - < LIST FILE TYPES >
            - This does NOT apply to documentation or configuration files (e.g., .md, .mdc, .cursor/*).

            PROCESS FOR ADDING FILES:
            When manually adding files to the project file, follow these steps:

            1) Identify reference files:
               - Search for similar files in the same directory to understand the pattern.

            2) Identify the sections to modify:
               - < DESCRIBE SECTIONS AND FORMATS >

            3) Perform the modifications:
               - < DESCRIBE STEPS >

            4) Verify consistency:
               - < DESCRIBE VERIFICATION >

            In the reasoning section, explicitly state:
              - which project/target(s) the file was added to,
              - where it lives in the project structure,
              - that all required sections were updated correctly.
        """) + removal_block
    else:
        content = textwrap.dedent("""\
            < Combine Option A (for the package) and Option B (for the app).
              Replace this placeholder with actual content. >
        """)

    path = ROOT / "stack-fragment.md"
    safe_write(path, content)


# ---------------------------------------------------------------------------
# Sub-agent symlinks (BL-S53, Cursor only)
# ---------------------------------------------------------------------------

# Canonical sub-agent sources live in aias/.cursor/agents/ (framework, read-only).
# Projected shortcuts live in .cursor/agents/ (created by aias init, validated by aias health).
FW_AGENTS_DIR = ROOT / "aias" / ".cursor" / "agents"
REVIEW_SUBAGENTS = (
    "aias-correctness-reviewer.md",
    "aias-quality-reviewer.md",
    "aias-architecture-reviewer.md",
    "aias-test-auditor.md",
    "aias-security-auditor.md",
    "aias-reflector.md",
)
# Frontmatter invariants enforced by aias health
SUBAGENT_REQUIRED_FRONTMATTER = {
    "readonly": "true",
    "is_background": "false",
}


def _parse_subagent_frontmatter(agent_file: pathlib.Path) -> Dict[str, str]:
    """Parse YAML frontmatter from a Cursor sub-agent .md file."""
    if not agent_file.is_file():
        return {}
    text = agent_file.read_text(encoding="utf-8")
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


def _create_symlink_for_path(link_path: pathlib.Path, target_path: pathlib.Path) -> None:
    """Create a relative symlink. Idempotent: removes existing file or symlink first."""
    rel_target = os.path.relpath(target_path, link_path.parent)
    if link_path.is_symlink() or link_path.exists():
        link_path.unlink()
    link_path.parent.mkdir(parents=True, exist_ok=True)
    link_path.symlink_to(rel_target)


def _ensure_review_subagent_symlinks() -> None:
    """Create/refresh .cursor/agents/ symlinks for the 6 BL-S53 review sub-agents."""
    agents_dir = ROOT / ".cursor" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    created = 0
    skipped = 0
    for agent_name in REVIEW_SUBAGENTS:
        source = FW_AGENTS_DIR / agent_name
        link = agents_dir / agent_name
        if not source.is_file():
            print(f"  [WARN] Framework sub-agent not found: {source.relative_to(ROOT)}")
            skipped += 1
            continue
        _create_symlink_for_path(link, source)
        created += 1
    print(f"\n  Review sub-agents: {created} symlink(s) created/refreshed in .cursor/agents/"
          + (f" ({skipped} skipped — source not found)" if skipped else ""))


def _check_review_subagent_integrity(results: List[HealthStatus]) -> None:
    """Validate presence and frontmatter invariants for all 6 BL-S53 review sub-agents."""
    agents_dir = ROOT / ".cursor" / "agents"
    missing: List[str] = []
    violations: List[str] = []

    for agent_name in REVIEW_SUBAGENTS:
        link = agents_dir / agent_name
        if not link.exists():
            missing.append(agent_name)
            continue
        # Resolve symlink to read actual content
        actual = link.resolve() if link.is_symlink() else link
        fm = _parse_subagent_frontmatter(actual)
        for field, expected in SUBAGENT_REQUIRED_FRONTMATTER.items():
            actual_val = fm.get(field, "").lower()
            if actual_val != expected:
                violations.append(f"{agent_name}: {field}={actual_val!r} (expected {expected!r})")

    if not missing:
        results.append(("Review sub-agents presence", "OK",
                        f"All {len(REVIEW_SUBAGENTS)} sub-agents present in .cursor/agents/"))
    else:
        preview = "; ".join(missing[:3])
        suffix = f" (+{len(missing) - 3} more)" if len(missing) > 3 else ""
        results.append(("Review sub-agents presence", "WARN",
                        f"Missing sub-agent(s): {preview}{suffix}. Run: aias init"))

    if not violations:
        results.append(("Review sub-agents invariants", "OK",
                        "readonly: true and is_background: false confirmed for all sub-agents"))
    else:
        preview = "; ".join(violations[:3])
        suffix = f" (+{len(violations) - 3} more)" if len(violations) > 3 else ""
        results.append(("Review sub-agents invariants", "FAIL",
                        f"Invariant violation(s): {preview}{suffix}"))


# ---------------------------------------------------------------------------
# init — provider config helper
# ---------------------------------------------------------------------------

def _init_providers() -> None:
    print("\n--- Provider Configs (aias-config/providers/) ---")
    print("Select which categories to configure:\n")

    selected = []
    for cat in PROVIDER_CATEGORIES:
        cap = CAPABILITY_SUGGESTIONS.get(cat, "")
        mcp = MCP_SERVER_EXAMPLES.get(cat, "")
        hint = f"e.g. {mcp}, capability: {cap}"
        if confirm(f"  Configure {cat}? ({hint})"):
            selected.append(cat)

    if not selected:
        print("  No categories selected. Skipping.")
        return

    for cat in selected:
        print(f"\n--- {cat} provider ---")
        new_provider(cat)

    print(f"\n  {len(selected)} provider config(s) created in aias-config/providers/.")


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

def cmd_init(args: List[str]) -> None:
    print("=" * 60)
    print("  Rho AIAS — Project Onboarding")
    print("=" * 60)

    rhoaias = ROOT / "RHOAIAS.md"
    profile = ROOT / "stack-profile.md"
    fragment = ROOT / "stack-fragment.md"

    exists = [f for f in (rhoaias, profile, fragment) if f.is_file()]
    missing = [f for f in (rhoaias, profile, fragment) if not f.is_file()]

    if len(exists) == 3:
        print("\nAll configuration files already exist:")
        for f in exists:
            print(f"  - {f.relative_to(ROOT)}")
        if not confirm("Reconfigure? This will overwrite existing files."):
            print("Aborted.")
            return
    elif exists:
        print("\nPartial setup detected. Existing files will be kept unless you overwrite:")
        for f in exists:
            print(f"  [exists] {f.relative_to(ROOT)}")
        for f in missing:
            print(f"  [missing] {f.relative_to(ROOT)}")
        print()

    # Step 2: Context
    if not rhoaias.is_file() or confirm("Create/overwrite RHOAIAS.md?", default_yes=True):
        new_context()

    # Step 3: Stack profile
    if not profile.is_file() or confirm("Create/overwrite stack-profile.md?", default_yes=True):
        new_stack_profile()

    # Step 4: Stack fragment
    if not fragment.is_file() or confirm("Create/overwrite stack-fragment.md?", default_yes=True):
        new_stack_fragment()

    # Step 5: Context symlinks (→ RHOAIAS.md, scoped by tool selection)
    try:
        max_depth = _parse_max_depth(args, default=0)
    except ValueError as exc:
        print(f"Error: {exc}")
        sys.exit(1)
    selected_tools = _read_tools_from_profile()
    print("\nCreating context symlinks → RHOAIAS.md...")
    rhoaias_files = _discover_rhoaias_files(max_depth=max_depth)
    for rhoaias_target in rhoaias_files:
        context_dir = rhoaias_target.parent
        rel_dir = context_dir.relative_to(ROOT)
        prefix = "." if str(rel_dir) == "." else str(rel_dir)
        for filename, required_tools in TOOL_CONTEXT_MAP.items():
            if selected_tools and not any(t in selected_tools for t in required_tools):
                continue
            link_path = context_dir / filename
            if link_path.is_symlink():
                current = (link_path.parent / os.readlink(link_path)).resolve()
                if current == rhoaias_target.resolve():
                    print(f"  [ok] {prefix}/{filename} → RHOAIAS.md (already a valid symlink)")
                    continue
            if link_path.is_file():
                rel_file = link_path.relative_to(ROOT)
                if not confirm(f"  '{rel_file}' exists as a regular file. Replace with symlink?", default_yes=True):
                    print(f"  Skipped: {rel_file}")
                    continue
            _create_symlink(link_path, rhoaias_target)
            rel_file = link_path.relative_to(ROOT)
            print(f"  Created: {rel_file} → {rhoaias_target.relative_to(ROOT)}")

    # Step 5b: Ensure aias-config/ structure
    for d in (AIAS_CONFIG_DIR, RULES_DIR, MODES_DIR, PROVIDERS_DIR):
        d.mkdir(parents=True, exist_ok=True)
    print(f"\n  aias-config/ structure ensured.")

    # Step 5c: Sub-agent symlinks (Cursor only — BL-S53)
    if "cursor" in selected_tools:
        _ensure_review_subagent_symlinks()

    # Step 6: Generate
    rc = run_generator(shortcuts=True)
    if rc == 0:
        print("\n" + "=" * 60)
        print("  Project setup complete!")
        print("=" * 60)
    else:
        print(f"\nGenerator exited with code {rc}. Check errors above.")

    sys.exit(rc)


# ---------------------------------------------------------------------------
# new (dispatcher)
# ---------------------------------------------------------------------------

NEW_HELP = """\
Usage: aias new <flag> [name]

Flags:
  -m, --mode <name>         Create a mode (file-specific or intelligent)
  -r, --rule <name>         Create an always-apply rule
  -c, --command <name>      [DEPRECATED] Redirect to --skill (advisory or operative)
  -s, --skill <name>        Create a skill (mcp|knowledge|tool|advisory|operative)
  --migrate-commands        Migrate aias-config/commands/ to aias-config/skills/
  -P, --provider <category> Create a provider config (knowledge|tracker|design|vcs)
  -C, --context             Create RHOAIAS.md
  -p, --stack-profile       Create stack-profile.md
  -f, --stack-fragment      Create stack-fragment.md
"""


def cmd_new(args: List[str]) -> None:
    if not args:
        print(NEW_HELP)
        return

    flag = args[0]
    name = args[1] if len(args) > 1 else ""

    post_generate = True

    if flag in ("-m", "--mode"):
        if not name:
            print("Error: mode name is required. Usage: aias new --mode <name>")
            sys.exit(1)
        new_mode(name)
    elif flag in ("-r", "--rule"):
        if not name:
            print("Error: rule name is required. Usage: aias new --rule <name>")
            sys.exit(1)
        new_rule(name)
    elif flag in ("-c", "--command"):
        if not name:
            print("Error: command name is required. Usage: aias new --command <name>")
            sys.exit(1)
        new_command(name)
    elif flag in ("-s", "--skill"):
        if not name:
            print("Error: skill name is required. Usage: aias new --skill <name>")
            sys.exit(1)
        new_skill(name)
    elif flag == "--migrate-commands":
        migrate_commands()
        post_generate = False
    elif flag in ("-P", "--provider"):
        if not name:
            print("Error: provider category is required. Usage: aias new --provider <category>")
            sys.exit(1)
        new_provider(name)
        post_generate = False
    elif flag in ("-C", "--context"):
        new_context()
    elif flag in ("-p", "--stack-profile"):
        new_stack_profile()
    elif flag in ("-f", "--stack-fragment"):
        new_stack_fragment()
    else:
        print(f"Unknown flag: {flag}")
        print(NEW_HELP)
        sys.exit(1)

    if post_generate:
        rc = run_generator(shortcuts=True)
        sys.exit(rc)


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------

def cmd_generate(args: List[str]) -> None:
    shortcuts = any(a in ("-s", "--shortcuts") for a in args)
    tools_arg = None
    max_depth = 0
    for i, a in enumerate(args):
        if a in ("-t", "--tools") and i + 1 < len(args):
            tools_arg = args[i + 1]
    try:
        max_depth = _parse_max_depth(args, default=0)
    except ValueError as exc:
        print(f"Error: {exc}")
        sys.exit(1)
    cmd = [sys.executable, str(GENERATOR)]
    if shortcuts:
        cmd.append("--shortcuts")
    if tools_arg:
        cmd.extend(["--tools", tools_arg])
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode == 0 and shortcuts:
        selected_tools = _read_tools_from_profile()
        rhoaias_files = _discover_rhoaias_files(max_depth=max_depth)
        created = _ensure_context_symlinks_for_rhoaias(rhoaias_files, selected_tools)
        if created:
            print(f"Created {created} nested context symlink(s).")
        if "cursor" in selected_tools:
            _ensure_review_subagent_symlinks()
    sys.exit(result.returncode)


# ---------------------------------------------------------------------------
# health
# ---------------------------------------------------------------------------

HealthStatus = Tuple[str, str, str]  # (check_name, status, detail)


def _is_within_shortcut_boundary(
    target: pathlib.Path,
    boundaries: List[pathlib.Path],
) -> bool:
    """Check if a resolved path stays inside allowed shortcut boundary paths."""
    for boundary in boundaries:
        resolved_boundary = boundary.resolve(strict=False)
        if target == resolved_boundary:
            return True
        try:
            target.relative_to(resolved_boundary)
            return True
        except ValueError:
            continue
    return False


def _extract_shortcut_refs(content: str) -> List[str]:
    """Extract canonical path references embedded in enriched-text shortcuts."""
    return SHORTCUT_REF_RE.findall(content)


def _check_shortcut_runtime_integrity(
    selected_tools: List[str],
    results: List[HealthStatus],
) -> None:
    """Validate runtime shortcut directories, links, boundaries, and content references."""
    applicable_tools = [tool for tool in selected_tools if tool in TOOL_SHORTCUT_DIRS]
    if not applicable_tools:
        return

    shortcut_dirs = [
        (tool, ROOT / rel_dir)
        for tool in applicable_tools
        for rel_dir in TOOL_SHORTCUT_DIRS[tool]
    ]
    boundaries = [ROOT / rel_path for rel_path in SHORTCUT_BOUNDARY_PATHS]

    missing_dirs: List[str] = []
    broken_symlinks: List[str] = []
    out_of_bounds: List[str] = []
    missing_refs: List[str] = []
    symlink_count = 0

    for tool, shortcut_dir in shortcut_dirs:
        if not shortcut_dir.is_dir():
            missing_dirs.append(f"{tool}:{shortcut_dir.relative_to(ROOT)}")
            continue

        for item in shortcut_dir.rglob("*"):
            if item.is_symlink():
                symlink_count += 1
                if not item.exists():
                    broken_symlinks.append(str(item.relative_to(ROOT)))
                    continue

                target = (item.parent / os.readlink(item)).resolve()
                if not _is_within_shortcut_boundary(target, boundaries):
                    out_of_bounds.append(f"{item.relative_to(ROOT)} -> {target}")
                continue

            if item.is_file() and item.suffix in (".md", ".mdc"):
                content = item.read_text(encoding="utf-8", errors="replace")
                for ref in _extract_shortcut_refs(content):
                    referenced_path = (ROOT / ref).resolve(strict=False)
                    if not referenced_path.exists():
                        missing_refs.append(f"{item.relative_to(ROOT)} references {ref}")

    if not missing_dirs:
        results.append(("Shortcut dirs", "OK", "All expected runtime shortcut directories exist"))
    else:
        preview = "; ".join(missing_dirs[:3])
        suffix = f" (+{len(missing_dirs) - 3} more)" if len(missing_dirs) > 3 else ""
        results.append(("Shortcut dirs", "WARN", f"Missing directory(ies): {preview}{suffix}"))

    if not broken_symlinks:
        results.append(("Shortcut symlinks", "OK", f"{symlink_count} symlink(s) resolve correctly"))
    else:
        preview = "; ".join(broken_symlinks[:3])
        suffix = f" (+{len(broken_symlinks) - 3} more)" if len(broken_symlinks) > 3 else ""
        results.append(("Shortcut symlinks", "FAIL", f"Broken symlink(s): {preview}{suffix}"))

    if not out_of_bounds:
        results.append(("Shortcut boundary", "OK", "All shortcut targets are within allowed boundaries"))
    else:
        preview = "; ".join(out_of_bounds[:3])
        suffix = f" (+{len(out_of_bounds) - 3} more)" if len(out_of_bounds) > 3 else ""
        results.append(("Shortcut boundary", "FAIL", f"Out-of-bound shortcut(s): {preview}{suffix}"))

    if not missing_refs:
        results.append(("Shortcut content refs", "OK", "All canonical references in shortcut content exist"))
    else:
        preview = "; ".join(missing_refs[:3])
        suffix = f" (+{len(missing_refs) - 3} more)" if len(missing_refs) > 3 else ""
        results.append(("Shortcut content refs", "WARN", f"Missing reference(s): {preview}{suffix}"))

    # Legacy command shortcut check: detect symlinks pointing into aias/.commands/ (retired)
    legacy_dir = ROOT / LEGACY_COMMAND_DIR
    legacy_shortcuts: List[str] = []
    for tool, shortcut_dir in shortcut_dirs:
        if not shortcut_dir.is_dir():
            continue
        for item in shortcut_dir.rglob("*"):
            if item.is_symlink() and item.exists():
                target = (item.parent / os.readlink(item)).resolve()
                if legacy_dir.exists() and str(target).startswith(str(legacy_dir.resolve())):
                    legacy_shortcuts.append(str(item.relative_to(ROOT)))

    if not legacy_shortcuts:
        results.append(("Legacy command shortcuts", "OK", "No shortcuts pointing to retired aias/.commands/"))
    else:
        preview = "; ".join(legacy_shortcuts[:3])
        suffix = f" (+{len(legacy_shortcuts) - 3} more)" if len(legacy_shortcuts) > 3 else ""
        results.append((
            "Legacy command shortcuts", "WARN",
            f"Shortcut(s) still pointing to retired aias/.commands/: {preview}{suffix}. "
            "Run: aias new --migrate-commands  (project) or update generator (framework).",
        ))

    # Stale .cursor/commands/ directory check: Cursor no longer uses this directory.
    # Command-shaped skills are now projected into .cursor/skills/. If .cursor/commands/
    # still exists with content, it is a stale artifact from a previous generator run.
    if "cursor" in selected_tools:
        cursor_cmds_dir = ROOT / ".cursor" / "commands"
        stale_entries = (
            [p.name for p in cursor_cmds_dir.iterdir()]
            if cursor_cmds_dir.is_dir() else []
        )
        if stale_entries:
            preview = "; ".join(stale_entries[:3])
            suffix = f" (+{len(stale_entries) - 3} more)" if len(stale_entries) > 3 else ""
            results.append((
                "Stale .cursor/commands/", "WARN",
                f"Directory exists with content: {preview}{suffix}. "
                "Remove it — commands are now skills in .cursor/skills/. "
                "Run: rm -rf .cursor/commands/",
            ))
        else:
            results.append(("Stale .cursor/commands/", "OK", "Directory absent or empty (correct)"))


def cmd_health() -> None:
    print("=" * 60)
    print("  Rho AIAS — Health Check")
    print("=" * 60)
    print()

    results: List[HealthStatus] = []

    # 1. RHOAIAS.md (existence + staleness + placeholders)
    rhoaias = ROOT / "RHOAIAS.md"
    if rhoaias.is_file():
        results.append(("RHOAIAS.md", "OK", "Exists"))
        rhoaias_content = rhoaias.read_text(encoding="utf-8", errors="replace")
        if re.search(r"<\s+[^>]+\s+>", rhoaias_content):
            results.append(("RHOAIAS.md freshness", "WARN",
                "Contains unfilled placeholders — complete onboarding"))
        else:
            try:
                mtime = rhoaias.stat().st_mtime
                import datetime
                age_days = (datetime.datetime.now().timestamp() - mtime) / 86400
                git_count = subprocess.run(
                    ["git", "rev-list", "--count",
                     f"--after={int(mtime)}", "HEAD"],
                    capture_output=True, text=True, cwd=str(ROOT),
                ).stdout.strip()
                commits_since = int(git_count) if git_count.isdigit() else 0
                if age_days > 60 and commits_since > 30:
                    results.append(("RHOAIAS.md freshness", "WARN",
                        f"Last modified {int(age_days)} days ago "
                        f"({commits_since} commits since). "
                        "Consider `/aias refresh-context`"))
                else:
                    results.append(("RHOAIAS.md freshness", "OK",
                        f"Modified {int(age_days)} days ago "
                        f"({commits_since} commits since)"))
            except Exception:
                pass
        results.append(("RHOAIAS.md context sync", "INFO",
            "Run `/aias refresh-context` to check for pending "
            "context updates from published deltas"))
    else:
        results.append(("RHOAIAS.md", "FAIL", "Not found"))

    nested_rhoaias = [p for p in _discover_rhoaias_files(max_depth=5) if p != rhoaias]
    if nested_rhoaias:
        stale_nested = 0
        import datetime
        for nested in nested_rhoaias:
            try:
                age_days = (datetime.datetime.now().timestamp() - nested.stat().st_mtime) / 86400
            except Exception:
                age_days = 0
            if age_days >= 30:
                stale_nested += 1
        if stale_nested:
            results.append(("Nested RHOAIAS.md freshness", "WARN",
                f"{stale_nested}/{len(nested_rhoaias)} nested context file(s) older than 30 days"))
        else:
            results.append(("Nested RHOAIAS.md freshness", "OK",
                f"{len(nested_rhoaias)} nested context file(s) within freshness threshold"))

    # 2. stack-profile.md
    profile = ROOT / "stack-profile.md"
    if profile.is_file():
        results.append(("stack-profile.md", "OK", "Exists"))
    else:
        results.append(("stack-profile.md", "FAIL", "Not found"))

    # 3. stack-fragment.md
    fragment = ROOT / "stack-fragment.md"
    if fragment.is_file():
        results.append(("stack-fragment.md", "OK", "Exists"))
    else:
        results.append(("stack-fragment.md", "FAIL", "Not found"))

    # 4. aias/ + aias-config/ structure
    aias_root = ROOT / "aias"
    if not aias_root.is_dir():
        results.append(("aias/ structure", "FAIL", "aias/ directory not found"))
    else:
        # aias/.commands/ is retired (BL-S36); only aias/.skills/ is required.
        fw_dirs = [FW_SKILLS_DIR]
        missing_fw = [d for d in fw_dirs if not d.is_dir()]
        if not missing_fw:
            results.append(("aias/ structure", "OK", "Framework directories present"))
        else:
            names = ", ".join(str(d.relative_to(ROOT)) for d in missing_fw)
            results.append(("aias/ structure", "WARN", f"Missing: {names}"))

    config_dirs = [RULES_DIR, MODES_DIR, PROVIDERS_DIR]
    if not AIAS_CONFIG_DIR.is_dir():
        results.append(("aias-config/ structure", "WARN", "aias-config/ not found — run 'aias init' or 'aias generate'"))
    else:
        missing_cfg = [d for d in config_dirs if not d.is_dir()]
        if not missing_cfg:
            results.append(("aias-config/ structure", "OK", "All subdirectories present"))
        else:
            names = ", ".join(str(d.relative_to(ROOT)) for d in missing_cfg)
            results.append(("aias-config/ structure", "WARN", f"Missing: {names}"))

    # 5. Contracts
    contracts = ROOT / "aias" / "contracts"
    if contracts.is_dir():
        count = len(list(contracts.glob("*.md")))
        if count >= 10:
            results.append(("Contracts", "OK", f"{count} contract files"))
        else:
            results.append(("Contracts", "WARN", f"Only {count} contracts (expected >= 10)"))
    else:
        results.append(("Contracts", "FAIL", "aias/contracts/ not found"))

    # 6. Generator
    if GENERATOR.is_file():
        results.append(("Generator", "OK", "generate_modes_and_rules.py present"))
    else:
        results.append(("Generator", "FAIL", "Generator script not found"))

    # 7. Shortcut consistency (scoped by tool selection)
    selected_tools = _read_tools_from_profile()
    _tool_rules_dirs: Dict[str, pathlib.Path] = {
        "cursor": ROOT / ".cursor" / "rules",
        "claude": ROOT / ".claude" / "rules",
    }
    canonical_modes = list(MODES_DIR.glob("*.mdc")) if MODES_DIR.is_dir() else []
    canonical_rules = list(RULES_DIR.glob("*.mdc")) if RULES_DIR.is_dir() else []
    canonical_count = len(canonical_modes) + len(canonical_rules)

    if not selected_tools:
        results.append(("Shortcuts", "WARN", "Cannot determine tools (no binding.generation.tools in stack-profile.md)"))
    else:
        divergences = []
        for tool, sdir in _tool_rules_dirs.items():
            if tool not in selected_tools:
                continue
            if sdir.is_dir():
                sc_count = len(list(sdir.glob("*.mdc"))) + len(list(sdir.glob("*.md")))
                if sc_count != canonical_count:
                    divergences.append(f"{tool}: {sc_count} shortcuts vs {canonical_count} canonical")
        if not divergences:
            results.append(("Shortcuts", "OK", f"Counts match canonical (tools: {','.join(selected_tools)})"))
        else:
            results.append(("Shortcuts", "WARN", "; ".join(divergences)))

    # 7b. Shortcut integrity (G6/G7 from generator)
    if selected_tools and canonical_modes:
        try:
            gen_dir = str(CANONICAL_DIR / "generation")
            if gen_dir not in sys.path:
                sys.path.insert(0, gen_dir)
            from generate_modes_and_rules import (
                _gate_6_shortcut_consistency,
                _gate_7_no_duplication,
            )
            mode_names = [p.stem for p in canonical_modes]
            g6_errors = _gate_6_shortcut_consistency(mode_names, list(selected_tools))
            g7_errors = _gate_7_no_duplication(list(selected_tools))
            integrity_errors = g6_errors + g7_errors
            if not integrity_errors:
                results.append(("Shortcut integrity", "OK", "G6/G7 passed"))
            else:
                preview = "; ".join(integrity_errors[:3])
                suffix = f" (+{len(integrity_errors) - 3} more)" if len(integrity_errors) > 3 else ""
                results.append(("Shortcut integrity", "FAIL",
                    f"{len(integrity_errors)} issue(s): {preview}{suffix}. Run 'aias generate --shortcuts' to fix"))
        except ImportError:
            results.append(("Shortcut integrity", "WARN", "Could not import generator module for G6/G7 checks"))
    elif not selected_tools:
        results.append(("Shortcut integrity", "WARN", "Cannot run G6/G7 (no binding.generation.tools)"))

    # 7c. Shortcut runtime integrity checks (always active)
    if selected_tools:
        _check_shortcut_runtime_integrity(selected_tools, results)

    # 8. Context symlinks (scoped by tool selection)
    rhoaias_path = ROOT / "RHOAIAS.md"
    if not selected_tools:
        results.append(("Context symlinks", "WARN", "Cannot determine expected symlinks (no binding.generation.tools)"))
    else:
        expected_files = [f for f, tools in TOOL_CONTEXT_MAP.items() if any(t in selected_tools for t in tools)]
        ctx_missing: List[str] = []
        ctx_not_symlink: List[str] = []
        ctx_broken: List[str] = []
        for f in expected_files:
            p = ROOT / f
            if not p.exists() and not p.is_symlink():
                ctx_missing.append(f)
            elif p.is_symlink():
                target = (p.parent / os.readlink(p)).resolve()
                if not p.exists():
                    ctx_broken.append(f)
                elif target != rhoaias_path.resolve():
                    ctx_not_symlink.append(f"{f} (wrong target)")
            else:
                ctx_not_symlink.append(f"{f} (regular file)")

        if not ctx_missing and not ctx_not_symlink and not ctx_broken:
            results.append(("Context symlinks", "OK", f"{len(expected_files)} symlink(s) → RHOAIAS.md"))
        elif ctx_missing:
            results.append(("Context symlinks", "WARN", f"Missing: {', '.join(ctx_missing)}"))
        elif ctx_broken:
            results.append(("Context symlinks", "WARN", f"Broken symlinks: {', '.join(ctx_broken)}"))
        else:
            results.append(("Context symlinks", "WARN", f"Not symlinks: {', '.join(ctx_not_symlink)}"))

    # 8b. Review sub-agent integrity (Cursor only — BL-S53)
    if selected_tools and "cursor" in selected_tools:
        _check_review_subagent_integrity(results)

    # 9. Provider configs
    if PROVIDERS_DIR.is_dir():
        configs = list(PROVIDERS_DIR.glob("*-config.md"))
        if configs:
            results.append(("Provider configs", "OK", f"{len(configs)} config(s) in aias-config/providers/"))
        else:
            results.append(("Provider configs", "WARN", "aias-config/providers/ exists but has no *-config.md files"))
    else:
        results.append(("Provider configs", "WARN", "aias-config/providers/ not found — run 'aias new --provider <category>' to create"))

    # 9b. Legacy provider location detection
    if LEGACY_PROVIDERS_DIR.is_dir():
        results.append(("Legacy providers", "WARN",
            "Legacy provider location: aias-providers/. Run /aias health in AI assistant to migrate and clean up (coexistence period expired in v8.0)"))

    # 9c. Legacy generated rules/modes location detection
    legacy_rules = ROOT / "aias" / ".rules"
    legacy_modes = ROOT / "aias" / ".modes"
    if legacy_rules.is_dir() and list(legacy_rules.glob("*.mdc")):
        results.append(("Legacy rules", "WARN",
            "Legacy generated rules in aias/.rules/. Run /aias health in AI assistant to regenerate and clean up (coexistence period expired in v8.0)"))
    if legacy_modes.is_dir() and list(legacy_modes.glob("*.mdc")):
        results.append(("Legacy modes", "WARN",
            "Legacy generated modes in aias/.modes/. Run /aias health in AI assistant to regenerate and clean up (coexistence period expired in v8.0)"))

    # 9d. Legacy shortcut targets
    if selected_tools and "cursor" in selected_tools:
        cursor_rules = ROOT / ".cursor" / "rules"
        if cursor_rules.is_dir():
            for link in cursor_rules.iterdir():
                if link.is_symlink():
                    target = str(os.readlink(link))
                    if "aias/.rules/" in target or "aias/.modes/" in target:
                        results.append(("Legacy shortcuts", "WARN",
                            "Shortcuts point to legacy location. Run aias generate --shortcuts to update"))
                        break

    # 9e. Canonical output bindings
    for _ck, _ce, _cl in [
        ("binding.generation.canonical_mode_output_dir", "aias-config/modes", "aias/.modes"),
        ("binding.generation.canonical_rule_output_dir", "aias-config/rules", "aias/.rules"),
    ]:
        _cv = _read_binding_from_profile(_ck)
        if _cv and _cv in (_cl, _cl.rstrip("/")):
            results.append(("Legacy canonical bindings", "WARN",
                f"{_ck} points to legacy '{_cv}'. Expected: '{_ce}'"))
    _dep_val = _read_binding_from_profile("binding.generation.mode_output_dir")
    if _dep_val:
        results.append(("Deprecated binding", "WARN",
            "binding.generation.mode_output_dir is deprecated. Remove it and use canonical_mode_output_dir."))

    # 10. Provider referenced files (resource_files validation)
    CATEGORIES_WITH_RESOURCE_FILES = {"tracker", "knowledge"}
    LEGACY_PREFIXES = ("aias-providers/",)
    if PROVIDERS_DIR.is_dir():
        for cfg in sorted(PROVIDERS_DIR.glob("*-config.md")):
            cat = cfg.stem.replace("-config", "")
            if cat not in CATEGORIES_WITH_RESOURCE_FILES:
                continue
            text = cfg.read_text(encoding="utf-8")
            resource_files: List[str] = []
            has_resource_files_key = False
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("resource_files:"):
                    has_resource_files_key = True
                    if "[]" in stripped:
                        resource_files = []
                    continue
                if has_resource_files_key and stripped.startswith("- "):
                    path_val = stripped[2:].strip().strip("'\"")
                    if path_val and not path_val.startswith("#"):
                        resource_files.append(path_val)
                elif has_resource_files_key and not stripped.startswith("-") and not stripped.startswith("#"):
                    break

            check_name = f"Referenced files ({cat})"
            if not has_resource_files_key:
                results.append((check_name, "FAIL",
                    f"Missing resource_files in {cfg.name}. Run /aias configure-providers to generate referenced files"))
            elif not resource_files:
                results.append((check_name, "WARN",
                    f"No referenced files configured in {cfg.name}. Run /aias configure-providers to generate referenced files"))
            else:
                for rf in resource_files:
                    rf_path = ROOT / rf
                    if any(rf.startswith(lp) for lp in LEGACY_PREFIXES):
                        results.append((check_name, "WARN",
                            f"Legacy location: {rf}. Run /aias health in AI assistant to migrate"))
                    elif rf_path.is_file():
                        results.append((check_name, "OK", f"{rf} exists"))
                    else:
                        results.append((check_name, "FAIL",
                            f"Missing: {rf}. Run /aias configure-providers to generate missing files"))

    # 10b. Section validation for referenced files
    if PROVIDERS_DIR.is_dir():
        for provider_dir in sorted(PROVIDERS_DIR.iterdir()):
            if not provider_dir.is_dir():
                continue
            for ref_file in sorted(provider_dir.glob("*.md")):
                schema = EXPECTED_SECTIONS.get(ref_file.name)
                if not schema:
                    continue
                ref_content = ref_file.read_text(encoding="utf-8", errors="replace")
                missing, inconsistencies = _validate_sections(
                    ref_content,
                    schema["mandatory"],
                    schema["optional"],
                    filename=ref_file.name,
                )
                sec_check = f"Sections ({ref_file.name})"
                if missing:
                    results.append((sec_check, "FAIL",
                        f"Missing mandatory section(s): {', '.join(missing)}. "
                        f"Run /aias health in AI assistant to repair (Scenario F)"))
                elif inconsistencies:
                    for kind, detail in inconsistencies:
                        results.append((sec_check, "WARN", f"{kind}: {detail}"))
                else:
                    results.append((sec_check, "OK", "All mandatory sections present"))

    # 11. Tasks directory
    tasks_dir_raw = _read_tasks_dir_from_profile()
    if not tasks_dir_raw:
        results.append(("Tasks directory", "FAIL", "binding.generation.tasks_dir not found in stack-profile.md"))
    else:
        resolved = pathlib.Path(tasks_dir_raw).expanduser()
        if resolved.is_dir():
            results.append(("Tasks directory", "OK", f"{tasks_dir_raw} exists"))
        else:
            results.append(("Tasks directory", "WARN", f"{tasks_dir_raw} does not exist yet (will be created on first task)"))

    # Print results table
    max_name = max(len(r[0]) for r in results)
    max_status = max(len(r[1]) for r in results)
    has_fails = False

    for name, status, detail in results:
        indicator = "✓" if status == "OK" else ("!" if status == "WARN" else "✗")
        print(f"  {indicator} {name:<{max_name}}  [{status:<{max_status}}]  {detail}")
        if status == "FAIL":
            has_fails = True

    has_warns = any(r[1] == "WARN" for r in results)
    print()
    if has_fails:
        print("Some checks failed. Review the details above for specific corrective actions.")
    elif has_warns:
        print("All critical checks passed. Warnings above may require attention.")
    else:
        print("All checks passed.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

MAIN_HELP = """\
Rho AIAS CLI — scaffolding, generation, and health checks.

Usage: aias <subcommand> [options]

Subcommands:
  init [--max-depth N]  Full project onboarding (interactive)
  new <flag> [name]     Create a new artifact (mode, rule, command, skill, etc.)
  generate [--shortcuts] [--max-depth N] Run the canonical generator (alias: gen)
  health                Verify setup health

Run 'aias new' for artifact creation flags.
Run 'aias init' for guided onboarding.
"""


def main() -> int:
    if sys.version_info < (3, 10):
        print(f"Error: Python 3.10+ is required (found {sys.version}). "
              "Please upgrade your Python installation.")
        return 1

    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(MAIN_HELP)
        return 0

    subcmd = args[0]
    rest = args[1:]

    if subcmd == "init":
        cmd_init(rest)
    elif subcmd == "new":
        cmd_new(rest)
    elif subcmd in ("generate", "gen"):
        cmd_generate(rest)
    elif subcmd == "health":
        cmd_health()
    else:
        print(f"Unknown subcommand: {subcmd}")
        print(MAIN_HELP)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
