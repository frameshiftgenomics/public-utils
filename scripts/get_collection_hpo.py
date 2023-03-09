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
import api_sample_hpo_terms as api_hpo

def main():
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {'MOSAIC_TOKEN': {'value': args.token, 'desc': 'An access token', 'long': '--token', 'short': '-t'},
                    'MOSAIC_URL': {'value': args.url, 'desc': 'The api url', 'long': '--url', 'short': '-u'}}
  mosaicConfig   = mosaic_config.mosaicConfigFile(args.config)
  mosaicConfig   = mosaic_config.commandLineArguments(mosaicConfig, mosaicRequired)

  # Get all the project id
  projectIds = api_p.getCollectionProjectsDictIdName(mosaicConfig, args.collection_id)

  # Get the HPO terms for each project
  hpoTerms   = {}
  termCounts = {}
  for projectId in projectIds:
    projectTerms = api_hpo.getProjectHpo(mosaicConfig, projectId)
    for sampleId in projectTerms:
      for term in projectTerms[sampleId]:
        if term['label'] not in hpoTerms: hpoTerms[term['label']] = [projectIds[projectId]]
        else: hpoTerms[term['label']].append(projectIds[projectId])

        # Keep count of how often terms are seen
        if term['label'] not in termCounts: termCounts[term['label']] = 1
        else: termCounts[term['label']] += 1

  # Print out count information
  temp         = sorted(termCounts.items(), key=lambda x:x[1], reverse = True)
  sortedCounts = dict(temp)
  for label in sortedCounts: print(label, sortedCounts[label])
  print()

  # Print out info or return projects with the desired term
  if args.hpo_label:
    foundTerm = False
    for label in hpoTerms:
      if str(label) == args.hpo_label:
        print('The following projects contain the HPO term "' + str(label) + '"')
        for project in hpoTerms[label]: print(project)
        foundTerm = True
        break
    if not foundTerm: print('Term "' + str(args.hpo_label) + '" was not found in this collection')
  else:
    for label in hpoTerms: print(label, hpoTerms[label])

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Arguments related to the config file
  parser.add_argument('--token', '-t', required = False, metavar = 'string', help = 'The Mosaic authorization token')
  parser.add_argument('--url', '-u', required = False, metavar = 'string', help = 'The base url for Mosaic curl commands, up to an including "api". Do NOT include a trailing ')
  parser.add_argument('--config', '-c', required = False, metavar = 'string', help = 'A config file containing token / url information')

  # The attribute id to get information on
  parser.add_argument('--collection_id', '-d', required = True, metavar = 'integer', help = 'The collection id to get hpo terms from')

  # The HPO label to search for
  parser.add_argument('--hpo_label', '-l', required = False, metavar = 'string', help = 'If set, only projects with this term will be returned')

  return parser.parse_args()

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
