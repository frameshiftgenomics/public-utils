#!/bin/bash

TOKEN=$1
URL=$2
PROJECT_ID=$3
SAMPLE_ID=$4
URI=$5
NAME=$6
REF=$7
VCF_SAMPLE_NAME=$8

curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
-d "{\"type\": \"vcf\", \
	\"vcf_sample_name\": \"$VCF_SAMPLE_NAME\", \
	\"name\": \"$NAME\",
	\"reference\": \"$REF\", \
	\"uri\": \"$URI\"}" \
$URL"/v1/projects/$PROJECT_ID/samples/$SAMPLE_ID/files"
