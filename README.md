# EVEATLAS — Business Operating System

An Obsidian-native, GitHub-versioned control center for developing **multiple independent income streams**.

## First steps
1. Clone this repository and open its folder in Obsidian as a vault.
2. Read [[00-Atlas/Home]], [[07-Business/Portfolio]], and [[AGENTS]].
3. Run `python tools/atlas.py audit` and `python -m unittest discover -s tests -v`.

## Core rules
- Markdown notes govern plans, hypotheses, decisions and research; Git preserves revisions. Tests and deployed systems establish implementation truth. Reconciled accounts establish revenue truth.
- Document sources and dates; never invent sales, clients, demand, product capabilities or API features.
- No secrets, medical/identity information, customer data or private agent memory in this **public** repository.
- Agents do not autonomously spend, publish, send outreach, or deploy without approval.
- Discover → validate → build → launch → measure → scale or stop.

## Sections
`00-Atlas`: dashboards; `01-Projects`: projects; `02-Agents`: reusable skills; `03-Architecture`: persistence; `04-Operations`: policies; `05-Decisions`: decision records; `06-Templates`: note templates; `07-Business`: portfolio; `08-Research`: evidence; `09-Metrics`: scorecards; `tools` and `tests`: validation.

**Current state:** Core vault published. External API integrations, paid services, automated research and actual revenue results must be verified separately.
## Signal Intelligence (foundation)
The offline-first [Signal Intelligence skill](02-Agents/Signal%20Intelligence.md) and [research operations guide](08-Research/Signal%20Desk.md) define an evidence-first research desk. Run `python tools/signal_desk.py examples/signal-desk-candidates.json` to ingest reviewed candidate records; run `python -m unittest discover -s tests -v` to check behavior locally. This does **not** provide X search, autonomous monitoring, source verification or a scheduled Bot. External adapters and routine scheduling require separate implementation, testing and approval.
