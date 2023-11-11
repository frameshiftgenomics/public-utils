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
import api_pedigree as api_ped
import api_samples as api_s

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

  # If no sample id is provided, list the sample ids for the project
  if not args.sample_id:
    sampleIds = api_s.getSamplesDictIdName(mosaicConfig, args.project_id)
    for sampleId in sampleIds: print('Sample: ', sampleIds[sampleId], ', id: ', sampleId, sep = '')
    exit(0)

  # If there is a sample id, output the pedigree
  else:
    ped = api_ped.getPedLines(mosaicConfig, args.project_id, args.sample_id)
    for line in ped: print(line)

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
  additionalArgs.append({'long': '--sample_id', 'short': '-s', 'required': False, 'metavar': 'integer', 'help': 'The sample id to get the pedigree for. If not included, all sample ids in the project will be output'})

  return additionalArgs

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables
mosaicConfig = {}

if __name__ == "__main__":
  main()
