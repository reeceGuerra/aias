# Stub Output Contract

> CANONICAL SOURCE — DO NOT DEPLOY DIRECTLY

---

## Template

```markdown
---
description: {{description}}
alwaysApply: true
---

ENVIRONMENT
{{environment}}

DELIVERABLES
{{#deliverables_extra}}
- {{deliverables_extra}}
{{/deliverables_extra}}

DOCUMENTATION
- Tool: {{documentation_tool}}
{{#documentation_extra}}
- {{documentation_extra}}
{{/documentation_extra}}

LINTER
{{comment_style}}

TESTING
{{testing}}

BUILD SYSTEM INTEGRATION
{{build_system_integration}}

{{#file_header_section}}
{{file_header_section}}
{{/file_header_section}}

{{#domain_considerations}}
DOMAIN CONSIDERATIONS
{{domain_considerations}}
{{/domain_considerations}}
```
