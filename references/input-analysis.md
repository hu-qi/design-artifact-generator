# Input analysis protocol

## Evidence hierarchy

When sources disagree, use this precedence unless the user specifies otherwise:

1. official brand source files and approved VI manuals;
2. explicit product requirements and current business rules;
3. official website and current production product;
4. approved screenshots or design files;
5. user-designated reference products;
6. general visual inspiration.

Implementation code is evidence of current behavior, not automatically the desired design rule.

## Source ledger

For every source, record:

| Field | Meaning |
|---|---|
| ID | stable local identifier such as `S01` |
| Source | path or URL |
| Accessed | ISO date or file timestamp |
| Role | brand / product / reference / constraint |
| Extracted facts | concise factual observations |
| Confidence | high / medium / low |
| Distribution | may embed / reference only / private |

## What to extract

### Brand files

- exact logo variants and safe area;
- normative colors and their stated roles;
- typefaces and licensing constraints;
- imagery, illustration, icon, and motion posture;
- prohibited usage.

### Reference websites

- information architecture and page rhythm;
- density, alignment, grid, spacing, and responsive transitions;
- component anatomy and interaction behavior;
- visual details worth adapting;
- details that are unique to the reference brand and therefore must not be copied.

Record the access date. A reference site may change.

### Screenshots

- viewport/aspect ratio and probable device class;
- measurable spacing and type scale ranges;
- repeated colors, borders, radii, shadows, and control heights;
- persistent navigation and content hierarchy;
- missing states that must be proposed.

A screenshot is evidence of one state at one viewport, not a complete interaction specification.

### Existing product or code

- route and layout structure;
- actual component inventory;
- current tokens and hard-coded styles;
- domain states, permissions, tables, filters, forms, charts, and workflows;
- localization and accessibility behavior;
- technical constraints and reusable assets.

## Decision log language

Use explicit labels:

```markdown
- [observed][S01] Official primary color is #004AA8.
- [derived][S01,S04] A 4px base spacing unit best explains the measured layout values.
- [proposed] Use a 40px default control height to balance density and accessibility.
```

## Missing evidence

Do not halt merely because one source type is missing. Continue with documented proposals. Material ambiguities that affect brand authenticity should be surfaced as review items, not hidden.

## Privacy and rights

- Never copy credentials, tokens, private API endpoints, hidden metadata, or personal information into the artifact.
- Do not redistribute third-party website images or commercial fonts merely because they were visible in a reference.
- Preserve original files only when the user supplied them for inclusion and distribution is appropriate.
