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
import api_project_attributes as api_pa

def main():
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {'MOSAIC_TOKEN': {'value': args.token, 'desc': 'An access token', 'long': '--token', 'short': '-t'},
                    'MOSAIC_URL': {'value': args.url, 'desc': 'The api url', 'long': '--url', 'short': '-u'}}
  mosaicConfig   = mosaic_config.mosaicConfigFile(args.config)
  mosaicConfig   = mosaic_config.commandLineArguments(mosaicConfig, mosaicRequired)

  # Get all public project attributes
  attributes = api_pa.getPublicProjectAttributesNameIdUid(mosaicConfig)
  for attribute in attributes: print(attribute)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Arguments related to the config file
  parser.add_argument('--token', '-t', required = False, metavar = 'string', help = 'The Mosaic authorization token')
  parser.add_argument('--url', '-u', required = False, metavar = 'string', help = 'The base url for Mosaic curl commands, up to an including "api". Do NOT include a trailing ')
  parser.add_argument('--config', '-c', required = False, metavar = 'string', help = 'A config file containing token / url information')

  return parser.parse_args()

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
