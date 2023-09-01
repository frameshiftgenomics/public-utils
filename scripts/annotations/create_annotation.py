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
import api_variant_annotations as api_va

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

  # Check if an annotation of the requested name already exists
  annotations = api_va.getAnnotationDictNameId(mosaicConfig, args.project_id)
  if args.annotation_name in annotations: fail('An annotation of the requested name (' + str(args.annotation_name) + ') already exists in the project')

  # Check that the value type is allowed
  if args.value_type not in allowedTypes: fail('The defined value type is not recognised. Allowed values are:\n  ' + '\n  '.join(allowedTypes))

  # If there is no existing annotation, create a private annotation
  annotationId = api_va.createPrivateAnnotationIdUid(mosaicConfig, args.annotation_name, args.value_type, args.project_id)

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
  additionalArgs.append({'long': '--annotation_name', 'short': '-n', 'required': True, 'metavar': 'integer', 'help': 'The name of the annotation to create'})
  additionalArgs.append({'long': '--value_type', 'short': '-v', 'required': True, 'metavar': 'string', 'help': 'The type of the annotation to create. Allowed values are:\n  ' + '\n  '.join(allowedTypes)})

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
