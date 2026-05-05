# Cross-Repo Integration Reference (v1.0)

## Jira Hierarchy Pattern

- Parent ticket: cross-repo objective.
- Subtask per repo: scoped implementation plan with repo-local acceptance.
- Integration subtask: sequencing + compatibility + rollout checks.

## Sequencing Template

1. Producer repo change planned and merged (or published version prepared).
2. Adopter repo plan updates dependency and integration points.
3. Integration workspace validates end-to-end compatibility.
4. Final handoff back to adopter repo for completion.

## Per-Folder Command Scoping (v1.0)

Resolution algorithm:
1. Resolve active repo by nearest ancestor containing repo marker (`.git`, repo root conventions, or explicit workspace mapping).
2. Resolve command from active repo scope.
3. If multiple candidates remain, request explicit repo selection before execution.

## Risks to track

- Version skew between producer and adopter repos.
- Concurrent breaking changes in shared dependencies.
- Missing integration validation after repo-local green checks.
