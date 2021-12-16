#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
CHART_ID=$4

BODY="{\"type\": \"chart\", \"chart_id\": \"$CHART_ID\", \"is_active\": \"true\"}"

curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
-d "$BODY" \
$URL"/v1/projects/$PROJECT_ID/dashboard"
