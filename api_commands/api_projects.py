#!/usr/bin/python

# This contains API routes for project attributes (mirrors the API docs)

######
###### GET routes
######

# Get information about a project
def getProject(mosaicConfig, projectId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += str(url) + 'api/v1/projects/' + str(projectId)

  return command

# Get a list of projects the user has access to
def getProjects(mosaicConfig):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += str(url) + 'api/v1/projects'

  return command

# Get all projects in a collection
def getCollectionProjects(mosaicConfig, projectId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += str(url) + 'api/v1/projects/' + str(projectId) + '/sub-projects'

  return command

######
###### POST routes
######

# Create a project
def postProject(mosaicConfig, name, reference):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"name": "' + str(name) + '", "reference": "' + str(reference) + '"}\' ' + str(url) + 'api/v1/projects'

  return command

######
###### PUT routes
######

######
###### DELETE routes
######

