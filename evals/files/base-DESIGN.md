---
version: alpha
name: Harbor Operations
colors:
  primary: "#174A7E"
  primary-hover: "#103C69"
  surface-default: "#FFFFFF"
  surface-subtle: "#F4F7FA"
  text-primary: "#16202A"
  text-secondary: "#52606D"
  border-default: "#D5DDE5"
  status-success: "#247A49"
typography:
  headline-lg:
    fontFamily: "Arial, sans-serif"
    fontSize: 32px
    fontWeight: 700
    lineHeight: 1.2
  body-md:
    fontFamily: "Arial, sans-serif"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
  label-md:
    fontFamily: "Arial, sans-serif"
    fontSize: 13px
    fontWeight: 600
    lineHeight: 1.4
rounded:
  sm: 4px
  md: 8px
spacing:
  sm: 8px
  md: 16px
  grid-columns: 12
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface-default}"
    typography: "{typography.label-md}"
    rounded: "{rounded.md}"
    padding: 12px
    height: 40px
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  surface-page:
    backgroundColor: "{colors.surface-subtle}"
  text-body:
    textColor: "{colors.text-primary}"
  text-muted:
    textColor: "{colors.text-secondary}"
  border-sample:
    backgroundColor: "{colors.border-default}"
  status-success:
    backgroundColor: "{colors.status-success}"
---

# Harbor Operations

## Overview
A precise operations interface for high-density logistics work.

## Colors
Brand blue leads actions; neutral surfaces prioritize operational data.

## Typography
Arial is used in this fixture for deterministic local rendering.

## Layout
A 12-column desktop grid collapses to a single-column mobile flow.

## Elevation & Depth
Borders and tonal surfaces provide hierarchy with minimal shadows.

## Shapes
Controls use restrained 4–8px radii.

## Components
Buttons, forms, tables, alerts, and dialogs share the same state model.

## Do's and Don'ts
- Do prioritize task status.
- Don't use color as the only status cue.

## Accessibility
Keyboard focus and semantic labels are required.
