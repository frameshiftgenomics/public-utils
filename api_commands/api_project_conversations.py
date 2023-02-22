#!/usr/bin/python

from __future__ import print_function
import json
import os
import math

# The first section of this file contains routines to execute the API routes and acts as a layer between the
# calling script and the Pythonized API routes. This will check for errors, deal with looping over pages of 
# results etc and return data objects. The API routes themselves occur later in this file

######
###### Execute GET routes
######

# Return a dictionary of conversations with the id as the key and the title and description as value
def getConversationsIdToTitleDesc(config, projectId):
  limit = 100
  page  = 1
  ids   = {}

  # Execute the command
  try: data = json.loads(os.popen(getConversationsCommand(config, limit, page, projectId)).read())
  except: fail('Failed to get conversations for project: ' + str(projectId))
  if 'message' in data: fail('Failed to get conversations for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for conv in data['data']: ids[conv['id']] = {'title': conv['title'], 'description': conv['description']}

  # Determine the number of pages
  noPages = int( math.ceil( float(data['count']) / float(limit) ) )

  # Loop over all necessary pages
  for page in range(1, noPages):
    try: data = json.loads(os.popen(getConversationsCommand(config, limit, page + 1, projectId)).read())
    except: fail('Failed to get conversations for project: ' + str(projectId))
    if 'message' in data: fail('Failed to get conversations for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

    # Loop over the returned data object and put the filter ids in a list to return
    for conv in data['data']: ids[conv['id']] = {'title': conv['title'], 'description': conv['description']}

  # Return the dictionary of conversations
  return ids

######
###### Execute POST routes
######

# Create a new conversation and return the id of the created conversation
def createConversation(config, projectId, title, description):
  try: data = json.loads(os.popen(postConversationCommand(config, title, description, projectId)).read())
  except: fail('Failed to create conversation for project: ' + str(projectId))
  if 'message' in data: fail('Failed to create conversation for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Return the conversation id
  return data['id']

#################
#################
################# Following are the API routes for variant filters (mirrors the API docs)
#################
#################

# This contains API routes for conversations (mirrors the API docs)

######
###### GET routes
######

# Get all project conversations
def getConversationsCommand(mosaicConfig, limit, page, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/conversations?limit=' + str(limit) + '&page=' + str(page) + '"'

  return command

######
###### POST routes
######

# Create a new project conversation
def postConversationCommand(mosaicConfig, title, description, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"title": "' + str(title) + '", "description": "' + str(description) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/conversations' + '"'

  return command

######
###### PUT routes
######

# Update a project conversation title and description
def putUpdateConversationCommand(mosaicConfig, title, description, projectId, conversationId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"title": "' + str(title) + '", "description": "' + str(description) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/conversations/' + str(conversationId) + '"'

  return command

######
###### DELETE routes
######

# Delete a project conversation
def deleteConversationCommand(mosaicConfig, projectId, conversationId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X DELETE -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/conversations/' + str(conversationId) + '"'

  return command

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)
