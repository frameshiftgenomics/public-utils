#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
SAMPLE_ID=$4
LIMIT=$5
PAGE=$6

curl -s -S -X GET -H "Authorization: Bearer $TOKEN" \
$URL"/v1/projects/$PROJECT_ID/samples/$SAMPLE_ID/files"
