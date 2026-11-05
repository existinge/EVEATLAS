# ATLAS Context Profile Registry

Profiles are compact, versioned **references**, not a copy of the user's full private memory.

| Key | Reference | Intended retrieval |
|---|---|---|
| `bl_taste` | [BL Taste & Discovery](BL_TASTE.md) | BL research, candidate ranking, romance/media adjacent work |
| `interests_projects` | [Intersecting Interests & Projects](INTERESTS_PROJECTS.md) | project planning, research routing, learning, cross-domain opportunities |

## Agent loading contract
1. Determine task purpose and selectively open relevant profile(s). Don't inject both in every prompt.
2. Resolve authoritative **dynamic** information from current project records before acting (BL workbook and corrections, project task state, execution receipts).
3. Label the source and date of externally derived facts; don't treat a preference profile as evidence of a production's plot or current availability.
4. Respect privacy: this is a public GitHub repository. Never commit private/sensitive user data or raw memories to these profiles.
5. On conflicts, explicit recent user correction > current canonical project state > these stable contextual summaries; escalate unresolved conflicts rather than silently overwrite.
6. Log profile reference/version in the handoff for reproducibility.

Example handoff:
```yaml
context_profiles:
  - key: bl_taste
    path: profiles/BL_TASTE.md
  - key: interests_projects
    path: profiles/INTERESTS_PROJECTS.md
authoritative_dynamic_sources:
  - latest canonical BL tracker + corrections, when BL discovery is in scope
```

Profile references do **not** imply that a runtime retrieval adapter is deployed. ATLAS agents must explicitly load these files or an authorized context router must be implemented and tested.
