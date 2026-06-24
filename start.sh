#!/bin/sh
# Start the auth server in background
node /app/packages/auth-server/dist/index.js &
AUTH_PID=$!

# Trap SIGTERM/SIGINT to forward to nginx and clean up
trap 'kill $AUTH_PID 2>/dev/null; nginx -s quit 2>/dev/null; exit 0' TERM INT

# Start nginx in foreground
nginx -g "daemon off;"

# If nginx exits, also kill auth server
kill $AUTH_PID 2>/dev/null
