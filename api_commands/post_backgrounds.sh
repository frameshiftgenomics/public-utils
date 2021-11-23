#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
NAME=$4
FILE=$5

BODY="{\"name\": \"$NAME\", \"payload\": `cat $FILE`}"

curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
-d "$BODY" \
$URL"/v1/projects/$PROJECT_ID/backgrounds"
