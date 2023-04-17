FROM ubuntu:22.04

RUN apt-get update && apt-get install -y python 3.7.3 curl

COPY . /public-utils
