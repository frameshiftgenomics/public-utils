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
  for attribute in project.get_project_attributes():
    print(attribute['name'], ' (id: ', attribute['id'], ')', sep = '')
    if attribute['description']: print('  description: ', attribute['description'], sep = '')
    print('    uid: ', attribute['uid'], sep = '')
    print('    value_type: ', attribute['value_type'], sep = '')
    print('    original_project_id: ', attribute['original_project_id'], sep = '')
    print('    is_custom: ', attribute['is_custom'], sep = '')
    print('    is_editable: ', attribute['is_editable'], sep = '')
    print('    is_public: ', attribute['is_public'], sep = '')
    if attribute['predefined_values']:
      print('    predefined_values:')
      for value in attribute['predefined_values']: print('      ', value, sep = '')
    if attribute['source']: print('    source: ', attribute['source'], sep = '')
    if attribute['start_attribute_id']: print('    Start id: ', attribute['start_attribute_id'], ', End id: ', attribute['end_attribute_id'], sep = '')
    print('    created_at: ', attribute['created_at'], ', updated_at: ', attribute['updated_at'], sep = '')

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Define the location of the api_client and the ini config file
  parser.add_argument('--client_config', '-c', required = True, metavar = 'string', help = 'The ini config file for Mosaic')
  parser.add_argument('--api_client', '-a', required = True, metavar = 'string', help = 'The api_client directory')

  # The project id to which the filter is to be added is required
  parser.add_argument('--project_id', '-p', required = True, metavar = 'integer', help = 'The Mosaic project id to upload attributes to')

  return parser.parse_args()

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

if __name__ == "__main__":
  main()
