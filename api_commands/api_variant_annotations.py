#!/usr/bin/python

import json
import os

# The first section of this file contains routines to execute the API routes and acts as a layer between the
# calling script and the Pythonized API routes. This will check for errors, deal with looping over pages of 
# results etc and return data objects. The API routes themselves occur later in this file

######
###### Execute the GET routes
######

# Return a list of annotation ids
def getAnnotationIds(config, projectId):
  ids = []

  # Execute the GET route
  try: data = json.loads(os.popen(getVariantAnnotations(config, projectId)).read())
  except: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId))
  if 'message' in data: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for annotation in data: ids.append(annotation['id'])

  # Return the list of annotation ids
  return ids

# Return a dictionary with annotation ids as keys and annotation names as values
def getAnnotationIdsWithNames(config, projectId):
  ids = []

  # Execute the GET route
  try: data = json.loads(os.popen(getVariantAnnotations(config, projectId)).read())
  except: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId))
  if 'message' in data: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for annotation in data: ids[annotation['id']] = annotation['name']

  # Return the dictionary
  return ids

# Return a list of all annotation uids
def getAnnotationUids(config, projectId):
  uids = []

  # Execute the GET route
  try: data = json.loads(os.popen(getVariantAnnotations(config, projectId)).read())
  except: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId))
  if 'message' in data: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for annotation in data: uids.append(annotation['uid'])

  # Return the list of variant filter ids
  return uids

# Return a dictionary of uids with the corresponding value type
def getAnnotationUidsWithTypes(config, projectId):
  uids = {}

  # Execute the GET route
  try: data = json.loads(os.popen(getVariantAnnotations(config, projectId)).read())
  except: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId))
  if 'message' in data: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for annotation in data: uids[annotation['uid']] = annotation['value_type']

  # Return the list of variant filter ids
  return uids

######
###### Execute the DELETE routes
######

#################
#################
################# Following are the API routes for variant filters (mirrors the API docs)
#################
#################

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
