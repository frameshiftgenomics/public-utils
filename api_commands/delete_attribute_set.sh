#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
SET_ID=$4

curl -S -s -X DELETE -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
$URL"/v1/projects/$PROJECT_ID/attributes/sets/$SET_ID"
