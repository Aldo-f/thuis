# AGENTS.md — 06-apps-thuis-v5

Thuis v5 — VRT MAX video downloader, next iteration of the thuis app. Managed as git submodule `Aldo-f/thuis` branch `v5/main`.

## Structure

```
06-apps-thuis-v5/
├── specs/                    # Spec-kit feature specs
│   ├── 002-thuis-web-downloader/
│   ├── 003-multi-provider-platform/
│   ├── 004-video-viewer-download/
│   └── 005-ytdlp-vrtmax-wrapper/
├── website/                  # MkDocs documentation site
│   └── docs/                 # THS documentation (imported by aldo-f.github.io)
├── scripts/                  # Build scripts (APK packaging)
├── SPEC.md                   # Master spec
├── pnpm-workspace.yaml       # Monorepo workspace config
└── .gitignore
```

> **Note:** This is a submodule checkout — the actual source lives in `git@github.com:Aldo-f/thuis.git` branch `v5/main`. Only the `infra/` subdir is managed by Ansible; the rest is developer workspace.

## Conventions

- **Spec-driven development**: Features get a spec under `specs/<nn>-<name>/` before implementation
- **pnpm monorepo**: Uses pnpm workspaces; never use npm/yarn
- **MkDocs docs**: Website docs are imported into `aldo-f.github.io` via multirepo plugin
- **Branch discipline**: Always work on feature branches; main is deployment target

## Deployment

Managed via `01-core-infra/templates/infra/repos.manifest.jsonc`. Ansible clones the repo at the specified branch and deploys the `infra/` subdir.

## Anti-patterns

- ❌ Don't edit source directly in this checkout — it's a submodule
- ❌ Don't commit `.env` or credentials
- ❌ Don't use npm/yarn — use pnpm
- ❌ Don't push to main without spec approval
