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
import api_project_attributes as api_pa

def main():
  global mosaicConfig

  # Parse the command line
  additionalArgs = getArgs()
  args           = clp.parseCommandLine(additionalArgs)

  # Parse the mosaic configuration file
  mosaicRequired = {'MOSAIC_TOKEN': {'value': args.token, 'desc': 'An access token', 'long': '--token', 'short': '-t'},
                    'MOSAIC_URL': {'value': args.url, 'desc': 'The api url', 'long': '--url', 'short': '-u'},
                    'MOSAIC_ATTRIBUTES_PROJECT_ID': {'value': args.attributes_project, 'desc': 'The public attributes project id', 'long': '--attributes_project', 'short': '-a'}}
  mosaicConfig   = mosaic_config.mosaicConfigFile(args.config)
  mosaicConfig   = mosaic_config.commandLineArguments(mosaicConfig, mosaicRequired)

  # If an attribute isn't provided, display a list of timestamps from the MOSAIC_ATTRIBUTES_PROJECT
  if not args.attribute_id:
    attributes = api_pa.getTimestampsDictNameId(mosaicConfig, mosaicConfig['MOSAIC_ATTRIBUTES_PROJECT_ID'])
    print('Available timestamps from the Mosaic Public Attributes project:')
    for attribute in attributes: print('  ', attribute, ': ', attributes[attribute], sep = '')
    exit(0)

  # If no value was defined, set it to null, then import the event
  if not args.value: args.value = 'null'
  attributeId = api_pa.importProjectAttribute(mosaicConfig, args.project_id, args.attribute_id, args.value)

# Input options
def getArgs():
  additionalArgs = []

  # Additional required attributes
  additionalArgs.append({'long': '--attribute_id', 'short': '-r', 'required': False, 'metavar': 'integer', 'help': 'The Mosaic attribute id to import'})
  additionalArgs.append({'long': '--value', 'short': '-i', 'required': False, 'metavar': 'integer', 'help': 'The value to give to the imported attribute (optional)'})

  return additionalArgs

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
