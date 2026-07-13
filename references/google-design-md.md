# Google DESIGN.md compatibility profile

This skill targets `@google/design.md` 0.3.0 and the format version named `alpha`.

## Normative frontmatter

```yaml
---
version: alpha
name: Example
# description: optional
colors:
  primary: "#123456"
typography:
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.5
rounded:
  md: 8px
spacing:
  md: 16px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: 12px
---
```

Allowed top-level normative groups are:

- `version`
- `name`
- `description`
- `colors`
- `typography`
- `rounded`
- `spacing`
- `components`

### Colors

`colors` is a flat map. Every value must be a valid CSS color string. Use names such as `brand-primary`, `surface-default`, `text-primary`, `status-danger`, and `theme-executive-surface`; do not nest `brand`, `semantic`, or `theme` objects.

### Typography

Each typography token is an object. Supported fields:

- `fontFamily` string
- `fontSize` dimension using `px`, `em`, or `rem`
- `fontWeight` number
- `lineHeight` dimension or unitless number
- `letterSpacing` dimension
- `fontFeature` string
- `fontVariation` string

Do not use aliases such as `size`, `weight`, `line_height`, `body_font`, or `display_font` in normative frontmatter.

### Dimensions

Dimensions use `px`, `em`, or `rem`. Spacing may also be a number for quantities such as column count or ratios.

### References

Use `{path.to.token}`. A component may reference a primitive or a composite typography token. All references must resolve and must not form a cycle.

## Standard Markdown sections

Use `##` headings in this sequence:

1. `Overview` (alias accepted by the spec: `Brand & Style`)
2. `Colors`
3. `Typography`
4. `Layout` (alias: `Layout & Spacing`)
5. `Elevation & Depth` (alias: `Elevation`)
6. `Shapes`
7. `Components`
8. `Do's and Don'ts`

Do not prefix these headings with numbers. Unknown extension sections are allowed and should follow the standard sequence.

## Full UI specification extensions

The Google format deliberately leaves room for domain-specific prose. Add only relevant sections after the standard set:

- Iconography
- Motion
- Accessibility
- Content & Terminology
- Data Visualization
- Domain Components
- Responsive Matrix
- Localization
- Themes
- Governance
- Agent Implementation Guide

Keep additional machine-readable data in separate files such as `tokens/themes.json`, not in nonstandard frontmatter groups.

## Official checks

```bash
npx --yes @google/design.md@0.3.0 lint DESIGN.md
npx --yes @google/design.md@0.3.0 export --format dtcg DESIGN.md
npx --yes @google/design.md@0.3.0 export --format css-tailwind DESIGN.md
```

The bundled validator is stricter about unsupported top-level keys and malformed typography because generated artifacts should remain portable across consumers.
