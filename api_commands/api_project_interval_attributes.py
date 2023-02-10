#!/usr/bin/python

# This contains API routes for project interval attributes (mirrors the API docs)

######
###### GET routes
######

# Get the project interval attributes for the defined project
def getProjectIntervalAttributes(mosaicConfig, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/attributes/intervals' + '"'

  return command

# Get all public project interval attributes
def getPublicProjectIntervalAttributes(mosaicConfig, limit, page):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/attributes/intervals?limit=' + str(limit) + '&page=' + str(page) + '"'

  return command

######
###### POST routes
######

# Create a new project interval attribute
def postProjectIntervalAttribute(mosaicConfig, name, isPublic, startAttribute, endAttribute, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"name": "' + str(name) + '", "is_public": "' + str(isPublic) + '", "start_attribute_id": "' + str(startAttribute) + '", "end_attribute_id": "' + str(endAttribute) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/attributes/intervals' + '"'

  return command

# Import a project interval attribute
def postImportProjectIntervalAttribute(mosaicConfig, intervalId, projectId):
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
def deleteProjectIntervalAttribute(mosaicConfig, intervalId, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X DELETE -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/attributes/intervals/' + str(intervalId) + '"'

  return command
