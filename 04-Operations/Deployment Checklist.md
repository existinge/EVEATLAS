# Deployment Checklist

- [x] GitHub write integration confirmed via initial README commit.
- [ ] Clone GitHub repo and open in Obsidian.
- [ ] Verify all remote files and branch history.
- [ ] Run `python tools/atlas.py audit` and `python -m unittest discover -s tests -v` locally.
- [ ] Turn on branch protection and mandatory checks if available.
- [ ] Configure agent read access to AGENTS.md and relevant notes; do not load whole vault for every request.
- [ ] Connect optional research APIs only after privacy, permission and billing review.
- [ ] Produce first sourced opportunity dossier and human-validate.
- [ ] Set per-task and total API spending caps.
- [ ] Verify provider caching on observed logs and invoices.
- [ ] Store transaction-level finances privately, keep public summaries redacted.
- [ ] Pilot independent adversarial review on one existing software change.

This checklist is a plan, not evidence that outside integrations are configured.