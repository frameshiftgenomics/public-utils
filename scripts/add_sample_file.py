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

  # Build the command to create a variant filter
  addFile(args)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Arguments related to the config file
  parser.add_argument('--config', '-c', required = True, metavar = "string", help = "A config file containing token / url information")
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic curl commands, up to an including \"api\". Do NOT include a trailing /")

  # The project id to which the filter is to be added is required
  parser.add_argument('--project', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")

  # Arguments related to the file to add
  parser.add_argument('--reference', '-r', required = True, metavar = "string", help = "The project reference genome")
  parser.add_argument('--name', '-n', required = True, metavar = "string", help = "The name of the file")
  parser.add_argument('--nickname', '-k', required = False, metavar = "string", help = "The nickname of the file (optional)")
  parser.add_argument('--type', '-y', required = True, metavar = "string", help = "The file type to add (\"bam\", \"bai\", \"cram\", \"crai\", \"vcf\", \"bcf\", \"tbi\", \"csi\"")
  parser.add_argument('--uri', '-i', required = True, metavar = "string", help = "The file location")
  parser.add_argument('--sample_name', '-s', required = True, metavar = "string", help = "The sample id to attach the file to")
  parser.add_argument('--vcf_sample_name', '-v', required = False, metavar = "string", help = "The sample name in the vcf file. Only required if adding a vcf file")

  return parser.parse_args()

# Add the file
def addFile(args):
  global token
  global apiUrl

  # Get the project reference
  jsonData = json.loads(os.popen(api_ps.getProjectSettings(mosaicConfig, args.project)).read())
  if jsonData['reference'] != args.reference: fail("Supplied reference (" + str(args.reference) + ") is different to the project reference (" + str(jsonData['reference']) + ")")

  # Get the sample id
  jsonData = json.loads(os.popen(api_s.getSamples(mosaicConfig, args.project)).read())

  # Loop over all samples and file the one with the correct name
  sampleId = False
  for sample in jsonData:
    if sample['name'] == args.sample_name:
      if sampleId: fail("Sample: " + str(args.sample_name) + " appears multiple times in the project")
      sampleId = sample['id']
  if not sampleId: fail("Sample: " + str(args.sample_name) + " was not found in the project")

  # Add the sample
  try: jsonData = json.loads(os.popen(api_sf.postSampleFile(mosaicConfig, args.name, args.nickname, args.type, args.uri, args.reference, args.sample_name, args.project, sampleId)).read())
  except: fail("Failed to add file")
  if "message" in jsonData: print(jsonData)

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
