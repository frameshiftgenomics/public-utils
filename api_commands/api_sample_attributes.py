#!/usr/bin/python

# This contains API routes for sample attributes (mirrors the API docs)

######
###### GET routes
######

# Get sample attributes in a project
def getSampleAttributes(mosaicConfig, projectId, includeValues):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += str(url) + 'api/v1/projects/' + str(projectId) + '/samples/attributes'
  if includeValues: command += '?include_values=true'

  return command

# Get attributes for a sample in a project
def getAttributesForSample(mosaicConfig, projectId, sampleId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += str(url) + 'api/v1/projects/' + str(projectId) + '/samples/' + str(sampleId) + '/attributes'

  return command

######
###### POST routes
######

# Create a new sample attribute
def postSampleAttribute(mosaicConfig, name, valueType, value, isPublic, xLabel, yLabel, projectId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"name": "' + str(name) + '", "value_type": "' + str(valueType) + '", "value": "' + str(value) + '", "is_public": "'
  command += str(isPublic) + '", "x_label": "' + str(xLabel) + '", "y_label": "' + str(yLabel) + '"}\' '
  command += str(url) + 'api/v1/projects/' + str(projectId) + '/samples/attributes'

  return command

# Update the value for a sample attribute
def postUpdateSampleAttribute(mosaicConfig, value, projectId, sampleId, attributeId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"value": "' + str(value) + '"}\' '
  command += str(url) + 'api/v1/projects/' + str(projectId) + '/samples/' + str(sampleId) + '/attributes/' + str(attributeId)

  return command

# Import a sample attribute
def postImportSampleAttribute(mosaicConfig, attributeId, projectId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"attribute_id": "' + str(attributeId) + '"}\' '
  command += str(url) + 'api/v1/projects/' + str(projectId) + '/samples/attributes/import'

  return command

# Upload a sample attribute
def postUploadSampleAttribute(mosaicConfig, filename, projectId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -i -X POST -H "Content-Type: multipart/form-data" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-F "file=@' + str(filename) + '" -F "disable_queue=true" '
  command += str(url) + 'api/v1/projects/' + str(projectId) + '/samples/attributes/upload'

  return command

######
###### PUT routes
######

# Update a sample attribute
def putSampleAttribute(mosaicConfig, fields, projectId, attributeId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -i -X PUT -H "Content-Type: multipart/form-data" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{'
  for i, field in enumerate(fields):
    command += '"' + str(field) + '": "' + str(fields[field]) + '"'
    if int(i) + 1 != len(fields): command += ', '
  command += '}\' '
  command += str(url) + 'api/v1/projects/' + str(projectId) + '/samples/attributes/' + str(attributeId)

  return command

######
###### DELETE routes
######
