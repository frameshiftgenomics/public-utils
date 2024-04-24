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

  # Upload the variants
  notifications = 'false' if args.enable_notifications else 'true'
  data = project.post_variant_file(args.vcf, upload_type = args.method, disable_successful_notification = notifications)
  print(data['message'], '. Variant upload job id: ', data['redis_job_id'], sep = '')

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Define the location of the api_client and the ini config file
  parser.add_argument('--client_config', '-c', required = True, metavar = 'string', help = 'The ini config file for Mosaic')
  parser.add_argument('--api_client', '-a', required = True, metavar = 'string', help = 'The api_client directory')

  # The project id to which the filter is to be added is required
  parser.add_argument('--project_id', '-p', required = True, metavar = 'integer', help = 'The Mosaic project id to add variant filters to')

  # Additional arguments
  parser.add_argument('--method', '-m', required = True, metavar = 'string', help = 'The variant upload method: "allele, no-validation, position"')
  parser.add_argument('--vcf', '-v', required = True, metavar = 'string', help = 'The vcf file to upload variants from')
  parser.add_argument('--enable_notifications', '-e', required = False, action = 'store_true', help = 'If set, notifications will be provided. Otherwise, notifications will only be provided for failures')

  return parser.parse_args()

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

if __name__ == "__main__":
  main()
