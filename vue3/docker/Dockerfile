ARG NODE_VERSION=22.7.0-alpine3.20
ARG NGINX_VERSION=1.27.1

#######################################################################################
## Stage: build front-end
FROM node:${NODE_VERSION} AS frontend-builder

WORKDIR /app
RUN apk add --no-cache bash
COPY ./package.json ./src ./public *config.js index.html /app/

RUN npm install
RUN npm run build

#######################################################################################
## Stage: dev image (with hot swap)
FROM node:${NODE_VERSION} AS dev-server

WORKDIR /app

# ui source code should be mounted in /app
RUN apk update && apk add --no-cache gettext bash

RUN mkdir /docker-entrypoint-banking.d/
COPY --chmod=774 ./docker/scripts/banking-entrypoint.sh /usr/local/bin/
COPY --chmod=774 ./docker/scripts/run-npm-install.sh /docker-entrypoint-banking.d/750-run-npm-install.sh

ENTRYPOINT ["docker-entrypoint.sh", "banking-entrypoint.sh"]

# rebuild (ignoring current node-module folder) then serve
CMD ["npm", "run", "dev", "--", "--host='0.0.0.0'", "--port='80'"]

#######################################################################################
## Stage: building nginx image serving the front-end
FROM nginx:${NGINX_VERSION}-alpine AS prod-server

ARG NGINX_VERSION

WORKDIR /app

# nginx configuration
COPY scripts/configs/nginx.conf /etc/nginx/nginx.conf

# actual front end
COPY --from=frontend-builder /app/dist /app

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]