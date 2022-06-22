#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
FILTER_ID=$4

curl -S -s -X DELETE -H -H "Authorization: Bearer $TOKEN" \
$URL"/v1/projects/$PROJECT_ID/variants/filters/$FILTER_ID"


curl -X DELETE -H "Authorization: Bearer ca41d8f4d3c26717a351e0fa0ea53130839d1fb0" https://mosaic.chpc.utah.edu/api/v1/projects/938/variants/filters/4

