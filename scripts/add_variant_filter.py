#!/usr/bin/python

from __future__ import print_function
from os.path import exists

import os
import math
import argparse
import json
from random import random

def main():

  # Parse the command line
  args = parseCommandLine()

  # Parse the config file, if supplied
  if args.config: parseConfig(args)

  # Check that the token, url, and api commands directory are set
  checkCommands(args)

  # Build the command to create a variant filter
  buildFilter(args)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Arguments related to the config file
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "A config file containing token / url information")
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic curl commands, up to an including \"api\". Do NOT include a trailing /")

  # The project id to which the filter is to be added is required
  parser.add_argument('--project', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")

  # Arguments related to the variant filter
  parser.add_argument('--name', '-n', required = True, metavar = "string", help = "The name to give to the saved filter")
  parser.add_argument('--filters', '-f', required = True, metavar = "string", help = "The json containing the required filters")

  return parser.parse_args()

# Parse the config file, if supplied
def parseConfig(args):
  global apiUrl
  global token

  # Check that the config file exists
  if not exists(args.config):
    print("Config file does not exist")
    exit(1)

  # Parse the file and extract recognised fields
  with open(args.config) as configFile:
    for line in configFile:
      if "=" in line:
        argument = line.rstrip().split("=")
 
        # Strip any whitespace from the arguments
        argument[0] = argument[0].strip()
        argument[1] = argument[1].strip()
 
        # Set the recognized values
        if argument[0] == "MOSAIC_TOKEN": token = argument[1]
        if argument[0] == "MOSAIC_URL":
          if argument[1].endswith("/"): apiUrl = argument[1] + "api"
          else: apiUrl = argument[1] + "/api"
        #if argument[0] == "MOSAIC_API_COMMANDS_PATH": apiCommandsPath = argument[1]
        #if argument[0] == "MOSAIC_ATTRIBUTES_PROJECT_ID": attributesProjectId = argument[1]

# Check that the token, url, and api commands directory are set
def checkCommands(args):
  global apiUrl
  global token

  # Explicitly set attributes will overwrite the config file
  if args.token:
    if token:
      print("The token can only be defined once - either in the config file, or on the command line")
      exit(1)
    else: token = args.token
  if args.url:
    if apiUrl:
      print("The url can only be defined once - either in the config file, or on the command line")
      exit(1)
    else:

      # If the url was specified on the command line, make sure it ends with "/api"
      if not args.url.endswith("/api"):
        print("The url must end with \"\\api\"")
        exit(1)
      apiUrl = args.url

#  if args.api_commands:
#    if apiCommandsPath:
#      print("The path to the api commands can only be defined once - either in the config file, or on the command line")
#      exit(1)
#    else: apiCommandsPath = args.api_commands
#  if args.attributesProject:
#    if attributesProjectId:
#      print("The attributes project id can only be defined once - either in the config file, or on the command line")
#      exit(1)
#    else: attributesProjectId = args.attributesProject

  # Check that all required values are set
  if not token:
    print("An access token is required. You can either supply a token with '--token (-t)' or")
    print("supply a config file '--config (-c)' which includes the line:")
    print("  MOSAIC_TOKEN = <TOKEN>")
    exit(1)
  if not apiUrl:
    print("The api url is required. You can either supply the url with '--url (-u)' or")
    print("supply a config file '--config (-c)' which includes the line:")
    print("  MOSAIC_URL = <URL>")
    exit(1)
#  if not apiCommandsPath:
#    print("The path to the directory containing api commands is required. You can either supply the path with '--apiCommands (-s)' or")
#    print("supply a config file '--config (-c)' which includes the line:")
#    print("  MOSAIC_API_COMMANDS_PATH = <PATH>")
#    exit(1)
#  if not attributesProjectId:
#    print("The project id for the attributes project is required. You can either supply the id with '--attributesProject (-a)' or")
#    print("supply a config file '--config (-c)' which includes the line:")
#    print("  MOSAIC_ATTRIBUTES_PROJECT_ID = <ID>")
#    exit(1)

# Build the command to create a variant filter
def buildFilter(args):
  global token
  global apiUrl

  command  = "curl -S -s -X POST -H \"Content-Type: application/json\" -H \"Authorization: Bearer " + token + "\""
  command += " -d '{\"name\": \"" + args.name + "\", \"filter\": "

  # Open the json with the required filters
  try: jsonFile = open(args.filters, "r")
  except: fail("Couldn't open json file: " + args.filters)

  # Parse the json contents
  try: data = json.load(jsonFile)
  except: fail("Could not read contents of json file: " + args.filters + ". Is this a valid json?")
  command += json.dumps(data) + "}' " + apiUrl + "/v1/projects/" + args.project + "/variants/filters"
  execute = json.loads(os.popen(command).read())

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables

# Attributes from the config file
apiUrl              = False
token               = False

if __name__ == "__main__":
  main()
