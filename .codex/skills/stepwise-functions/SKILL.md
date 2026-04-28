---
name: stepwise-functions
description: Guide Python and JavaScript implementation toward step-level helper methods when a function's processing would exceed about 30 lines. Use when Codex is implementing, modifying, reviewing, or refactoring Python or JavaScript code and a single function is becoming long, multi-step, or hard to scan.
---

# Stepwise Functions

## Core Rule

When implementing Python or JavaScript functions, try to split processing into step-level helpers if the function would exceed about 30 lines.

Treat 30 lines as a review trigger, not a hard ban. A longer function can remain intact when splitting would obscure a straightforward algorithm, introduce awkward parameter plumbing, or conflict with local style.

## Workflow

1. Identify the function's natural stages before writing or expanding it.
2. Keep the public function focused on orchestration when multiple stages are present.
3. Extract private/local helpers for coherent steps such as validation, normalization, lookup, transformation, persistence, rendering, or error translation.
4. Name helpers after the step they perform, not after implementation details.
5. Keep data flow explicit. Prefer passing the few values a helper needs over sharing mutable outer state.
6. Preserve existing project conventions for helper visibility, placement, naming, typing, async style, and tests.

## Extraction Guidance

Extract a helper when it gives the code one clear reason to change, has a name that reads naturally in the caller, and can be understood or tested independently.

Avoid extraction when the helper would be a thin wrapper around one expression, when it hides essential control flow, or when it forces readers to jump around for a short linear operation.

For Python, prefer module-private helpers with leading underscores unless the project uses nested functions, class methods, or another established pattern.

For JavaScript and TypeScript, prefer nearby private helpers, module-scoped functions, or class-private methods according to the existing code style.

## Checks Before Finishing

- Confirm no newly implemented or expanded function exceeds about 30 lines without a deliberate reason.
- Confirm extracted helpers each represent one step and are named from the caller's point of view.
- Update or add focused tests when behavior changes or helper extraction exposes edge cases.
