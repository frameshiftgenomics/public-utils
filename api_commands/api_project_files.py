#!/usr/bin/python

# This contains API routes for project files (mirrors the API docs)

######
###### GET routes
######

# Get all files attached to a project
def getProjectFiles(mosaicConfig, projectId, limit, page, fileTypes):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" "'
  command += str(url) + 'api/v1/projects/' + str(projectId) + '/files'
  command += '?limit=' + str(limit) + '&page=' + str(page)
  if fileTypes: command += '&filetypes=\\"' + str(fileTypes) + '\\"'
  command += '"'

  return command

# Get the url for a project file
def getProjectFileUrl(mosaicConfig, projectId, fileId, create):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/files/' + str(fileId) + '/url?create_activity=' + str(create) + '"'

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
