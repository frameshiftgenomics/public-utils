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
import api_variants as api_v

def main():
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {"token": True, "url": True, "attributesProjectId": False}
  mosaicConfig   = mosaic_config.parseConfig(args, mosaicRequired)

  # Check the arguments are valid
  checkArguments(args)

  # Upload the variants
  uploadVariants(args)

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
  parser.add_argument('--method', '-m', required = True, metavar = "string", help = 'The variant upload method: "allele"')
  parser.add_argument('--input_vcf', '-i', required = True, metavar = "string", help = 'The vcf file to upload variants from')

  return parser.parse_args()

# Check the arguments are valid
def checkArguments(args):
  global allowedMethods

  # Check that the vcf file exists
  if not exists(args.input_vcf): fail('Input vcf file could not be found: ' + str(args.input_vcf))

  # Check that the supplied method is valid
  if args.method not in allowedMethods: fail('Upload method (' + str(args.method) + ') is invalid. Allowed values are: ' + ', '.join(allowedMethods))

# Upload the variants from the supplied vcf file
def uploadVariants(args):
  global mosaicConfig

  # Get all of the project attributes
  try: data = json.loads(os.popen(api_v.postUploadVariants(mosaicConfig, args.input_vcf, args.method, args.description, project_id)).read())
  except: fail('Couldn\'t upload variants to Mosaic')

  # If a message is returned instead of data, check that the user has access to the project
  if 'message' in data: fail('Failed to upload variants. The following was returned:\n' + data{'message'})

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables
mosaicConfig = {}

# The available display types
allowedMethods = ["allele"]

if __name__ == "__main__":
  main()
