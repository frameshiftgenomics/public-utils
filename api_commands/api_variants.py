#!/usr/bin/python

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
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X POST -H "Content-Type: multipart/form-data" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-F "file=@' + str(filename) + '" -F "type=' + str(fileType) + '" -F "create_variant_set=false' + '" '
  command += str(url) + 'api/v1/projects/' + str(projectId) + '/variants/upload'

  return command

# Upload variants via a file and create a variant set
def postUploadVariantsWithSet(mosaicConfig, filename, fileType, name, projectId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X POST -H "Content-Type: multipart/form-data" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-F "file=@' + str(filename) + '" -F "type=' + str(fileType) + '" -F "create_variant_set=true" -F "name=' + str(name) + '" '
  command += str(url) + 'api/v1/projects/' + str(projectId) + '/variants/upload'

  return command

######
###### PUT routes
######

######
###### DELETE routes
######

