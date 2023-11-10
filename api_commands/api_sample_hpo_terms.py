#!/usr/bin/python

from __future__ import print_function
import os
import json

# The first section of this file contains routines to execute the API routes and acts as a layer between the
# calling script and the Pythonized API routes. This will check for errors, deal with looping over pages of 
# results etc and return data objects. The API routes themselves occur later in this file

######
###### Execute the GET routes
######

# Return a list of details of all HPO terms for a sample
def getSampleHpo(config, projectId, sampleId):
  hpos = []

  # Execute the GET route
  try: data = json.loads(os.popen(getSampleHpoTermsCommand(config, projectId, sampleId)).read())
  except: fail('Failed to get sample HPO terms for project: ' + str(projectId))
  if 'message' in data: fail('Failed to get sample HPO terms for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for hpo in data: hpos.append({'id': hpo['id'], 'hpoId': hpo['hpo_id'], 'label': hpo['label']})

  # Return the dictionary
  return hpos

# Return a list of HPO terms for a sample
def getSampleHpoList(config, projectId, sampleId):
  hpos = []

  # Execute the GET route
  try: data = json.loads(os.popen(getSampleHpoTermsCommand(config, projectId, sampleId)).read())
  except: fail('Failed to get sample HPO terms for project: ' + str(projectId))
  if 'message' in data: fail('Failed to get sample HPO terms for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for hpo in data: hpos.append(hpo['hpo_id'])

  # Return the dictionary
  return hpos

# Return a list of HPO terms for a project
def getProjectHpo(config, projectId):
  hpos = {}

  # Execute the GET route
  try: data = json.loads(os.popen(getProjectHpoTermsCommand(config, projectId)).read())
  except: fail('Failed to get HPO terms for project: ' + str(projectId))
  if 'message' in data: fail('Failed to get HPO terms for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for hpo in data:
    if hpo['sample_id'] not in hpos: hpos[hpo['sample_id']] = []
    hpos[hpo['sample_id']].append({'id': hpo['id'], 'hpoTermId': hpo['hpo_term_id'], 'label': hpo['label'], 'hpo_id': hpo['hpo_id']})

  # Return the dictionary
  return hpos

######
###### Execute the POST routes
######

# Post an HPO term to a sample
def addSampleHpo(config, projectId, sampleId, hpoTerm):
  try: data = json.loads(os.popen(postSampleHpoTermsCommand(config, projectId, sampleId, hpoTerm)).read())
  except: fail('Failed to add HPO term ' + str(hpoTerm) + ' to project: ' + str(projectId))
  if 'message' in data: fail('Failed to add HPO term to project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

#################
#################
################# Following are the API routes for HPO Terms (mirrors the API docs)
#################
#################

# This contains API routes for samples (mirrors the API docs)

######
###### GET routes
######

# Get the HPO terms associated with a sample
def getSampleHpoTermsCommand(mosaicConfig, projectId, sampleId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples' + '/' + str(sampleId) + '/hpo-terms"'

  return command

# Get the HPO terms associated with a project
def getProjectHpoTermsCommand(mosaicConfig, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples' + '/hpo-terms"'

  return command

######
###### POST routes
######

# Post an HPO term to a sample
def postSampleHpoTermsCommand(mosaicConfig, projectId, sampleId, hpo):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"hpo_id": "' + str(hpo) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/' + str(sampleId) + '/hpo-terms" '

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
