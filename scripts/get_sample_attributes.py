#!/usr/bin/python

from __future__ import print_function

import sys
import os
import math
import argparse
import json
from random import random

# Add the path of the common functions and import them
from sys import path
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/common_components")
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/api_commands")
import mosaic_config
import api_sample_attributes as api_sa

def main():
  global peddyProjectId
  global hasSampleAttributes
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {'MOSAIC_TOKEN': {'value': args.token, 'desc': 'An access token', 'long': '--token', 'short': '-t'},
                    'MOSAIC_URL': {'value': args.url, 'desc': 'The api url', 'long': '--url', 'short': '-u'},
                    'MOSAIC_ATTRIBUTES_PROJECT_ID': {'value': args.attributes_project, 'desc': 'The public attribtes project id', 'long': '--attributes_project', 'short': '-a'}}
  mosaicConfig = mosaic_config.parseConfig(args.config, mosaicRequired)

  # Get the sample attributes in a project
  getSampleAttributes(args)

# Input options
def parseCommandLine():
  global version

  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Required arguments
  parser.add_argument('--project_id', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")

  # Optional mosaic arguments
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "The config file for Mosaic")
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic")
  parser.add_argument('--attributes_project', '-a', required = False, metavar = "integer", help = "The Mosaic project id that contains public attributes")

  # Version
  parser.add_argument('--version', '-v', action="version", version='Get sample attributes version: ' + str(version))

  return parser.parse_args()

# Get the sample attributes
def getSampleAttributes(args):
  global mosaicConfig

  try: data = json.loads(os.popen(api_sa.getSampleAttributes(mosaicConfig, args.project_id, False)).read()) 
  except: fail('Couldn\'t get sample attributes')

  for att in data: print(att['id'], ': "Name": ', att['name'], ', "uid": ', att['uid'], sep = '')

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables

# Store mosaic info, e.g. the token, url etc.
mosaicConfig = {}

# Store the version
version = "0.0.1"

if __name__ == "__main__":
  main()
