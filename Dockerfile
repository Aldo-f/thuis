# Multi-stage build: Thuis Vite/React web-app
# ------------------------------------------------------
# Stage 1 – build core library and web-app
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

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source code
COPY tsconfig.base.json ./
COPY packages/core ./packages/core
COPY packages/web-app ./packages/web-app

# Build core, then web-app
RUN pnpm --filter @thuis/core build
RUN pnpm --filter @thuis/web-app build

# Stage 2 – serve with nginx
FROM nginx:alpine

# Copy nginx config for SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built web-app assets
COPY --from=builder /app/packages/web-app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
