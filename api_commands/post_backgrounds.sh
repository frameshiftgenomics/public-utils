#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
FILE=$4

curl -S -s -X POST \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $TOKEN" \
-d "@$FILE" \
$URL"/v1/projects/$PROJECT_ID/backgrounds"
