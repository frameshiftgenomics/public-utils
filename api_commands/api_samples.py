#!/usr/bin/python

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
  sampleIds = []

  # Execute the GET route
  try: data = json.loads(os.popen(getSamples(config, projectId)).read())
  except: fail('Failed to execute the GET samples route for project: ' + str(projectId))
  if 'message' in data: fail('Failed to execute the GET samples route for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for sample in data: sampleIds.append(sample['id'])

  # Return the list of variant filter ids
  return sampleIds

######
###### Execute the DELETE routes
######

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
def getSamples(mosaicConfig, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples' + '"'

  return command

######
###### POST routes
######

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
