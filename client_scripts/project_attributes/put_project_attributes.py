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

  # Get the project settings
  isEditable = 'false' if args.is_editable else 'true'
  values = args.predefined_values.split(',') if args.predefined_values else None
  data = project.put_project_attributes(args.attribute_id, description=args.description, name=args.name, predefined_values=values, is_editable=isEditable)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Define the location of the api_client and the ini config file
  parser.add_argument('--client_config', '-c', required = True, metavar = 'string', help = 'The ini config file for Mosaic')
  parser.add_argument('--api_client', '-a', required = True, metavar = 'string', help = 'The api_client directory')

  # The project id to which the filter is to be added is required
  parser.add_argument('--project_id', '-p', required = True, metavar = 'integer', help = 'The Mosaic project id to upload attributes to')
  parser.add_argument('--attribute_id', '-t', required = True, metavar = 'integer', help = 'The Mosaic attribute id to update')

  # Optional arguments to update
  parser.add_argument('--description', '-d', required = False, metavar = 'string', help = 'The attribute description')
  parser.add_argument('--name', '-n', required = False, metavar = 'string', help = 'The name of the attribute')
  parser.add_argument('--is_editable', '-e', required = False, action = 'store_true', help = 'If set, the attribute will not be editable')
  parser.add_argument('--predefined_values', '-r', required = False, metavar = 'string', help = 'A comma separated list of values that will be available by default')

  return parser.parse_args()

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

if __name__ == "__main__":
  main()
