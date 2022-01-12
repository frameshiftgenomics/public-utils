#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
CHART_ID=$4

curl -X DELETE -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
$URL"/v1/projects/$PROJECT_ID/charts/$CHART_ID"
