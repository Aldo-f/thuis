#!/bin/bash
set -euo pipefail
cd /home/aldo/dev/06-apps-thuis-v4
./thuis.sh \
  --watchlist watchlists/Fc_De_Kampioenen.txt \
  --watchlist watchlists/Flikken.txt \
  --watchlist watchlists/Flikken_Maastricht.txt \
  --watchlist watchlists/Thuis.txt \
  --watchlist watchlists/Thuis-test.txt \
  --watchlist watchlists/podcast.txt \
  "$@"