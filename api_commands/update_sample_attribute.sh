#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
SAMPLE_ID=$4
ATTRIBUTE_ID=$5
ATTRIBUTE_VALUE=$6

curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
-d "{\"value\": \"$ATTRIBUTE_VALUE\"}" \
$URL"v1/projects/$PROJECT_ID/samples/$SAMPLE_ID/attributes/$ATTRIBUTE_ID"
