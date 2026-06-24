# Multi-stage build: Thuis Vite/React web-app + Auth server
# ------------------------------------------------------
# Stage 1 – build core library, web-app, and auth server
FROM node:20-alpine AS builder

WORKDIR /app

# Install pnpm (pin to v10 which supports Node 20)
RUN corepack enable && corepack prepare pnpm@10.33.4 --activate

# Copy workspace manifests and lockfile
COPY pnpm-workspace.yaml ./
COPY package.json ./
COPY pnpm-lock.yaml ./
COPY packages/core/package.json ./packages/core/package.json
COPY packages/web-app/package.json ./packages/web-app/package.json
COPY packages/auth-server/package.json ./packages/auth-server/package.json

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source code
COPY tsconfig.base.json ./
COPY packages/core ./packages/core
COPY packages/web-app ./packages/web-app
COPY packages/auth-server ./packages/auth-server

# Build core, auth-server, then web-app
RUN pnpm --filter @thuis/core build
RUN pnpm --filter @thuis/auth-server build
RUN pnpm --filter @thuis/web-app build

# Stage 2 – serve with nginx + auth server
FROM node:20-alpine AS runner

RUN apk add --no-cache nginx

# Copy nginx config for SPA routing
COPY nginx.conf /etc/nginx/http.d/default.conf

# Copy built web-app assets
COPY --from=builder /app/packages/web-app/dist /usr/share/nginx/html

# Copy built auth server
COPY --from=builder /app/packages/auth-server/dist /app/packages/auth-server/dist
COPY --from=builder /app/packages/auth-server/package.json /app/packages/auth-server/package.json

# Copy start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 80

ARG MASTER_PASSWORD=changeme
ENV MASTER_PASSWORD=${MASTER_PASSWORD}
ENV AUTH_PORT=3001

CMD ["/start.sh"]
