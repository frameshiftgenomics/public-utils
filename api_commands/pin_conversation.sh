#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
CONVERSATION_ID=$4

curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
-d "{\"type\": \"conversation\", \
	\"project_conversation_id\": $CONVERSATION_ID, \
	\"is_active\": \"true\"}" \
$URL"/v1/projects/$PROJECT_ID/dashboard"
