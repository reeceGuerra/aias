# Output Contract Rule Contract — Cursor Rules System

This document defines the **canonical contract** for output contract rules (`.cursor/rules/output-contract.mdc`) in the Cursor configuration system.

It exists to:
- Establish standards for output contract structure and content
- Define what is invariant vs parametrizable in output contracts
- Enable deterministic generation of output contracts from stack profile bindings
- Prevent platform/tool hardcoding drift across focused workspaces

This document is written **for maintainers** of the Cursor configuration system.

---

## What is an Output Contract?

An **output contract** is a Cursor rule file (`.mdc` format) with `alwaysApply: true` that defines the **output structure, format, and integration rules** the AI assistant must follow when producing code changes in a specific workspace.

### Characteristics

- **Always active** — Applied to every interaction when the workspace is open
- **Workspace-specific** — Defines output behavior for a particular repository or workspace
- **Complementary to base rule** — Base rule defines *how to think*; output contract defines *how to deliver*
- **Complementary to mode rules** — Mode rules define *what to focus on*; output contract defines *structural format*
- **Platform/tool-specific by design** — Output contracts legitimately contain platform-specific details (build system, file headers, project integration)

### Location

- **Canonical location:** `aias-config/rules/output-contract.mdc` — the generated source of truth
- **Tool-specific locations** (shortcuts only — see `readme-tool-adapter.md`):
  - Cursor: `.cursor/rules/output-contract.mdc`
  - Claude Code: `.claude/rules/output-contract.md`
  - Windsurf: `.windsurf/rules/output-contract.md`
  - GitHub Copilot: referenced in `.github/copilot-instructions.md`

### Relationship with Mode Rules

Mode rules (`readme-mode-rule.md`) delegate output format responsibility to the workspace's `output-contract.mdc`. Modes define behavior and thinking; output contracts define delivery structure. Only modes that need a unique output format not covered by the workspace contract should define their own OUTPUT FORMAT section.

---

## Contract Structure

All output contract rules **must follow this structure and order**.

### 1. Frontmatter (Required)

```yaml
---
description: <brief description of the output contract's purpose>
alwaysApply: true
---
```

**Required fields:**
- `description`: One-line description of what this output contract defines
- `alwaysApply: true`: Must be explicitly set to `true`

---

### 2. Content Sections (Required Order)

#### ENVIRONMENT (Required)

Declare the development environment and toolchain versions.

**Must include:**
- IDE or build tool and version
- Platform/OS minimum deployment target
- Additional toolchain requirements (package manager, language version, framework)

**Parametrized by:** `binding.rule.output_contract.environment`

**Example (iOS app):**
```
ENVIRONMENT
- Xcode 26
- iOS 18 minimum deployment target
```

**Example (Android app):**
```
ENVIRONMENT
- Android Studio / AGP 8.x
- Kotlin 2.x
- Jetpack Compose, Material 3
- minSdk 31 (or project default); targetSdk as per project
```

---

#### DELIVERABLES (Required)

Define the required components of every response that includes code changes.

**Invariant structure** (must appear in all output contracts):

1. **Reasoning** (conversation language):
   - Approach summary + key trade-offs (pros/cons)
   - Risks/limitations relevant to the chosen approach
2. **Code changes**:
   - Complete file contents for each file created or modified (no partial diffs)
   - File content in English
3. **Documentation and comments**:
   - Documentation tool conventions (parametrized)
   - Comment style rules (parametrized)

**Parametrized elements within DELIVERABLES:**
- Documentation tool (e.g., "Xcode Quick Help docstrings" vs "KDoc for public APIs")
- Comment style rules (e.g., "No inline comments. Use MARK sections" vs "Avoid inline comments unless necessary for non-obvious logic")
- Additional deliverable sub-items (e.g., "Impact on generated code" for macro workspaces)

**Parametrized by:** `binding.rule.output_contract.documentation_tool`, `binding.rule.output_contract.linter`

---

#### BUILD SYSTEM INTEGRATION (Required when applicable)

Define how new files are integrated into the project's build system.

**This section varies significantly by project type.** Canonical profiles determine which variant applies:

