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
import api_sample_attributes as api_sa

def main():
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {'MOSAIC_TOKEN': {'value': args.token, 'desc': 'An access token', 'long': '--token', 'short': '-t'},
                    'MOSAIC_URL': {'value': args.url, 'desc': 'The api url', 'long': '--url', 'short': '-u'}}
  mosaicConfig = mosaic_config.parseConfig(args.config, mosaicRequired)

  # Update the attribute
  updateAttribute(args)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Arguments related to the config file
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "A config file containing token / url information")
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic curl commands, up to an including \"api\". Do NOT include a trailing /")

  # The project and attribute ids to which the filter is to be added is required
  parser.add_argument('--project_id', '-p', required = True, metavar = "integer", help = "The Mosaic project id containing the attribute to update")
  parser.add_argument('--attribute_id', '-a', required = True, metavar = "integer", help = "The Mosaic attribute id to update")

  # Arguments related to the event
  parser.add_argument('--privacy_level', '-r', required = False, metavar = "string", help = 'The privacy level of the project - "public" or "private"')
  parser.add_argument('--display_type', '-d', required = False, metavar = "string", help = 'Can be "text", "badge", or "percent"')
  parser.add_argument('--severity', '-s', required = False, metavar = "string", help = 'Requires a json map describing the severities')

  return parser.parse_args()

# Update the attribute
def updateAttribute(args):
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
  data = api_sa.putSampleAttribute(mosaicConfig, fields, args.project_id, args.attribute_id)
  print(data)
  
  #try: data = json.loads(os.popen(api_va.updateVariantAnnotation(mosaicConfig, args.project, fields, args.annotation_id)).read())
  #except: fail("Couldn't update variant annotation")

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
