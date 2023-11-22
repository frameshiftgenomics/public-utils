#!/usr/bin/python

from __future__ import print_function
import os
import json

# The first section of this file contains routines to execute the API routes and acts as a layer between the
# calling script and the Pythonized API routes. This will check for errors, deal with looping over pages of 
# results etc and return data objects. The API routes themselves occur later in this file

######
###### Execute GET routes
######

# Get all the project settings
def getProjectSettings(config, projectId):
  try: data = json.loads(os.popen(getProjectSettingsCommand(config, projectId)).read())
  except: fail('Failed to get the settings for for project: ' + str(projectId))
  if 'message' in data: fail('Failed to get the settings for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Return the project reference
  return data

# Get the project reference
def getProjectReference(config, projectId):
  try: data = json.loads(os.popen(getProjectSettingsCommand(config, projectId)).read())
  except: fail('Failed to get the settings for for project: ' + str(projectId))
  if 'message' in data: fail('Failed to get the settings for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Return the project reference
  return data['reference']

# Get the project privacy level
def getProjectPrivacyLevel(config, projectId):
  try: data = json.loads(os.popen(getProjectSettingsCommand(config, projectId)).read())
  except: fail('Failed to get the settings for for project: ' + str(projectId))
  if 'message' in data: fail('Failed to get the settings for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Return the project reference
  return data['privacy_level']

######
###### Execute POST routes
######

######
###### Execute PUT routes
######

# Set the privacy level of the project
def setProjectPrivacy(mosaicConfig, projectId, privacyLevel):
  allowedPrivacyLevels = ['public', 'protected', 'private']
  if privacyLevel not in allowedPrivacyLevels: fail('Defined privacy level (' + str(privacyLevel) + ') is not valid. Allowed values are\n  ' + str('\n  '.join(allowedPrivacyLevels)))

  try: data = json.loads(os.popen(putPrivacyLevel(mosaicConfig, projectId, privacyLevel)).read())
  except: fail('Failed to set the privacy level to ' + str(privacyLevel) + ' for project: ' + str(projectId))
  if 'message' in data: fail('Failed to set the privacy level to ' + str(privacyLevel) + ' for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

# Set the default sample attribute table columns and analytics charts
def setDefaultTableAndCharts(mosaicConfig, projectId, columnIds, chartIds):
  try: data = json.loads(os.popen(setDefaultTableAndChartsCommand(mosaicConfig, projectId, columnIds, chartIds)).read())
  except: fail('Failed to set the default variant annotations for project: ' + str(projectId))
  if 'message' in data: fail('Failed to set the default variant annotations for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

# Set the default variant annotations
def setDefaultVariantAnnotations(mosaicConfig, projectId, annIds):
  try: data = json.loads(os.popen(putDefaultAnnotationsCommand(mosaicConfig, projectId, annIds)).read())
  except: fail('Failed to set the default variant annotations for project: ' + str(projectId))
  if 'message' in data: fail('Failed to set the default variant annotations for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

# Set the sort order of variant filters
def setVariantFilterSortOrder(mosaicConfig, projectId, filterRecords):
  try: data = json.loads(os.popen(putSortVariantFiltersCommand(mosaicConfig, projectId, filterRecords)).read())
  except: fail('Failed to set the variant filter sort order for project: ' + str(projectId))
  if 'message' in data: fail('Failed to set the variant filter sort order for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

######
###### Execute DELETE routes
######

#################
#################
################# Following are the API routes for variant filters (mirrors the API docs)
#################
#################

# This contains API routes for project settings (mirrors the API docs)

######
###### GET routes
######

# Get the project settings
def getProjectSettingsCommand(mosaicConfig, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/settings' + '"'

  return command

######
###### POST routes
######

######
###### PUT routes
######

# Set both the default column ids for the Samples table and the default chart ids
def setDefaultTableAndChartsCommand(mosaicConfig, projectId, columnIds, chartIds):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"selected_sample_attribute_chart_data": {"chart_ids": ' + str(chartIds) + ', "chart_data": {}}, '
  command += '"selected_sample_attribute_column_ids": ' + str(columnIds) + '}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/settings' + '"'

  return command

# Set a variant annotation as a default
def putDefaultAnnotationsCommand(mosaicConfig, projectId, annotationIds):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"selected_variant_annotation_ids": ' + str(annotationIds) + '}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/settings' + '"'

  return command

# Set the sort order of variant filters and annotations
def putSortVariantFiltersCommand(mosaicConfig, projectId, filterRecords):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"sorted_annotations": {"variant_filters": ['
  for i, record in enumerate(filterRecords):
    if i == 0: command += '["VARIANT_FILTERS|' + str(record['category']) + '", [' + ','.join(record['sortOrder']) + ']]'
    else: command += ', ["VARIANT_FILTERS|' + str(record['category']) + '", [' + ','.join(record['sortOrder']) + ']]'
  command += ']}}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/settings' + '"'

  return command

# Set the privacy level of a project
def putPrivacyLevel(mosaicConfig, projectId, privacyLevel):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"privacy_level": "' + str(privacyLevel) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/settings' + '"'

  return command

######
###### DELETE routes
######

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)
