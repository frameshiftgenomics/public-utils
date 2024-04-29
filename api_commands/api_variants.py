#!/usr/bin/python

from __future__ import print_function
import json

# This contains API routes for variant (mirrors the API docs)

######
###### GET routes
######

######
###### POST routes
######

# Upload variants via a file, but do not create a variant set
def postUploadVariants(mosaicConfig, filename, fileType, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: multipart/form-data" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-F "file=@' + str(filename) + '" -F "type=' + str(fileType) + '" -F "create_variant_set=false' + '" '
  command += '-F "disable_successful_notification=true" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/variants/upload' + '"'

  return command

# Upload variants via a file and create a variant set
def postUploadVariantsWithSet(mosaicConfig, filename, fileType, name, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: multipart/form-data" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-F "file=@' + str(filename) + '" -F "type=' + str(fileType) + '" -F "create_variant_set=true" -F "name=' + str(name) + '" '
  command += '-F "disable_successful_notification=true" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/variants/upload' + '"'

  return command

######
###### PUT routes
######

######
###### DELETE routes
######

