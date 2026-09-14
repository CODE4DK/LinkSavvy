# Multi-stage build: `builder` runs the npm workspace install and Vite
# build; the runtime stage is a bare nginx image serving only the built
# static output -- no Node, no source, no node_modules ship in it.

FROM node:22-slim AS builder

WORKDIR /repo

# The workspace's shared lockfile/root manifest, then each workspace's
# own manifest -- same layering rationale as the API image: dependency
# install is the expensive layer, so it's cached separately from source
# changes.
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
COPY packages/contracts/package.json packages/contracts/package.json
RUN npm ci

COPY packages/contracts packages/contracts
COPY apps/web apps/web
RUN npm run build --workspace=@linksavvy/web

FROM nginx:1.27-alpine AS runtime

COPY apps/web/nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=builder /repo/apps/web/dist /usr/share/nginx/html

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://localhost:8080/ || exit 1
