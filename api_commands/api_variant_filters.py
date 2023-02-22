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

# Return aill information on variant filters for a project
def getVariantFilters(config, projectId):

  # Execute the GET route
  try: data = json.loads(os.popen(getVariantFiltersCommand(config, projectId)).read())
  except: fail('Failed to execute the GET variant filters route for project: ' + str(projectId))
  if 'message' in data: fail('Failed to execute the GET variant filters route for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Return the data
  return data

# Return a list of all variant filter ids for a project
def getVariantFilterIds(config, projectId):
  filterIds = []

  # Execute the GET route
  try: data = json.loads(os.popen(getVariantFiltersCommand(config, projectId)).read())
  except: fail('Failed to execute the GET variant filters route for project: ' + str(projectId))
  if 'message' in data: fail('Failed to execute the GET variant filters route for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for variantFilter in data: filterIds.append(variantFilter['id'])

  # Return the list of variant filter ids
  return filterIds

# Return a dictionary keyed by id for all variant filters in a project, with names as values
def getVariantFilterIdsNames(config, projectId):
  filterIds = {}

  # Execute the GET route
  try: data = json.loads(os.popen(getVariantFiltersCommand(config, projectId)).read())
  except: fail('Failed to execute the GET variant filters route for project: ' + str(projectId))
  if 'message' in data: fail('Failed to execute the GET variant filters route for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for variantFilter in data: filterIds[variantFilter['id']] = variantFilter['name']

  # Return the list of variant filter ids
  return filterIds

# Return a dictionary keyed by name for all variant filters in a project, with ids as values
def getVariantFilterNamesIds(config, projectId):
  filterIds = {}

  # Execute the GET route
  try: data = json.loads(os.popen(getVariantFiltersCommand(config, projectId)).read())
  except: fail('Failed to execute the GET variant filters route for project: ' + str(projectId))
  if 'message' in data: fail('Failed to execute the GET variant filters route for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for variantFilter in data: filterIds[variantFilter['name']] = variantFilter['id']

  # Return the list of variant filter ids
  return filterIds

######
###### Execute POST routes
######

# Create a variant filter in a project and return the id of the created filter
def createVariantFilter(mosaicConfig, projectId, name, category, annotationFilters):
  try: data = json.loads(os.popen(postVariantFilterCommand(mosaicConfig, name, category, annotationFilters, projectId)).read())
  except: fail('Failed to POST a new variant filter for project ' + str(projectId))
  if 'message' in data: fail('Failed to POST a new variant for project ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Return the filter id
  return data['id']

######
###### Execute DELETE routes
######

# Given a project id and a list of filter ids, delete every filter
def deleteAllVariantFiltersInProject(config, projectId, filterIds):

  # Loop over the list of provided filter Ids and delete each filter
  for filterId in filterIds:
    try: data = os.popen(deleteVariantFilterCommand(config, projectId, filterId))
    except: fail('Failed to DELETE the variant filter with id ' + str(filterId) + ' for project ' + str(projectId))
    if 'message' in data: fail('Failed to DELETE the variant filter with id ' + str(filterId) + ' for project ' + str(projectId) + '. API returned the message: ' + str(data['message']))

#################
#################
################# Following are the API routes for variant filters (mirrors the API docs)
#################
#################

######
###### GET routes
######

# Get the variant filters in the project
def getVariantFiltersCommand(mosaicConfig, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" ' + str(url) + 'api/v1/projects/'
  command += '"' + str(projectId) + '/variants/filters' + '"'

  return command

######
###### POST routes
######

# Post a new variant filter
def postVariantFilterCommand(mosaicConfig, name, category, annotationFilters, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"name": "' + str(name) + '", '
  if category: command += '"category": "' + str(category) + '", '
  command += '"filter": ' + json.dumps(annotationFilters) + '}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/variants/filters' + '"'

  return command

######
###### PUT routes
######

# Update a variant filter
def putVariantFilterCommand(mosaicConfig, name, annotationFilters, projectId, filterId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"name": "' + str(name) + '", "filter": ' + json.dumps(annotationFilters) + '}\' '
  command += str(url) + 'api/v1/projects/' + str(projectId) + '/variants/filters/' + str(filterId)

  return command

# Update a variant filter category
def putVariantFilterCategoryCommand(mosaicConfig, category, projectId, filterId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"category": "' + str(category) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/variants/filters/' + str(filterId) + '"'

  return command


######
###### DELETE routes
######

# Delete a variant filter
def deleteVariantFilterCommand(mosaicConfig, projectId, filterId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X DELETE -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/variants/filters/' + str(filterId) + '"'

  return command

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)
