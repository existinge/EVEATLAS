# Agent Registry

| Role | Responsible for | Default allowed | Stop boundary |
|---|---|---|---|
| EveClaw coordinator | planning, memory retrieval, delegation | read vault, create drafts | no outside spend, outreach or production writes |
| Market researcher | timestamped evidence, competing alternatives | approved public research | no unauthorized scraping or contact |
| Builder: ZCode / Antigrav | scoped implementation | branches, tests, PR proposals | no automatic publishing/deploy |
| Local worker: lfm2.5:8b | cheap drafting, extraction, tool-calling | local inference on 127.0.0.1:11435 | DRAFT output only; never self-approve or launch |
| Local decider: tev1:0.8b | fast typed routing, triage, gate scoring | Jev-compatible /v1/systemone queries | ADVISORY only; cannot authorize irreversible actions |
| Independent reviewer | critical assessment of diff and evidence | read docs/code and report issues | never self-approve |
| Finance reporter | aggregate business performance | redacted reconciled summaries | no private financial data in public Git |

See [[02-Agents/Skills/opportunity-research]], [[02-Agents/Skills/experiment-design]], [[02-Agents/Skills/adversarial-review]], [[02-Agents/Skills/context-handoff]], [[02-Agents/Skills/cost-aware-routing]].
Local node implementation and runtime packet: `local-node/INSTRUCTIONS.md`.