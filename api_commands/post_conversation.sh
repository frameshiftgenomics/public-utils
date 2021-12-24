#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
TITLE=$4
DESCRIPTION=$5

curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
-d "{\"title\": \"$TITLE\", \
	\"description\": \"$DESCRIPTION\"}" \
$URL"/v1/projects/$PROJECT_ID/conversations"