| Profile | Integration mechanism |
|---|---|
| `ios-app` | Xcode project (`.pbxproj`) — manual section modification |
| `ios-spm-package` | Swift Package Manager — automatic inclusion via `Sources/` directory |
| `ios-spm-package-with-demo` | SPM for package + Xcode project for demo app |
| `ios-xcode-template` | Template directory structure + `TemplateInfo.plist` validation |
| `android-app` | Gradle — automatic inclusion via `src/main/java` conventions |

**Parametrized by:** the fragment file at `<repo_root>/stack-fragment.md` (see § Build System Integration Fragments below).

---

#### FILE HEADER (Required when applicable)

Define the standard header for new source files.

**Parametrized by:** `binding.rule.output_contract.file_header_project_name` + `binding.rule.output_contract.file_header_author` (generator builds the section dynamically). Absent when platform convention has no file header (e.g., Android).

**When to include:**
- When the project has a standard file header convention
- Skip if the platform convention is "no mandatory file header" (e.g., Kotlin/Android)

**Example (iOS):**
```
SWIFT FILE HEADER (NEW FILES)
- For every NEW `.swift` file created, include this header at the very top (before imports):

//
//  FILENAME.swift
//  ProjectName
//
//  Created by Author with Cursor on DD/MM/YY.
//

- Replace `FILENAME.swift` with the actual filename.
- Replace `DD/MM/YY` with the creation date.
```

---

#### DOMAIN CONSIDERATIONS (Optional)

Workspace-specific considerations relevant to output quality.

**When to include:**
- When the workspace has domain-specific output requirements not covered by other sections
- Examples: design system considerations (rdsui), networking considerations (rdsnetworking), macro considerations (rdsmacros), template validation (xctemplates)

**Constraint:** Domain considerations must be specific to the workspace's purpose and not duplicate guidance that belongs in base rules or mode rules.

---

#### TESTING (Required)

Define testing conventions for the workspace.

**Invariant structure:**
- When tests are required, add or modify test file(s) together with the production change
- Reference to `/commit` command for staging

**Parametrized elements:**
- Test framework and conventions (e.g., "Swift Testing" vs "JUnit + MockK")
- Test file location conventions (e.g., `src/test/java/` with matching package)
- Test types available (unit, UI, instrumented)

**Parametrized by:** `binding.rule.output_contract.testing`

---

## Canonical Profiles

Output contracts are classified into canonical profiles based on the workspace's build system and project type:

| Profile ID | Platform | Build system | Key characteristics |
|---|---|---|---|
| `ios-app` | iOS | Xcode project | `.pbxproj` integration, Swift file headers, Xcode Quick Help |
| `ios-spm-package` | iOS | Swift Package Manager | No `.pbxproj`, auto-inclusion via `Sources/`, Swift file headers |
| `ios-spm-package-with-demo` | iOS | SPM + Xcode (demo) | Hybrid: SPM for package + `.pbxproj` for demo app |
| `ios-xcode-template` | iOS | Xcode templates | `TemplateInfo.plist` validation, template variable formatting |
| `android-app` | Android | Gradle | Source set conventions, KDoc, no mandatory file header |

**Workspace-to-profile mapping:**

| Workspace | Profile |
|---|---|
| `mobilemax-dev` | `ios-app` |
| `rdsui-dev` | `ios-spm-package-with-demo` |
| `rdsnetworking-dev` | `ios-spm-package` |
| `rdsmacros+rdsnetworking-dev` | `ios-spm-package` |
| `xctemplates-dev` | `ios-xcode-template` |
| `mobilemax-android-dev` | `android-app` |

---

## Build System Integration Fragments

### What are fragments

The BUILD SYSTEM INTEGRATION section of an output contract contains workspace-specific content that is too large and complex to store as an inline binding value in a stack profile. A **fragment** is an external file that holds this content — a binding value externalized to a file for readability and maintainability.

Examples of content that lives in a fragment:
- Xcode `.pbxproj` add/remove procedures (100+ lines for `ios-app`)
- Swift Package Manager directory conventions (3–5 lines for `ios-spm-package`)
- Gradle source set and resource conventions (15–20 lines for `android-app`)
- Hybrid procedures (SPM + demo app pbxproj for `ios-spm-package-with-demo`)

### Fragment location and naming

