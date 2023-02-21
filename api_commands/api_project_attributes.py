#!/usr/bin/python

import os
import json
import math

# The first section of this file contains routines to execute the API routes and acts as a layer between the
# calling script and the Pythonized API routes. This will check for errors, deal with looping over pages of 
# results etc and return data objects. The API routes themselves occur later in this file

######
###### Execute the GET routes
######

# Return all project attribute information for a project
def getProjectAttributes(config, projectId):
  try: data = json.loads(os.popen(getProjectAttributesCommand(config, projectId)).read())
  except: fail('Failed to GET project attributes for project: ' + str(projectId))
  if 'message' in data: fail('Failed to GET project attributes for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Return all the data
  return data

# Return a dictionary of project attributes for a project with the name as key, and id, and uid as values
def getProjectAttributesNameIdUid(config, projectId):
  atts = {}

  # Get the data
  try: data = json.loads(os.popen(getProjectAttributesCommand(config, projectId)).read())
  except: fail('Failed to GET project attributes for project: ' + str(projectId))
  if 'message' in data: fail('Failed to GET project attributes for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))
  for att in data: atts[att['name']] = {'id': att['id'], 'uid': att['uid']}

  # Return all the data
  return atts

# Loop over all pages of public attributes and return all information
def getPublicProjectAttributesNameIdUid(mosaicConfig):
  limit = 100
  page  = 1
  pAtts = []

  # Get the first page of attributes
  try: data = json.loads(os.popen(getPublicProjectAttributesCommand(mosaicConfig, limit, page)).read())
  except: fail('Failed to GET public project attributes')
  if 'message' in data: fail('Failed to GET public project attributes')

  # Store the required data
  for record in data['data']: pAtts.append({'name': record['name'], 'id': record['id'], 'uid': record['uid']})

  # Calculate the number of pages
  noPages = math.ceil(int(data['count']) / int(limit))

  # Loop over all pages of public attributes and store information to return
  for page in range(2, noPages + 1):
    try: data = json.loads(os.popen(getPublicProjectAttributesCommand(mosaicConfig, limit, page)).read())
    except: fail('Failed to GET public project attributes')
    if 'message' in data: fail('Failed to GET public project attributes')
    for record in data['data']: pAtts.append({'name': record['name'], 'id': record['id'], 'uid': record['uid']})

  # Return the data
  return pAtts

######
###### Execute POST routes
######

# Import a project attribute
def importProjectAttribute(config, projectId, attId, value):
  try: data = json.loads(os.popen(postImportProjectAttributeCommand(config, attId, value, projectId)).read())
  except: fail('Failed to import a project attributes for project ' + str(projectId))
  if 'message' in data: fail('Failed to import a project attributes for project ' + str(projectId) + '. API returned the message: ' + str(data['message']))

######
###### Execute the PUT routes
######

# Update a project attribute
def updateProjectAttribute(config, projectId, attId, value):
  try: data = json.loads(os.popen(putProjectAttributeCommand(config, value, projectId, attId)).read())
  except: fail('Failed to update a project attributes for project ' + str(projectId))
  if 'message' in data: fail('Failed to update a project attributes for project ' + str(projectId) + '. API returned the message: ' + str(data['message']))

#################
#################
################# Following are the API routes for variant filters (mirrors the API docs)
#################
#################

# This contains API routes for project attributes (mirrors the API docs)

######
###### GET routes
######

# Get the project attributes for the defined project
def getProjectAttributesCommand(mosaicConfig, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" ' 
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/attributes' + '"'

  return command

# Get all public project attributes
def getPublicProjectAttributesCommand(mosaicConfig, limit, page):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/attributes?limit=' + str(limit) + '&page=' + str(page) + '"'

  return command

# Get the project attributes for the all projects the user has access to
def getUserProjectAttributesCommand(mosaicConfig):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" ' 
  command += '"' + str(url) + 'api/v1/user/projects/attributes' + '"'

  return command

######
###### POST routes
######

# Create a new project attribute
def postProjectAttributeCommand(mosaicConfig, name, valueType, value, isPublic, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"name": "' + str(name) + '", "value_type": "' + str(valueType) + '", "value": "' + str(value) + '", "is_public": "' + str(isPublic) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/attributes' + '"'

  return command

# Import a project attribute
def postImportProjectAttributeCommand(mosaicConfig, attributeId, value, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"attribute_id": "' + str(attributeId) + '", "value": '

  # If the value is null, it should not be enclosed in quotation marks
  if str(value) == 'null': command += 'null}\' '
  else: command += '"' + str(value) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/attributes/import' + '"'

  return command

######
###### PUT routes
######

# Update the value of a project attribute
def putProjectAttributeCommand(mosaicConfig, value, projectId, attributeId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"value": "' + str(value) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/attributes/' + str(attributeId) + '"'

  return command

######
###### DELETE routes
######

# Delete a project attribute
def deleteProjectAttributeCommand(mosaicConfig, projectId, attributeId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X DELETE -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/attributes/' + str(attributeId) + '"'

  return command

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)
