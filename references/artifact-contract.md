# Artifact contract

## Default directory

```text
<slug>-design-v<version>/
├── DESIGN.md                    # normative design source of truth
├── README.md                    # how to review and run the artifact
├── index.html                   # main catalog/review entry
├── artifact.json                # generated manifest and checksums
├── assets/                      # approved logos, images, CSS, JS
├── prototype/                   # optional additional product pages/flows
├── tokens/
│   ├── tokens.json
│   ├── tokens.css
│   └── themes.json              # only when multiple themes exist
├── evidence/
│   ├── sources.md
│   ├── decisions.md
│   └── asset-inventory.json
├── reports/
│   ├── design-md-lint.json
│   ├── google-design-md-lint.json  # when official CLI is available
│   ├── artifact-audit.json
│   └── critique.json
└── screenshots/                # recommended when browser capture is available
```

Additional files are allowed, but the main entry and design source must remain at the root.

## `artifact.json`

The packager writes:

- schema and artifact version;
- name and slug;
- `entry` and `designSystem` paths;
- discovered HTML entries;
- validation summary;
- UTC packaging timestamp;
- SHA-256 and size for distributable files.

Checksums exclude `artifact.json` itself to avoid a recursive hash.

## ZIP naming

Use `<slug>-design-v<version>.zip`, for example `xsxc-design-v1.1.0.zip`.

## Exclusions

Always exclude:

- `.git/`, `node_modules/`, virtual environments, caches;
- `__MACOSX/`, `.DS_Store`, editor state;
- nested output ZIP files;
- secret files and local environment configuration;
- unapproved original source documents.
