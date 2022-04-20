#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
COMMENT=$4
CONVERSATION_ID=$5

BODY="{\"text\": \"$COMMENT\", \
	\"type\": \"project_conversation\", \
	\"id\": $CONVERSATION_ID}"

curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
-d "$BODY" \
$URL"/v1/projects/$PROJECT_ID/comments"
