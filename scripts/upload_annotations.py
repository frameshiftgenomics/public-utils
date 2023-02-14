#!/usr/bin/python

from __future__ import print_function
from os.path import exists

import os
import argparse
import json

# Add the path of the common functions and import them
from sys import path
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/common_components")
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/api_commands")
import mosaic_config
import api_variant_annotations as api_va

def main():
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Parse the Mosaic config file to get the token and url for the api calls
  mosaicRequired = {'MOSAIC_TOKEN': {'value': args.token, 'desc': 'An access token', 'long': '--token', 'short': '-t'},
                    'MOSAIC_URL': {'value': args.url, 'desc': 'The api url', 'long': '--url', 'short': '-u'}}
  mosaicConfig   = mosaic_config.mosaicConfigFile(args.config)
  mosaicConfig   = mosaic_config.commandLineArguments(mosaicConfig, mosaicRequired)

  # Upload variants
  uploadAnnotations(args)

# Input options
def parseCommandLine():
  global version

  parser = argparse.ArgumentParser(description='Process the command line')

  # Required arguments
  parser.add_argument('--tsv_file', '-i', required = True, metavar = "string", help = "The vcf file containing variants to upload")
  parser.add_argument('--project_id', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")

  # Optional arguments
  parser.add_argument('--no_deletion', '-d', required = False, action = "store_true", help = "If set, blank values will NOT overwite existing annotation values")

  # Optional mosaic arguments
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "The config file for Mosaic")
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic")

  # Version
  parser.add_argument('--version', '-v', action="version", version="Calypso variant uploader version: " + version)

  return parser.parse_args()

# Upload the supplied VCF file to Mosaic
def uploadAnnotations(args):
  global mosaicConfig

  # By default overwrite existing annotations with a blank
  allowDeletion = "false" if args.no_deletion else "true"
  api_va.uploadAnnotations(mosaicConfig, args.project_id, args.tsv_file, allowDeletion)

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables. These annotations are in the order they should be output to file
version = "0.0.2"
mosaicConfig = {}

if __name__ == "__main__":
  main()
