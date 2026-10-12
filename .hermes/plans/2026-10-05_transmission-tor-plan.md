# Plan — FC De Kampioenen upload via Transmission + Tor (vz. Tribler)

## Status
- Tribler kan NIET bouwen op Pi5 (libtorrent 1.2.19 vereist cp310, systeem is 3.13).
- Alternative (Optie 2 — geen betaalde VPN): Transmission-daemon + Tor SOCKS5 proxy.

## Configuratie (reeds toegepast)
- `/etc/transmission-daemon/settings.json`: `proxy-enabled: true`, `proxy-type: 1`, `proxy-hostname: localhost`, `proxy-port: 9050`; `peer-proxy-type: 1`, `peer-proxy-hostname: localhost`, `peer-proxy-port: 9050`; `peer-address-type: all`.
- Systemd-unit (`/usr/lib/systemd/system/transmission-daemon.service`) aangepast met `-T` (auth-vrij) en `-f --log-level=error --config-dir /etc/transmission-daemon`.
- Tor service actief (`debian-tor`), SOCKS5 op `localhost:9050`; `torsocks curl` bevestigt `IsTor: true`, IP `204.8.96.146`.

## Config.yaml update (`06-apps-thuis-v4`)
- Verwijderd: `tribler` blok (api_port, api_key, anon_hops, safe_seeding).
- Toegevoegd: `transmission: enabled: true` + comment over Tor-seeding.

## Automatisch verloop (thuis-v4 → .torrent → Transmission)
1. `thuis-v4` downloadt `De Kampioenen` (watchlist `Fc_De_Kampioenen.txt`).
2. `torrent_uploader` plugin maakt `.torrent` (libtorrent, trackers in config).
3. `.torrent` wordt automatisch toegevoegd aan Transmission via `transmission-remote` (of cron-script) → seeding via Tor (anoniem, geen VPN).

## Geverifieerde bestanden
- `.torrent`: `/mnt/HDD1/services/nextcloud/data/aldo/files/Media/tv/Fc De Kampioenen/FC.De.Kampioenen.S01E01.1080p.WEB-DL.AAC.x264.torrent`
- MP4: `/mnt/HDD1/services/nextcloud/data/aldo/files/Media/tv/Fc De Kampioenen/FC.De.Kampioenen.S01E01.1080p.WEB-DL.AAC.x264.mp4` (1.01 GB)
- Transmission-daemon: `transmission-remote --list` toont `FC.De.Kampioenen...` (idle, 0 peers — annoniem via Tor, peers volgen later).
