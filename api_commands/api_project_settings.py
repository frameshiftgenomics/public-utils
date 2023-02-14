#!/usr/bin/python

import os
import json

# The first section of this file contains routines to execute the API routes and acts as a layer between the
# calling script and the Pythonized API routes. This will check for errors, deal with looping over pages of 
# results etc and return data objects. The API routes themselves occur later in this file

######
###### Execute GET routes
######

######
###### Execute POST routes
######

######
###### Execute PUT routes
######

# Set the default variant annotations
def setDefaultVariantAnnotations(mosaicConfig, projectId, annIds):
  try: data = json.loads(os.popen(putDefaultAnnotationsCommand(mosaicConfig, projectId, annIds)).read())
  except: fail('Failed to set the default variant annotations for project: ' + str(projectId))
  if 'message' in data: fail('Failed to set the default variant annotations for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

# Set the sort order of variant filters
def setVariantFilterSortOrder(mosaicConfig, projectId, filterRecords):
  putSortVariantFilters(mosaicConfig, projectId, filterRecords)
  exit(0)
  try: data = json.loads(os.popen(putSortVariantFilters(mosaicConfig, projectId, filterRecords)).read())
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

  print('TEST')
  print(filterRecords)
  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"sorted_annotations": {"variant_filters": ['
  for i, record in enumerate(filterRecords):
    print('  ', i, record)
    print(','.join(str(record['sortOrder'])))
    if i == 0: command += '["VARIANT_FILTERS|' + str(record['category']) + '", [' + ','.join(record['sortOrder']) + ']]'
    else: command += ', ["VARIANT_FILTERS|' + str(record['category']) + '", [' + ','.join(record['sortOrder']) + ']]'
  command += ']}}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/settings' + '"'

  print(command)
  return command

######
###### DELETE routes
######

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)
