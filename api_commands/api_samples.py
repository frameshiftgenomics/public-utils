import os
import json

# The first section of this file contains routines to execute the API routes and acts as a layer between the
# calling script and the Pythonized API routes. This will check for errors, deal with looping over pages of 
# results etc and return data objects. The API routes themselves occur later in this file

######
###### Execute the GET routes
######

# Return a list of all sample ids for a project
def getSampleIds(config, projectId):
  sIds = []

  # Execute the GET route
  try: data = json.loads(os.popen(getSamplesCommand(config, projectId)).read())
  except: fail('Failed to execute the GET samples route for project: ' + str(projectId))
  if 'message' in data: fail('Failed to execute the GET samples route for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for sample in data: sIds.append(sample['id'])

  # Return the list of variant filter ids
  return sIds

# Return a dictionary with the sample ids as keys and the sample names as values
def getSamplesDictIdName(config, projectId):
  sIds = {}

  # Execute the GET route
  try: data = json.loads(os.popen(getSamplesCommand(config, projectId)).read())
  except: fail('Failed to GET the sample names and ids for project: ' + str(projectId))
  if 'message' in data: fail('Failed to GET the sample names and ids for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for sample in data: sIds[sample['id']] = sample['name']

  # Return the dictionary
  return sIds

# Return a dictionary with the sample names as keys and the sample ids as values
def getSampleNamesAndIds(config, projectId):
  sIds = {}

  # Execute the GET route
  try: data = json.loads(os.popen(getSamplesCommand(config, projectId)).read())
  except: fail('Failed to GET the sample names and ids for project: ' + str(projectId))
  if 'message' in data: fail('Failed to GET the sample names and ids for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for sample in data: sIds[sample['name']] = sample['id']

  # Return the dictionary
  return sIds

# Return a list of samples with their name and id
def getSampleNameId(config, projectId):
  sIds = []

  # Execute the GET route
  try: data = json.loads(os.popen(getSamplesCommand(config, projectId)).read())
  except: fail('Failed to GET the sample names and ids for project: ' + str(projectId))
  if 'message' in data: fail('Failed to GET the sample names and ids for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for sample in data: sIds.append({'name': str(sample['name']), 'id': sample['id']})

  # Return the dictionary
  return sIds

######
###### Execute POST routes
######

# Create a new sample in a project
def createSample(config, projectId, name):
  try: data = json.loads(os.popen(postSampleCommand(config, projectId, name)).read())
  except: fail('Failed to create a new sample in project: ' + str(projectId))
  if 'message' in data: fail('Failed to create a new sample in project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Return the sample id
  return data['id']

#################
#################
################# Following are the API routes for variant filters (mirrors the API docs)
#################
#################

# This contains API routes for samples (mirrors the API docs)

######
###### GET routes
######

# Get all samples in a project
def getSamplesCommand(mosaicConfig, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples' + '"'

  return command

######
###### POST routes
######

# Create a new sample in a project
def postSampleCommand(mosaicConfig, projectId, name):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"name": "' + str(name) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples' + '"'

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
