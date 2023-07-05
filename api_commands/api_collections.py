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

# Add projects to a collection
def addProjectsToCollection(mosaicConfig, collectionId, projectIds, roleType):
  try: data = json.loads(os.popen(postSubProjectsCommand(mosaicConfig, collectionId, projectIds, roleType)).read())
  except: fail('Failed to add projects to the collection')
  if 'message' in data: fail('Failed to add projects to the collection. API returned the message: ' + str(data['message']))

######
###### Execute PUT routes
######

# Update the default columns in the Samples table
def updateSamplesTableDefaults(mosaicConfig, collectionId, attributeIds):
  try: data = json.loads(os.popen(putSamplesTableColumnsCommand(mosaicConfig, collectionId, attributeIds)).read())
  except: fail('Failed to update samples table defaults in collection')
  if 'message' in data: fail('Failed to update samples table defaults in collection. API returned the message: ' + str(data['message']))

# Update the default system columns in the Projects table
def updateProjectsTableSystemDefaults(mosaicConfig, collectionId, attributeNames):
  try: data = json.loads(os.popen(putProjectsTableSystemColumnsCommand(mosaicConfig, collectionId, attributeNames)).read())
  except: fail('Failed to update projects table system defaults in collection')
  if 'message' in data: fail('Failed to update projects table system defaults in collection. API returned the message: ' + str(data['message']))

# Update the default columns in the Projects table
def updateProjectsTableDefaults(mosaicConfig, collectionId, attributeIds):
  try: data = json.loads(os.popen(putProjectsTableColumnsCommand(mosaicConfig, collectionId, attributeIds)).read())
  except: fail('Failed to update projects table defaults in collection')
  if 'message' in data: fail('Failed to update projects table defaults in collection. API returned the message: ' + str(data['message']))

# Update all the default columns in the Projects table
def updateAllProjectsTableDefaults(mosaicConfig, collectionId, attributeNames, attributeIds):
  try: data = json.loads(os.popen(putProjectsTableAllColumnsCommand(mosaicConfig, collectionId, attributeNames, attributeIds)).read())
  except: fail('Failed to update projects table defaults in collection')
  if 'message' in data: fail('Failed to update projects table defaults in collection. API returned the message: ' + str(data['message']))

# Update the default charts
def updateChartsDefaults(mosaicConfig, collectionId, chartIds):
  try: data = json.loads(os.popen(putDefaultChartsCommand(mosaicConfig, collectionId, chartIds)).read())
  except: fail('Failed to update default charts in collection')
  if 'message' in data: fail('Failed to update default charts in collection. API returned the message: ' + str(data['message']))

######
###### Execute DELETE routes
######

#################
#################
################# Following are the API routes for variant filters (mirrors the API docs)
#################
#################

######
###### GET routes
######

######
###### POST routes
######

# Add projects to a collection
def postSubProjectsCommand(mosaicConfig, collectionId, projectIds, roleType):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"collection_projects": [' + str(','.join(map(str,projectIds))) + '], '
  command += '"role_type_id": ' + str(roleType) + '}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(collectionId) + '/sub-projects' + '"'

  return command

######
###### PUT routes
######

# Update the default sample attributes in the Samples table
def putSamplesTableColumnsCommand(mosaicConfig, collectionId, attributeIds):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"selected_sample_attribute_column_ids": [' + str(','.join(map(str,attributeIds))) + ']}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(collectionId) + '/settings' + '"'

  return command

# Update the default system project attributes in the Projects table
def putProjectsTableSystemColumnsCommand(mosaicConfig, collectionId, attributeNames):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"selected_collections_table_columns": ['
  for i, name in enumerate(attributeNames):
    if i == 0: command += str('"' + name + '"')
    else: command += str(', "' + name + '"')
  command += ']}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(collectionId) + '/settings' + '"'

  return command

# Update the default project attributes in the Projects table
def putProjectsTableColumnsCommand(mosaicConfig, collectionId, attributeIds):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"selected_collection_attributes": [' + str(','.join(map(str,attributeIds))) + ']}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(collectionId) + '/settings' + '"'

  return command

# Update the default system and custom project attributes in the Projects table
def putProjectsTableAllColumnsCommand(mosaicConfig, collectionId, attributeNames, attributeIds):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"selected_collections_table_columns": ['
  for i, name in enumerate(attributeNames):
    if i == 0: command += str('"' + name + '"')
    else: command += str(', "' + name + '"')
  command += '], "selected_collection_attributes": [' + str(','.join(map(str,attributeIds))) + ']}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(collectionId) + '/settings' + '"'

  return command

# Set the default chart ids
def putDefaultChartsCommand(mosaicConfig, collectionId, chartIds):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"selected_sample_attribute_chart_data": {"chart_ids": ' + str(chartIds) + ', "chart_data": {}}}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(collectionId) + '/settings' + '"'

  return command

######
###### DELETE routes
######

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)
