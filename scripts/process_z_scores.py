#!/usr/bin/python

from __future__ import print_function
from os.path import exists
from random import random

import argparse
import json
import math
import os
import statistics

from sys import path
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/api_commands")
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/common_components")
import mosaic_config
import api_sample_attributes as api_sa
import api_samples as api_s
import api_projects as api_p

def main():
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {"token": True, "url": True, "attributesProjectId": False}
  mosaicConfig   = mosaic_config.parseConfig(args, mosaicRequired)

  # Get a list of all projects in the collection, If this is not a collection, fail
  projects = getSubProjects(args)

  # If no attribute id to generate z-scores for was provided, get all the sample attributes in the supplied project, otherwise
  # check the Z-score attribute id belongs to a Z-score attributes, collect the values for all samples in the project, and update
  # the values
  if not args.attribute_id or not args.z_score_id: getSampleAttributes(args)
  checkZScoreId(args)

  # Loop over all projects in the collection and determine their samples
  getProjectSamples(args, projects)

  # Calculate and assign the Z-scores
  calculateZscores(args)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Arguments related to the config file
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "A config file containing token / url information")
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic curl commands, up to an including \"api\". Do NOT include a trailing /")

  # The project id to which the filter is to be added is required
  parser.add_argument('--project_id', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")

  # Optional arguments
  parser.add_argument('--attribute_id', '-a', required = False, metavar = "string", help = "The attribute id to calculate z-scores for")
  parser.add_argument('--z_score_id', '-z', required = False, metavar = "string", help = "The Mosaic uid of the Z-score sample attribute")
  #parser.add_argument('--public', '-b', required = False, action = "store_true", help = "If not set, the created event will be private")

  return parser.parse_args()

# Get a list of all projects in the collection
def getSubProjects(args):
  global mosaicConfig
  projects = []

  # Get all project information for the collection
  try: data = json.loads(os.popen(api_p.getCollectionProjects(mosaicConfig, args.project_id)).read())
  except: fail('Couldn\'t get collection projects')
  for project in data: projects.append(project['id'])

  # This script is only for collections. If there are no sub-projects, fail
  if len(projects) == 0: fail('The defined project_id must be associated with a collection')

  # Return the list of projects
  return projects

# If no attribute id to generate z-scores for was provided, get all the sample attributes in the supplied project
def getSampleAttributes(args):
  global mosaicConfig

  try: data = json.loads(os.popen(api_sa.getSampleAttributes(mosaicConfig, args.project_id, False)).read())
  except: fail('Couldn\'t get sample attribute for the project')

  # Print the attribute ids
  for attribute in data: print(attribute['name'], ': ', attribute['id'], sep = '')
  exit(0)

# Check the Z-score attribute id belongs to an attribute with Z-score in the name
def checkZScoreId(args):
  global mosaicConfig

  try: data = json.loads(os.popen(api_sa.getSampleAttributes(mosaicConfig, args.project_id, False)).read())
  except: fail('Couldn\'t get sample attribute for the project')

  # Print the attribute ids
  for attribute in data:
    if int(attribute['id']) == int(args.z_score_id):
      if 'Z-score' not in attribute['name']: fail('Supplied Z-score attribute (' + str(args.z_score_id) + ') should be associated with an attribute with Z-score in the name, instead got: ' + str(attribute['name']))
      break

# Loop over all projects in the collection and determine their samples
def getProjectSamples(args, projects):
  global mosaicConfig
  global samples

  # Loop over the projects and extract all samples from the project
  for projectId in projects:
    try: data = json.loads(os.popen(api_s.getSamples(mosaicConfig, projectId)).read())
    except: fail('Couldn\'t get samples for project ' + str(projectId))
    for sample in data: samples[sample['id']] = {'name': sample['name'], 'projectId': projectId}

# Get the values for the specified sample attribute
def calculateZscores(args):
  global mosaicConfig
  global samples

  attributeValues = {}
  values = []

  try: data = json.loads(os.popen(api_sa.getSampleAttributes(mosaicConfig, args.project_id, True)).read())
  except: fail('Couldn\'t get sample attribute for the project')

  # Loop over all attributes and find the selected id
  for attribute in data:
    if int(attribute['id']) == int(args.attribute_id):
      for entry in attribute['values']:

        # Check that the project id for this sample is known
        if entry['sample_id'] not in samples: fail('Project for sample with id ' + str(entry['sample_id']) + ' could not be determined')

        # Store values
        attributeValues[entry['sample_id']] = {'value': entry['value'], 'projectId': samples[entry['sample_id']]['projectId']}
        values.append(entry['value'])
      break

  # Calculate the mean of the values
  mean = statistics.mean(values)
  sd   = statistics.stdev(values, mean)

  # Loop over all the samples and calculate their z-score
  for sampleId in attributeValues:
    zScore    = float((attributeValues[sampleId]['value'] - mean) / sd)
    projectId = attributeValues[sampleId]['projectId']

    # Check if the sample has this attribute, otherwise import it
    try: data = json.loads(os.popen(api_sa.getAttributesForSample(mosaicConfig, projectId, sampleId)).read())
    except: fail('Couldn\'t get attributes for sample ' + str(samples[sampleId]['name']) + ' (id:' + str(sampleId) + ')')

    # Update the value of the Z-score attribute for this sample
    hasAttribute = False
    for attribute in data:
      if int(attribute['id']) == int(args.z_score_id): hasAttribute = True

    if hasAttribute:
      try: data = json.loads(os.popen(api_sa.postUpdateSampleAttribute(mosaicConfig, zScore, projectId, sampleId, args.z_score_id)).read())
      except: fail('Couldn\'t update value for sample: ' + str(sampleId))
    else:
      try: data = json.loads(os.popen(api_sa.postImportSampleAttribute(mosaicConfig, args.z_score_id, projectId)).read())
      except: fail('Couldn\'t import Z-score variable to project ' + str(projectId))
      try: data = json.loads(os.popen(api_sa.postUpdateSampleAttribute(mosaicConfig, zScore, projectId, sampleId, args.z_score_id)).read())
      except: fail('Couldn\'t update value for sample: ' + str(sampleId))
    print(samples[sampleId], zScore)

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables
mosaicConfig = {}
samples = {}

if __name__ == "__main__":
  main()
