#!/usr/bin/python

from __future__ import print_function

import sys
import os
import math
import argparse
import json
from random import random

# Add the path of the common functions and import them
from sys import path
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/common_components")
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/api_commands")
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
  mosaicRequired = {"token": True, "url": True, "attributeProjectId": True}
  mosaicConfig   = mosaic_config.parseConfig(args, mosaicRequired)

  # Get the samples from a project
  getSamples(args)

# Input options
def parseCommandLine():
  global version

  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Required arguments
  parser.add_argument('--project', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")

  # Optional mosaic arguments
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "The config file for Mosaic")
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic")
  parser.add_argument('--attributes_project', '-a', required = False, metavar = "integer", help = "The Mosaic project id that contains public attributes")

  # Version
  parser.add_argument('--version', '-v', action="version", version='Get samples version: ' + str(version))

  return parser.parse_args()

# Get the samples
def getSamples(args):
  global mosaicConfig

  command = api_s.getSamples(mosaicConfig, args.project)
  data    = json.loads(os.popen(command).read()) 

  # Loop over the samples and determine the proband, mother, father and sibs
  samples     = {}
  hasProband  = False
  probandName = False
  success     = True
  for sample in data:
    samples[sample["name"]] = {"id": sample["id"], "name": sample["name"], "uid": sample["uid"]}

    # Get data from the pedigree information
    if sample["pedigree"]["affection_status"] == 2:
      if hasProband:
        print("WARNING: Multiple probands")
        success = False
      else: 
        hasProband  = True
        probandName = sample["name"]
        samples[sample["name"]]["is_proband"] = True
        if sample["pedigree"]["maternal_id"]: samples[sample["name"]]["maternal_id"] = sample["pedigree"]["maternal_id"]
        if sample["pedigree"]["paternal_id"]: samples[sample["name"]]["paternal_id"] = sample["pedigree"]["paternal_id"]

    else: samples[sample["name"]]["is_proband"] = False

  # If there is a single proband, use this to assign the parents
  if success:
    for sample in samples:
      samples[sample]["is_mother"] = True if str(samples[probandName]["maternal_id"]) == str(samples[sample]["id"]) else False
      samples[sample]["is_father"] = True if str(samples[probandName]["paternal_id"]) == str(samples[sample]["id"]) else False
  for sample in samples: print(sample, samples[sample])

# Initialise global variables

# Store mosaic info, e.g. the token, url etc.
mosaicConfig = {}

# Store the version
version = "0.0.1"

if __name__ == "__main__":
  main()
