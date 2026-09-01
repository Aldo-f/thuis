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

## Watchlist Functionality
The thuis tool includes a `--watchlist` feature for automated processing of multiple URLs from text files.

### Watchlist File Format

1. **First non-comment line**: Output directory (where files will be saved)
   - Supports absolute paths, relative paths, and `~/` home expansion
   - Example: `/mnt/HDD1/nextcloud/data/aldo/files/Seed/media/tv/`

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
./thuis.sh --watchlist watchlists/Fc_De_Kampioenen.txt --dry-run

# Process manual entries for a series (requires --now)
./thuis.sh --watchlist watchlists/Fc_De_Kampioenen.txt --now

# Process multiple series at once (all require --now for manual entries)
./thuis.sh --watchlist watchlists/Fc_De_Kampioenen.txt \
           --watchlist watchlists/Flikken.txt \
           --watchlist watchlists/Flikken_Maastricht.txt \
           --watchlist watchlists/Thuis.txt \
           --now --dry-run

# Process podcasts (scheduled entries run automatically, manual need --now)
./thuis.sh --watchlist watchlists/podcast.txt --now --dry-run
```

### ‑‑now override
`--now` forces all entries (scheduled or manual) to be processed again, ignoring the
last‑run timestamps stored in `~/.thuis/state.db`. Use this when a previous run
failed or new episodes appeared.

| Example Watchlist Files

Each series has its own watchlist file in `watchlists/`:
- `watchlists/Fc_De_Kampioenen.txt` - Fc De Kampioenen series (manual entries, use --now)
- `watchlists/Flikken.txt` - Flikken series (manual entries, use --now)
- `watchlists/Flikken_Maastricht.txt` - Flikken Maastricht series (manual entries, use --now)
- `watchlists/Thuis.txt` - Thuis series (manual entries, use --now)
- `watchlists/podcast.txt` - Podcasts (scheduled entries: weekly)

All TV series watchlists output to `/mnt/HDD1/nextcloud/data/aldo/files/Seed/media/tv/`
Podcast watchlist outputs to `/mnt/HDD1/nextcloud/data/aldo/files/Media/podcasts/_seed`
