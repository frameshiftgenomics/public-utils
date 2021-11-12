#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
CONVERSATION_ID=$4

curl -X GET -H "Authorization: Bearer $TOKEN" \
$URL"/v1/projects/$PROJECT_ID/conversations/$CONVERSATION_ID"
