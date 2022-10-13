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
  deleteFile(args)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Arguments related to the config file
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic curl commands, up to an including \"api\". Do NOT include a trailing /")
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "A config file containing token / url information")

  # The project id to which the filter is to be added is required
  parser.add_argument('--project', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")

  # Arguments related to the file to add
  parser.add_argument('--sample_name', '-s', required = True, metavar = "string", help = "The sample id to attach the file to")
  parser.add_argument('--file_id', '-f', required = False, metavar = "string", help = "The file id to be deleted. If not included, a list of file id will be presented")

  return parser.parse_args()

# Delete the file
def deleteFile(args):
  global token
  global apiUrl
  limit = 100
  page  = 1

  # Get the sample id
  jsonData = json.loads(os.popen(api_s.getSamples(mosaicConfig, args.project)).read())

  # Loop over all samples and file the one with the correct name
  sampleId = False
  for sample in jsonData:
    if sample['name'] == args.sample_name:
      if sampleId: fail("Sample: " + str(args.sample_name) + " appears multiple times in the project")
      sampleId = sample['id']
  if not sampleId: fail("Sample: " + str(args.sample_name) + " was not found in the project")

  # Get all files for the sample and print to screen
  if not args.file_id: 
    jsonData = json.loads(os.popen(api_sf.getSampleFiles(mosaicConfig, args.project, sampleId, limit, page)).read())
    for sampleFile in jsonData['data']: print(sampleFile['name'], ": ", sampleFile['id'], sep = "")

  # Delete the sample file
  else: 
    try: data = os.popen(api_sf.deleteSampleFile(mosaicConfig, args.project, sampleId, args.file_id)).read()
    except: fail("Failed to delete file")
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
