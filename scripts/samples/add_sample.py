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
import api_samples as api_s

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

  # Create the new sample
  api_s.createSample(mosaicConfig, args.project_id, args.name)

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
  additionalArgs.append({'long': '--name', 'short': '-n', 'required': True, 'metavar': 'string', 'help': 'The name of the sample to add'})

  return additionalArgs

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables
mosaicConfig = {}

if __name__ == "__main__":
  main()
