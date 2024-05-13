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

  # Import tha annotation
  data = project.put_variant_annotation(args.annotation_id, name = args.name, value_type = args.type, privacy_level = args.privacy_level, display_type = args.display_type, severity = args.severity, category = args.category, value_truncate_type = args.value_truncate_type, value_max_length = args.value_max_length)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Define the location of the api_client and the ini config file
  parser.add_argument('--client_config', '-c', required = True, metavar = 'string', help = 'The ini config file for Mosaic')
  parser.add_argument('--api_client', '-a', required = True, metavar = 'string', help = 'The api_client directory')

  # The project id to which the filter is to be added is required
  parser.add_argument('--project_id', '-p', required = True, metavar = 'integer', help = 'The Mosaic project id to upload attributes to')

  # The annotation id to update
  parser.add_argument('--annotation_id', '-i', required = True, metavar = 'integer', help = 'The Mosaic annotation id to import')

  # Optional values to update
  parser.add_argument('--name', '-n', required = False, metavar = 'string', help = 'The name of the annotation')
  parser.add_argument('--type', '-t', required = False, metavar = 'string', help = 'The type of the annotation')
  parser.add_argument('--privacy_level', '-l', required = False, metavar = 'string', help = 'The privacy level of the annotation')
  parser.add_argument('--display_type', '-d', required = False, metavar = 'string', help = 'The display type of the annotation')
  parser.add_argument('--severity', '-s', required = False, metavar = 'string', help = 'The severity of the annotation')
  parser.add_argument('--category', '-g', required = False, metavar = 'string', help = 'The category of the annotation')
  parser.add_argument('--value_truncate_type', '-v', required = False, metavar = 'string', help = 'The method of truncating the annotation values')
  parser.add_argument('--value_max_length', '-m', required = False, metavar = 'string', help = 'The max length of the of the annotation values')

  return parser.parse_args()

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

if __name__ == "__main__":
  main()
