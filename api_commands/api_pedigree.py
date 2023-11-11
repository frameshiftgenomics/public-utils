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

# Get the samples in the pedigree
def getPedigree(config, projectId, sampleId):
  samples = []

  # Get the pedigree information
  try: data = json.loads(os.popen(getPedigreeCommand(config, projectId, sampleId)).read())
  except: fail('Failed to get pedigree information for project: ' + str(projectId))
  if 'message' in data: fail('Failed to get pedigree information for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))
  for sample in data: samples.append({'id': sample['id'], 'name': sample['name'], 'pedigree': sample['pedigree']})
  
  # Return the pedigree information
  return samples

# Get the pedigree information based on a sample id and then populate a list with the lines of a ped file
def getPedLines(config, projectId, sampleId):
  pedLines = []
  pedLines.append('#Family_id\tindividual_id\tpaternal_id\tmaternal_id\tsex\taffected_status')

  # Get the pedigree information
  try: data = json.loads(os.popen(getPedigreeCommand(config, projectId, sampleId)).read())
  except: fail('Failed to get pedigree information for project: ' + str(projectId))
  if 'message' in data: fail('Failed to get pedigree information for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Get the sample names and ids
  samples = {}
  for sample in data: samples[sample['id']] = sample['name']
  for sample in data:
    pedigreeInfo = sample['pedigree']
    paternalName = samples[pedigreeInfo['paternal_id']] if pedigreeInfo['paternal_id'] else 0
    maternalName = samples[pedigreeInfo['maternal_id']] if pedigreeInfo['maternal_id'] else 0
    line         = str(pedigreeInfo['kindred_id']) + '\t' + str(sample['name']) +'\t' + str(paternalName) + '\t' + str(maternalName) + '\t' + str(pedigreeInfo['sex']) + '\t' + str(pedigreeInfo['affection_status'])
    pedLines.append(line)
  
  # Return the pedigree information
  return pedLines

######
###### Execute POST routes
######

# Create pedigree information about a sample
def addSampleToPedigree(mosaicConfig, projectId, sampleId, kindred, affected, maternalId, paternalId, sex):
  try: data = json.loads(os.popen(postPedigreeCommand(mosaicConfig, projectId, sampleId, kindred, affected, maternalId, paternalId, sex)).read())
  except: fail('Failed to add pedigree information for sample: ' + str(sampleId))
  if 'message' in data: fail('Failed to add pedigree information for sample: ' + str(sampleId) + '. API returned the message: ' + str(data['message']))

# Create pedigree information about a sample
def uploadPedigree(mosaicConfig, projectId, filename):
  try: data = json.loads(os.popen(postUploadPedigreeCommand(mosaicConfig, projectId, filename)).read())
  except: fail('Failed to upload pedigree information for project: ' + str(projectId))
  if 'message' in data: fail('Failed to upload pedigree to project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

# Create pedigree information about a sample
def addSampleToPedigree(mosaicConfig, projectId, sampleId, kindred, affected, maternalId, paternalId, sex):
  try: data = json.loads(os.popen(postPedigreeCommand(mosaicConfig, projectId, sampleId, kindred, affected, maternalId, paternalId, sex)).read())
  except: fail('Failed to add pedigree information for sample: ' + str(sampleId))
  if 'message' in data: fail('Failed to add pedigree information for sample: ' + str(sampleId) + '. API returned the message: ' + str(data['message']))

######
###### Execute PUT routes
######

# Update pedigree information about a sample
def updateSamplePedigree(mosaicConfig, projectId, sampleId, kindred, affected, maternalId, paternalId, sex):
  print(putPedigreeCommand(mosaicConfig, projectId, sampleId, kindred, affected, maternalId, paternalId, sex))
  try: data = json.loads(os.popen(putPedigreeCommand(mosaicConfig, projectId, sampleId, kindred, affected, maternalId, paternalId, sex)).read())
  except: fail('Failed to add pedigree information for sample: ' + str(sampleId))
  if 'message' in data: fail('Failed to add pedigree information for sample: ' + str(sampleId) + '. API returned the message: ' + str(data['message']))

# Update the kindred id associated with a pedigree
def updateKindredId(mosaicConfig, projectId, sampleId, kindredId):
  try: data = json.loads(os.popen(putPedigreeKindredCommand(mosaicConfig, projectId, sampleId, kindredId)).read())
  except: fail('Failed to update kindred id for pedigree in project: ' + str(projectId))
  if 'message' in data: fail('Failed to update kindred id for pedigree in project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

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
###### PUT routes
######

# Update pedigree information for a sample
def putPedigreeCommand(mosaicConfig, projectId, sampleId, kindred, affected, maternalId, paternalId, sex):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"kindred_id": "' + str(kindred) + '", "affection_status": ' + str(affected) + ', "maternal_id": "'
  command += str(maternalId) + '", "paternal_id": "' + str(paternalId) + '", "sex": ' + str(sex) + '}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/' + str(sampleId) + '/pedigree"'

  return command

######
###### POST routes
######

# Generate and add pedigree information to a project for a sample
def postPedigreeCommand(mosaicConfig, projectId, sampleId, kindred, affected, maternalId, paternalId, sex):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"kindred_id": "' + str(kindred) + '", "affection_status": ' + str(affected) + ', "maternal_id": "'
  command += str(maternalId) + '", "paternal_id": "' + str(paternalId) + '", "sex": ' + str(sex) + '}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/' + str(sampleId) + '/pedigree"'

  return command

# Generate and add pedigree information to a project for a sample
def postUploadPedigreeCommand(mosaicConfig, projectId, filename):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: multipart/form-data" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-F "file=@' + str(filename) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/pedigree"'

  return command

######
###### PUT routes
######

# Generate and add pedigree information to a project for a sample
def putPedigreeKindredCommand(mosaicConfig, projectId, sampleId, kindredId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"kindred_id": "' + str(kindredId) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/' + str(sampleId) + '/pedigree"'

  return command

######
###### DELETE routes
######

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)
