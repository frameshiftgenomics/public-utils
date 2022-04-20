#!/bin/bash

TOKEN=$1
URL=$2

curl -s -S -X GET -H "Authorization: Bearer $TOKEN" \
$URL"/v1/user/projects/attributes"
