import argparse
import json
import os

from sys import path

def main():

  # Parse the command line
  args = parseCommandLine()

  # Import the api client
  path.append(args.api_client)
  from mosaic import Mosaic, Project, Store
  apiStore  = Store(config_file = args.client_config)
  apiMosaic = Mosaic(config_file = args.client_config)

  # Build the json object
  attributesJson = []
  if args.required_attributes:
    attributes = args.required_attributes.split(',')
    for attributeId in attributes: attributesJson.append({'attribute_id': int(attributeId), 'type': 'required'})
  if args.suggested_attributes:
    attributes = args.suggested_attributes.split(',')
    for attributeId in attributes: attributesJson.append({'attribute_id': int(attributeId), 'type': 'suggested'})
  if args.optional_attributes:
    attributes = args.optional_attributes.split(',')
    for attributeId in attributes: attributesJson.append({'attribute_id': int(attributeId), 'type': 'optional'})

  if len(attributesJson) == 0:
    print('WARNING: No attributes added - no attribute form created')
    exit(0)

  # Post an attribute form
  data = apiMosaic.post_attribute_form(name = args.name, attributes = attributesJson)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Define the location of the api_client and the ini config file
  parser.add_argument('--client_config', '-c', required = True, metavar = 'string', help = 'The ini config file for Mosaic')
  parser.add_argument('--api_client', '-a', required = True, metavar = 'string', help = 'The api_client directory')

  # Required arguments
  parser.add_argument('--name', '-n', required = True, metavar = 'string', help = 'The name of the attribute form')

  # Optional arguments
  parser.add_argument('--required_attributes', '-r', required = False, metavar = 'string', help = 'A comma separated list of the ids of all required attributes')
  parser.add_argument('--suggested_attributes', '-s', required = False, metavar = 'string', help = 'A comma separated list of the ids of all suggested attributes')
  parser.add_argument('--optional_attributes', '-o', required = False, metavar = 'string', help = 'A comma separated list of the ids of all optional attributes')

  return parser.parse_args()

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

if __name__ == "__main__":
  main()
