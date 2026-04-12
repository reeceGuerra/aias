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


ROOT = pathlib.Path(__file__).resolve().parents[3]
CANONICAL_DIR = ROOT / "aias" / ".canonical"
CONTRACTS_DIR = ROOT / "aias" / "contracts"
AIAS_CONFIG_DIR = ROOT / "aias-config"
RULES_DIR = AIAS_CONFIG_DIR / "rules"
MODES_DIR = AIAS_CONFIG_DIR / "modes"
FW_COMMANDS_DIR = ROOT / "aias" / ".commands"
FW_SKILLS_DIR = ROOT / "aias" / ".skills"
PROJECT_COMMANDS_DIR = AIAS_CONFIG_DIR / "commands"
PROJECT_SKILLS_DIR = AIAS_CONFIG_DIR / "skills"
PROVIDERS_DIR = AIAS_CONFIG_DIR / "providers"
LEGACY_PROVIDERS_DIR = ROOT / "aias-providers"
GENERATOR = CANONICAL_DIR / "generation" / "generate_modes_and_rules.py"

KEBAB_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
PROVIDER_CATEGORIES = ("knowledge", "tracker", "design", "vcs")

SUPPORTED_TOOLS = ("cursor", "claude", "windsurf", "copilot", "codex")

TOOL_CONTEXT_MAP: Dict[str, Tuple[str, ...]] = {
    "AGENTS.md": ("cursor", "windsurf", "copilot"),
    "CLAUDE.md": ("claude",),
    "codex.md": ("codex",),
}


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


def existing_names(directory: pathlib.Path, suffix: str = ".mdc") -> List[str]:
    if not directory.is_dir():
        return []
    return sorted(p.stem for p in directory.glob(f"*{suffix}") if p.is_file())


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
    if not validate_kebab(name):
        print(f"Error: '{name}' is not valid kebab-case (expected: ^[a-z][a-z0-9]*(-[a-z0-9]+)*$)")
        sys.exit(1)

    existing = existing_names(PROJECT_COMMANDS_DIR, suffix=".md") + existing_names(FW_COMMANDS_DIR, suffix=".md")
    if name in existing:
        if not confirm(f"  Command '{name}' already exists. Overwrite?"):
            return

    cmd_type = ask_choice("Command type:", ["Advisory (chat-only)", "Operative (procedural, writes files)"])
    type_label = "Advisory" if "Advisory" in cmd_type else "Operative"

    identity = ask("Identity (what does this command do?)")
    invocation = ask("Invocation example (e.g. /<name> --flag value)")
    inputs = ask("Inputs (what information does it consume?)")
    output_format = ask("Output format (Rendered Markdown, code block, file...)")
    content_rules = ask("Content rules (what to include/exclude, language)")
    output_structure = ask("Output structure (sections of the output)")
    non_goals = ask("Non-goals (what must this command NOT do?)")
    skills = ask("Skills (comma-separated, optional)")

    content = textwrap.dedent(f"""\
        # {name.replace('-', ' ').title()} — v1

        ## 1. Identity
        **Command Type:** {type_label}
        {identity}

        ## 2. Invocation / Usage
        {invocation if invocation else f'`/{name}`'}

        ## 3. Inputs
        {inputs}

        ## 4. Output Contract (Format)
        {output_format}

        ## 5. Content Rules (Semantics)
        {content_rules}

        ## 6. Output Structure (Template)
        {output_structure}

        ## 7. Non-Goals / Forbidden Actions
        {non_goals}
    """)

    if skills:
        skill_list = [s.strip() for s in skills.split(",") if s.strip()]
        content += "\n## Skills\n" + "\n".join(f"- **{s}**" for s in skill_list) + "\n"

    path = PROJECT_COMMANDS_DIR / f"{name}.md"
    safe_write(path, content)


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

    category = ask_choice("Skill category:", ["MCP", "Tool"])
    description = ask("Description (WHAT + WHEN with trigger terms, max 1024 chars)")
    if not description or len(description) < 50:
        print(f"Warning: description should be >= 50 chars with trigger terms (current: {len(description)}).")

    purpose = ask("Purpose (1-2 sentences: what it enables)")

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

    safety = ask("Safety rules (read/write boundary, abort-on-failure, data integrity)")
    if not safety:
        safety = "- Read-only by default. Write operations require explicit user request.\n- Abort on failure. Do not invent data.\n- Data integrity: do not fabricate or assume data not returned by the service."

    # Build SKILL.md
    content = f"---\nname: {name}\ndescription: \"{description}\"\n---\n"
    content += f"\n## PURPOSE\n{purpose}\n"
    content += "\n## OPERATIONS\n"
    for op_name, op_when, op_prereq, op_sequence, op_output in operations:
        content += f"\n### {op_name}\n"
        content += f"- **When**: {op_when}\n"
        content += f"- **Prerequisites**: {op_prereq}\n"
        content += f"- **Call sequence**: {op_sequence}\n"
        content += f"- **Output**: {op_output}\n"

    content += f"\n## SAFETY RULES\n{safety}\n"

    path = PROJECT_SKILLS_DIR / name / "SKILL.md"
    safe_write(path, content)


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
        - **Commands**: `aias/.commands/` (framework) + `aias-config/commands/` (project) — Command definitions
        - **Skills**: `aias/.skills/` (framework) + `aias-config/skills/` (project) — Reusable operational skills
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
        - `binding.generation.mode_output_dir`: `aias-config/modes`
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

