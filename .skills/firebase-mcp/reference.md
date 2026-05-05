# Firebase MCP Reference (v1.0)

## Curated Tool Matrix

| Tool | Category | Usage in AIAS v1.0 |
|---|---|---|
| `firebase_login` / `firebase_logout` | Session | Authenticate/terminate Firebase MCP session |
| `firebase_get_environment` / `firebase_update_environment` | Environment | Inspect and update active MCP Firebase context |
| `firebase_init` | Environment bootstrap | Initialize MCP Firebase setup when explicitly requested |
| `firebase_list_projects` / `firebase_get_project` / `firebase_create_project` | Project scope | Discover project inventory; create only on explicit instruction |
| `firebase_list_apps` / `firebase_create_app` / `firebase_get_sdk_config` | App scope | Discover app surfaces and retrieve SDK config |
| `firebase_read_resources` | Resource inspection | Primary entry point for Auth/Firestore/Functions/Storage/Hosting reads |
| `firebase_get_security_rules` | Rules inspection | Validate Firestore/Storage rules before planning changes |
| `developerknowledge_search_documents` / `developerknowledge_answer_query` / `developerknowledge_get_documents` | Supplemental docs | Secondary source only; never override live project data |

## Safety-by-Action

- Any action that mutates project/app/environment requires explicit user request.
- Firestore destructive actions require explicit human confirmation at execution time.
- Auth user lifecycle mutations are forbidden by default.
- Production-impact operations in Functions/Hosting require explicit confirmation.

## Notes

- This reference follows the MCP descriptor surface tested on `2026-05-05`.
- If descriptor surfaces change, refresh `tested_against` in `SKILL.md` and update this table.
