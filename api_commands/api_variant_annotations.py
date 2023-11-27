#!/usr/bin/python

from __future__ import print_function
import json
import os
import math

# The first section of this file contains routines to execute the API routes and acts as a layer between the
# calling script and the Pythonized API routes. This will check for errors, deal with looping over pages of 
# results etc and return data objects. The API routes themselves occur later in this file

######
###### Execute the GET routes
######

# Return a list of all annotations with all their data
def getAnnotations(config, projectId):

  # Execute the GET route
  try: data = json.loads(os.popen(getVariantAnnotationsCommand(config, projectId)).read())
  except: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId))
  if 'message' in data: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Return the list of annotation ids
  return data

# Return a dictionary with annotation names as keys and ids as values
def getAnnotationDictNameId(config, projectId):
  annotations = {}

  # Execute the GET route
  try: data = json.loads(os.popen(getVariantAnnotationsCommand(config, projectId)).read())
  except: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId))
  if 'message' in data: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for annotation in data: annotations[annotation['name']] = annotation['id']

  # Return the list of annotation ids
  return annotations

# Return a dictionary with annotation names as keys and ids and uids as values
def getAnnotationDictNameIdUid(config, projectId):
  annotations = {}

  # Execute the GET route
  try: data = json.loads(os.popen(getVariantAnnotationsCommand(config, projectId)).read())
  except: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId))
  if 'message' in data: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for annotation in data: annotations[annotation['name']] = {'id': annotation['id'], 'uid': annotation['uid']}

  # Return the list of annotation ids
  return annotations

# Return a list of annotation ids
def getAnnotationIds(config, projectId):
  ids = []

  # Execute the GET route
  try: data = json.loads(os.popen(getVariantAnnotationsCommand(config, projectId)).read())
  except: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId))
  if 'message' in data: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for annotation in data: ids.append(annotation['id'])

  # Return the list of annotation ids
  return ids

# Return a dictionary with annotation ids as keys and annotation names as values
def getAnnotationIdsWithNames(config, projectId):
  ids = {}

  # Execute the GET route
  try: data = json.loads(os.popen(getVariantAnnotationsCommand(config, projectId)).read())
  except: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId))
  if 'message' in data: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for annotation in data: ids[annotation['id']] = annotation['name']

  # Return the dictionary
  return ids

# Return a list of all annotation uids
def getAnnotationUids(config, projectId):
  uids = []

  # Execute the GET route
  try: data = json.loads(os.popen(getVariantAnnotationsCommand(config, projectId)).read())
  except: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId))
  if 'message' in data: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for annotation in data: uids.append(annotation['uid'])

  # Return the list of variant filter ids
  return uids

# Return a dictionary of uids with the corresponding value type
def getAnnotationUidsWithTypes(config, projectId):
  uids = {}

  # Execute the GET route
  try: data = json.loads(os.popen(getVariantAnnotationsCommand(config, projectId)).read())
  except: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId))
  if 'message' in data: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for annotation in data: uids[annotation['uid']] = annotation['value_type']

  # Return the list of variant filter ids
  return uids

# Return a dictionary of uids with the corresponding names and value types
def getAnnotationUidsWithNamesTypes(config, projectId):
  uids = {}

  # Execute the GET route
  try: data = json.loads(os.popen(getVariantAnnotationsCommand(config, projectId)).read())
  except: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId))
  if 'message' in data: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for annotation in data: uids[annotation['uid']] = {'name': annotation['name'], 'type': annotation['value_type']}

  # Return the list of variant filter ids
  return uids

# Get the name, uid and id of all annotations in the project
def getVariantAnnotationsNameIdUId(config, projectId):
  anns = []

  # Get the annotations
  try: data = json.loads(os.popen(getVariantAnnotationsCommand(config, projectId)).read())
  except: fail('Unable to find annotations available for project ' + str(projectId)) 
  if 'message' in data: fail('Unable to find annotations available for project ' + str(projectId) + '. API returned the message: ' + str(data['messgage'])) 
  for ann in data: anns.append({'name': ann['name'], 'id': ann['id'], 'uid': ann['uid']})
                                                                  
  # Return the list
  return anns

