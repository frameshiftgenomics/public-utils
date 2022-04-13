#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
SAMPLE_ID=$4
FILE_ID=$5

curl -X DELETE -H "Authorization: Bearer $TOKEN" \
$URL"/v1/projects/$PROJECT_ID/samples/$SAMPLE_ID/files/$FILE_ID"
