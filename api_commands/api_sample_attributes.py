#!/usr/bin/python

from __future__ import print_function
import os
import json
import math

# The first section of this file contains routines to execute the API routes and acts as a layer between the
# calling script and the Pythonized API routes. This will check for errors, deal with looping over pages of 
# results etc and return data objects. The API routes themselves occur later in this file

######
###### Execute GET routes
######

# Return all sample attribute information, excluding values, for a project
def getSampleAttributes(config, projectId):
  try: data = json.loads(os.popen(getSampleAttributesCommand(config, projectId, 'false')).read())
  except: fail('Failed to get sample attributes for project: ' + str(projectId))
  if 'message' in data: fail('Failed to get sample attributes for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Return all the data
  return data

# Return a dictionary with the sample attribute name as key and id as value
def getSampleAttributesDictNameId(config, projectId):
  atts = {}

  # Get the data
  try: data = json.loads(os.popen(getSampleAttributesCommand(config, projectId, 'false')).read())
  except: fail('Failed to get sample attributes for project: ' + str(projectId))
  if 'message' in data: fail('Failed to get sample attributes for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))
  for att in data: atts[att['name']] = att['id']

  # Return all the data
  return atts

# Return a dictionary with the sample attribute id as key and name as value
def getSampleAttributesDictIdName(config, projectId):
  atts = {}

  # Get the data
  try: data = json.loads(os.popen(getSampleAttributesCommand(config, projectId, 'false')).read())
  except: fail('Failed to get sample attributes for project: ' + str(projectId))
  if 'message' in data: fail('Failed to get sample attributes for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))
  for att in data: atts[att['id']] = att['name']

  # Return all the data
  return atts

# Return sample attribute names and ids
def getSampleAttributesNameId(config, projectId):
  atts = []

  # Get the data
  try: data = json.loads(os.popen(getSampleAttributesCommand(config, projectId, 'false')).read())
  except: fail('Failed to get sample attributes for project: ' + str(projectId))
  if 'message' in data: fail('Failed to get sample attributes for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))
  for att in data: atts.append({'name': att['name'], 'id': att['id']})

  # Return all the data
  return atts

# Return all sample attribute information, including values, for a project
def getSampleAttributesWValues(config, projectId):
  try: data = json.loads(os.popen(getSampleAttributesCommand(config, projectId, 'true')).read())
  except: fail('Failed to get sample attributes for project: ' + str(projectId))
  if 'message' in data: fail('Failed to get sample attributes for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Return all the data
  return data

######
###### Execute POST routes
######

# Create a new public sample attribute
def createPublicSampleAttribute(config, projectId, name, value, valueType, xLabel, yLabel):
  try: data = json.loads(os.popen(postSampleAttributeCommand(config, name, valueType, value, 'true', xLabel, yLabel, projectId)).read())
  except: fail('Failed to create public sample attribute for project: ' + str(projectId))
  if 'message' in data: fail('Failed to create public sample attribute for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

# Create a new private sample attribute
def createPrivateSampleAttribute(config, projectId, name, value, valueType, xLabel, yLabel):
  try: data = json.loads(os.popen(postSampleAttributeCommand(config, name, valueType, value, 'false', xLabel, yLabel, projectId)).read())
  except: fail('Failed to create private sample attribute for project: ' + str(projectId))
  if 'message' in data: fail('Failed to create private sample attribute for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

# Import a sample attribute
def importSampleAttribute(config, projectId, attId):
  try: data = json.loads(os.popen(postImportSampleAttributeCommand(config, attId, projectId)).read())
  except: fail('Failed to import sample attribute for project: ' + str(projectId))
  if 'message' in data: fail('Failed to import sample attribute for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

# Upload a tsv file of sample attributes
def uploadSampleAttributes(config, projectId, tsvFile):
  try: data = os.popen(postUploadSampleAttributesCommand(config, tsvFile, projectId))
  except: fail('Failed to upload tsv file of sample attributes for project: ' + str(projectId))
  if 'message' in data: fail('Failed to upload tsv file of sample attributes for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

#################
#################
################# Following are the API routes for variant filters (mirrors the API docs)
#################
#################

# This contains API routes for sample attributes (mirrors the API docs)

######
###### GET routes
######

# Get sample attributes in a project
def getSampleAttributesCommand(mosaicConfig, projectId, includeValues):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/attributes'
  if includeValues: command += '?include_values=true'
  command += '"'

  return command

# Get a specified list of sample attributes in a project
def getSpecifiedSampleAttributesCommand(mosaicConfig, projectId, includeValues, attributeIds):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" "'
  command += str(url) + 'api/v1/projects/' + str(projectId) + '/samples/attributes?'
  for i, attributeId in enumerate(attributeIds):
    if i == 0: command += 'attribute_ids[]=' + str(attributeId)
    else: command += '?attribute_ids[]=' + str(attributeId)
  if includeValues: command += '&include_values=true'
  command += '"'

  return command

# Get attributes for a sample in a project
def getAttributesForSampleCommand(mosaicConfig, projectId, sampleId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/' + str(sampleId) + '/attributes' + '"'

  return command

######
###### POST routes
######

# Create a new sample attribute
def postSampleAttributeCommand(mosaicConfig, name, valueType, value, isPublic, xLabel, yLabel, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"name": "' + str(name) + '", "value_type": "' + str(valueType) + '", "value": "' + str(value) + '", "is_public": "'
  command += str(isPublic) + '", "x_label": "' + str(xLabel) + '", "y_label": "' + str(yLabel) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/attributes' + '"'

  return command

# Update the value for a sample attribute
def postUpdateSampleAttributeCommand(mosaicConfig, value, projectId, sampleId, attributeId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"value": "' + str(value) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/' + str(sampleId) + '/attributes/' + str(attributeId) + '"'

  return command

# Import a sample attribute
def postImportSampleAttributeCommand(mosaicConfig, attributeId, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"attribute_id": "' + str(attributeId) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/attributes/import' + '"'

  return command

# Upload a sample attribute
def postUploadSampleAttributesCommand(mosaicConfig, filename, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: multipart/form-data" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-F "file=@' + str(filename) + '" -F "disable_queue=true" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/attributes/upload' + '"'

  return command

######
###### PUT routes
######

# Update a sample attribute value
def putSampleAttributeValueCommand(mosaicConfig, projectId, sampleId, attributeId, value):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"value": "' + str(value) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/' + str(sampleId) + '/attributes/' + str(attributeId) + '"'

  return command

# Update a sample attribute
def putSampleAttributeCommand(mosaicConfig, fields, projectId, attributeId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{'
  for i, field in enumerate(fields):
    command += '"' + str(field) + '": "' + str(fields[field]) + '"'
    if int(i) + 1 != len(fields): command += ', '
  command += '}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/attributes/' + str(attributeId) + '"'

  return command

######
###### DELETE routes
######

# Delete a sample attribute from a project
def deleteSampleAttributeCommand(mosaicConfig, projectId, attributeId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X DELETE -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/attributes/' + str(attributeId) + '"'

  return command

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)
