#!/usr/bin/python

from __future__ import print_function
import json
import os

# Read through the Mosaic json file describing the mosaic information for uploading annotations
def readAnnotationsJson(jsonFilename):
  jsonInfo = {}

  # Try and open the file
  try: jsonFile = open(jsonFilename, 'r')
  except: fail('The file describing the annotations (' + str(mosaicFilename) + ') could not be found')

  # Extract the json information
  try: jsonData = json.loads(jsonFile.read())
  except: fail('The json file (' + str(jsonFilename) + ') is not valid')

  # Store the data version
  try: jsonInfo['version'] = jsonData['version']
  except: fail('The json file (' + str(jsonFilename) + ') does not include a version')

  # Loop over all the specified annotations and add these to the public attributes project
  try: annotations = jsonData['annotations']
  except: fail('The json file (' + str(jsonFilename) + ') does not include annotations to add to the public attributes project')
  jsonInfo['annotations'] = {}
  for annotation in annotations:
    jsonInfo['annotations'][annotation] = {}

    try: jsonInfo['annotations'][annotation]['type'] = annotations[annotation]['type']
    except: fail('The json file does not contain the "type" field for annotation "' + str(annotation) + '"')

    # Check if the annotation has a category, display_type and severity
    jsonInfo['annotations'][annotation]['category'] = annotations[annotation]['category'] if 'category' in annotations[annotation] else False
    jsonInfo['annotations'][annotation]['display_type'] = annotations[annotation]['display_type'] if 'display_type' in annotations[annotation] else False
    jsonInfo['annotations'][annotation]['severity'] = annotations[annotation]['severity'] if 'severity' in annotations[annotation] else False

  # Return the annotation information
  return jsonInfo

# Determine the status of the annotations in the input json in the Mosaic public attributes project. Determine which
# annotations need to be created, updated, or left alone
def annotationStatus(mosaicConfig, api_va, annotationsInfo, publicAnnotations):
  for annotation in annotationsInfo['annotations']:
    if annotation not in publicAnnotations: annotationId, annotationUid = createAnnotation(mosaicConfig, api_va, annotation, annotationsInfo['annotations'][annotation])
    else:
      update = False
      category    = annotationsInfo['annotations'][annotation]['category']
      displayType = annotationsInfo['annotations'][annotation]['display_type'] if annotationsInfo['annotations'][annotation]['display_type'] else 'text'
      severity    = annotationsInfo['annotations'][annotation]['severity']

      # Check if the category needs updating
      if category and publicAnnotations[annotation]['category'] and category != publicAnnotations[annotation]['category']: update = True
      elif category and not publicAnnotations[annotation]['category']: update = True
      elif not category and publicAnnotations[annotation]['category']: update = True

      # Check if the display type needs updating
      if displayType and publicAnnotations[annotation]['display_type'] and displayType != publicAnnotations[annotation]['display_type']: update = True
      elif displayType and not publicAnnotations[annotation]['display_type']: update = True
      elif not displayType and publicAnnotations[annotation]['display_type']: update = True

      # Check if the severity needs updating
      if severity and publicAnnotations[annotation]['severity'] and severity != publicAnnotations[annotation]['severity']: update = True
      elif severity and not publicAnnotations[annotation]['severity']: update = True
      elif not severity and publicAnnotations[annotation]['severity']: update = True

      if update: updateAnnotation(mosaicConfig, api_va, annotation, annotationsInfo['annotations'][annotation], publicAnnotations[annotation])
      else:
        annotationId  = publicAnnotations[annotation]['id']
        annotationUid = publicAnnotations[annotation]['uid']

# Create a new public annotation
def createAnnotation(mosaicConfig, api_va, name, annotation):
  projectId   = mosaicConfig['MOSAIC_ATTRIBUTES_PROJECT_ID']
  valueType   = annotation['type']
  category    = annotation['category']
  severity    = annotation['severity']
  displayType = annotation['display_type']
  annotationId, annotationUid = api_va.createAnnotationWithAll(mosaicConfig, projectId, name, valueType, 'public', category, displayType, severity)

  # Return the annotation id and uid
  return annotationId, annotationUid

# Update an existing public annotation
def updateAnnotation(mosaicConfig, api_va, name, annotation, publicAnnotation):
  projectId    = mosaicConfig['MOSAIC_ATTRIBUTES_PROJECT_ID']
  valueType    = annotation['type']
  category     = annotation['category']
  severity     = annotation['severity'] if annotation['severity'] else None
  displayType  = annotation['display_type']
  annotationId = publicAnnotation['id']
  annotationId, annotationUid = api_va.updateAnnotationWithAll(mosaicConfig, projectId, annotationId, name, valueType, category, displayType, severity)

  # Return the annotation id and uid
  return annotationId, annotationUid

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)
