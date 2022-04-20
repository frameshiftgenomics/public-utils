#!/bin/bash

TOKEN=$1
URL=$2
UNID=$3

curl -S -s -X GET -H "Authorization: Bearer $TOKEN" \
$URL"/v1/user/unid/$UNID"
