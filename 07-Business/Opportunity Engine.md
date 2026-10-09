# Opportunity Engine — problem to product

## Purpose
Systematically discover expensive, recurring unmet problems and route them toward appropriate products **before** a large build.

## Pipeline
1. **Discover:** public niche communities, interviews, support requests, competitor reviews, searches; preserve URLs, dates and precise pain.
2. **Cluster:** identify independent examples of the same underlying customer job, not superficial keywords.
3. **Validate:** check buyer identity, willingness to pay, alternatives, distribution and counterevidence. Reddit upvotes are not sales.
4. **Score:** pain, frequency, paying buyers, payment evidence, solution gap, feasibility, distribution, differentiation minus risk and ongoing support. Unknown remains unknown.
5. **Select solution format:** guide, template, done-for-you service, automation, micro-SaaS, or no product.
6. **Experiment:** choose cheapest falsifiable test with time and cost limit.
7. **Build:** small specific MVP only when adequate evidence exists.
8. **Launch:** human-approved public release and distribution.
9. **Measure:** leads, conversion, gross receipts, cost, margin, support and retention.
10. **Scale or stop:** decide from real observations; record reasons.

## Tooling
`tools/opportunities.py` supplies deterministic partial scoring; `data/opportunities.example.json` is purely synthetic.
Use [[06-Templates/Opportunity Template]], [[06-Templates/Experiment Template]], and [[08-Research/Validation Playbook]].

## Controls
Respect data-use restrictions, platform community rules and privacy; don't build scraping/spam machinery or invent statistics. Human approves direct outreach, campaigns, paid research and commercial claims.