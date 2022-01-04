#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
ATTRIBUTE_ID=$4
BACKGROUND_ID=$5
NAME=$6
COLOR=$7
COMPARE=$8
YLABEL=$9

BODY="{\"name\": \"$NAME\", \
	\"chart_type\": \"scatterplot\", \
	\"attribute_id\": $ATTRIBUTE_ID, \
	\"project_background_id\": $BACKGROUND_ID, \
	\"saved_chart_data\": \
		{\"x_axis\": \"attribute\", \
		\"y_label\": \"$YLABEL\", \
		\"color_by\": \"attribute\", \
		\"color_by_attribute_id\": $COLOR, \
		\"compare_to_attribute_id\": $COMPARE} \
	}"

curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
-d "$BODY" \
$URL"/v1/projects/$PROJECT_ID/charts"
