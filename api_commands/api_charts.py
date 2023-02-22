#!/usr/bin/python

import os
import json

# The first section of this file contains routines to execute the API routes and acts as a layer between the
# calling script and the Pythonized API routes. This will check for errors, deal with looping over pages of 
# results etc and return data objects. The API routes themselves occur later in this file

######
###### Execute GET routes
######

# Return a list of charts, including the name, id, and background project id
def getCharts(config, projectId):
  charts = []

  # Get the chart info
  try: data = json.loads(os.popen(getProjectChartsCommand(config, projectId)).read())
  except: fail('Failed to get chart information for project: ' + str(projectId))
  if 'message' in data: fail('Failed to get chart information for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))
  for chart in data: charts.append({'id': chart['id'], 'name': chart['name'], 'projectBackgroundId': chart['project_background_id']})

  # Return the sample id
  return charts

######
###### Execute POST routes
######

# Create a new scatterplot chart with background data
def createScatterChartWithBackgrounds(config, projectId, name, attId, backgroundsId, ylabel, colourId, compareId):
  try: data = json.loads(os.popen(postProjectBackgroundChartCommand(config, name, 'scatterplot', attId, backgroundsId, ylabel, colourId, compareId, projectId)).read())
  except: fail('Failed to get chart information for project: ' + str(projectId))
  if 'message' in data: fail('Failed to get chart information for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Return the id of the chart
  return data['id']

######
###### Execute DELETE routes
######

# Delete a chart
def deleteChart(config, projectId, chartId):
  try: data = os.popen(deleteSavedChartCommand(config, projectId, chartId))
  except: fail('Failed to delete chart for project: ' + str(projectId))
  if 'message' in data: fail('Failed to delete chart for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

#################
#################
################# Following are the API routes for variant filters (mirrors the API docs)
#################
#################

# This contains API routes for charts (mirrors the API docs)

######
###### GET routes
######

# Get all project charts
def getProjectChartsCommand(mosaicConfig, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/charts' + '"'

  return command

######
###### POST routes
######

# Post a chart with background data
def postProjectBackgroundChartCommand(mosaicConfig, name, chartType, attributeId, backgroundId, ylabel, colorId, compareId, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"name": "' + str(name) + '", "chart_type": "' + str(chartType) + '", "attribute_id": "' + str(attributeId)
  command += '", "project_background_id": "' + str(backgroundId) + '", "saved_chart_data": {"x_axis": "attribute", "y_label": "'
  command += str(ylabel) + '", "color_by": "attribute", "color_by_attribute_id": "' + str(colorId) + '", "compare_to_attribute_id": "'
  command += str(compareId) + '"}}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/charts' + '"'

  return command

######
###### PUT routes
######

######
###### DELETE routes
######

# Delete chart
def deleteSavedChartCommand(mosaicConfig, projectId, chartId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X DELETE -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/charts/' + str(chartId) + '"'

  return command

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)
