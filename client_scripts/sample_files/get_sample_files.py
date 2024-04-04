import os
import argparse

from sys import path

def main():

  # Parse the command line
  args = parseCommandLine()
  if not args.write_info: args.write_info = 1

  # Import the api client
  path.append(args.api_client)
  from mosaic import Mosaic, Project, Store
  apiStore  = Store(config_file = args.client_config)
  apiMosaic = Mosaic(config_file = args.client_config)

  # Open an api client project object for the defined project
  project = apiMosaic.get_project(args.project_id)

  # Get all of the sample files
  sampleFileGenerator = project.get_sample_files(args.sample_id)
  for sample in sampleFileGenerator:
    if int(args.write_info) == 1: print(sample['name'], ': ', sample['id'], ', ', sample['type'], sep = '')
    elif int(args.write_info) == 2:
      print(sample['name'])
      print('  ', sample['id'], sep = '')
      print('  ', sample['type'], sep = '')
      print('  ', sample['uri'], sep = '')

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Define the location of the api_client and the ini config file
  parser.add_argument('--client_config', '-c', required = True, metavar = 'string', help = 'The ini config file for Mosaic')
  parser.add_argument('--api_client', '-a', required = True, metavar = 'string', help = 'The api_client directory')

  # The project id to which the filter is to be added is required
  parser.add_argument('--project_id', '-p', required = True, metavar = 'integer', help = 'The Mosaic project id to upload attributes to')

  # Arguments related to the file to add
  parser.add_argument('--sample_id', '-s', required = True, metavar = 'string', help = 'The sample id the file is attached to')

  # Determine what information to print to screen
  parser.add_argument('--write_info', '-w', required = False, metavar = 'integer', help = 'What information should be written to screen:')

  return parser.parse_args()

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

if __name__ == "__main__":
  main()