def cmd_init() -> None:
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
    selected_tools = _read_tools_from_profile()
    print("\nCreating context symlinks → RHOAIAS.md...")
    rhoaias_target = ROOT / "RHOAIAS.md"
    for filename, required_tools in TOOL_CONTEXT_MAP.items():
        if selected_tools and not any(t in selected_tools for t in required_tools):
            continue
        link_path = ROOT / filename
        if link_path.is_symlink():
            current = (link_path.parent / os.readlink(link_path)).resolve()
            if current == rhoaias_target.resolve():
                print(f"  [ok] {filename} → RHOAIAS.md (already a valid symlink)")
                continue
        if link_path.is_file():
            if not confirm(f"  '{filename}' exists as a regular file. Replace with symlink?", default_yes=True):
                print(f"  Skipped: {filename}")
                continue
        _create_symlink(link_path, rhoaias_target)
        print(f"  Created: {filename} → RHOAIAS.md")

    # Step 5b: Ensure aias-config/ structure
    for d in (AIAS_CONFIG_DIR, RULES_DIR, MODES_DIR, PROVIDERS_DIR):
        d.mkdir(parents=True, exist_ok=True)
    print(f"\n  aias-config/ structure ensured.")

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
  -m, --mode <name>        Create a mode (file-specific or intelligent)
  -r, --rule <name>        Create an always-apply rule
  -c, --command <name>     Create a command
  -s, --skill <name>       Create a skill
  -P, --provider <category> Create a provider config (knowledge|tracker|design|vcs)
  -C, --context            Create RHOAIAS.md
  -p, --stack-profile      Create stack-profile.md
  -f, --stack-fragment     Create stack-fragment.md
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
    for i, a in enumerate(args):
        if a in ("-t", "--tools") and i + 1 < len(args):
            tools_arg = args[i + 1]
    cmd = [sys.executable, str(GENERATOR)]
    if shortcuts:
        cmd.append("--shortcuts")
    if tools_arg:
        cmd.extend(["--tools", tools_arg])
    result = subprocess.run(cmd, cwd=str(ROOT))
    sys.exit(result.returncode)


# ---------------------------------------------------------------------------
# health
# ---------------------------------------------------------------------------

HealthStatus = Tuple[str, str, str]  # (check_name, status, detail)


def cmd_health() -> None:
    print("=" * 60)
    print("  Rho AIAS — Health Check")
    print("=" * 60)
    print()

    results: List[HealthStatus] = []

    # 1. RHOAIAS.md
    rhoaias = ROOT / "RHOAIAS.md"
    if rhoaias.is_file():
        results.append(("RHOAIAS.md", "OK", "Exists"))
    else:
        results.append(("RHOAIAS.md", "FAIL", "Not found"))

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
        fw_dirs = [FW_COMMANDS_DIR, FW_SKILLS_DIR]
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
            "Legacy provider location: aias-providers/. Run /aias health in AI assistant to migrate to aias-config/providers/"))

    # 9c. Legacy generated rules/modes location detection
    legacy_rules = ROOT / "aias" / ".rules"
    legacy_modes = ROOT / "aias" / ".modes"
    if legacy_rules.is_dir() and list(legacy_rules.glob("*.mdc")):
        results.append(("Legacy rules", "WARN",
            "Legacy generated rules in aias/.rules/. Run aias generate to regenerate in aias-config/rules/"))
    if legacy_modes.is_dir() and list(legacy_modes.glob("*.mdc")):
        results.append(("Legacy modes", "WARN",
            "Legacy generated modes in aias/.modes/. Run aias generate to regenerate in aias-config/modes/"))

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

    # 10. Provider referenced files (resource_files validation)
    CATEGORIES_WITH_RESOURCE_FILES = {"tracker", "knowledge"}
    LEGACY_PREFIXES = ("aias/.skills/", "aias-providers/")
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
  init                  Full project onboarding (interactive)
  new <flag> [name]     Create a new artifact (mode, rule, command, skill, etc.)
  generate [--shortcuts] Run the canonical generator (alias: gen)
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
        cmd_init()
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
