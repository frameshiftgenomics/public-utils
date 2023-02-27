import os
import json

# The first section of this file contains routines to execute the API routes and acts as a layer between the
# calling script and the Pythonized API routes. This will check for errors, deal with looping over pages of 
# results etc and return data objects. The API routes themselves occur later in this file

######
###### Execute GET routes
######

# 
def getCollectionProjects(config, projectId):
  ids = []

  # Execute the GET route
  try: data = json.loads(os.popen(getCollectionProjectsCommand(config, projectId)).read())
  except: fail('Failed to get projects for collection: ' + str(projectId))
  if 'message' in data: fail('Failed to get projects for collection: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for projectId in data: ids.append(projectId)

  # Return the projectIds
  return ids

#################
#################
################# Following are the API routes for variant filters (mirrors the API docs)
#################
#################

# This contains API routes for project attributes (mirrors the API docs)

######
###### GET routes
######

# Get information about a project
def getProjectCommand(mosaicConfig, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '"'

  return command

# Get a list of projects the user has access to
def getProjectsCommand(mosaicConfig, limit, page):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects?limit=' + str(limit) + '&page=' + str(page) + '"'

  return command

# Get all projects in a collection
def getCollectionProjectsCommand(mosaicConfig, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/sub-projects' + '"'

  return command

######
###### POST routes
######

# Create a project
def postProjectCommand(mosaicConfig, name, reference):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"name": "' + str(name) + '", "reference": "' + str(reference) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects' + '"'

  return command

######
###### PUT routes
######

######
###### DELETE routes
######

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)
