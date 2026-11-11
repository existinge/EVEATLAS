# T00 — Environment, source and architecture preflight

Timebox: 10–15 minutes. Status: NOT STARTED. Depends on: none.

## Agent assignment
Audit EVEATLAS without changing its authority rules. Check Node/npm availability, browser build tooling, current test baseline, and whether a suitable tldraw Agent Starter Kit or minimal editor integration is faster to use in this environment. Confirm current tldraw terms for the intended distribution. Identify likely duplex adapter candidates by *documented observable events*, not marketing claims. Choose only a provisional approach; provider connection comes later.

## Required outputs
- Brief report at 01-Projects/Living-Canvas/worklogs/T00.md or equivalent Atlas-compliant handoff; no secrets.
- A recommendation: minimal tldraw editor vs Agent Starter Kit, with source references.
- Expected code path and exact setup commands for next ticket.
- Existing test results with exit codes; no invented pass.
- Explicit note of whether public repository permission covers the intended implementation.

## Commands to attempt
~~~sh
python tools/atlas.py audit
python -m unittest discover -s tests -v
node --version
npm --version
~~~

## Forbidden
Do not install LiveKit by default, call paid models, download model weights, create a separate Atlas control plane, publish/deploy, or redesign event schema unilaterally.

## Acceptance gate P0
Clean documented baseline or clearly captured failure, decided minimal runtime location, no changed canonical authority files. Return handoff: branch/commit, evidence, next T01 action.
