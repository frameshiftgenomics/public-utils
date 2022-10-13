#!/usr/bin/python

from __future__ import print_function
from os.path import exists

import os
import math
import argparse
import json
from random import random

from sys import path
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/api_commands")
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/common_components")
import mosaic_config
import api_project_attributes as api_pa
import api_project_intervals as api_pi

def main():
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {"token": True, "url": True, "attributesProjectId": False}
  mosaicConfig   = mosaic_config.parseConfig(args, mosaicRequired)

  # If project ids aren't provided, get all project attributes from the project and display
  if not args.interval: getIntervals(args)

  # Create the interval
  deleteInterval(args)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Arguments related to the config file
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "A config file containing token / url information")
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic curl commands, up to an including \"api\". Do NOT include a trailing /")

  # The project id to which the filter is to be added is required
  parser.add_argument('--project', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")

  # Arguments related to the event
  parser.add_argument('--interval', '-i', required = False, metavar = "string", help = "The project interval attribute id to be deleted")

  return parser.parse_args()

# Get all the project attributes for the project
def getIntervals(args):
  global mosaicConfig

  # Get all of the project attributes
  data = json.loads(os.popen(api_pi.getProjectIntervalAttributes(mosaicConfig, args.project)).read())

  # Loop over all attributes and output the applicable attribute (e.g. timestamps)
  print("Available intervals:")
  for attribute in data:
    print("  ", attribute['name'], ": ", attribute['id'], sep = "")
  exit(0)

# Delete the interval
def deleteInterval(args):
  global mosaicConfig

  try: data = os.popen(api_pi.deleteProjectIntervalAttribute(mosaicConfig, args.interval, args.project)).read()
  except: fail("Couldn't delete interval")

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables
mosaicConfig = {}

if __name__ == "__main__":
  main()
