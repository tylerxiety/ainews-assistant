---
name: source-command-verify
description: Execute + Self-Verify Loop
---

# Execute with Self-Verification

Implement the plan, then self-verify and fix issues in a scoped loop.

## Phase 1: Implementation

Follow `/execute` instructions precisely.

**Track files touched** — keep a list of all files you create or modify. This scopes Phase 2.

Do NOT update the plan document yet — wait until the end.

## Phase 2: Verify-Fix Loop

**Scope: Only files touched in Phase 1.** Do not review/test other files — another agent may be working on them.

```
for iteration in 1..3:
    1. PROVE IT WORKS (behavioral)
       - Execute the **Testing** section from the plan document
       - For each scenario: perform the action, verify the expected outcome
       - Record actual results (PASS/FAIL + what you observed)

       Fallback (if plan has no Testing section):
       - Backend: Run in REPL or curl with real input, verify output
       - Frontend: Use browser tools to navigate and interact with the feature

       "Build passes" is NOT proof. Actually exercise the code path.

    2. SELF-REVIEW (logic)
       - Follow the checklist in `/review` (scoped to files touched only)
       - Focus on CRITICAL and HIGH severity items first
       - Record any issues found with [File:line] format

    3. AUTOMATED CHECKS
       - Type check: mypy, tsc --noEmit
       - Lint: ruff, eslint (if configured)
       - Build: npm run build

    4. If issues found → fix them → next iteration
    5. If clean → exit loop
```

**Stop conditions:**
- No issues remain → SUCCESS
- 3 iterations completed → STOP (report remaining issues)

**Common mistakes to avoid:**
- Declaring "PASS" without actually running the feature
- Skipping behavioral checks because "build passed"
- Missing cleanup in useEffect, event listeners, intervals

## Phase 3: Final Report

1. **Update the plan document** — mark steps as done (🟩), update progress %

2. **Report to user:**

```
## Implementation Summary

### Files Touched
- [list of files created/modified]

### Verify-Fix Loop
- Iterations: X/3
- Issues fixed: Y
- Exit reason: [clean / max iterations]

### Proof of Behavior
- [What you actually ran/clicked to verify it works]
- [Observed output/result]

### Automated Checks
- Types: PASS/FAIL
- Build: PASS/FAIL

### Remaining Issues (if any)
- [File:line] Description

### Ready for Review
YES / NO (explain blockers if NO)
```

## Important

- **Scope is everything** — only touch files from Phase 1
- **Prove behavior first** — "it compiles" is not verification
- Fix all issues found
- If stuck on an issue after 2 attempts, note it and move on
