#!/bin/bash

TOKEN=$1
URL=$2
PAGE=$3

curl -S -s -X GET -H "Authorization: Bearer $TOKEN" \
$URL"/v1/projects/attributes?limit=2&page=$PAGE"
