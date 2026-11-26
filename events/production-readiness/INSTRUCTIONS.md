# ATLAS Event — Production Readiness (PRD)
Version: 1.0 | Status: instruction set, not an installed or executed toolchain

## Invocation
Give an agent the URL of this file and access to the target project. Run PRD for that project; optionally specify a phase (e.g. PRD-03). Read the root [AGENTS.md](../../AGENTS.md) first. The target project is the subject, not the ATLAS vault. Do not modify ATLAS to record private project details. Default to audit-only, one phase at a time; stop at approval gates. No merge, deployment, game launch, display/GPU changes, live captures, spending, or external publication without separate explicit authorization. Never upload private source, logs, secrets or assets to external analysis services.

## Entry contract
Identify project root, current branch/commit, dirty changes, target runtime, release baseline, protected behavior, approved visual/audio assets, existing tests and operator constraints. Preserve unrelated work. Create an isolated working branch only for approved changes. Record actual access and distinguish evidence from hypotheses. If inaccessible, report blocked rather than simulating execution.

## Setup — selective skill and tool acquisition
Inspect upstream instructions, licenses, provenance, dependencies and compatibility before adopting any skill. Pin reviewed versions; do not execute remote install scripts blindly. Use local or isolated tooling with least privilege. Load only the skill needed for the current phase.
- https://github.com/mattpocock/skills — architecture improvement; inspect improve-codebase-architecture if available.
- https://github.com/trailofbits/skills — security, code analysis, test quality, release preparation.
- https://github.com/obra/superpowers — systematic debugging, verification and independent review.
- https://github.com/tomazb/agent-skills — simplification/resilience candidate; verify availability.
- https://github.com/Natchannnn/repository-engineering-skills — repository audit candidate; verify availability.
These are upstream candidates, not trusted or preinstalled dependencies. Adapt locally into independently invocable SKILL.md workflows only after review. Determine the actual harness discovery mechanism; do not change provider, model or reasoning effort. Record unavailable tools, substitute supported local checks, never fabricate output.

Tool candidates: [Luacheck](https://github.com/lunarmodules/luacheck), [LuaLS](https://github.com/LuaLS/lua-language-server), [jscpd](https://github.com/kucherenko/jscpd), [Lizard](https://github.com/terryyin/lizard), [Semgrep](https://github.com/semgrep/semgrep), [PSScriptAnalyzer](https://github.com/PowerShell/PSScriptAnalyzer), [Knip](https://github.com/webpro-nl/knip), [Madge](https://github.com/pahen/madge). Verify language support and run only applicable tools. Configure Lua 5.1/LuaJIT/FFI and dynamically invoked engine callbacks correctly. Use actual parser/runtime checks, not grep alone. Exclude vendor, generated assets, caches, archived checkpoints and historical packages from active-source metrics; inspect package inputs separately.

## Ordered event phases
Each phase must produce an evidence-backed finding ledger, affected paths/symbols, reproducer or rationale, severity, confidence, proposed smallest change, validation plan and stop condition. No remediation in PRD-01..06. If invoked for a single phase, do not silently run others.

| Phase | Instructions | Required evidence / exit |
|---|---|---|
| PRD-01 Repository reconnaissance | Trace entry points, dependency graph, state owners, production vs dev paths, build/package manifests, dynamic hooks and test topology. | Ownership map, scope/exclusions, baseline commit and baseline test results or blocker. |
| PRD-02 Architecture detangling | Identify duplicate ownership, circular dependencies, excessive coupling, leaky interfaces, needless wrappers and conflicting implementations. Compare simplification options; preserve behavior and extension contracts. | Ranked refactor candidates with before/after dependency sketch, risk and migration path. |
| PRD-03 Redundancy audit | Run applicable duplication, unused code/export and complexity analyzers. Trace runtime dispatch and config toggles before declaring code dead. Identify redundant paths, stale flags, abandoned experiments, repeated transforms and dependencies. | Verified vs suspected redundancy register; no automatic deletion. |
| PRD-04 Adversarial bug audit | Parse available logs and source; trace state transitions, stale state, race conditions, invalid inputs, nils, timeout/retry, ordering, cache identity, boundary conditions, fallback and cancellation. Reproduce deterministically where possible. | Minimal repro or source trace per defect, impact and confidence; separate known bugs from hypotheses. |
| PRD-05 Lifecycle and performance | Trace allocation/ownership/release on success, failure, cancellation, unload and transition. Identify blocking work, hot-path allocations, leaks, unbounded queues and cache issues. | Lifecycle matrix and measured timings where available; mark projections; no unauthorized live profiling. |
| PRD-06 Test integrity | Map requirements to tests, inspect assertions and fixtures, distinguish actual production-path evidence from mocks, find false positives, missing negative cases and stale expectations. | Coverage-gap register and targeted regression plan; no weakening tests to obtain green results. |
| PRD-07 Controlled remediation | Only after human approval of specific findings. Apply small behavior-preserving changes in isolated commits. Run targeted tests per change, compare outputs to baseline, rollback regressions. | Diff, tests actually run, remaining risk; independent reviewer examines evidence before signoff. |
| PRD-08 Release readiness | Verify production entry point, packaging allowlist, version/cache migration, dependencies, config defaults, clean install/disable/uninstall, rollback and documentation. Confirm research tooling is not shipped unintentionally. | Release checklist, manifest, hashes where available, known limitations, independent review and human go/no-go. Do not publish. |

## Mod/UI engineering overlay (when applicable)
Protect approved visual/audio identity; no redesign under a cleanup task. Trace native actors, render targets, transient materials, streaming flags, capture state machine, engine callbacks, cache fingerprinting, HUD adapter ownership, event/audio deduplication, asset fallback and game-thread stalls. Compare production and offline image processing; distinguish cached display cost from generation cost. Preserve standalone and optional host paths that are actually supported. Do not infer private/undisclosed gameplay data. Keep native fallback. Do not classify a passing fixture as live proof. Use existing captures and offline tests unless live validation is separately authorized. Compact visual evidence boards; respect provider image limits.

## Evidence and grading
Severity: P0 critical safety/data corruption/crash; P1 major correctness or release blocker; P2 maintainability/performance defect; P3 minor polish. Confidence: reproduced / source-proven / suspected. Include file:line and exact test command/result when available. Deduplicate findings by root cause. Review changes independently of the author; self-review is not independent signoff. Distinguish technical pass, artistic approval, and release approval. Do not inflate grades, hide failures, claim zero cost from unmeasured paths, or report tests not run.

## Output and handoff
Write project-local PRD report(s) only when authorized by the project's workspace rules. Include baseline SHA, scope, tool versions, commands, findings, protected contracts, actual changes, test counts, blockers and next phase. Keep a compact checkpoint so a fresh agent can resume without ingesting the entire history. Redact sensitive data. Report stop/approval state explicitly.
Default completion: stop after PRD-06 with prioritized remediation proposal (each phase reviewed separately); PRD-07 and PRD-08 require explicit gates. A single event link invokes the workflow, not permission to run everything autonomously.
