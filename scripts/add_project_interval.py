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
import api_project_attributes as api_pa
import api_project_intervals as api_pi

def main():
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {'MOSAIC_TOKEN': {'value': args.token, 'desc': 'An access token', 'long': '--token', 'short': '-t'},
                    'MOSAIC_URL': {'value': args.url, 'desc': 'The api url', 'long': '--url', 'short': '-u'}}
  mosaicConfig = mosaic_config.parseConfig(args.config, mosaicRequired)

  # If project ids aren't provided, get all project attributes from the project and display
  if not args.start_attribute or not args.end_attribute: getAttributes(args)

  # Create the interval
  addInterval(args)

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
  parser.add_argument('--name', '-n', required = False, metavar = "string", help = "The name to give to the saved filter")
  parser.add_argument('--start_attribute', '-s', required = False, metavar = "string", help = "The project attribute id for the start of the interval")
  parser.add_argument('--end_attribute', '-e', required = False, metavar = "string", help = "The project attribute id for the end of the interval")
  parser.add_argument('--public', '-b', required = False, action = "store_true", help = "If not set, the created event will be private")

  return parser.parse_args()

# Get all the project attributes for the project
def getAttributes(args):
  global mosaicConfig

  # Get all of the project attributes
  data = json.loads(os.popen(api_pa.getProjectAttributes(mosaicConfig, args.project)).read())

  # Loop over all attributes and output the applicable attribute (e.g. timestamps)
  print("Available events:")
  for attribute in data:
    if attribute['value_type'] == 'timestamp': print("  ", attribute['name'], ": ", attribute['id'], sep = "")
  exit(0)

# Add the event
def addInterval(args):
  global mosaicConfig

  # Default to private if not specifically set to public
  isPublic = "true" if args.public else "false"

  # Fail if no name has been provided for the interval
  if not args.name: fail("Please provide a name for the interval: --name (-n)")
  try: data = json.loads(os.popen(api_pi.postProjectIntervalAttribute(mosaicConfig, args.name, isPublic, args.start_attribute, args.end_attribute, args.project)).read())
  except: fail("Couldn't add interval")

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables
mosaicConfig = {}

if __name__ == "__main__":
  main()
