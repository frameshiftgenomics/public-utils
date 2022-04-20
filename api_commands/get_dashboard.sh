#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3

curl -s -S -X GET -H "Authorization: Bearer $TOKEN" \
$URL"/v1/projects/$PROJECT_ID/dashboard"
