#!/usr/bin/python

import json
import os
import math

# The first section of this file contains routines to execute the API routes and acts as a layer between the
# calling script and the Pythonized API routes. This will check for errors, deal with looping over pages of 
# results etc and return data objects. The API routes themselves occur later in this file

######
###### Execute GET routes
######

# Get all the dashboard information
def getDashboard(config, projectId):
  try: data = json.loads(os.popen(getDashboardCommand(config, projectId)).read())
  except: fail('Failed to get dashboard for project: ' + str(projectId))
  if 'message' in data: fail('Failed to get dashboard for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Return the data
  return data

######
###### Execute POST routes
######

# Pin a project attribute to the dashboard
def pinProjectAttribute(config, projectId, attId, isNamePinned):
  try: data = json.loads(os.popen(postPinAttributeCommand(config, attId, isNamePinned, projectId)).read())
  except: fail('Failed to pin project attribute to the dashboard for project: ' + str(projectId))
  if 'message' in data: fail('Failed to pin project attribute to the dashboard for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

# Pin a conversation
def pinConversation(config, projectId, convId):
  try: data = json.loads(os.popen(postPinConversationCommand(config, convId, projectId)).read())
  except: fail('Failed to pin conversation to the dashboard for project: ' + str(projectId))
  if 'message' in data: fail('Failed to pin conversation to the dashboard for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

# Pin a chart
def pinChart(config, projectId, chartId):
  try: data = json.loads(os.popen(postPinChartCommand(config, chartId, projectId)).read())
  except: fail('Failed to pin chart to the dashboard for project: ' + str(projectId))
  if 'message' in data: fail('Failed to pin chart to the dashboard for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

#################
#################
################# Following are the API routes for variant filters (mirrors the API docs)
#################
#################

# This contains API routes for dashboards (mirrors the API docs)

######
###### GET routes
######

# Get dashboard information
def getDashboardCommand(mosaicConfig, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig["MOSAIC_URL"]

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/dashboard' + '"'

  return command

######
###### POST routes
######

# Pin a chart to the dashboard
def postPinChartCommand(mosaicConfig, chartId, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"type": "chart", "chart_id": "' + str(chartId) + '", "is_active": "true"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/dashboard' + '"'

  return command

# Pin an attribute to the dashboard
def postPinAttributeCommand(mosaicConfig, attributeId, showName, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"type": "project_attribute", "attribute_id": "' + str(attributeId) + '", "is_active": "true", '
  command += '"should_show_name_in_badge": "' + str(showName) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/dashboard' + '"'

  return command

# Pin a conversation to the dashboard
def postPinConversationCommand(mosaicConfig, conversationId, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"type": "conversation", "project_conversation_id": "' + str(conversationId) + '", "is_active": "true"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/dashboard' + '"'

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
