#!/bin/bash

TOKEN=$1
URL=$2
LIMIT=$3
PAGE=$4

curl -S -s -X GET -H "Authorization: Bearer $TOKEN" \
$URL"/v1/projects/attributes?limit=$LIMIT&page=$PAGE"
