#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
ATTRIBUTE_ID=$4
ATTRIBUTE_VALUE=$5

curl -s -S -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
-d "{\"attribute_id\": $ATTRIBUTE_ID, \
	\"value\": \"$ATTRIBUTE_VALUE\"}" \
$URL"v1/projects/$PROJECT_ID/attributes/import"
