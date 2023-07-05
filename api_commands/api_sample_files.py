#!/usr/bin/python

from __future__ import print_function
import os
import json
import math

# The first section of this file contains routines to execute the API routes and acts as a layer between the
# calling script and the Pythonized API routes. This will check for errors, deal with looping over pages of 
# results etc and return data objects. The API routes themselves occur later in this file

######
###### Execute GET routes
######

# Get all vcf files for a specified sample
def getSampleVcfs(config, projectId, sampleId):
  limit = 100
  page  = 1
  ids   = {}

  # Execute the command
  try: data = json.loads(os.popen(getSampleFilesCommand(config, projectId, sampleId, limit, page)).read())
  except: fail('Failed to get sample files for project: ' + str(projectId))
  if 'message' in data: fail('Failed to get sample files for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for sFile in data['data']:
    if str(sFile['type']) == 'vcf': ids[sFile['id']] = {'name': sFile['name'], 'uri': sFile['uri'], 'vcf_sample_name': sFile['vcf_sample_name']}

  # Determine the number of pages
  noPages = int( math.ceil( float(data['count']) / float(limit) ) )

  # Loop over all necessary pages
  for page in range(1, noPages):
    for sFile in data['data']:
      if str(sFile['type']) == 'vcf': ids[sFile['id']] = {'name': sFile['name'], 'uri': sFile['uri']}

  # Return the sample files
  return ids

# Get all sample files of a specified type
def getSampleFiles(config, projectId, sampleId, fileType):
  limit = 100
  page  = 1
  ids   = {}

  # Execute the command
  try: data = json.loads(os.popen(getSampleFilesCommand(config, projectId, sampleId, limit, page)).read())
  except: fail('Failed to get sample files for project: ' + str(projectId))
  if 'message' in data: fail('Failed to get sample files for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for sFile in data['data']:
    if str(sFile['type']) == str(fileType): ids[sFile['id']] = {'name': sFile['name'], 'uri': sFile['uri']}

  # Determine the number of pages
  noPages = int( math.ceil( float(data['count']) / float(limit) ) )

  # Loop over all necessary pages
  for page in range(1, noPages):
    for sFile in data['data']:
      if str(sFile['type']) == str(fileType): ids[sFile['id']] = {'name': sFile['name'], 'uri': sFile['uri']}

  # Return the sample files
  return ids

######
###### Execute POST routes
######

# Attach a vcf file to a project
def attachVcfFile(config, name, nickname, uri, reference, sampleName, sampleId, projectId):
  try: data = json.loads(os.popen(postSampleFileCommand(config, name, nickname, 'vcf', uri, reference, sampleName, sampleId, projectId)).read())
  except: fail('Failed to attach vcf file to project: ' + str(projectId))
  if 'message' in data: fail('Failed to attach vcf file to project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

# Attach a tbi file to a project
def attachTbiFile(config, name, nickname, uri, reference, sampleName, sampleId, projectId):
  try: data = json.loads(os.popen(postSampleFileCommand(config, name, nickname, 'tbi', uri, reference, sampleName, sampleId, projectId)).read())
  except: fail('Failed to attach tbi file to project: ' + str(projectId))
  if 'message' in data: fail('Failed to attach tbi file to project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

# Attach a bam file to a project
def attachBamFile(config, name, nickname, uri, reference, sampleName, sampleId, projectId):
  try: data = json.loads(os.popen(postSampleFileCommand(config, name, nickname, 'bam', uri, reference, sampleName, sampleId, projectId)).read())
  except: fail('Failed to attach bam file to project: ' + str(projectId))
  if 'message' in data: fail('Failed to attach bam file to project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

# Attach a bai file to a project
def attachBaiFile(config, name, nickname, uri, reference, sampleName, sampleId, projectId):
  try: data = json.loads(os.popen(postSampleFileCommand(config, name, nickname, 'bai', uri, reference, sampleName, sampleId, projectId)).read())
  except: fail('Failed to attach bai file to project: ' + str(projectId))
  if 'message' in data: fail('Failed to attach bai file to project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

# Attach an alignstats.json file to a project
def attachAlignstatsFile(config, name, nickname, uri, reference, sampleName, sampleId, projectId):
  try: data = json.loads(os.popen(postSampleFileCommand(config, name, nickname, 'alignstats.json', uri, reference, sampleName, sampleId, projectId)).read())
  except: fail('Failed to attach alignstats json file to project: ' + str(projectId))
  if 'message' in data: fail('Failed to attach alignstats json file to project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

# Attach a peddy.html file to a project
def attachPeddyFile(config, name, nickname, uri, reference, sampleName, sampleId, projectId):
  try: data = json.loads(os.popen(postSampleFileCommand(config, name, nickname, 'peddy.html', uri, reference, sampleName, sampleId, projectId)).read())
  except: fail('Failed to attach alignstats json file to project: ' + str(projectId))
  if 'message' in data: fail('Failed to attach alignstats json file to project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

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
