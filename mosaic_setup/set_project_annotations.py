from __future__ import print_function

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
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/api_commands")
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/common_components")
import annotations_json as ann
import mosaic_config

import api_variant_annotations as api_va

def main():
  global mosaicConfig
  global workingDir
  global version
  global allowedReferences

  # Parse the command line
  args = parseCommandLine()

  # Parse the Mosaic config file to get the token and url for the api calls
  mosaicRequired = {'MOSAIC_TOKEN': {'value': args.token, 'desc': 'An access token', 'long': '--token', 'short': '-t'},
                    'MOSAIC_URL': {'value': args.url, 'desc': 'The api url', 'long': '--url', 'short': '-u'},
                    'MOSAIC_ATTRIBUTES_PROJECT_ID': {'value': args.attributes_project, 'desc': 'The public attribtes project id', 'long': '--attributes_project', 'short': '-a'}}
  mosaicConfig   = mosaic_config.mosaicConfigFile(args.config)
  mosaicConfig   = mosaic_config.commandLineArguments(mosaicConfig, mosaicRequired)

  # Get the project reference
  #if args.reference not in allowedReferences: fail('The specified reference (' + str(args.reference) + ') is not recognised. Allowed values are: ' + str(', '.join(allowedReferences)))
  #print('  Using the reference: ', args.reference, sep = '')

  # Read the resources json file to identify all the resources that will be used in the annotation pipeline
  #resourceInfo = res.checkResources(args.reference, args.data_directory, args.tools_directory, args.resource_json)
  #else: resourceInfo = res.checkResources(args.reference, args.data_directory, args.tools_directory, args.data_directory + 'resources_' + str(args.reference) + '.json')
  #resourceInfo = res.readResources(args.reference, rootPath, resourceInfo)

  # Define the tools to be used by Calypso
  #resourceInfo = res.calypsoTools(resourceInfo)

  # Define paths to be used by Calypso
  #setWorkingDir(resourceInfo['version'])

  # Get all the available public project attributes
  #publicAttributes = {}
  #data             = api_pa.getPublicProjectAttributesNameIdUid(mosaicConfig)
  #for record in data: publicAttributes[record['uid']] = {'name': record['name'], 'id': record['id']}

  # Read the Mosaic json and validate its contents
  annotationsInfo   = ann.readAnnotationsJson(args.json)

  # Get all the public annotations in the Mosaic Public Attributes project
  publicAnnotations = api_va.getVariantAnnotationsImportName(mosaicConfig, mosaicConfig['MOSAIC_ATTRIBUTES_PROJECT_ID'])

  # Determine which of the annotations in the json need to be created, updated, or already exist
  ann.annotationStatus(mosaicConfig, api_va, annotationsInfo, publicAnnotations)

  #mosr.createPublicAnnotations(mosaicConfig, api_va, mosaicInfo['resources'], publicAnnotations)

# Input options
def parseCommandLine():
  global version
  parser = argparse.ArgumentParser(description='Process the command line')

  # Required arguments
  #parser.add_argument('--data_directory', '-d', required = True, metavar = 'string', help = 'The path to the directory where the resources live')
  #parser.add_argument('--tools_directory', '-s', required = False, metavar = 'string', help = 'The path to the directory where the tools to use live')
  #parser.add_argument('--utils_directory', '-l', required = True, metavar = 'string', help = 'The path to the public-utils directory')
  parser.add_argument('--config', '-c', required = True, metavar = "string", help = "The config file for Mosaic")

  # Optional pipeline arguments
  #parser.add_argument('--reference', '-r', required = True, metavar = 'string', help = 'The reference genome to use. Allowed values: ' + ', '.join(allowedReferences))
  parser.add_argument('--json', '-j', required = True, metavar = 'string', help = 'The json file describing the annotation resources')

  # Optional mosaic arguments
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic")
  parser.add_argument('--attributes_project', '-a', required = False, metavar = "integer", help = "The Mosaic project id that contains public attributes")
  #parser.add_argument('--mosaic_json', '-m', required = False, metavar = 'string', help = 'The json file describing the Mosaic parameters')

  # Version
  parser.add_argument('--version', '-v', action="version", version='Calypso annotation pipeline version: ' + str(version))

  return parser.parse_args()

# Create a directory where all Calypso associated files will be stored
def setWorkingDir(version):
  global workingDir

  workingDir += version + "/"

  # If the directory doesn't exist, create it
  if not os.path.exists(workingDir): os.makedirs(workingDir)

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables

# Pipeline version
version = "1.1.5"
date    = str(date.today())

# The working directory where all created files are kept
workingDir = os.getcwd() + "/calypso_v" + version + "r"

# Store information related to Mosaic
mosaicConfig = {}

# Store the allowed references that can be specified on the command line
allowedReferences = ['GRCh37', 'GRCh38']

if __name__ == "__main__":
  main()
