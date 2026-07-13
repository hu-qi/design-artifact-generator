# Quality rubric

## P0 — packaging blockers

- `DESIGN.md` has zero validation errors.
- Normative YAML uses only supported groups and value shapes.
- All token references resolve; no cycles.
- `index.html` opens locally and all local references resolve.
- No secrets, private endpoints, personal data, `TODO`, `[REPLACE]`, lorem ipsum, or invented claims.
- Prototype visibly implements the specification and contains product proof, not only a token page.
- Required component states and responsive paths exist.
- Keyboard focus is visible and core controls have accessible names.
- `reports/critique.json` is complete.

## P1 — expected quality

- Evidence ledger distinguishes observed, derived, and proposed choices.
- Brand assets and colors are used according to documented roles.
- Visual hierarchy is clear within two seconds.
- Component anatomy and states are consistent across pages.
- Content density matches the product domain.
- Typography and spacing form a deliberate rhythm rather than arbitrary local values.
- Mobile layouts are re-composed, not desktop pages scaled down.
- Domain-specific components prove the system is not generic.

## P2 — high polish

- Screenshot snapshots are included for key widths.
- Micro-interactions improve orientation without distracting.
- Data visualizations include labels, legends, empty states, and non-color cues.
- Localization expansion and long-content stress cases are demonstrated.
- The package includes a clear migration map for an existing codebase.

## Critique schema

Create `reports/critique.json`:

```json
{
  "schemaVersion": 1,
  "score": 4.6,
  "axes": {
    "evidence": {"score": 4.7, "notes": "..."},
    "brand": {"score": 4.6, "notes": "..."},
    "hierarchy": {"score": 4.6, "notes": "..."},
    "typography": {"score": 4.5, "notes": "..."},
    "components": {"score": 4.7, "notes": "..."},
    "interaction": {"score": 4.5, "notes": "..."},
    "responsive": {"score": 4.5, "notes": "..."},
    "accessibility": {"score": 4.4, "notes": "..."},
    "specificity": {"score": 4.8, "notes": "..."},
    "restraint": {"score": 4.6, "notes": "..."}
  },
  "exceptions": []
}
```

Scores range from 1 to 5. Notes must name visible evidence and remaining weaknesses. A 5 means no material improvement is currently evident, not merely “looks good.”
