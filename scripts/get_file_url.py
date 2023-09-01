#!/usr/bin/python

from __future__ import print_function
from os.path import exists

import os
import math
import argparse
import json
from random import random

from sys import path
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/api_commands")
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/common_components")
import mosaic_config
import api_project_files as api_pf
import api_sample_files as api_sf

def main():
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {'MOSAIC_TOKEN': {'value': args.token, 'desc': 'An access token', 'long': '--token', 'short': '-t'},
                    'MOSAIC_URL': {'value': args.url, 'desc': 'The api url', 'long': '--url', 'short': '-u'},
                    'MOSAIC_ATTRIBUTES_PROJECT_ID': {'value': args.attributes_project, 'desc': 'The public attribtes project id', 'long': '--attributes_project', 'short': '-a'}}
  mosaicConfig   = mosaic_config.mosaicConfigFile(args.config)
  mosaicConfig   = mosaic_config.commandLineArguments(mosaicConfig, mosaicRequired)

  # If no file id was supplied, show all the files for the project
  if not args.file_id: getFileIds(args)

  # Get the file url
  else: getUrl(args)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Arguments related to the config file
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "A config file containing token / url information")
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic curl commands, up to an including \"api\". Do NOT include a trailing /")
  parser.add_argument('--attributes_project', '-a', required = False, metavar = "integer", help = "The Mosaic project id that contains public attributes")

  # The project id to which the filter is to be added is required
  parser.add_argument('--project_id', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")

  # Optional arguments
  parser.add_argument('--file_type', '-l', required = False, metavar = "string", help = 'The file type to get ids for')
  parser.add_argument('--file_id', '-f', required = False, metavar = "string", help = 'The id of the file to generate the url for')

  return parser.parse_args()

# Get the file ids for the project
def getFileIds(args):
  global mosaicConfig

  data = api_sf.getSampleFiles(mosaicConfig, args.project_id, sampleId, fileType)

# Get the file url
def getUrl(args):
  global mosaicConfig

  # Get the URL
  url = api_sf.getFileUrl(mosaicConfig, args.project_id, args.file_id, 'false')
  print(url)

# Get all the project attributes for the project
def getAnnotations(projectId):
  global mosaicConfig

  # Get all of the project attributes
  data = json.loads(os.popen(api_va.getVariantAnnotations(mosaicConfig, projectId)).read())

  # If a message is returned instead of data, check that the user has access to the project
  if 'message' in data: fail("No annotation data returned. Check you have access to the project")

  # Loop over all attributes and output the applicable attribute (e.g. timestamps)
  print("Available annotations:")
  for annotation in data:
    print("  Name: ", annotation['name'], ", id: ", annotation['id'], sep = "")
    print("    original project: ", annotation['original_project_id'], sep = "")
    print("    uid: ", annotation['uid'], sep = "")
    print("    type: ", annotation['value_type'], sep = "")
    print("    privacy level: ", annotation['privacy_level'], sep = "")
    print("    display type: ", annotation['display_type'], sep = "")
    print("    severity: ", annotation['severity'], sep = "")
  exit(0)

# Add the event
def updateAnnotation(args):
  global mosaicConfig
  global displayTypes

  # Create a dictionary of the updates
  fields = {}

  # Privacy level
  if args.privacy_level:
    if args.privacy_level in privacyLevels: fields["privacy_level"] = args.privacy_level
    else: fail("Unknown privacy_level: " + args.privacy_level)

  # Display type
  if args.display_type:
    if args.display_type in displayTypes: fields["display_type"] = args.display_type
    else: fail("Unknown display type: " + args.display_type)

  # If severity is defined, check the value is a valid json
  if args.severity:
    args.severity = args.severity.replace('"', '\\"')
    args.severity = args.severity.replace('\'', '\\"')
    fields["severity"] = args.severity

  # Make sure some updates have been applied
  if len(fields) == 0: fail("Some fields must be provided to be updated")

  # Update the annotation
  data = api_va.updateVariantAnnotation(mosaicConfig, args.project, fields, args.annotation_id)
  print(data)
  
  try: data = json.loads(os.popen(api_va.updateVariantAnnotation(mosaicConfig, args.project, fields, args.annotation_id)).read())
  except: fail("Couldn't update variant annotation")

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables
mosaicConfig = {}

# The available privacy levels
privacyLevels = []
privacyLevels.append("public")
privacyLevels.append("private")

# The available display types
displayTypes = []
displayTypes.append("text")
displayTypes.append("badge")
displayTypes.append("percent")

if __name__ == "__main__":
  main()
