ARG IMAGE_VERSION=1.25.4-alpine3.18-perl

FROM nginx:${IMAGE_VERSION}

COPY configuration/nginx.conf /etc/nginx/nginx.conf

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx"]