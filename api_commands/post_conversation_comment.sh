#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
COMMENT=$4
CONVERSATION_ID=$5

curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
-d "{\"text\": \"$COMMENT\", \"type\": \"project_conversation\", \"id\": \"$CONVERSATION_ID\"}" \
$URL"/i/projects/$PROJECT_ID/comments"
