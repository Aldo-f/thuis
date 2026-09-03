# AGENTS.md — Thuis v4 Website

Docusaurus documentation site for the `thuis` project. Static site, no build step beyond
`npm install && docusaurus build`.

## OVERVIEW

Docusaurus v2 site at `~/dev/06-apps-thuis-v4/website/`. Generates a versioned docs site with
sidebar navigation. Source: `docs/`, `src/`. Config: `docusaurus.config.ts`.

## STRUCTURE

```
website/
├── docs/                  # Documentation source (intro, installation, usage, credentials, dev)
├── src/                   # React components (css/, pages/)
├── static/                # Static assets
├── docusaurus.config.ts   # Site config (theme, nav, plugins)
├── sidebars.ts            # Sidebar structure
├── package.json            # Dependencies (Docusaurus, React)
├── postcss.config.mjs      # PostCSS config
└── versioned_docs/         # Versioned docs snapshots (v1.0.0 → v4.1.0)
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| Add a doc page | `docs/*.md` |
| Add a React component | `src/` |
| Edit nav/sidebar | `docusaurus.config.ts`, `sidebars.ts` |
| Add static asset | `static/` |
| Version docs | `versioned_docs/`, `versions.json` |

## CONVENTIONS

- **Docusaurus v2** with `@docusaurus/preset-classic`.
- **Sidebar** defined in `sidebars.ts` — auto-generates from `docs/_category_.json`.
- **Versioning** — `versions.json` pins available versions; `versioned_docs/` holds snapshots.
- **PostCSS** for styling (`postcss.config.mjs`).

## ANTI-PATTERNS

- **NEVER edit `versioned_docs/` directly** — regenerate via `npm run docusaurus docs:version`.
- **NEVER commit build artifacts** — `build/` is gitignored.

## COMMANDS

```bash
cd ~/dev/06-apps-thuis-v4/website
npm install
npm run docusaurus start    # dev server (port 3000)
npm run docusaurus build    # production build
npm run docusaurus docs:version  # snapshot current docs as a new version
```

## NOTES

- The parent `06-apps-thuis-v4/AGENTS.md` covers the broader app context (orchestration, specs).
- See `docs/credentials.md` for credential handling conventions.