# AGENTS.md — 06-apps-thuis-v4

## Overview
Thuis v4 home app (repo `aldo-f/thuis`, branch `v4/main`), deployed via manifest to `~/dev/06-apps-thuis-v4/`.

## Structure
```
06-apps-thuis-v4/
└── infra/
    ├── docker-compose.yml   # source of truth (copied to runtime on deploy)
    └── .env.template        # env template → runtime .env (gitignored)
```

## WHERE TO LOOK
| File | Purpose |
|------|---------|
| `infra/docker-compose.yml` | Service definition: image, ports, volumes, networks, healthcheck |
| `infra/.env.template` | Required env vars (no secrets; copy to `.env` at runtime) |
| `templates/infra/repos.manifest.jsonc` | Repo mapping: `infraSubdir: "infra"`, branch `v4/main` |
| `templates/infra/repos.manifest.jsonc` | Repo mapping: `infraSubdir: "infra"`, branch `v4/main` |

## CONVENTIONS
- **Edit templates only** — runtime dir `~/dev/06-apps-thuis-v4/` is regenerated on deploy
- **Manifest deploy** — Ansible clones/updates `aldo-f/thuis@v4/main`, copies `infra/` to runtime, runs `docker compose up -d`
- **External network** — joins `traefik_net` for TLS termination via Traefik
- **Healthcheck** — `GET /health` (Traefik + Docker both probe)
- **Volumes** — `config` (app config), `data` (app data) persisted

## ANTI-PATTERNS
- ❌ Editing `~/dev/06-apps-thuis-v4/infra/` directly — overwritten on next deploy
- ❌ Committing `.env` or secrets to the thuis repo — use `.env.template` + vault
- ❌ Hardcoding paths in compose — use `${CONFIG_DIR}`, `${DATA_DIR}` placeholders
- ❌ Adding services to this compose — one service per component; create new component instead