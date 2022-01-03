FROM node:12.22-alpine3.14

# for dev: 
#   from frontend root: docker build -f Dockerfile.dev -t nodedev .
#   from frontend root: docker run -v ~/repos/banking/frontend/src:/app/src -p 8080:8080 --rm -it nodedev
# définit le dossier 'app' comme dossier de travail
WORKDIR /app

RUN apk add --no-cache bash

COPY ./yarn.lock ./package.json /app/
  
# installe les dépendances du projet
RUN yarn install

ADD ./src /app/src
ADD ./public /app/public
ADD ./bin /app/bin 

ENTRYPOINT [ "yarn", "serve" ]