#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
NAME=$4
TYPE=$5
PRIVACY=$6

curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
-d "{\"name\": \"$NAME\", \
	\"value_type\": \"$TYPE\", \
	\"privacy_level\": \"$PRIVACY\"}" \
$URL"/v1/projects/$PROJECT_ID/variants/annotations"
