#!/usr/bin/python

from __future__ import print_function

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

def main():
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {'MOSAIC_TOKEN': {'value': args.token, 'desc': 'An access token', 'long': '--token', 'short': '-t'},
                    'MOSAIC_URL': {'value': args.url, 'desc': 'The api url', 'long': '--url', 'short': '-u'}}
  mosaicConfig   = mosaic_config.mosaicConfigFile(args.config)
  mosaicConfig   = mosaic_config.commandLineArguments(mosaicConfig, mosaicRequired)

  # Get all project attributes from the project and display
  if not args.attribute_id: getAttributes(args)

  # Delete the attribute from the project
  deleteAttribute(args)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Arguments related to the config file
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "A config file containing token / url information")
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic curl commands, up to an including \"api\". Do NOT include a trailing /")

  # The project id to which the filter is to be added is required
  parser.add_argument('--project_id', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")

  # Arguments related to the event
  parser.add_argument('--attribute_id', '-a', required = False, metavar = "string", help = "The id of the attribute to delete")

  return parser.parse_args()

# Get all the project attributes for the project
def getAttributes(args):
  global mosaicConfig

  # Get all of the project attributes
  data = api_pa.getProjectAttributes(mosaicConfig, args.project_id)

  # Loop over all attributes and output to screen
  print("Available attributes:")
  for attribute in data:
    print("  ", data[attribute]['name'], ": ", data[attribute]['id'], ", ", data[attribute]['value_type'], sep = "")
  exit(0)

# Delete the attribute
def deleteAttribute(args):
  data = api_pa.deleteProjectAttribute(mosaicConfig, args.project_id, args.attribute_id)

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables
mosaicConfig = {}

if __name__ == "__main__":
  main()
