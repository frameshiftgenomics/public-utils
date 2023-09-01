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
import api_samples as api_s
import api_sample_files as api_sf

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
  mosaicConfig   = mosaic_config.mosaicConfigFile(args.config)
  mosaicConfig   = mosaic_config.commandLineArguments(mosaicConfig, mosaicRequired)

  # Check file type
  checkType(args.file_type)

  # Get the files from a project
  getFiles(args)

# Input options
def parseCommandLine():
  global version

  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Required arguments
  parser.add_argument('--project_id', '-p', required = True, metavar = 'integer', help = 'The Mosaic project id to upload attributes to')
  parser.add_argument('--file_type', '-f', required = True, metavar = 'string', help = 'The file type to get urls for. Allowed values: vcf, tbi')

  # Optional mosaic arguments
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "The config file for Mosaic")
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic")
  parser.add_argument('--attributes_project', '-a', required = False, metavar = "integer", help = "The Mosaic project id that contains public attributes")

  # Version
  parser.add_argument('--version', '-v', action="version", version='Get files version: ' + str(version))

  return parser.parse_args()

# Check the file type
def checkType(fileType):
  global allowedTypes

  # Check if the requested file type is allowed
  if fileType not in allowedTypes: fail('The requested file type (' + str(fileType) + ') is not recognised. The allowed types are:\n  ' + '\n  '.join(allowedTypes))

# Get the files
def getFiles(args):
  global mosaicConfig
  observedFiles = []

  # Get all the sample ids in the project
  sampleIds = api_s.getSampleIds(mosaicConfig, args.project_id)

  # Loop over all the samples and get the vcf files for them
  for sampleId in sampleIds:
    data = api_sf.getAllSampleFilesData(mosaicConfig, args.project_id, sampleId)
    for fileInfo in data:

      # Only extract vcf files
      if fileInfo['type'] == args.file_type:
        fileId = fileInfo['id']
        name   = fileInfo['name']

        # The same file can be associated with multiple samples, but we only want to process each unique file once.
        # Check if we've already seen a file with this name and only get the url for new files
        if name not in observedFiles:
          url = api_sf.getFileUrl(mosaicConfig, args.project_id, fileId, 'false')
          observedFiles.append(name)
          print(url)

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables

# Store mosaic info, e.g. the token, url etc.
mosaicConfig = {}

# The allowed file types
allowedTypes = []
allowedTypes.append('vcf')
allowedTypes.append('tbi')

# Store the version
version = "0.0.1"

if __name__ == "__main__":
  main()
