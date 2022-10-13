#!/usr/bin/python

# This contains API routes for samples (mirrors the API docs)

######
###### GET routes
######

# Get all files associated with a sample in a project
def getSampleFiles(mosaicConfig, projectId, sampleId, limit, page):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/' + str(sampleId) + '/files?limit=' + str(limit) + '&page=' + str(page) + '"'

  return command

# Get all sample files in a project
def getAllSampleFiles(mosaicConfig, projectId, limit, page):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/files?limit=' + str(limit) + '&page=' + str(page) + '"'

  return command

######
###### POST routes
######

# Add a file attached to a specific sample
def postSampleFile(mosaicConfig, name, nickname, fileType, fileUri, reference, sampleName, projectId, sampleId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

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
def putUpdateSampleFileName(mosaicConfig, name, projectId, sampleId, fileId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"name": "' + str(name) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/' + str(sampleId) + '/files/' + str(fileId) + '"'

  return command

# Update a files nickname
def putUpdateSampleFileNickname(mosaicConfig, name, projectId, sampleId, fileId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"nickname": "' + str(name) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/' + str(sampleId) + '/files/' + str(fileId) + '"'

  return command

######
###### DELETE routes
######

# Delete a sample file
def deleteSampleFile(mosaicConfig, projectId, sampleId, fileId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X DELETE -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/samples/' + str(sampleId) + '/files/' + str(fileId) + '"'

  return command
