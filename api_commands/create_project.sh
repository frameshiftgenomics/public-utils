#!/bin/bash

TOKEN=$1
URL=$2
NAME=$3
REFERENCE=$4

curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
-d "{\"name\": \"$NAME\", \"reference\": \"$REFERENCE\"}" \
$URL"/v1/projects"
