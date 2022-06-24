#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3

BODY="{\"name\": \"Splice\", \"filter\": {\"annotation_filters\": [{\"uid\": \"gene_consequence_GRCh38\", \"values\": [\"splice_acceptor\", \"splice_donor\"], \"value_type\": \"string\", \"include_nulls\": false}]}}"

curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
-d "$BODY" \
$URL"/v1/projects/$PROJECT_ID/variants/filters"

