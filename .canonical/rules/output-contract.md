# Canonical Output Contract

> **CANONICAL SOURCE — DO NOT DEPLOY DIRECTLY**
>
> This file defines the canonical structure for focused workspace `output-contract.mdc` files.
> Placeholders (`{{...}}`) are resolved from stack profile bindings (`binding.rule.output_contract.*`).
> See `aias/contracts/readme-output-contract.md` for the governing contract.

---

## Template

```markdown
---
description: {{description}}
alwaysApply: true
---

ENVIRONMENT
{{environment}}

DELIVERABLES (every response that includes code changes)
1) Reasoning (Spanish):
   - Approach summary + key trade-offs (pros/cons).
   - Risks/limitations relevant to the chosen approach.
{{#deliverables_extra}}
   - {{deliverables_extra}}
{{/deliverables_extra}}

2) Code changes:
   - Show the COMPLETE file contents for each file created or modified (no partial diffs).
   - The file content must be in English.

3) Documentation and comments:
   - {{documentation_tool}}
   - {{comment_style}}
{{#documentation_extra}}
   - {{documentation_extra}}
{{/documentation_extra}}

{{build_system_integration}}

{{#file_header_section}}
{{file_header_section}}

{{/file_header_section}}
{{#domain_considerations}}
{{domain_considerations}}

{{/domain_considerations}}
TESTING
{{testing}}
```

---

## Placeholder Reference

| Placeholder | Binding key | Required | Example |
|---|---|---|---|
| `{{description}}` | — | Yes | `Output contract: complete file contents + reasoning` |
| `{{environment}}` | `binding.rule.output_contract.environment` | Yes | `- Xcode 26\n- iOS 18 minimum deployment target` |
| `{{deliverables_extra}}` | `binding.rule.output_contract.deliverables_extra` | No | `Impact on generated code and RDSNetworking integration.` |
| `{{documentation_tool}}` | `binding.rule.output_contract.documentation_tool` | Yes | `Use short, concise docstrings (Xcode Quick Help). Document parameters and return value; do not elaborate.` |
| `{{comment_style}}` | `binding.rule.output_contract.linter` | Yes | `No inline comments. Use MARK sections for structure if needed; follow SwiftLint rules when they apply.` |
| `{{documentation_extra}}` | `binding.rule.output_contract.documentation_extra` | No | `Component documentation: one short usage example when helpful, no lengthy explanations.` |
| `{{build_system_integration}}` | Fragment file: `<repo_root>/stack-fragment.md` | Yes | Full section with headers and content |
| `{{file_header_section}}` | Built from `file_header_project_name` + `file_header_author` | No | Full SWIFT FILE HEADER section (generator builds dynamically) |
| `{{domain_considerations}}` | `binding.rule.output_contract.domain_considerations` | No | Full section with header + content |
| `{{testing}}` | `binding.rule.output_contract.testing` | Yes | Testing conventions |

---

## Conditional Sections

- `{{#deliverables_extra}}...{{/deliverables_extra}}`: Only rendered when workspace needs additional deliverable items (e.g., macro impact analysis).
- `{{#file_header_section}}...{{/file_header_section}}`: Only rendered when the platform uses file headers (iOS: yes, Android: no).
- `{{#domain_considerations}}...{{/domain_considerations}}`: Only rendered when workspace has domain-specific output considerations.
- `{{#documentation_extra}}...{{/documentation_extra}}`: Only rendered when workspace needs additional documentation rules.

---

## Profile-Specific Build System Integration

The `{{build_system_integration}}` placeholder resolves to different content based on the canonical profile:

| Profile | Build system integration content |
|---|---|
| `ios-app` | XCODE PROJECT INTEGRATION section with full `.pbxproj` add/remove procedures |
| `ios-spm-package` | SWIFT PACKAGE STRUCTURE section (auto-inclusion via `Sources/`) |
| `ios-spm-package-with-demo` | SWIFT PACKAGE STRUCTURE + XCODE PROJECT INTEGRATION for demo app |
| `ios-xcode-template` | TEMPLATE STRUCTURE RULES + TEMPLATEINFO.PLIST VALIDATION |
| `android-app` | SOURCE SETS AND PACKAGES + RESOURCES + KOTLIN / COMPOSE CONVENTIONS |

### Fragment source

The build system integration content is **not** stored inline in stack profile bindings. It lives in an external **fragment file** at:

```
<repo_root>/stack-fragment.md
```

The generator reads the single `stack-fragment.md` at repo root and injects its content verbatim at the `{{build_system_integration}}` position. Fragment structure and lifecycle are documented in `aias/contracts/readme-output-contract.md` § Build System Integration Fragments.

To create a new fragment, follow the "Fragment Structure Options" section in `aias/contracts/readme-output-contract.md` and save the result as `stack-fragment.md` at repo root.
