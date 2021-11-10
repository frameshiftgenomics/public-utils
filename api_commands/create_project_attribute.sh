#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
NAME=$4
TYPE=$5
VALUE=$6
PUBLIC=$7

curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
-d "{\"name\": \"$NAME\", \"value_type\": \"$TYPE\", \"value\": \"$VALUE\", \"is_public\": \"$PUBLIC\"}" \
$URL"/v1/projects/$PROJECT_ID/attributes"
