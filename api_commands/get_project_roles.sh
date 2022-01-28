#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
LIMIT=$4
PAGE=$5

curl -X GET -H "Authorization: Bearer $TOKEN" \
$URL"/v1/projects/$PROJECT_ID/roles?limit=$LIMIT&page=$PAGE"