# Get the name, uid, id, and type of all annotations in the project
def getVariantAnnotationsNameIdUIdType(config, projectId):
  anns = []

  # Get the annotations
  try: data = json.loads(os.popen(getVariantAnnotationsCommand(config, projectId)).read())
  except: fail('Unable to find annotations available for project ' + str(projectId)) 
  if 'message' in data: fail('Unable to find annotations available for project ' + str(projectId) + '. API returned the message: ' + str(data['messgage'])) 
  for ann in data: anns.append({'name': ann['name'], 'id': ann['id'], 'uid': ann['uid'], 'type': ann['value_type']})
                                                                  
  # Return the list
  return anns

# Get the name, uid and id of all annotations available for import
def getVariantAnnotationsImportNameIdUid(config, projectId):
  limit = 100
  page  = 1
  anns  = []

  # Get the annotations
  try: data = json.loads(os.popen(getVariantAnnotationsImportCommand(config, projectId, limit, page)).read())
  except: fail('Unable to find annotations available for import for project ' + str(projectId)) 
  if 'message' in data: fail('Unable to find annotations available for import for project ' + str(projectId) + '. API returned the message: ' + str(data['messgage'])) 
  for ann in data['data']: anns.append({'name': ann['name'], 'id': ann['id'], 'uid': ann['uid'], 'type': ann['value_type']})
                                                                  
  # Determine how many annotations there are and consequently how many pages of annotations
  noPages = math.ceil(int(data['count']) / int(limit))            
                                                                  
  # Loop over remainig pages of annotations
  for page in range(2, noPages + 1):
    try: data = json.loads(os.popen(getVariantAnnotationsImportCommand(config, projectId, limit, page)).read())
    except: fail('Unable to find annotations available for import for project ' + str(projectId)) 
    if 'message' in data: fail('Unable to find annotations available for import for project ' + str(projectId) + '. API returned the message: ' + str(data['messgage'])) 
    for ann in data['data']: anns.append({'name': ann['name'], 'id': ann['id'], 'uid': ann['uid'], 'type': ann['value_type']})

  # Return the list
  return anns

# Get the info for all annotations available for import
def getVariantAnnotationsImportName(config, projectId):
  limit = 100
  page  = 1
  anns  = {}

  # Get the annotations
  try: data = json.loads(os.popen(getVariantAnnotationsImportCommand(config, projectId, limit, page)).read())
  except: fail('Unable to find annotations available for import for project ' + str(projectId)) 
  if 'message' in data: fail('Unable to find annotations available for import for project ' + str(projectId) + '. API returned the message: ' + str(data['messgage'])) 
  for ann in data['data']: anns[ann['name']] = {'id': ann['id'], 'uid': ann['uid'], 'type': ann['value_type'], 'original_project_id': ann['original_project_id'], 'category': ann['category'], 'display_type': ann['display_type'], 'severity': ann['severity']}
                                                                  
  # Determine how many annotations there are and consequently how many pages of annotations
  noPages = math.ceil(int(data['count']) / int(limit))            
                                                                  
  # Loop over remainig pages of annotations
  for page in range(2, noPages + 1):
    try: data = json.loads(os.popen(getVariantAnnotationsImportCommand(config, projectId, limit, page)).read())
    except: fail('Unable to find annotations available for import for project ' + str(projectId)) 
    if 'message' in data: fail('Unable to find annotations available for import for project ' + str(projectId) + '. API returned the message: ' + str(data['messgage'])) 
    for ann in data['data']: anns[ann['name']] = {'id': ann['id'], 'uid': ann['uid'], 'type': ann['value_type'], 'original_project_id': ann['original_project_id'], 'category': ann['category'], 'display_type': ann['display_type'], 'severity': ann['severity']}

  # Return the list
  return anns

