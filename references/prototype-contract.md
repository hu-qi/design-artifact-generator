# Prototype implementation contract

## Purpose

The prototype is executable evidence that `DESIGN.md` is implementable. It is not a decorative mood board and not a collection of disconnected cards.

## Required surfaces in full mode

### 1. Design catalog

The catalog must demonstrate:

- core and semantic colors with token names and contrast-conscious pairings;
- the complete typography scale;
- spacing, grid, container, and breakpoint behavior;
- radii, borders, elevation, overlays, and layering;
- icon rules and icon examples;
- buttons, links, badges, tags, inputs, textareas, selects, date controls, checkbox, radio, switch, upload, and validation;
- navigation, breadcrumb, tabs, pagination, table, card, dialog, drawer, popover, tooltip, toast, alert, and empty/loading/error states;
- charts or data displays when the product uses them;
- domain-specific components.

### 2. Product proof

Implement at least one coherent, realistic screen set:

- marketing product: homepage plus one conversion or detail state;
- SaaS/admin: dashboard/list plus detail/form/overlay state;
- mobile app: primary flow with at least three connected screens;
- public-sector/enterprise: workbench, list/detail, workflow status, permission/sensitive-data state;
- existing product refresh: one representative high-density page and one interaction-heavy page.

Use navigation or links so the reviewer can move through the proof.

## State coverage

Show or make interactively reachable:

- default;
- hover;
- focus-visible;
- active/selected;
- disabled;
- loading/skeleton;
- empty;
- validation error;
- system error;
- success feedback;
- permission-restricted;
- destructive confirmation where applicable.

## Responsive matrix

At minimum verify:

| Width | Expected behavior |
|---:|---|
| 1440 | full desktop hierarchy and density |
| 1024 | reduced columns or collapsible navigation |
| 768 | tablet reflow, simplified controls |
| 390 | mobile task flow; reflow rather than scale-down |

Avoid fixed widths that cause whole-page horizontal scrolling. Data tables may use a documented local overflow container or transform into cards.

## Accessibility baseline

- semantic landmarks (`header`, `nav`, `main`, `aside`, `footer`);
- one logical `h1` per page and ordered heading hierarchy;
- accessible names for controls;
- `<label>` or equivalent for form controls;
- alt text for informative images and empty alt for decorative images;
- visible keyboard focus;
- keyboard-operable menus, tabs, dialogs, and custom controls;
- status not communicated by color alone;
- `prefers-reduced-motion` support;
- normal text contrast target 4.5:1 and large text/UI graphics target 3:1.

## Implementation rules

- Generate styles from `tokens/tokens.css` or mirror the same variable names.
- Keep brand assets in `assets/`; preserve aspect ratio.
- Keep data and UI copy realistic but traceable to supplied facts or clearly marked samples.
- Avoid fashionable but unsupported visual effects. A brand system should explain every major choice.
- Prefer no external runtime dependency. If an external dependency is essential, vendor it or document the offline limitation.
