import os
import argparse
import json
import sys

from os.path import exists
from pprint import pprint
from sys import path

def main():
  global version

  # Parse the command line
  args = parseCommandLine()

  # Import the api client
  path.append(args.api_client)
  from mosaic import Mosaic, Project, Store
  store   = Store(config_file = args.config)
  mosaic  = Mosaic(config_file = args.config)
  project = mosaic.get_project(args.project_id)

  # Check that the json containing the required defaults exists and read in the information
  #if not exists(args.json): fail('Json file (' + str(args.json) + ') does not exist')
  try: jsonFile = open(args.json, 'r')
  except: fail('Could not open the json file: ' + str(args.json))
  try: jsonInfo = json.load(jsonFile)
  except: fail('Could not read contents of json file ' + str(args.json) + '. Check that this is a valid json')
  jsonFile.close()

  # Set the analytics default charts

  # Set the samples table defaults
  samplesTableColumns = []
  if 'sample_table' not in jsonInfo: warning('No information on the Samples table - defaults will not be set')
  else: samplesTableColumns = jsonInfo['sample_table']

  # Set the variants table defaults
  variantAnnotations = []
  if 'annotations' not in jsonInfo: warning('No information on the Variants table annotations - defaults will not be set')
  else: variantAnnotations = jsonInfo['annotations']

  # Set the variant watchlist annotation defaults
  watchlist = []
  if 'watchlist_annotations' not in jsonInfo: warning('No information on the pinned Variants table annotations - defaults will not be set')
  else: watchlist = jsonInfo['watchlist_annotations']

  # Set the project settings
  data = project.put_project_settings(selected_sample_attribute_column_ids = samplesTableColumns, selected_variant_annotation_ids = variantAnnotations, default_variant_set_annotation_ids = watchlist)

  # Get the id of the variant watchlist
  watchlistId = False
  for variantSet in project.get_variant_sets():
    if variantSet['name'] == 'Variant Watchlist':
      watchlistId = variantSet['id']
      break
  if watchlistId: project.post_project_dashboard(dashboard_type = 'variant_set', is_active = 'true', variant_set_id = watchlistId)

# Input options
def parseCommandLine():
  global version
  parser = argparse.ArgumentParser(description='Process the command line')

  # Required arguments
  parser.add_argument('--config', '-c', required = True, metavar = 'string', help = 'The config file for Mosaic')
  parser.add_argument('--api_client', '-a', required = True, metavar = 'string', help = 'The directory where the Python api wrapper lives')

  # Optional pipeline arguments
  parser.add_argument('--json', '-j', required = True, metavar = 'string', help = 'The json file describing the project defaults')

  # The project id to which the filter is to be added is required
  parser.add_argument('--project_id', '-p', required = True, metavar = 'integer', help = 'The Mosaic project id to upload attributes to')

  # Version
  parser.add_argument('--version', '-v', action="version", version='Calypso annotation pipeline version: ' + str(version))

  return parser.parse_args()

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = '')
  exit(1)

# Throw a warning
def warning(message):
  print('WARNING: ', message, sep = '')

# Initialise global variables

# Pipeline version
version = "0.0.1"

if __name__ == "__main__":
  main()
