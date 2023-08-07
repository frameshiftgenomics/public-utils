import os
import argparse
import json
import math
import glob
import importlib
import sys

from datetime import date
from os.path import exists
from sys import path

# Add the path of the common functions and import them
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/common_components")
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/api_commands")
import mosaic_config
import mosaic_samples as sam
import variant_filters as vFilters
import api_project_settings as api_ps
import api_samples as api_s
import api_sample_attributes as api_sa
import api_variant_annotations as api_va
import api_variant_filters as api_vf

def main():
  global mosaicConfig
  global workingDir
  global version

  # Parse the command line
  args = parseCommandLine()

  # Parse the Mosaic config file to get the token and url for the api calls
  mosaicRequired = {'MOSAIC_TOKEN': {'value': args.token, 'desc': 'An access token', 'long': '--token', 'short': '-t'},
                    'MOSAIC_URL': {'value': args.url, 'desc': 'The api url', 'long': '--url', 'short': '-u'},
                    'MOSAIC_ATTRIBUTES_PROJECT_ID': {'value': args.attributes_project, 'desc': 'The public attribtes project id', 'long': '--attributes_project', 'short': '-a'}}
  mosaicConfig   = mosaic_config.mosaicConfigFile(args.config)
  mosaicConfig   = mosaic_config.commandLineArguments(mosaicConfig, mosaicRequired)

  # Get information on the sample available in the Mosaic project. Some variant filters require filtering on genotype. The variant filter
  # description will contain terms like "Proband": "alt". Therefore, the term Proband needs to be converted to a Mosaic sample id. If
  # ggenotype based filters are being omitted, this can be skipped
  samples = {}
  proband = False
  if not args.no_genotype_filters: 
    samples = sam.getMosaicSamples(mosaicConfig, api_s, api_sa, args.project_id)
    proband = sam.getProband(mosaicConfig, samples)

  # Set up the filters
  vFilters.setVariantFilters(mosaicConfig, api_ps, api_va, api_vf, args.project_id, args.variant_filters, samples)

# Input options
def parseCommandLine():
  global version
  parser = argparse.ArgumentParser(description='Process the command line')

  # Required arguments
  parser.add_argument('--project_id', '-p', required = True, metavar = 'string', help = 'The project id that variants will be uploaded to')
  parser.add_argument('--config', '-c', required = True, metavar = 'string', help = 'The config file for Mosaic')
  parser.add_argument('--variant_filters', '-f', required = True, metavar = 'string', help = 'The json file describing the variant filters to apply to each project')

  # Optional mosaic arguments
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic")
  parser.add_argument('--attributes_project', '-a', required = False, metavar = "integer", help = "The Mosaic project id that contains public attributes")
  parser.add_argument('--no_genotype_filters', '-n', required = False, action = "store_true", help = 'If set, all filters that include genotypes will be omitted')

  # Version
  parser.add_argument('--version', '-v', action="version", version='Calypso annotation pipeline version: ' + str(version))

  return parser.parse_args()

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables

# Pipeline version
version = "1.1.5"
date    = str(date.today())

# Store information related to Mosaic
mosaicConfig = {}

if __name__ == "__main__":
  main()
