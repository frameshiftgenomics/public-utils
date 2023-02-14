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
import api_variant_annotations as api_va

def main():
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {'MOSAIC_TOKEN': {'value': args.token, 'desc': 'An access token', 'long': '--token', 'short': '-t'},
                    'MOSAIC_URL': {'value': args.url, 'desc': 'The api url', 'long': '--url', 'short': '-u'},
                    'MOSAIC_ATTRIBUTES_PROJECT_ID': {'value': args.attributes_project, 'desc': 'The public attribtes project id', 'long': '--attributes_project', 'short': '-a'}}
  mosaicConfig   = mosaic_config.mosaicConfigFile(args.config)
  mosaicConfig   = mosaic_config.commandLineArguments(mosaicConfig, mosaicRequired)

  # Create the annotation
  createAnnotation(args)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Arguments related to the config file
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "A config file containing token / url information")
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic curl commands, up to an including \"api\". Do NOT include a trailing /")
  parser.add_argument('--attributes_project', '-a', required = False, metavar = "string", help = "The project id for the public attributes project")

  # Arguments related to the ClinVar annotations
  parser.add_argument('--privacy_level', '-r', required = False, metavar = "string", help = 'The privacy level of the project - "public" or "private"')
  parser.add_argument('--display_type', '-d', required = False, metavar = "string", help = 'Can be "text", "badge", or "percent"')
  parser.add_argument('--name', '-n', required = True, metavar = "string", help = 'The annotation name')

  return parser.parse_args()

# Create the annotation
def createAnnotation(args):
  global mosaicConfig
  global displayTypes

  # Privacy level
  if not args.privacy_level: args.privacy_level = "public"
  if args.privacy_level not in privacyLevels: fail("Unknown privacy_level: " + args.privacy_level)

  # Display type
  if not args.display_type: args.display_type = "badge"
  if args.display_type not in displayTypes: fail("Unknown display type: " + args.display_type)

  # Severity
  severity = "{'Pathogenic': 1, 'Pathogenic/Likely_pathogenic': 1, 'Likely_pathogenic': 2, 'Established risk allele': 3, 'Uncertain_significance': 4, 'Conflicting_interpretations_of_pathogenicity': 4, 'Likely_risk_allele': 4, 'association': 4, 'Uncertain_risk_allele': 5, 'Likely_benign': 7, 'Benign/Likely_benign': 8, 'Benign': 8, 'protective': 9}"
  severity = severity.replace('"', '\\"')
  severity = severity.replace('\'', '\\"')
  fields = {}
  fields["display_type"]  = args.display_type
  fields["severity"]      = severity

  # Update the annotation
  uid = api_va.createAnnotationSeverityUid(mosaicConfig, mosaicConfig['MOSAIC_ATTRIBUTES_PROJECT_ID'], args.name, 'string', args.privacy_level, fields)

  # Output the id of the created annotation
  print(uid)

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables
mosaicConfig = {}

# The available privacy levels
privacyLevels = []
privacyLevels.append("public")
privacyLevels.append("private")

# The available display types
displayTypes = []
displayTypes.append("text")
displayTypes.append("badge")
displayTypes.append("percent")

if __name__ == "__main__":
  main()
