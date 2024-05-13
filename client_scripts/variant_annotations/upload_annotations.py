import os
import argparse

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

  # Upload the variant annotations
  allow_deletion = 'true' if args.allow_deletion else 'false'
  disable_successful_notification = 'true' if args.disable_successful_notification else 'false'
  data = project.post_annotation_file(args.tsv, allow_deletion = allow_deletion, disable_successful_notification = disable_successful_notification)
  print(data['message'], '. Annotation upload job id: ', data['redis_job_id'], ', file: ', args.tsv, sep = '')

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Define the location of the api_client and the ini config file
  parser.add_argument('--client_config', '-c', required = True, metavar = 'string', help = 'The ini config file for Mosaic')
  parser.add_argument('--api_client', '-a', required = True, metavar = 'string', help = 'The api_client directory')

  # The project id to which the filter is to be added is required
  parser.add_argument('--project_id', '-p', required = True, metavar = 'integer', help = 'The Mosaic project id to add variant filters to')

  # Additional arguments
  parser.add_argument('--tsv', '-t', required = True, metavar = 'string', help = 'The annotation tsv file to upload')
  parser.add_argument('--allow_deletion', '-d', required = False, action = 'store_true', help = 'If tsv file contains blank annotation, overwrite the existing value in the database will null. Default: false')
  parser.add_argument('--disable_successful_notification', '-n', required = False, action = 'store_false', help = 'Only send notifications if the upload fails. Default: true')

  return parser.parse_args()

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

if __name__ == "__main__":
  main()
