#!/usr/bin/python

import os
import json

# The first section of this file contains routines to execute the API routes and acts as a layer between the
# calling script and the Pythonized API routes. This will check for errors, deal with looping over pages of 
# results etc and return data objects. The API routes themselves occur later in this file

######
###### Execute POST routes
######

# Attach a vcf file to a project
def attachVcfFile(config, name, nickname, uri, reference, sampleName, sampleId, projectId):

  # Execute the GET route
  try: data = json.loads(os.popen(postSampleFileCommand(config, name, nickname, 'vcf', uri, reference, sampleName, sampleId, projectId)).read())
  except: fail('Failed to attach vcf file to project: ' + str(projectId))
  if 'message' in data: fail('Failed to attach vcf file to project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

######
###### Execute DELETE routes
######

# Delete a file given a sample id and file id
def deleteFile(config, projectId, sampleId, fileId):
  try: data = os.popen(deleteSampleFileCommand(config, projectId, sampleId, fileId))
  except: fail('Failed to delete file from project: ' + str(projectId))
  if 'message' in data: fail('Failed to delete file from project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

#################
#################
################# Following are the API routes for variant filters (mirrors the API docs)
#################
#################

# This contains API routes for samples (mirrors the API docs)

######
###### GET routes
######

# Get all files associated with a sample in a project
def getSampleFilesCommand(mosaicConfig, projectId, sampleId, limit, page):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/' + str(sampleId) + '/files?limit=' + str(limit) + '&page=' + str(page) + '"'

  return command

# Get all sample files in a project
def getAllSampleFilesCommand(mosaicConfig, projectId, limit, page):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/files?limit=' + str(limit) + '&page=' + str(page) + '"'

  return command

# Get the url for a sample file
def getSampleFileUrlCommand(mosaicConfig, projectId, fileId, create):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/files/' + str(fileId) + '/url?create_activity=' + str(create) + '"'

  return command

######
###### POST routes
######

# Add a file attached to a specific sample
def postSampleFileCommand(mosaicConfig, name, nickname, fileType, fileUri, reference, sampleName, sampleId, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{'
  command += '"name": "' + str(name) + '"'
  if nickname: command += ', "nickname": "' + str(nickname) + '"'
  command += ', "type": "' + str(fileType) + '"'
  command += ', "uri": "' + str(fileUri) + '"'
  command += ', "reference": "' + str(reference) + '"'
  if (fileType == "vcf") or (fileType == "bcf"): command += ', "vcf_sample_name": "' + str(sampleName) + '"'
  command += '}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/' + str(sampleId) + '/files' + '"'

  return command

######
###### PUT routes
######

# Update a files name
def putUpdateSampleFileNameCommand(mosaicConfig, name, projectId, sampleId, fileId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"name": "' + str(name) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/' + str(sampleId) + '/files/' + str(fileId) + '"'

  return command

# Update a files nickname
def putUpdateSampleFileNicknameCommand(mosaicConfig, name, projectId, sampleId, fileId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"nickname": "' + str(name) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/' + str(sampleId) + '/files/' + str(fileId) + '"'

  return command

######
###### DELETE routes
######

# Delete a sample file
def deleteSampleFileCommand(mosaicConfig, projectId, sampleId, fileId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X DELETE -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/' + str(sampleId) + '/files/' + str(fileId) + '"'

  return command

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)
