# Skill: independent adversarial review

Trigger: before accepting material implementation or publishing claims.

Review scope: project objectives, specification, actual changed files/diff, tests, screenshots when applicable, regressions, architecture drift, security/privacy, accessibility, performance, fabricated features and unnecessary model expense.

Severity: blocker / major / minor / note. For each issue include source evidence, reproduction, and minimal proposed repair. Distinguish verified problems from hypotheses.

Output:
```
Decision: APPROVE | REQUEST_CHANGES | INSUFFICIENT_EVIDENCE
Acceptance criteria: pass/fail/unknown per criterion
Findings: severity / evidence / fix
Tests actually run: ...
Residual risk: ...
```

Never invent test results; reviewer does not merge own change.