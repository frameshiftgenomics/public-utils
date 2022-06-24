#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
FILTER_ID=$4

curl -S -s -X DELETE -H "Authorization: Bearer $TOKEN" \
$URL"/v1/projects/$PROJECT_ID/variants/filters/$FILTER_ID"
