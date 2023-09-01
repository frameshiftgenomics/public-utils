import os
import argparse

# Standard input options plus any passed from the calling script
def parseCommandLine(args):
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Arguments related to the config file
  parser.add_argument('--config', '-c', required = False, metavar = 'string', help = 'A config file containing token / url information')
  parser.add_argument('--token', '-t', required = False, metavar = 'string', help = 'The Mosaic authorization token')
  parser.add_argument('--url', '-u', required = False, metavar = 'string', help = 'The base url for Mosaic curl commands, up to an including "api". Do NOT include a trailing "')
  parser.add_argument('--attributes_project', '-a', required = False, metavar = 'integer', help = 'The Mosaic project id that contains public attributes')

  # The project id to which the filter is to be added is required
  parser.add_argument('--project_id', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")

  # Loop over the additional arguments and add to the parser
  for arg in args:
    parser.add_argument(arg['long'], arg['short'], required = arg['required'], metavar = arg['metavar'], help = arg['help'])

  return parser.parse_args()

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)
