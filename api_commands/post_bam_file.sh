#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
SAMPLE_ID=$4
FILE=$5
NAME=$6
REF=$7

curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
-d "{\"type\": \"bam\", \
	\"name\": \"$NAME\",
	\"reference\": \"$REF\", \
	\"uri\": \"$FILE\"}" \
$URL"/v1/projects/$PROJECT_ID/samples/$SAMPLE_ID/files"