| Aspect | Value |
|---|---|
| **Location** | `<repo_root>/stack-fragment.md` — one file per repo, at the repository root |
| **Name** | `stack-fragment.md` (fixed name, analogous to `Podfile` or `Package.swift`) |
| **Structure guide** | § Fragment Structure Options (below) |
| **Encoding** | UTF-8, LF line endings |

### Fragment structure

A fragment must contain:

1. **At least one section header in UPPERCASE** — the header names the build system integration approach (e.g., `XCODE PROJECT INTEGRATION (NEW FILES)`, `SWIFT PACKAGE STRUCTURE`, `SOURCE SETS AND PACKAGES (NEW FILES)`)
2. **Actionable rules** — bullet points or numbered steps that the AI assistant follows when creating or modifying files in the workspace
3. **No frontmatter** — fragments are injected into the output contract body; they must not contain YAML frontmatter

The fragment content is injected verbatim at the `{{build_system_integration}}` placeholder in the output contract template. No further processing or placeholder resolution occurs within the fragment.

### How to set up a fragment

When onboarding a new repo:

1. **Identify the canonical profile** — determine which build system integration pattern applies (see "Canonical Profiles" above). If no existing profile fits, define a new profile ID.
2. **Create the fragment** — follow the "Fragment Structure Options" below to create `stack-fragment.md` at the repo root. Choose the option (A, B, C) that matches your build system.
3. **Fill applicable sections** — replace the placeholders with workspace-specific content. Delete sections that do not apply.
4. **Add the workspace's output contract bindings** to `stack-profile.md` at the repo root, including `binding.rule.output_contract.<workspace-id>.profile` pointing to the canonical profile.
5. **Run the generator** — the pre-flight validation (G4) will confirm the fragment is valid before generating.

### Fragment lifecycle

| Event | Action |
|---|---|
| New repo onboarded | Copy template to `stack-fragment.md` at repo root, add bindings to `stack-profile.md` |
| Build system changes | Update `stack-fragment.md` directly; re-run generator |
| Generator runs | Fragment is read from `<repo_root>/stack-fragment.md` and injected at `{{build_system_integration}}`; validated by pre-flight Gate 4 |

### Fragment Structure Options

When creating `stack-fragment.md`, choose the structure option that matches the workspace's build system. Save the file at the repo root. The content below is injected verbatim at the `{{build_system_integration}}` placeholder in the output contract — do not include YAML frontmatter.

After creating the fragment, ensure `stack-profile.md` also exists at repo root with the workspace's output contract bindings, and run the generator.

#### Option A: Automatic inclusion (SPM, Gradle, pub, Cargo, npm, etc.)

Use when the build system auto-discovers files by directory convention.

```markdown
BUILD SYSTEM STRUCTURE
- Files are managed by <BUILD_TOOL>, not manual project configuration.
- New files are automatically included if placed in the correct <SOURCE_DIRECTORY> structure.
- No manual build file modifications needed.
```

#### Option B: Manual project file integration (Xcode pbxproj, CMake, etc.)

Use when new files must be explicitly registered in a project file.

```markdown
PROJECT FILE INTEGRATION (NEW FILES)
- When creating a new file that must be part of the project, ensure it is added to the correct project and target(s).
- This applies ONLY to source and resource files managed by the build system such as:
  - <LIST_FILE_TYPES>
- This does NOT apply to documentation or configuration files (e.g., .md, .mdc, .cursor/*).

PROCESS FOR ADDING FILES:
When manually adding files to the project file, follow these steps:

1) Identify reference files:
   - Search for similar files in the same directory to understand the pattern.

2) Identify the sections to modify:
   - <DESCRIBE_SECTIONS_AND_FORMATS>

3) Perform the modifications:
   - <DESCRIBE_STEPS>

4) Verify consistency:
   - <DESCRIBE_VERIFICATION>

In the reasoning section, explicitly state:
  - which project/target(s) the file was added to,
  - where it lives in the project structure,
  - that all required sections were updated correctly.
```

**File removal process** (recommended for Option B) — include if removing files also requires updating the project file (e.g., Xcode pbxproj references, CMakeLists.txt entries):

