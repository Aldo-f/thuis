# Plan: Docusaurus Documentation Site

Add a Docusaurus documentation site and publish via GitHub Actions to GitHub Pages.

## TODOs

- [x] 1. **Scaffold Docusaurus site** — Initialize Docusaurus classic template in `website/` directory with npm, TypeScript enabled, custom title "thuis"
- [x] 2. **Configure GitHub Pages** — Set `url: https://aldo-f.github.io`, `baseUrl: /thuis/`, `organizationName: Aldo-f`, `projectName: thuis` in `docusaurus.config.ts`
- [x] 3. **Write documentation content** — Create pages for: intro, installation, usage, credentials, project structure, development
- [x] 4. **Create GitHub Actions workflow** — Create `.github/workflows/deploy-docs.yml` that builds and deploys to GitHub Pages on push to v4/main
- [x] 5. **Build and verify** — Run `npm run build` and confirm output is clean
- [x] 6. **Commit and push** — Commit all new files and push to remote

## Final Verification Wave

- [x] F1. **Docs build passes** — `npm run build` exits 0
- [x] F2. **Pages config correct** — baseUrl is `/thuis/`, org/user is `Aldo-f`, project is `thuis`
- [x] F3. **Workflow valid** — GitHub Actions YAML is syntactically correct with proper triggers and permissions
- [x] F4. **Content reasonable** — At least 4 doc pages exist with real content about the project
