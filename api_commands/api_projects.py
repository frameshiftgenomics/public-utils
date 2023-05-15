import math
import os
import json

# The first section of this file contains routines to execute the API routes and acts as a layer between the
# calling script and the Pythonized API routes. This will check for errors, deal with looping over pages of 
# results etc and return data objects. The API routes themselves occur later in this file

######
###### Execute GET routes
######

# Get
def getProjectsDictNameId(config):
  limit = 100
  page  = 1
  projects = {}

  # Execute the GET route
  try: data = json.loads(os.popen(getProjectsCommand(config, limit, page)).read())
  except: fail('Failed to get projects')
  if 'message' in data: fail('Failed to get projects for collection: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Store the project ids, indexed by the name
  for project in data['data']: projects[project['name']] = project['id']

  # Determine how many annotations there are and consequently how many pages of annotations
  noPages = math.ceil(int(data['count']) / int(limit))

  # Loop over remainig pages of annotations
  for page in range(2, noPages + 1):
    try: data = json.loads(os.popen(getProjectsCommand(config, limit, page)).read())
    except: fail('Unable to get projects')
    if 'message' in data: fail('Unable to get projects. API returned the message: ' + str(data['messgage']))

    # Store the project ids, indexed by the name
    for project in data['data']: projects[project['name']] = project['id']

  # Return the data
  return projects

# Get the ids of all projects in a collection
def getCollectionProjects(config, projectId):
  ids = []

  # Execute the GET route
  try: data = json.loads(os.popen(getCollectionProjectsCommand(config, projectId)).read())
  except: fail('Failed to get projects for collection: ' + str(projectId))
  if 'message' in data: fail('Failed to get projects for collection: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for project in data: ids.append(project['id'])

  # Return the projectIds
  return ids

# Get the ids of all projects in a collection
def getCollectionProjectsDictIdName(config, projectId):
  ids = {}

  # Execute the GET route
  try: data = json.loads(os.popen(getCollectionProjectsCommand(config, projectId)).read())
  except: fail('Failed to get projects for collection: ' + str(projectId))
  if 'message' in data: fail('Failed to get projects for collection: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for project in data: ids[project['id']] = project['name']

  # Return the projectIds
  return ids

######
###### Execute POST routes
######

# Create a new project
def createProject(config, name, reference):
  try: data = json.loads(os.popen(postProjectCommand(config, name, reference)).read())
  except: fail('Failed to create project with name: ' + str(name))
  if 'message' in data: fail('Failed to create projects with name: ' + str(name) + '. API returned the message: ' + str(data['message']))

  # Return the projectIds
  return data['id']

######
###### Execute DELETE routes
######

# Delete a  project
def deleteProject(config, projectId):
  try: data = os.popen(deleteProjectCommand(config, projectId)).read()
  except: fail('Failed to delete project with id: ' + str(projectId))
  if 'message' in data: fail('Failed to delete project with id: ' + str(projectId) + '. API returned the message: ' + str(json.loads(data)['message']))

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

# Delete a project
def deleteProjectCommand(mosaicConfig, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X DELETE -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '"'

  return command

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)
