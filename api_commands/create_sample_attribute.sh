#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
NAME=$4
TYPE=$5
XLABEL=$6
YLABEL=$7
VALUE=$8
PUBLIC=$9

curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
-d "{\"name\": \"$NAME\", \
	\"value_type\": \"$TYPE\", \
	\"value\": \"$VALUE\", \
	\"is_public\": \"$PUBLIC\", \
	\"x_label\": \"$XLABEL\", \
	\"y_label\": \"$YLABEL\"}" \
$URL"/v1/projects/$PROJECT_ID/samples/attributes"
