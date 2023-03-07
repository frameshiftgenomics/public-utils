FROM alpine:3.17.1

RUN apk add --no-cache curl python3

COPY . /public-utils
