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
import api_projects as api_p

def main():
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {"token": True, "url": True, "attributesProjectId": False}
  mosaicConfig   = mosaic_config.parseConfig(args, mosaicRequired)

  # Get the project roles
  getId(args)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Arguments related to the config file
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "A config file containing token / url information")
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic curl commands, up to an including \"api\". Do NOT include a trailing /")

  # The project name to fild the id for
  parser.add_argument('--project_name', '-n', required = True, metavar = 'integer', help = 'The Mosaic project name to get the id for')

  return parser.parse_args()

# Get the project Id
def getId(args):
  global mosaicConfig
  limit = 100
  page  = 1
  noMatches = 0
  projectId = False

  # Get the project reference
  try: data = json.loads(os.popen(api_p.getProjects(mosaicConfig, limit, page)).read())
  except: fail('Could not get projects information')

  # Loop over the projects
  for project in data['data']:
    if project['name'].startswith(args.project_name):
      noMatches += 1
      projectId  = project['id']

  # Loop over all pages of projects
  noPages = int(math.ceil(float(data['count']) / float(limit)))

  # Loop over all necessary pages
  for i in range(2, noPages + 1):
    try: data = json.loads(os.popen(api_p.getProjects(mosaicConfig, limit, i)).read())
    except: fail('Could not get projects information')

    # Loop over the projects
    for project in data['data']:
      if project['name'].startswith(args.project_name):
        noMatches += 1
        projectId  = project['id']

  # If there are multiple results or no results, fail
  if noMatches == 0: fail('No projects found starting with ' + str(args.project_name))
  elif noMatches > 1: fail('Multiple projects found starting with ' + str(args.project_name))
  else: print(projectId)

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables
mosaicConfig = {}

# Attributes from the config file
apiUrl              = False
token               = False

if __name__ == "__main__":
  main()
