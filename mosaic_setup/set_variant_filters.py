import os
import argparse
import json
import math
import glob
import importlib
import sys

from os.path import exists
from sys import path

# Add the path of the common functions and import them
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/common_components")
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/api_commands")
import variant_filters2 as vFilters

def main():

  # Parse the command line
  args = parseCommandLine()

  # Import the api client
  path.append(args.api_client)
  from mosaic import Mosaic, Project, Store
  apiStore  = Store(config_file = args.client_config)
  apiMosaic = Mosaic(config_file = args.client_config)

  # Open an api client project object for the defined project
  project = apiMosaic.get_project(args.project_id)

  # Get information on the sample available in the Mosaic project. Some variant filters require filtering on genotype. The variant filter
  # description will contain terms like "Proband": "alt". Therefore, the term Proband needs to be converted to a Mosaic sample id. If
  # genotype based filters are being omitted, this can be skipped
  samples    = {}
  hasProband = False
  proband    = False
  if not args.no_genotype_filters: 
    samples = {}
    for sample in project.get_samples():
      samples[sample['name']] = {'id': sample['id'], 'relation': False}
      for attribute in project.get_attributes_for_sample(sample['id']):
        if attribute['uid'] == 'relation':
          for value in attribute['values']:
            if value['sample_id'] == sample['id']:
              samples[sample['name']]['relation'] = value['value']
              if value['value'] == 'Proband':
                if hasProband: fail('Multiple samples in the Mosaic project are listed as the proband')
                hasProband = True
                proband    = sample['name']
              break

  # Set up the filters
  vFilters.setVariantFilters(args.project_id, args.variant_filters, project, samples, proband)

# Input options
def parseCommandLine():
  global version
  parser = argparse.ArgumentParser(description='Process the command line')

  # Required arguments
  parser.add_argument('--client_config', '-c', required = True, metavar = 'string', help = 'The ini config file for Mosaic')
  parser.add_argument('--api_client', '-a', required = True, metavar = 'string', help = 'The api_client directory')
  parser.add_argument('--project_id', '-p', required = True, metavar = 'string', help = 'The project id that variants will be uploaded to')
  parser.add_argument('--variant_filters', '-f', required = True, metavar = 'string', help = 'The json file describing the variant filters to apply to each project')

  # Optional mosaic arguments
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
version = "1.1.6"

if __name__ == "__main__":
  main()
