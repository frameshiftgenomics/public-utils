#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3

curl -S -s -X GET -H "Authorization: Bearer $TOKEN" \
$URL"/v1/projects/$PROJECT_ID/charts"
