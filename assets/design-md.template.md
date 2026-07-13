---
version: alpha
name: "[REPLACE: Design System Name]"
description: "[REPLACE: One-sentence purpose]"
colors:
  brand-primary: "#0057B8"
  brand-primary-hover: "#004A9E"
  brand-primary-active: "#003E85"
  surface-default: "#FFFFFF"
  surface-subtle: "#F5F7FA"
  text-primary: "#17202A"
  text-secondary: "#5B6673"
  border-default: "#D8DEE6"
  status-success: "#1E7A46"
  status-warning: "#A65C00"
  status-danger: "#B42318"
typography:
  headline-lg:
    fontFamily: "system-ui, sans-serif"
    fontSize: 32px
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: -0.02em
  headline-md:
    fontFamily: "system-ui, sans-serif"
    fontSize: 24px
    fontWeight: 700
    lineHeight: 1.3
  body-md:
    fontFamily: "system-ui, sans-serif"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.55
  label-md:
    fontFamily: "system-ui, sans-serif"
    fontSize: 13px
    fontWeight: 600
    lineHeight: 1.4
rounded:
  none: 0px
  sm: 4px
  md: 8px
  lg: 12px
  full: 999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  page-gutter: 24px
  grid-columns: 12
components:
  button-primary:
    backgroundColor: "{colors.brand-primary}"
    textColor: "{colors.surface-default}"
    typography: "{typography.label-md}"
    rounded: "{rounded.md}"
    padding: 12px
    height: 40px
  button-primary-hover:
    backgroundColor: "{colors.brand-primary-hover}"
    textColor: "{colors.surface-default}"
  input-default:
    backgroundColor: "{colors.surface-default}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: 12px
    height: 40px
---

# [REPLACE: Design System Name]

## Overview

[REPLACE: Brand personality, product domain, target users, density, emotional tone, and the intended relationship between brand and task completion.]

## Colors

[REPLACE: Explain each palette role, semantic behavior, contrast constraints, theme behavior, and logo/background combinations.]

## Typography

[REPLACE: Explain font roles, hierarchy, numeric behavior, line length, localization, fallbacks, and licensing constraints.]

## Layout

[REPLACE: Explain grid, containers, navigation structures, spacing rhythm, density, breakpoints, and page templates.]

## Elevation & Depth

[REPLACE: Explain borders, tonal layering, shadows, overlays, sticky surfaces, and z-order.]

## Shapes

[REPLACE: Explain corner radius, control geometry, icon stroke/size, and where exceptions are allowed.]

## Components

[REPLACE: Define anatomy, variants, sizes, states, behavior, and content rules for common and domain-specific components.]

## Do's and Don'ts

- Do [REPLACE].
- Don't [REPLACE].

## Iconography

[REPLACE if relevant.]

## Motion

[REPLACE if relevant.]

## Accessibility

[REPLACE: contrast, focus, keyboard, semantics, reduced motion, non-color cues.]

## Content & Terminology

[REPLACE: tone, labels, dates, numbers, empty states, validation and domain terminology.]

## Data Visualization

[REPLACE if relevant.]

## Domain Components

[REPLACE: workflows and domain-specific patterns.]

## Responsive Matrix

[REPLACE: behavior at 1440, 1024, 768, 390.]

## Localization

[REPLACE if relevant.]

## Themes

[REPLACE if relevant; keep machine-readable overrides in tokens/themes.json.]

## Governance

[REPLACE: ownership, versioning, exceptions, review and migration rules.]

## Agent Implementation Guide

[REPLACE: deterministic instructions for coding agents implementing the system.]
