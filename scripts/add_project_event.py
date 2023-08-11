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

  # Add the event
  addEvent(args)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Arguments related to the config file
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "A config file containing token / url information")
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic curl commands, up to an including \"api\". Do NOT include a trailing /")
  parser.add_argument('--attributes_project', '-a', required = False, metavar = 'integer', help = 'The Mosaic project id that contains public attributes')

  # The project id to which the filter is to be added is required
  parser.add_argument('--project_id', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")

  # Arguments related to the event
  parser.add_argument('--name', '-n', required = True, metavar = 'string', help = 'The name to give to the saved filter')
  parser.add_argument('--description', '-d', required = False, metavar = 'string', help = 'An optional description of the timestamp')
  parser.add_argument('--value', '-v', required = False, metavar = 'string', help = 'The timestamp to apply')
  parser.add_argument('--public', '-b', required = False, action = 'store_true', help = 'If set, the created event will be public. If not, the event will be private to the given project')

  return parser.parse_args()

# Add the event
def addEvent(args):
  global mosaicConfig

  # Define the value to apply and default to private if not specifically set to public
  #value = "2022/01/01" if not args.value else args.value
  isPublic = 'true' if args.public else 'false'
  description = args.description if args.description else 'No description provided'
  attributeId = api_pa.createProjectAttribute(mosaicConfig, args.project_id, args.name, description, 'null', 'timestamp', isPublic)

  #try: jsonData = json.loads(os.popen(api_pa.postProjectAttribute(mosaicConfig, args.name, "timestamp", value, isPublic, args.project)).read())
  #except: fail("Couldn't add event")

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables
mosaicConfig = {}

if __name__ == "__main__":
  main()
