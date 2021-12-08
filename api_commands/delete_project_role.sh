#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
ROLE_ID=$4

curl -X DELETE -H "Authorization: Bearer $TOKEN" \
$URL"/v1/projects/$PROJECT_ID/roles/$ROLE_ID"
