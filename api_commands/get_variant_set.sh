#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
VARIANT_SET_ID=$4

curl -S -s -X GET -H "Authorization: Bearer $TOKEN" \
$URL"/v1/projects/$PROJECT_ID/variants/sets/$VARIANT_SET_ID?include_variant_data=true&?include_genotype_data=true"
