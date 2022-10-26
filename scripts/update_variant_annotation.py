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
import api_variant_annotations as api_va

def main():
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {"token": True, "url": True, "attributesProjectId": False}
  mosaicConfig   = mosaic_config.parseConfig(args, mosaicRequired)

  # If the annotation id is not provided, get all annotations ids from the project and display
  if not args.annotation_id: getAnnotations(args.project)

  # Update the annotation
  updateAnnotation(args)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Arguments related to the config file
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "A config file containing token / url information")
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic curl commands, up to an including \"api\". Do NOT include a trailing /")

  # The project id to which the filter is to be added is required
  parser.add_argument('--project', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")

  # Arguments related to the event
  parser.add_argument('--annotation_id', '-a', required = False, metavar = "string", help = 'The id of the annotation to update. If not provided, a list of available annotations for the project will be shown')
  parser.add_argument('--privacy_level', '-r', required = False, metavar = "string", help = 'The privacy level of the project - "public" or "private"')
  parser.add_argument('--display_type', '-d', required = False, metavar = "string", help = 'Can be "text", "badge", or "percent"')
  parser.add_argument('--severity', '-s', required = False, metavar = "string", help = 'Requires a json map describing the severities')

  return parser.parse_args()

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
