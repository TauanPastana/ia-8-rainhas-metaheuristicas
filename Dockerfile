FROM docker.n8n.io/n8nio/n8n:latest

USER root

COPY --from=alpine:3.22 /sbin/apk /sbin/apk
COPY --from=alpine:3.22 /lib/apk /lib/apk
COPY --from=alpine:3.22 /etc/apk /etc/apk

RUN apk add --no-cache python3 py3-pip

USER node