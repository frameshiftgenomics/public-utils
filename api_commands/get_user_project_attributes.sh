#!/bin/bash

TOKEN=$1
URL=$2

curl -X GET -H "Authorization: Bearer $TOKEN" \
$URL"/v1/user/projects/attributes"
