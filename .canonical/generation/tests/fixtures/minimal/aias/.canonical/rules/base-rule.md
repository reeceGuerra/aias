# Stub Base Rule

> CANONICAL SOURCE — DO NOT DEPLOY DIRECTLY

---

## Template

```markdown
---
description: {{description}}
alwaysApply: true
---

ROLE
{{role_specialty}}

LANGUAGE
- **{{conversation_language}}**: Conversation and reasoning.

ENGINEERING
{{engineering_domain_principle}}

SECURITY
{{security_line}}

PERFORMANCE
{{performance_line}}

ASSUMPTIONS
{{assumptions_domain}}

LIMITATIONS
{{limitations_truthfulness_line}}

{{platform_limitations}}

STYLE GUIDES
{{styleguide_paths}}

{{#domain_constraints_section}}
DOMAIN CONSTRAINTS
{{domain_constraints_section}}
{{/domain_constraints_section}}
```
