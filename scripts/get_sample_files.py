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
import api_sample_files as api_sf

def main():
  global peddyProjectId
  global hasSampleAttributes
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {"token": True, "url": True, "attributesProjectId": True}
  mosaicConfig   = mosaic_config.parseConfig(args, mosaicRequired)

  # Get the files from a project
  getFiles(args)

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
  parser.add_argument('--version', '-v', action="version", version='Get files version: ' + str(version))

  return parser.parse_args()

# Get the files
def getFiles(args):
  global mosaicConfig
  global sampleFiles
  limit = 100
  page  = 1

  try: data = json.loads(os.popen(api_sf.getAllSampleFiles(mosaicConfig, args.project_id, limit, page)).read()) 
  except: fail('Couldn\'t get files')
  for sampleFile in data['data']: sampleFiles[sampleFile['id']] = {'name': sampleFile['name'], 'nickname': sampleFile['nickname'], 'uri': sampleFile['uri']}

  # Determine how many annotations there are and consequently how many pages of annotations
  noPages = math.ceil(int(data['count']) / int(limit))

  # Loop over remainig pages of annotations
  for page in range(2, noPages + 1):
    try: data = json.loads(os.popen(api_sf.getAllSampleFiles(mosaicConfig, args.project_id, limit, page)).read()) 
    except: fail('Couldn\'t get files')
    for sampleFile in data['data']: sampleFiles[sampleFile['id']] = {'name': sampleFile['name'], 'nickname': sampleFile['nickname'], 'uri': sampleFile['uri']}

  # Print out the files
  for sampleFile in sampleFiles: print(sampleFile, sampleFiles[sampleFile])

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables

# Store mosaic info, e.g. the token, url etc.
mosaicConfig = {}

# Store info on the files
sampleFiles = {}

# Store the version
version = "0.0.1"

if __name__ == "__main__":
  main()
