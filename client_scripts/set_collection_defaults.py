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
  apiMosaic  = Mosaic(config_file = args.config)
  project = apiMosaic.get_project(args.project_id)

  # Check that the json containing the required defaults exists and read in the information
  #if not exists(args.json): fail('Json file (' + str(args.json) + ') does not exist')
  try:
    json_file = open(args.json, 'r')
  except:
    fail('Could not open the json file: ' + str(args.json))
  try:
    json_info = json.load(json_file)
  except:
    fail('Could not read contents of json file ' + str(args.json) + '. Check that this is a valid json')
  json_file.close()

  # Check if this is a collection
  data = project.get_project()
  if not data['is_collection']:
    fail('Supplied project id (' + args.project_id + ') is for a project, not a collection')

  # Get all the sample attributes in the project
  sample_attributes = {}
  for sample_attribute in project.get_sample_attributes():
    sample_attributes[sample_attribute['uid']] = sample_attribute['id']

  # Get all the annotations in the project
  annotations = {}
  for annotation in project.get_variant_annotations():
    annotations[annotation['uid']] = annotation['id']

  # Set the analytics default charts


  # Set the samples table defaults
  #samples_table_columns = json_info['sample_table'] if 'sample_table' in json_info else []
  samples_table_columns = []
  if 'sample_table' in json_info:
    for uid in json_info['sample_table']:
      if uid not in sample_attributes:
        fail('Sample table defaults includes a sample attribute that is not available: ' + uid)
      samples_table_columns.append(sample_attributes[uid])

  # Set the variants table defaults. The json file can include both annotation versions, or just annotation ids. If
  # annotation ids are provided, use the latest version
  annotation_version_ids = []
  annotations_to_import = False
  if 'annotations'in json_info:
    for uid in json_info['annotations']:

      # If the uid does not correspond to an annotation in the project it will need to be imported
      if uid not in annotations:

        # If annotations_to_import doesn't exist, get all the annotations that can be imported.
        # We only call this route if it's required, but once it exists, get the id of the annotation
        # that has been specified and import it
        if not annotations_to_import:
          annotations_to_import = {}
          for annotation in project.get_variant_annotations_to_import():
            annotations_to_import[annotation['uid']] = annotation['id']

        # Get the id of the annotation to import and import it
        annotation_id = annotations_to_import[uid]
        project.post_import_annotation(annotation_id)

      # Otherwise, just get the annotation id for the annotation in the project
      else:
        annotation_id = annotations[uid]

      # Find the latest version for this annotation
      annotation_version_id = False
      for annotation_version in project.get_variant_annotation_versions(annotation_id):
        if not annotation_version_id:
          annotation_version_id = annotation_version['id']
        elif annotation_version['id'] > annotation_version_id:
          annotation_version_id = annotation_version['id']

      # Store the annotation version id
      annotation_version_ids.append(annotation_version_id)

  if 'annotation_versions' in json_info:
    annotation_version_ids = annotation_version_ids + json_info['annotation_versions']

  # Set the variant watchlist annotation defaults
  watchlist = []
#  if 'watchlist_annotations' not in json_info:
#    warning('No information on the pinned Variants table annotations - defaults will not be set')
#  else:
#    watchlist = json_info['watchlist_annotations']

  # Set the project settings
  data = project.put_project_settings(selected_sample_attribute_column_ids = samples_table_columns, \
         selected_variant_annotation_version_ids = annotation_version_ids, \
         default_variant_set_annotation_ids = watchlist)
  
#    # Get the id of the variant watchlist
#    watchlist_id = False
#    for variant_set in project.get_variant_sets():
#      if variant_set['name'] == 'Variant Watchlist':
#        watchlist_id = variant_set['id']
#        break
#    if watchlist_id:
#      project.post_project_dashboard(dashboard_type = 'variant_set', is_active = 'true', variant_set_id = watchlist_id)

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
