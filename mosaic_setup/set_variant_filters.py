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
  # description will contain terms like "Proband": "alt". Therefore, the term Proband needs to be converted to a Mosaic sample id
  samples = sam.getMosaicSamples(mosaicConfig, api_s, api_sa, args.project_id)
  proband = sam.getProband(mosaicConfig, samples)

  # Get all of the annotations in the current project. When creating a filter, the project will be checked to ensure that it has all of the
  # required annotations before creating the filter
  annotations    = {}
  annotationUids = {}
  data           = api_va.getAnnotations(mosaicConfig, args.project_id)
  for annotation in data: annotations[annotation['name']] = {'id': annotation['id'], 'uid': annotation['uid'], 'type': annotation['type']}
  for annotation in annotations: annotationUids[annotations[annotation]['uid']] = {'name': annotation, 'type': annotations[annotation]['type']}

  # Determine all of the variant filters that are to be added; remove any filters that already exist with the same name; fill out variant
  # filter details not in the json (e.g. the uids of private annotations); create the filters; and finally update the project settings to
  # put the filters in the correct category and sort order. Note that the filters to be applied depend on the family structure. E.g. de novo
  # filters won't be added to projects without parents
  sampleMap                 = vFilters.createSampleMap(samples)
  annotationMap             = vFilters.createAnnotationMap(annotations)
  filtersInfo               = vFilters.readVariantFiltersJson(args.variant_filters)
  filterCategories, filters = vFilters.getFilterCategories(filtersInfo)
  filters                   = vFilters.getFilters(filtersInfo, filterCategories, filters, samples, sampleMap, annotations, annotationMap, annotationUids)

  # Get all of the filters that exist in the project, and check which of these share a name with a filter to be created
  vFilters.deleteFilters(mosaicConfig, api_vf, args.project_id, filters)

  # Create all the required filters and update their categories and sort order in the project settings
  vFilters.createFilters(mosaicConfig, api_ps, api_vf, args.project_id, annotations, filterCategories, filters)

# Input options
def parseCommandLine():
  global version
  parser = argparse.ArgumentParser(description='Process the command line')

  # Required arguments
  #parser.add_argument('--data_directory', '-d', required = True, metavar = 'string', help = 'The path to the directory where the resources live')
  #parser.add_argument('--tools_directory', '-s', required = False, metavar = 'string', help = 'The path to the directory where the tools to use live')
  #parser.add_argument('--utils_directory', '-l', required = True, metavar = 'string', help = 'The path to the public-utils directory')
  #parser.add_argument('--input_vcf', '-i', required = False, metavar = 'string', help = 'The input vcf file to annotate')
  #parser.add_argument('--ped', '-e', required = False, metavar = 'string', help = 'The pedigree file for the family. Not required for singletons')
  parser.add_argument('--project_id', '-p', required = True, metavar = 'string', help = 'The project id that variants will be uploaded to')
  parser.add_argument('--config', '-c', required = True, metavar = 'string', help = 'The config file for Mosaic')
  parser.add_argument('--variant_filters', '-f', required = True, metavar = 'string', help = 'The json file describing the variant filters to apply to each project')

  # Optional pipeline arguments
  #parser.add_argument('--reference', '-r', required = False, metavar = 'string', help = 'The reference genome to use. Allowed values: ' + ', '.join(allowedReferences))
  #parser.add_argument('--resource_json', '-j', required = False, metavar = 'string', help = 'The json file describing the annotation resources')
#  parser.add_argument('--no_comp_het', '-n', required = False, action = "store_true", help = "If set, comp het determination will be skipped")

  # Optional argument to handle HPO terms
  #parser.add_argument('--hpo', '-o', required = False, metavar = "string", help = "A comma separate list of hpo ids for the proband")

  # Optional mosaic arguments
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic")
  parser.add_argument('--attributes_project', '-a', required = False, metavar = "integer", help = "The Mosaic project id that contains public attributes")
  #parser.add_argument('--mosaic_json', '-m', required = False, metavar = 'string', help = 'The json file describing the Mosaic parameters')

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
