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

# Import a sample attribute
#def importSampleAttribute(config, projectId, attId):
#  try: data = json.loads(os.popen(postImportSampleAttributeCommand(config, attId, projectId)).read())
#  except: fail('Failed to import sample attribute for project: ' + str(projectId))
#  if 'message' in data: fail('Failed to import sample attribute for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

#################
#################
################# Following are the API routes for variant filters (mirrors the API docs)
#################
#################

# This contains API routes for attributes (mirrors the API docs)

######
###### GET routes
######

# Get all available attribute sets
def getProjectAttributeSetsCommand(mosaicConfig, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/attributes/sets' + '"'

  return command

######
###### POST routes
######

# Create an attribute set. ValueType should be one of "project", "sample", or "gene"
def postProjectAttributeSetCommand(mosaicConfig, name, description, isPublic, attributeIds, valueType, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"name": "' + str(name) + '", "description": "' + str(description) + '", "is_public_to_project": "' + str(isPublic)
  command += '", "attribute_ids": "' + str(attributeIds) + '", "type": "' + str(valueType) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/attributes/sets' + '"'

  return command

######
###### PUT routes
######

######
###### DELETE routes
######

# Delete an attribute set
def deleteProjectAttributeSetCommand(mosaicConfig, projectId, setId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X DELETE -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/attributes/sets/' + str(setId) + '"'

  return command

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)
