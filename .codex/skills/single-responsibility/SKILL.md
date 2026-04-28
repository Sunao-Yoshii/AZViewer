---
name: single-responsibility
description: Guide code changes, reviews, and refactors toward the Single Responsibility Principle. Use when Codex is implementing features, fixing bugs, reviewing code, or restructuring code where responsibilities may be mixed, modules/classes/functions are growing too broad, or the user asks to keep single responsibility, SRP, separation of concerns, or one reason to change as much as practical.
---

# Single Responsibility

## Overview

Keep each changed unit focused on one reason to change while still fitting the existing codebase. Apply SRP pragmatically: separate real responsibilities, but avoid speculative abstractions or broad rewrites that do not serve the requested task.

Also apply this when the user asks in Japanese to preserve "tannitsu sekinin" or the single responsibility principle.

## Workflow

1. Identify the requested behavior change first.
2. Find the smallest existing units involved: module, class, function, component, hook, service, command, or test helper.
3. Name each unit's current responsibility in one short phrase.
4. Mark responsibility mixing only when the unit has multiple reasons to change, not merely multiple implementation steps.
5. Prefer the smallest extraction that gives each responsibility a clear owner.
6. Keep public APIs stable unless the task explicitly requires changing them.
7. Add or update tests at the boundary where behavior could regress.

## Responsibility Check

Use these questions while reading and editing:

- Would this unit need to change for two different business or technical reasons?
- Does the name promise one thing while the implementation also performs another?
- Is orchestration mixed with validation, parsing, persistence, rendering, transport, formatting, caching, or policy decisions?
- Would a small behavior change force edits in several unrelated places?
- Is a new abstraction based on an actual responsibility boundary, rather than on file size alone?

Treat these as warning signs, not automatic refactor commands. Keep related logic together when splitting it would obscure the workflow, duplicate state, or create indirection without reducing change pressure.

## Implementation Guidance

- Separate pure decision logic from side effects when practical.
- Keep adapters thin: translate transport, framework, or storage details at the edge.
- Keep orchestration explicit: a coordinator may call several focused collaborators, but should not also own their internal policies.
- Extract naming-worthy responsibilities before extracting generic helpers.
- Prefer local private helpers for narrow cleanup; promote to shared modules only after a real second caller exists or the codebase already has that pattern.
- Preserve the repo's established layering, dependency direction, and naming conventions.
- Avoid combining unrelated cleanup with the requested change.

## Review Guidance

When reviewing or explaining changes, lead with concrete responsibility boundaries:

- State the responsibility each edited unit now owns.
- Call out remaining responsibility mixing when it is intentional or deferred.
- Mention tradeoffs if strict SRP would require a larger API, migration, or design change than the task justifies.
- Request changes when one unit now owns unrelated policy, I/O, formatting, and orchestration in a way that raises maintenance risk.

## Examples

Feature change:

- Keep request parsing, validation rules, business decisions, persistence, and response formatting in distinct units when the existing architecture supports it.
- Do not introduce a new service layer only to move three lines of code if the original unit still has one reason to change.

Bug fix:

- Fix the defect at the responsibility owner.
- Add regression tests near the owner or its public boundary.
- Avoid spreading guard clauses across callers when a central policy or parser should own the rule.

Refactor:

- Extract by reason to change, not by method length alone.
- Stop when the next extraction would mostly rename or shuffle code without clarifying ownership.
