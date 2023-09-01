#!/usr/bin/python

from __future__ import print_function
from os.path import exists

import os
import math
import argparse
import json
from random import random

from sys import path
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/../api_commands")
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/../common_components")
import command_line_parser as clp
import mosaic_config
import api_sample_attributes as api_sa

def main():
  global mosaicConfig
  global allowedTypes

  # Parse the command line
  additionalArgs = getArgs()
  args           = clp.parseCommandLine(additionalArgs)

  # Parse the mosaic configuration file
  mosaicRequired = {'MOSAIC_TOKEN': {'value': args.token, 'desc': 'An access token', 'long': '--token', 'short': '-t'},
                    'MOSAIC_URL': {'value': args.url, 'desc': 'The api url', 'long': '--url', 'short': '-u'},
                    'MOSAIC_ATTRIBUTES_PROJECT_ID': {'value': args.attributes_project, 'desc': 'The public attributes project id', 'long': '--attributes_project', 'short': '-a'}}
  mosaicConfig   = mosaic_config.mosaicConfigFile(args.config)
  mosaicConfig   = mosaic_config.commandLineArguments(mosaicConfig, mosaicRequired)

  # Get the attributes for this project
  attributes = api_sa.getSampleAttributes(mosaicConfig, args.project_id)

  # If not sample attribute id is provided, list the available sample attributes
  if not args.attribute_id:
    print('Avaliable sample attributes:')
    for attribute in attributes: print('  ', attribute['name'], ': ', attribute['id'], ', predefined values = ', attribute['predefined_values'], sep = '')
    exit(0)

  # If an attribute id is set, check that the predefined values are given, that the attribute id exists, and that the project id 
  # is that of the source project for the attribute 
  else:
    if not args.predefined_values: fail('Provide a comma separated list of values to use as the predefined values for this attribute')

    # Loop over the available attributes and find the one requested
    attributeInfo = {}
    for attribute in attributes:
      if int(attribute['id']) == int(args.attribute_id):
        attributeInfo = attribute
        break
    if not attributeInfo: fail('No attribute with id ' + str(args.attribute_id) + ' found in this project')

    # The predefined values can only be set in the attributes source project. Fail if this is not that project
    if int(attributeInfo['original_project_id']) != int(args.project_id): fail('Sample attribute can only be edited in its source project: ' + str(attributeInfo['original_project_id']))

    # Set the predefined values after converting the comma separated list into an array
    values = args.predefined_values.split(',') if ',' in args.predefined_values else [args.predefined_values]
    api_sa.setSampleAttributePredefinedValues(mosaicConfig, args.project_id, args.attribute_id, values)

# Input options
def getArgs():
  additionalArgs = []

  # The following standard command line arguments are imported automatically
  # --config, -c
  # --token, -t
  # --url, -u
  # --attributes_project, -a
  # --project_id, -p

  # Additional required attributes
  additionalArgs.append({'long': '--attribute_id', 'short': '-i', 'required': False, 'metavar': 'integer', 'help': 'The id of the attribute to set predefined values for'})
  additionalArgs.append({'long': '--predefined_values', 'short': '-v', 'required': False, 'metavar': 'string', 'help': 'A comma separated list of predefined values'})

  return additionalArgs

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables
mosaicConfig = {}

# Allowed annotation types
allowedTypes = ['float', 'string']

if __name__ == "__main__":
  main()
