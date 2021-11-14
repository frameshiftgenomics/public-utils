#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
NAME=$4
DESCRIPTION=$5
PUBLIC=$6
ATTRIBUTE_IDS=$7
TYPE=$8

curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
-d "{\"name\": \"$NAME\", \
\"description\": \"$DESCRIPTION\", \
\"is_public_to_project\": \"$PUBLIC\", \
\"attribute_ids\": $ATTRIBUTE_IDS, \
\"type\": \"$TYPE\"}" \
$URL"/v1/projects/$PROJECT_ID/attributes/sets"
