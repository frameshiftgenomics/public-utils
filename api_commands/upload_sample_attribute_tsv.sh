#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
FILENAME=$4

curl -i -X POST -H "Content-Type: multipart/form-data" -H "Authorization: Bearer $TOKEN" \
-F "file=@$FILENAME" \
-F "disable_queue=true" \
$URL"v1/projects/$PROJECT_ID/samples/attributes/upload"
