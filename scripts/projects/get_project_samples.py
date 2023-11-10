from __future__ import print_function

import sys
import os
import math
import argparse
import json
from random import random

# Add the path of the common functions and import them
from sys import path
path.append('/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[0:-1]) + '/../common_components')
path.append('/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[0:-1]) + '/../api_commands')
import mosaic_config
import api_attributes as api_a
import api_charts as api_c
import api_dashboards as api_d
import api_projects as api_p
import api_project_attributes as api_pa
import api_project_backgrounds as api_pb
import api_samples as api_s
import api_sample_attributes as api_sa

def main():
  global peddyProjectId
  global hasSampleAttributes
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {'MOSAIC_TOKEN': {'value': args.token, 'desc': 'An access token', 'long': '--token', 'short': '-t'},
                    'MOSAIC_URL': {'value': args.url, 'desc': 'The api url', 'long': '--url', 'short': '-u'}}
  mosaicConfig   = mosaic_config.mosaicConfigFile(args.config)
  mosaicConfig   = mosaic_config.commandLineArguments(mosaicConfig, mosaicRequired)

  # Get the samples from a project
  getSamples(args)

# Input options
def parseCommandLine():
  global version

  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Required arguments
  parser.add_argument('--project_id', '-p', required = True, metavar = 'integer', help = 'The Mosaic project id to upload attributes to')

  # Optional mosaic arguments
  parser.add_argument('--config', '-c', required = False, metavar = 'string', help = 'The config file for Mosaic')
  parser.add_argument('--token', '-t', required = False, metavar = 'string', help = 'The Mosaic authorization token')
  parser.add_argument('--url', '-u', required = False, metavar = 'string', help = 'The base url for Mosaic')
  parser.add_argument('--attributes_project', '-a', required = False, metavar = 'integer', help = 'The Mosaic project id that contains public attributes')

  # Version
  parser.add_argument('--version', '-v', action="version", version='Get samples version: ' + str(version))

  return parser.parse_args()

# Get the samples
def getSamples(args):
  global mosaicConfig

  # Get the sample ids and names
  samples = api_s.getSamplesDictIdName(mosaicConfig, args.project_id)
  for sampleId in samples: print(sampleId, ': ', samples[sampleId], sep = '')

# Initialise global variables

# Store mosaic info, e.g. the token, url etc.
mosaicConfig = {}

# Store the version
version = "0.0.1"

if __name__ == "__main__":
  main()
