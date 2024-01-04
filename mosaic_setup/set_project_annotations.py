import os
import argparse
import json
import sys

from datetime import date
from os.path import exists
from sys import path

def main():
  global mosaicConfig
  global version

  # Parse the command line
  args = parseCommandLine()

  # Import the api client
  path.append(args.api_client)
  from mosaic import Mosaic, Project, Store
  store   = Store(config_file = args.config)
  mosaic  = Mosaic(config_file = args.config)

  # Read the Mosaic json and validate its contents
  annotationsInfo = readAnnotationsJson(args.json)

  # Get all the public annotations in the Public annotations project for this reference
  if annotationsInfo['reference'] == 'GRCh37': projectId = store.get('Project ids', 'annotations_grch37')
  elif annotationsInfo['reference'] == 'GRCh38': projectId = store.get('Project ids', 'annotations_grch38')
  project           = mosaic.get_project(projectId)
  publicAnnotations = project.get_variant_annotations()

  # Determine which of the annotations in the json need to be created, updated, or already exist
  annotationStatus(project, projectId, annotationsInfo, publicAnnotations)

# Input options
def parseCommandLine():
  global version
  parser = argparse.ArgumentParser(description='Process the command line')

  # Required arguments
  parser.add_argument('--config', '-c', required = True, metavar = 'string', help = 'The config file for Mosaic')
  parser.add_argument('--api_client', '-a', required = True, metavar = 'string', help = 'The directory where the Python api wrapper lives')

  # Optional pipeline arguments
  parser.add_argument('--json', '-j', required = True, metavar = 'string', help = 'The json file describing the annotation resources')

  # Version
  parser.add_argument('--version', '-v', action="version", version='Calypso annotation pipeline version: ' + str(version))

  return parser.parse_args()

# Read through the Mosaic json file describing the mosaic information for uploading annotations
def readAnnotationsJson(jsonFilename):
  allowedReferences = ['GRCh37', 'GRCh38']
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

  # Store the reference
  try: jsonInfo['reference'] = jsonData['reference']
  except: fail('The json file (' + str(jsonFilename) + ') does not include a reference')
  if jsonInfo['reference'] not in allowedReferences: fail('The json file (' + str(jsonFilename) + ') has an unknown reference (' + str(jsonInfo['reference']) + '). Allowed values are:\n  ' + '\n  '.join(allowedReferences))

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
def annotationStatus(project, projectId, annotationsInfo, publicAnnotations):

  # Generate a list of the available annotation names
  availableAnnotations = {}
  for annotation in publicAnnotations: availableAnnotations[annotation['name']] = annotation

  # Loop over the annotations that should exist in the project and create or update as necessary
  for annotation in annotationsInfo['annotations']:
    if annotation not in availableAnnotations: annotationId, annotationUid = createAnnotation(project, projectId, annotation, annotationsInfo['annotations'][annotation])
    else:
      category    = annotationsInfo['annotations'][annotation]['category']
      displayType = annotationsInfo['annotations'][annotation]['display_type'] if annotationsInfo['annotations'][annotation]['display_type'] else 'text'
      severity    = annotationsInfo['annotations'][annotation]['severity']

      # If updating an annotation, use the original_project_id to ensure the update occurs
      originalProjectId = availableAnnotations[annotation]['original_project_id']
      updateAnnotation(project, originalProjectId, annotation, annotationsInfo['annotations'][annotation], availableAnnotations[annotation])

# Create a new public annotation
def createAnnotation(project, projectId, name, annotation):
  print('Creating: ', name, sep = '')
  valueType     = annotation['type']
  category      = annotation['category']
  severity      = annotation['severity']
  displayType   = annotation['display_type']
  data          = project.create_variant_annotation(name = name, value_type = valueType, privacy_level = 'public', display_type = displayType, severity = severity, category = category)
  annotationId  = data['id']
  annotationUid = data['uid']

  # Return the annotation id and uid
  return data['id'], data['uid']

# Update an existing public annotation
def updateAnnotation(project, projectId, name, annotation, publicAnnotation):
  print('Updating: ', name, sep = '')
  valueType     = annotation['type']
  category      = annotation['category']
  severity      = annotation['severity'] if annotation['severity'] else None
  displayType   = annotation['display_type']
  annotationId  = publicAnnotation['id']
  annotationUid = publicAnnotation['uid']
  project.put_variant_annotation(annotationId, name = name, value_type = valueType, display_type = displayType, severity = severity, category = category)

  # Return the annotation id and uid
  return publicAnnotation['id'], publicAnnotation['uid']

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables

# Pipeline version
version = "0.0.1"
date    = str(date.today())

# Store information related to Mosaic
mosaicConfig = {}

if __name__ == "__main__":
  main()
