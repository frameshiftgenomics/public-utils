FROM ubuntu:22.04

RUN apt-get update && apt-get install -y python3.6 curl

COPY . /public-utils
