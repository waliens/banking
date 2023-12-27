ARG NODE_VERSION=14.16.1-alpine3.13
ARG NGINX_VERSION=1.22.1

#######################################################################################
## Stage: build front-end
FROM node:${NODE_VERSION} as frontend-builder

WORKDIR /app
RUN apk add --no-cache bash
COPY ./yarn.lock ./package.json /app/
  
RUN yarn install

ADD ./src /app/src
ADD ./public /app/public
ADD ./bin /app/bin 

RUN VUE_APP_MODE=production yarn build 

#######################################################################################
## Stage: dev image (with hot swap)
FROM node:${NODE_VERSION} as dev-server

WORKDIR /app

# ui source code should be mounted in /app
RUN apk update && apk add --no-cache gettext bash

RUN mkdir /docker-entrypoint-banking.d/
COPY --chmod=774 ./scripts/banking-entrypoint.sh /usr/local/bin/
COPY --chmod=774 ./scripts/envsubst-on-templates-and-move.sh /docker-entrypoint-banking.d/500-envsubst-on-templates-and-move.sh
COPY --chmod=774 ./scripts/run-yarn-install.sh /docker-entrypoint-banking.d/750-run-yarn-install.sh
COPY ./scripts/samples/configuration.json.sample /samples/app/public/

ENTRYPOINT ["banking-entrypoint.sh", "docker-entrypoint.sh"]

# rebuild (ignoring current node-module folder) then serve
CMD ["yarn", "serve"]

#######################################################################################
## Stage: building nginx image serving the front-end
FROM nginx:${NGINX_VERSION}-alpine as prod-server

ARG NGINX_VERSION

WORKDIR /app

# copying entrypoint scripts
RUN mkdir /docker-entrypoint-banking.d/
COPY --chmod=774 ./scripts/banking-entrypoint.sh /usr/local/bin/
COPY --chmod=774 ./scripts/envsubst-on-templates-and-move.sh /docker-entrypoint-banking.d/500-envsubst-on-templates-and-move.sh
COPY ./scripts/samples/configuration.json.sample /samples/app/

# nginx configuration
COPY scripts/configs/nginx.conf /etc/nginx/nginx.conf

# actual front end
COPY --from=frontend-builder /app/dist /app

ENTRYPOINT ["banking-entrypoint.sh", "/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]