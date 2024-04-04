import os
import argparse

from pprint import pprint
from sys import path

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

  # Set the values to update
  reference = args.reference if args.reference else None
  privacyLevel = args.privacy_level if args.privacy_level else None

  # Update the project settings
  project.put_project_settings(privacy_level=None, reference=None, selected_sample_attribute_chart_data=None, selected_sample_attribute_column_ids=None, selected_variant_annotation_ids=None, sorted_annotations=None, is_template=args.is_template)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Define the location of the api_client and the ini config file
  parser.add_argument('--client_config', '-c', required = True, metavar = 'string', help = 'The ini config file for Mosaic')
  parser.add_argument('--api_client', '-a', required = True, metavar = 'string', help = 'The api_client directory')

  # The project id to which the filter is to be added is required
  parser.add_argument('--project_id', '-p', required = True, metavar = 'integer', help = 'The Mosaic project id to upload attributes to')

  # Optional arguments
  parser.add_argument('--privacy_level', '-l', required = False, metavar = 'string', help = 'The privacy level to assign to the project')
  parser.add_argument('--is_template', '-t', required = False, action='store_true', help = 'The privacy level to assign to the project')
  parser.add_argument('--reference', '-r', required = False, metavar = 'string', help = 'The genome reference to assign to the project')

  return parser.parse_args()

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

if __name__ == "__main__":
  main()
