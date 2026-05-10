---
name: firebase-mcp
description: Operate Firebase project and environment workflows through Firebase MCP. Use when the user asks to inspect Firebase setup, bootstrap environment access, read Firebase resources/security rules, or prepare changes for Auth, Firestore, Functions, Storage, and Hosting.
category: mcp
tested_against:
  mcp_server: user-firebase@2026-05-05
  tools_count: 17
---

# Firebase MCP

## PURPOSE

Teach the agent how to operate Firebase through the MCP server for environment bootstrap, project/app discovery, SDK configuration retrieval, and resource/rules inspection. This skill curates AIAS-relevant surfaces for Auth, Firestore, Functions, Storage, and Hosting.

---

## OPERATIONS

### 1) Bootstrap Firebase Session

**When:** First Firebase operation in the chat or after auth failure.

**Call sequence:**
1. `firebase_login` (authenticate session)
2. `firebase_get_environment` (confirm active context)
3. `firebase_init` only when the user explicitly asks to initialize/update MCP environment

Abort if login or environment resolution fails.

### 2) Discover Project and App Context

**When:** User asks about available projects/apps or to target a specific Firebase project.

**Call sequence:**
1. `firebase_list_projects`
2. `firebase_get_project` (for selected project)
3. `firebase_list_apps` (project apps)
4. `firebase_get_sdk_config` (selected app)

### 3) Read Resource Surfaces (AIAS-curated)

**When:** User asks about Firebase implementation state in any curated surface:
- Auth
- Firestore
- Functions
- Storage
- Hosting

**Call sequence:**
1. `firebase_read_resources` (surface-specific read)
2. `firebase_get_security_rules` when rules are relevant (Firestore/Storage)
3. `developerknowledge_*` tools only as supplemental reference, never as source of live project truth

### 4) Environment Update (Controlled)

**When:** User explicitly asks to change Firebase environment context.

**Call sequence:**
1. `firebase_get_environment` (capture current state)
2. `firebase_update_environment` (apply requested update)
3. `firebase_get_environment` (verify)

---

## SAFETY RULES

**Read-only by default:**
- Read/list/get operations are allowed by default.
- Mutating operations require explicit user instruction.

**Firestore destructive operations:**
- Any delete/reset/overwrite operation in Firestore data/rules requires explicit human confirmation immediately before execution.

**Auth user mutations:**
- Auth user create/update/delete is forbidden by default.
- Allow only when the user explicitly requests it and confirms target identities.

**Cloud Functions deploy surfaces:**
- Preview/simulated validation is allowed when available.
- Production-impact deploy actions require explicit confirmation.

**Abort on failure:**
- If authentication or environment resolution fails, abort and report the exact failing step.
- Do not invent Firebase resource state if API responses are empty or unavailable.

---

## REFERENCE

For detailed tool inputs/outputs and safety-by-tool notes, see [reference.md](reference.md).

---

## Out of Scope (skill v1.0)

This v1.0 skill intentionally does not curate:
- Realtime Database
- Remote Config
- Cloud Messaging
- Firebase Extensions lifecycle automation

These surfaces remain available through Firebase APIs/MCP evolution, but are non-canonical for AIAS v1.0.
