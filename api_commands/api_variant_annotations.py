#!/usr/bin/python

# This contains API routes for variant annotations (mirrors the API docs)

######
###### GET routes
######

# Get the variant annotations for the project
def getVariantAnnotations(mosaicConfig, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" ' + str(url) + 'api/v1/projects/'
  command += '"' + str(projectId) + '/variants/annotations' + '"'

  return command

# Get variant annotations available to import
def getVariantAnnotationsImport(mosaicConfig, projectId, limit, page):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/variants/annotations/import?limit=' + str(limit) + '&page=' + str(page) + '"'

  return command

######
###### POST routes
######

# Create a variant annotation
def postCreateVariantAnnotations(mosaicConfig, name, valueType, privacy, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token)
  command += '" -d \'{"name": "' + str(name) + '", "value_type": "' + str(valueType) + '", "privacy_level": "' + str(privacy) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/variants/annotations' + '"'

  return command

# Create a variant annotation with the display type and severity set
def postCreateVariantAnnotationWithSeverity(mosaicConfig, name, valueType, privacy, fields, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token)
  command += '" -d \'{"name": "' + str(name) + '", "value_type": "' + str(valueType) + '", "privacy_level": "' + str(privacy) + '"'
  for field in fields: command += ', "' + str(field) + '": "' + str(fields[field]) + '"'
  command += '}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/variants/annotations' + '"'

  return command

# Import variant annotations to the project
def postImportVariantAnnotations(mosaicConfig, annotationId, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token)
  command += '" -d \'{"annotation_id": ' + str(annotationId) + '}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/variants/annotations/import' + '"'

  return command

# Upload variant annotations to the project
def postUploadVariantAnnotations(mosaicConfig, filename, allowDeletion, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: multipart/form-data" -H "Authorization: Bearer ' + str(token)
  command += '" -F "file=@' + str(filename) + '" -F "allow_deletion=' + str(allowDeletion) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/variants/annotations/upload' + '"'

  return command

######
###### PUT routes
######

# Update a variant annotation
def updateVariantAnnotation(mosaicConfig, projectId, fields, annotationId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token)
  command += '" -d \'{'
  for i, field in enumerate(fields):
    command += '"' + str(field) + '": "' + str(fields[field]) + '"'
    if int(i) + 1 != len(fields): command += ', '
  command += '}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/variants/annotations/' + str(annotationId) + '"'

  return command

######
###### DELETE routes
######

# Delete a variant annotation from a project
def deleteVariantAnnotation(mosaicConfig, projectId, annotationId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X DELETE -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/variants/annotations/' + str(annotationId) + '"'

  return command
