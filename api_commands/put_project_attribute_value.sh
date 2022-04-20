#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
ATTRIBUTE_ID=$4
ATTRIBUTE_VALUE=$5

curl -s -S -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
-d "{\"value\": \"$ATTRIBUTE_VALUE\"}" \
$URL"v1/projects/$PROJECT_ID/attributes/$ATTRIBUTE_ID"