# Given an annotation id, return all information about the annotation
def getAnnotationInformation(config, annotationId, projectId):

  # Execute the GET route
  try: data = json.loads(os.popen(getVariantAnnotationsCommand(config, projectId)).read())
  except: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId))
  if 'message' in data: fail('Failed to execute the GET variant annotations route for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Loop over the returned data object and put the filter ids in a list to return
  for annotation in data: 
    if int(annotationId) == annotation['id']: return annotation

######
###### Execute the POST routes
######

# Create a new annotation and return the id and uid
def createPrivateAnnotationIdUid(config, ann, valueType, projectId):

  # Execute the command
  try: data = json.loads(os.popen(postCreateVariantAnnotationsCommand(config, ann, valueType, 'private', projectId)).read())
  except: fail('Failed to create private variant annotation for project: ' + str(projectId))
  if 'message' in data: fail('Failed to create private variant annotation for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Store the id and uid
  return {'id': data['id'], 'uid': data['uid']}

# Create a new annotation with a category and return the id and uid
def createPrivateAnnotationCategoryIdUid(config, ann, valueType, projectId, category):

  # Execute the command
  try: data = json.loads(os.popen(postCreateVariantAnnotationCategoryCommand(config, ann, valueType, 'private', projectId, category)).read())
  except: fail('Failed to create private variant annotation for project: ' + str(projectId))
  if 'message' in data: fail('Failed to create private variant annotation for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Store the id and uid
  return {'id': data['id'], 'uid': data['uid']}

# Create a new annotation with severity and return the uid
def createAnnotationSeverityUid(config, projectId, name, valueType, privacy, fields):
  try: data = json.loads(os.popen(postCreateVariantAnnotationWithSeverityCommand(config, name, valueType, privacy, fields, projectId)).read())
  except: fail('Failed to create variant annotation for project: ' + str(projectId))
  if 'message' in data: fail('Failed to create variant annotation for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Store the id and uid
  return data['uid']

# Create an annotation with all fields (display_type, severity, category)
def createAnnotationWithAll(config, projectId, name, valueType, privacy, category, displayType, severity):

  # If the severity is a dictionary, convert to a string, converting all single quotes to double quotes
  if type(severity) == dict: severity = str(severity).replace('\'', '"')

  try: data = json.loads(os.popen(postCreateVariantAnnotationWithAllCommand(config, projectId, name, valueType, privacy, category, displayType, severity)).read())
  except: fail('Failed to create variant annotation for project: ' + str(projectId))
  if 'message' in data: fail('Failed to create variant annotation for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Store the id and uid
  return data['id'], data['uid']

# Import an annotation
def importAnnotation(config, annId, projectId):
  try: data = json.loads(os.popen(postImportVariantAnnotationsCommand(config, annId, projectId)).read())
  except: fail('Failed to import annotation for project: ' + str(projectId))
  if 'message' in data: fail('Failed to import annotation for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

# Upload variant annotations
def uploadAnnotations(config, projectId, tsv, allowDeletion):
  try: data = json.loads(os.popen(postUploadVariantAnnotationsCommand(config, tsv, allowDeletion, projectId)).read())
  except: fail('Failed to upload annotations from ' + str(tsv) + ' to project: ' + str(projectId))

  # If the upload was successful, the message should be as expected
  if 'message' in data:
    if data['message'] != 'The file has been received and the data will be processed in the next few minutes.':
      fail('Failed to upload annotations from ' + str(tsv) + ' to project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))
  else: fail('Failed to upload annotations from ' + str(tsv) + ' to project: ' + str(projectId))

######
###### Execute the PUT routes
######

# Update an annotation if provided with a dictionary of values
def updateAnnotation(config, projectId, annotationId, fields):

  # The update command expects a list of fields to update. Set the category to update
  #fields = {}
  #fields['category'] = category

  # Update the annotation
  try: data = json.loads(os.popen(updateVariantAnnotationCommand(config, projectId, fields, annotationId)).read())
  except: fail('Failed to update the variant annotation in project: ' + str(projectId))
  if 'message' in data: fail('Failed to update the variant annotation in project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

# Create an annotation with all fields (display_type, severity, category)
def updateAnnotationWithAll(config, projectId, annotationId, name, valueType, category, displayType, severity):

  # If the severity is a dictionary, convert to a string, converting all single quotes to double quotes
  if type(severity) == dict: severity = str(severity).replace('\'', '"')

  try: data = json.loads(os.popen(putUpdateAnnotationCommand(config, projectId, annotationId, name, valueType, category, displayType, severity)).read())
  except: fail('Failed to create variant annotation for project: ' + str(projectId))
  if 'message' in data: fail('Failed to create variant annotation for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Store the id and uid
  return data['id'], data['uid']

# Update an annotation category
def updateAnnotationCategory(config, projectId, annotationId, category):

  # The update command expects a list of fields to update. Set the category to update
  fields = {}
  fields['category'] = category

  # Update the annotation
  try: data = json.loads(os.popen(updateVariantAnnotationCommand(config, projectId, fields, annotationId)).read())
  except: fail('Failed to update the variant annotation in project: ' + str(projectId))
  if 'message' in data: fail('Failed to update the variant annotation in project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

######
###### Execute the DELETE routes
######

# Delete an annotation by id
def deleteAnnotationById(config, projectId, annId):
  try: data = os.popen(deleteVariantAnnotationCommand(config, projectId, annId))
  except: fail('Failed to delete variant annotation in project: ' + str(projectId))
  if 'message' in data: fail('Failed to delete variant annotation in project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

#################
#################
################# Following are the API routes for variant filters (mirrors the API docs)
#################
#################

# This contains API routes for variant annotations (mirrors the API docs)

######
###### GET routes
######

# Get the variant annotations for the project
def getVariantAnnotationsCommand(mosaicConfig, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" ' + str(url) + 'api/v1/projects/'
  command += '"' + str(projectId) + '/variants/annotations' + '"'

  return command

# Get variant annotations available to import
def getVariantAnnotationsImportCommand(mosaicConfig, projectId, limit, page):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/variants/annotations/import?limit=' + str(limit) + '&page=' + str(page) + '"'

  return command

######
###### POST routes
######

# Create a variant annotation
def postCreateVariantAnnotationsCommand(mosaicConfig, name, valueType, privacy, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token)
  command += '" -d \'{"name": "' + str(name) + '", "value_type": "' + str(valueType) + '", "privacy_level": "' + str(privacy) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/variants/annotations' + '"'

  return command

# Create a variant annotation with a category set
def postCreateVariantAnnotationCategoryCommand(mosaicConfig, name, valueType, privacy, projectId, category):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token)
  command += '" -d \'{"name": "' + str(name) + '", "value_type": "' + str(valueType) + '", "privacy_level": "' + str(privacy) + '", "category": "' + str(category) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/variants/annotations' + '"'

  return command

# Create a variant annotation with the display type and severity set
def postCreateVariantAnnotationWithSeverityCommand(mosaicConfig, name, valueType, privacy, fields, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token)
  command += '" -d \'{"name": "' + str(name) + '", "value_type": "' + str(valueType) + '", "privacy_level": "' + str(privacy) + '"'
  for field in fields: command += ', "' + str(field) + '": "' + str(fields[field]) + '"'
  command += '}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/variants/annotations' + '"'

  return command

# Create a variant annotation with the category, display_type and severity set
def postCreateVariantAnnotationWithAllCommand(mosaicConfig, projectId, name, valueType, privacy, category, displayType, severity):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token)
  command += '" -d \'{"name": "' + str(name) + '", "value_type": "' + str(valueType) + '", "privacy_level": "' + str(privacy) + '"'
  if category: command += ', "category": "' + str(category) + '"'
  if displayType: command += ', "display_type": "' + str(displayType) + '"'
  if severity: command += ', "severity": ' + str(severity)
  command += '}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/variants/annotations' + '"'

  return command

# Import variant annotations to the project
def postImportVariantAnnotationsCommand(mosaicConfig, annotationId, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token)
  command += '" -d \'{"annotation_id": ' + str(annotationId) + '}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/variants/annotations/import' + '"'

  return command

# Upload variant annotations to the project
def postUploadVariantAnnotationsCommand(mosaicConfig, filename, allowDeletion, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: multipart/form-data" -H "Authorization: Bearer ' + str(token)
  command += '" -F "file=@' + str(filename) + '" -F "allow_deletion=' + str(allowDeletion) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/variants/annotations/upload' + '"'

  return command

######
###### PUT routes
######

# Create a variant annotation with the category, display_type and severity set
def putUpdateAnnotationCommand(mosaicConfig, projectId, annotationId, name, valueType, category, displayType, severity):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token)
  command += '" -d \'{"name": "' + str(name) + '", "value_type": "' + str(valueType) + '"'
  if category: command += ', "category": "' + str(category) + '"'
  if displayType: command += ', "display_type": "' + str(displayType) + '"'
  if severity: command += ', "severity": ' + str(severity)
  command += '}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/variants/annotations/' + str(annotationId) + '"'

  return command

# Update a variant annotation
def updateVariantAnnotationCommand(mosaicConfig, projectId, fields, annotationId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token)
  command += '" -d \'{'
  for i, field in enumerate(fields):
    command += '"' + str(field) + '": "' + str(fields[field]) + '"'
    if int(i) + 1 != len(fields): command += ', '
  command += '}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/variants/annotations/' + str(annotationId) + '"'

  return command

######
###### DELETE routes
######

# Delete a variant annotation from a project
def deleteVariantAnnotationCommand(mosaicConfig, projectId, annotationId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X DELETE -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/variants/annotations/' + str(annotationId) + '"'

  return command

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)
