#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
CONVERSATION_ID=$4
USER_IDS=$5

curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
-d "{\"user_ids\": $USER_IDS}" \
$URL"/v1/projects/$PROJECT_ID/conversations/$CONVERSATION_ID/watchers"
