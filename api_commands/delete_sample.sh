#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
SAMPLE_ID=$4

curl -X DELETE -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
$URL"/v1/projects/$PROJECT_ID/samples/$SAMPLE_ID"
