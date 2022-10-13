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
import api_sample_files as api_sf
import api_samples as api_s
import api_project_settings as api_ps

def main():
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {"token": True, "url": True, "attributesProjectId": False}
  mosaicConfig   = mosaic_config.parseConfig(args, mosaicRequired)

  # Delete the file
  updateFile(args)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Arguments related to the config file
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "A config file containing token / url information")
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic curl commands, up to an including \"api\". Do NOT include a trailing /")

  # The project id to which the filter is to be added is required
  parser.add_argument('--project', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")

  # Arguments related to the file to add
  parser.add_argument('--name', '-n', required = True, metavar = "string", help = "Update filename")
  parser.add_argument('--file_id', '-f', required = False, metavar = "string", help = "The file id to be deleted. If not included, a list of file id will be presented")

  return parser.parse_args()

# Updatee the file
def updateFile(args):
  global token
  global apiUrl
  sampleId = False

  # Get all files for the project
  jsonData = json.loads(os.popen(api_sf.getAllSampleFiles(mosaicConfig, args.project)).read())
  for sampleFile in jsonData['data']:
    if not args.file_id: print(sampleFile['nickname'], ": ", sampleFile['id'], ", sample_id: ", sampleFile['sample_id'], ", uri: ", sampleFile['uri'], sep = "")
    if args.file_id:
      if int(sampleFile['id']) == int(args.file_id): sampleId = sampleFile['sample_id']

  # Fail if the sample id was not found
  if not sampleId and args.file_id: fail("Sample id could not be found for file")

  # Update the file name
  elif sampleId and args.file_id:
    try: data = os.popen(api_sf.putUpdateSampleFileNickname(mosaicConfig, args.name, args.project, sampleId, args.file_id)).read()
    except: fail("Failed to update file")
    print(data)

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables
mosaicConfig = {}

# Attributes from the config file
apiUrl              = False
token               = False

if __name__ == "__main__":
  main()
