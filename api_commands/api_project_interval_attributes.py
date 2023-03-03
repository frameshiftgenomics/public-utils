#!/usr/bin/python

import json
import os
import math

# The first section of this file contains routines to execute the API routes and acts as a layer between the
# calling script and the Pythonized API routes. This will check for errors, deal with looping over pages of 
# results etc and return data objects. The API routes themselves occur later in this file

######
###### Execute GET routes
######

# Return a dictionary of intervals with the id as the key and the name as a value
def getIntervalsIdToName(config, projectId):
  ids = {}

  # Execute the GET route
  try: data = json.loads(os.popen(getProjectIntervalAttributesCommand(config, projectId)).read())
  except: fail('Failed to get intervals for project: ' + str(projectId))
  if 'message' in data: fail('Failed to get intervals for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for interval in data: ids[interval['id']] = {'name': interval['name']}

  # Return the dictionary of intervals
  return ids

def getIntervalsDictIdNamePrivacy(config, projectId):
  ids = []

  # Execute route
  try: data = json.loads(os.popen(getProjectIntervalAttributesCommand(config, projectId)).read())
  except: fail('Failed to get intervals for project: ' + str(projectId))
  if 'message' in data: fail('Failed to get intervals for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for interval in data:
    if interval['is_public']: ids.append({'id': interval['id'], 'name': interval['name'], 'privacy': 'public'})
    else: ids.append({'id': interval['id'], 'name': interval['name'], 'privacy': 'private'})

  # Return the dictionary of intervals
  return ids

######
###### Execute POST routes
######

# Import an interval attribute to the project
def postInterval(config, projectId, intervalId):
  try: data = json.loads(os.popen(postImportProjectIntervalAttributeCommand(config, projectId, intervalId)).read())
  except: fail('Failed to import interval into project: ' + str(projectId))
  if 'message' in data: fail('Failed to import interval into project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

#################
#################
################# Following are the API routes for variant filters (mirrors the API docs)
#################
#################

# This contains API routes for project interval attributes (mirrors the API docs)

######
###### GET routes
######

# Get the project interval attributes for the defined project
def getProjectIntervalAttributesCommand(mosaicConfig, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/attributes/intervals' + '"'

  return command

# Get all public project interval attributes
def getPublicProjectIntervalAttributesCommand(mosaicConfig, limit, page):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/attributes/intervals?limit=' + str(limit) + '&page=' + str(page) + '"'

  return command

######
###### POST routes
######

# Create a new project interval attribute
def postProjectIntervalAttributeCommand(mosaicConfig, name, isPublic, startAttribute, endAttribute, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"name": "' + str(name) + '", "is_public": "' + str(isPublic) + '", "start_attribute_id": "' + str(startAttribute) + '", "end_attribute_id": "' + str(endAttribute) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/attributes/intervals' + '"'

  return command

# Import a project interval attribute
def postImportProjectIntervalAttributeCommand(mosaicConfig, projectId, intervalId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"attribute_id": "' + str(intervalId) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/attributes/intervals/import' + '"'

  return command

######
###### PUT routes
######

######
###### DELETE routes
######

# Delete a project interval attribute
def deleteProjectIntervalAttributeCommand(mosaicConfig, intervalId, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X DELETE -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/attributes/intervals/' + str(intervalId) + '"'

  return command

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)
