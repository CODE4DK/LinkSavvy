# Multi-stage build: `builder` runs the npm install and Vite build; the
# runtime stage is a bare nginx image serving only the built static
# output -- no Node, no source, no node_modules ship in it.

FROM node:22-slim AS builder

WORKDIR /repo

# Dependency install is the expensive layer, so it's cached separately
# from source changes.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS runtime

COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=builder /repo/dist /usr/share/nginx/html

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://localhost:8080/ || exit 1
