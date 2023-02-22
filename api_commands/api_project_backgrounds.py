#!/usr/bin/python

from __future__ import print_function
import os
import json

# The first section of this file contains routines to execute the API routes and acts as a layer between the
# calling script and the Pythonized API routes. This will check for errors, deal with looping over pages of 
# results etc and return data objects. The API routes themselves occur later in this file

######
###### Execute POST routes
######

# Post background data to a project
def uploadBackgroundData(config, projectId, name):
  try: data = json.loads(os.popen(postBackgroundsCommand(config, name, projectId)).read())
  except: fail('Failed to upload background data to project: ' + str(projectId))
  if 'message' in data: fail('Failed to upload background data to project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Return the sample id
  return data['id']

#################
#################
################# Following are the API routes for variant filters (mirrors the API docs)
#################
#################

# This contains API routes for project backgrounds (mirrors the API docs)

######
###### GET routes
######

######
###### POST routes
######

# Post background data to a project
def postBackgroundsCommand(mosaicConfig, filename, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d "@' + str(filename) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/backgrounds' + '"'

  return command

# Post a background chart to a project
def postBackgroundChartCommand(mosaicConfig, name, chartType, attributeId, backgroundId, yLabel, colour, compare, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"name": "' + str(name) + '", "chart_type": "' + str(chartType) + '", "attribute_id": "' + str(attributeId)
  command += '", "project_background_id": "' + str(backgroundId) +'", "saved_chart_data": {"x_axis": "attribute", "y_label": "'
  command += str(yLabel) + '", "color_by": "attribute", "color_by_attribute_id": ' + str(colour) + ', "compare_to_attribute_id": '
  command += str(compare) + '}}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/charts' + '"'

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
