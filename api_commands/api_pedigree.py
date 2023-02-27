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

######
###### Execute POST routes
######

# 
def getPedigree(config, projectId, sampleId):
  samples = []

  # Get the pedigree information
  try: data = json.loads(os.popen(getPedigreeCommand(config, projectId, sampleId)).read())
  except: fail('Failed to get pedigree information for project: ' + str(projectId))
  if 'message' in data: fail('Failed to get pedigree information for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))
  for sample in data: samples.append({'id': sample['id'], 'name': sample['name'], 'pedigree': sample['pedigree']})
  
  # Return the pedigree information
  return samples

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
def getPedigreeCommand(mosaicConfig, projectId, sampleId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/' + str(sampleId) + '/pedigree"'

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
