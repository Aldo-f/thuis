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

## Watchlist Functionality
The thuis tool includes a `--watchlist` feature for automated processing of multiple URLs from text files.

### Watchlist File Format

1. **First non-comment line**: Output directory (where files will be saved)
   - Supports absolute paths, relative paths, and `~/` home expansion
   - Example: `/path/to/tv/shows/`

2. **Subsequent lines**: URL entries with optional scheduling
   - Format: `[schedule] URL # optional comment`
   - Schedule examples:
     - `[daily]` - run once per day
     - `[weekly]` - run once per week
     - `[weekdays 10:00]` - run on weekdays at 10:00 AM
     - No schedule - requires `--now` flag to run (manual entries)

### Usage Examples

```bash
# Process a single series watchlist (dry run)
./thuis.sh --watchlist watchlists/series_a.txt --dry-run

# Process manual entries for a series (requires --now)
./thuis.sh --watchlist watchlists/series_a.txt --now

# Process multiple series at once (all require --now for manual entries)
./thuis.sh --watchlist watchlists/series_a.txt \
           --watchlist watchlists/series_b.txt \
           --watchlist watchlists/series_c.txt \
           --watchlist watchlists/series_d.txt \
           --now --dry-run

# Process podcasts (scheduled entries run automatically, manual need --now)
./thuis.sh --watchlist watchlists/podcasts.txt --now --dry-run
```

### ‑‑now override
`--now` forces all entries (scheduled or manual) to be processed again, ignoring the
last‑run timestamps stored in `~/.thuis/state.db`. Use this when a previous run
failed or new episodes appeared.

### Example Watchlist Files

Example watchlist files are provided in the `watchlists/` directory for different types of content (TV shows, podcasts, etc.).

TV series watchlists typically point to a TV shows directory.
Podcast watchlist points to a podcasts directory.