```markdown
PROCESS FOR REMOVING FILES:
When deleting a file that is part of the project, ensure all references are removed from the project file to prevent build errors and orphaned references.

1) Locate all references to the file:
   - <DESCRIBE_HOW_TO_FIND_REFERENCES>

2) Identify the sections to clean up:
   - <DESCRIBE_SECTIONS>

3) Remove all entries:
   - <DESCRIBE_STEPS>

4) Verify removal:
   - <DESCRIBE_VERIFICATION>

In the reasoning section, explicitly state:
  - that the file was removed from the project,
  - which sections of the project file were modified,
  - that all references were verified as removed (no orphaned entries).
```

#### Option C: Hybrid (e.g., SPM package + Xcode demo app)

Combine Option A for the package and Option B for the app.

#### Optional sections

**Resources** — include if the workspace has specific resource file placement rules:

```markdown
RESOURCES (NEW FILES)
- <DESCRIBE_RESOURCE_PLACEMENT_RULES>
```

**Language/framework conventions** — include if the workspace has build-system-adjacent coding conventions that affect file creation (e.g., Kotlin/Compose naming, no file header):

```markdown
<FRAMEWORK> CONVENTIONS
- <DESCRIBE_CONVENTIONS>
```

---

### Relationship with stack profile bindings

The `binding.rule.output_contract.<ws>.profile` binding in the stack profile identifies the canonical profile type but does **not** contain the fragment content. The generator reads the single `stack-fragment.md` at repo root and uses its content for all workspaces defined in the profile.

---

## Content Guidelines

### What to Include

- Environment and toolchain declarations
- Output structure requirements (deliverables)
- Build system integration rules
- File header conventions
- Domain-specific output considerations
- Testing conventions

### What to Exclude

- Role definition (belongs in `base.mdc`)
- Engineering principles (belongs in `base.mdc`)
- Behavioral constraints (belongs in `base.mdc`)
- Mode-specific workflow (belongs in mode rules)
- Command-specific behavior (belongs in command definitions)
- Project context (belongs in `AGENTS.md`)

---

## Invariant vs Parametrizable Summary

| Aspect | Type | Description |
|---|---|---|
| Frontmatter structure | Invariant | `alwaysApply: true`, description field |
| ENVIRONMENT section existence | Invariant | Must exist |
| ENVIRONMENT content | Parametrizable | IDE, versions, platform targets |
| DELIVERABLES structure | Invariant | Reasoning + Code changes + Documentation |
| DELIVERABLES detail | Parametrizable | Documentation tool, comment style, extra sub-items |
| BUILD SYSTEM INTEGRATION | Parametrizable | Determined by canonical profile |
| FILE HEADER | Parametrizable | Project name, author, format (or absent) |
| DOMAIN CONSIDERATIONS | Parametrizable | Workspace-specific (optional) |
| TESTING structure | Invariant | Test + commit reference |
| TESTING detail | Parametrizable | Framework, location, types |

---

## Quality Criteria

A good output contract is:

### 1. **Platform-Appropriate**
- Reflects the actual build system and toolchain of the workspace
- Does not include irrelevant platform details

### 2. **Complete**
- Covers all required output aspects for the workspace
- A developer can understand what format to expect from every response

### 3. **Deterministic**
- Clear, unambiguous rules for output structure
- No subjective or vague formatting instructions

### 4. **Complementary**
- Does not duplicate base rule or mode rule content
- Works alongside other rules without conflict

### 5. **Maintainable**
- Well-organized sections in prescribed order
- Parametrized values traceable to stack profile bindings

---

## Formatting Standards

### Section Headers
- Use **UPPERCASE** for major sections
- Use `---` separator between major sections
- Keep headers concise

### Content Style
- Use numbered lists for ordered deliverables
- Use bullet points for rules and constraints
- Use code blocks for templates and examples

---

## Versioning

Output contracts should be versioned when:
- Environment versions change (e.g., Xcode version bump)
- Build system integration rules change
- File header conventions change
- New domain considerations are added

---

## Related Contracts

- `readme-base-rule.md` — Contract for `base.mdc` (behavioral rules)
- `readme-mode-rule.md` — Contract for mode rules (delegates output format here)
- `readme-stack-profile.md` — Contract for stack profiles (provides parametrization bindings)

---

This document is the **source of truth** for output contract rule structure and content.
