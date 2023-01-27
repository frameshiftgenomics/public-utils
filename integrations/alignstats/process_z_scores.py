#!/usr/bin/python

from __future__ import print_function
from os.path import exists
from random import random

import argparse
import json
import math
import os
import statistics

from datetime import datetime
from sys import path
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-2]) + "/api_commands")
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-2]) + "/common_components")
import mosaic_config
import api_sample_attributes as api_sa
import api_samples as api_s
import api_projects as api_p
import api_project_attributes as api_pa

def main():
  global mosaicConfig
  global alignstatsProjectId

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {'MOSAIC_TOKEN': {'value': args.token, 'desc': 'An access token', 'long': '--token', 'short': '-t'},
                    'MOSAIC_URL': {'value': args.url, 'desc': 'The api url', 'long': '--url', 'short': '-u'},
                    'MOSAIC_ATTRIBUTES_PROJECT_ID': {'value': args.attributes_project, 'desc': 'The public attribtes project id', 'long': '--attributes_project', 'short': '-a'},
                    'ALIGNSTATS_ATTRIBUTES_PROJECT_ID': {'value': args.alignstats_project, 'desc': 'The alignstats project id', 'long': '--alignstats_project', 'short': '-l'}}
  mosaicConfig = mosaic_config.parseConfig(args.config, mosaicRequired)

  # Define the alignstats project id
  alignstatsProjectId = mosaicConfig['ALIGNSTATS_ATTRIBUTES_PROJECT_ID']

  # Get a list of all projects in the collection, If this is not a collection, fail
  projects, sampleProjects = getSubProjects(args)

  # Get all of the Alignstats attributes from the Alignstats project
  attributes, zscoreAttributes = getSampleAttributes(args)

  # Calculate and assign the Z-scores
  failedSamples = calculateZscores(args, projects, sampleProjects, attributes, zscoreAttributes)
  for sampleId in failedSamples: print(sampleId, failedSamples[sampleId])

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Arguments related to the config file
  parser.add_argument('--config', '-c', required = False, metavar = 'string', help = 'A config file containing token / url information')
  parser.add_argument('--token', '-t', required = False, metavar = 'string', help = 'The Mosaic authorization token')
  parser.add_argument('--url', '-u', required = False, metavar = 'string', help = 'The base url for Mosaic curl commands, up to an including "api". Do NOT include a trailing "')
  parser.add_argument('--attributes_project', '-a', required = False, metavar = 'integer', help = 'The Mosaic project id that contains public attributes')
  parser.add_argument('--alignstats_project', '-l', required = False, metavar = 'integer', help = 'The Mosaic project id that contains alignstats attributes')

  # The project id to which the filter is to be added is required
  parser.add_argument('--project_id', '-p', required = True, metavar = 'integer', help = 'The Mosaic project id to upload attributes to')

  # The name to define the collection used for generating Z-scores. The same project could be in multiple collections and so
  # Z-scores could be calculated for different groups of samples. The Z-score attributes must therefore include some text to
  # indicate the collection they are associated with
  parser.add_argument('--collection_name', '-n', required = True, metavar = 'string', help = 'A name to identify the collection used to generate z-scores')

  # Include an optional pass/fail cutoff. Samples whose z-scores fall out of this range will be flagged
  parser.add_argument('--cutoff', '-f', required = False, metavar = 'integer', help = 'Z-score cutoff. Samples whose Z-score falls outside this range will be flagged')

  return parser.parse_args()

# Get a list of all projects in the collection
def getSubProjects(args):
  global mosaicConfig
  projects       = []
  sampleProjects = {}

  # Get all project information for the collection
  try: data = json.loads(os.popen(api_p.getCollectionProjects(mosaicConfig, args.project_id)).read())
  except: fail('Could not get collection projects')
  if 'message' in data: fail('Could not get collection projects. API returned the message' + str(data['message']) + '"')
  for project in data:
    projectId = project['id']
    projects.append(projectId)

    # Get all of the samples in the project
    try: samplesData = json.loads(os.popen(api_s.getSamples(mosaicConfig, projectId)).read())
    except: fail('Could not get samples for project ' + str(projectId))
    if 'message' in samplesData: fail('Could not get samples for project ' + str(projectId) + '. API returned the message "' + str(samplesData['message']) + '"')

    # Store the project for every sample
    for sample in samplesData: sampleProjects[sample['id']] = projectId

  # This script is only for collections. If there are no sub-projects, fail
  if len(projects) == 0: fail('The defined project_id must be associated with a collection')

  # Return the list of projects
  return projects, sampleProjects

# Get all of the sample attributes from the Alignstats project. Z-scores will be calulcated for all of these attributes
def getSampleAttributes(args):
  global mosaicConfig
  global alignstatsProjectId
  attributes       = {}
  zscoreAttributes = {}

  try: data = json.loads(os.popen(api_sa.getSampleAttributes(mosaicConfig, alignstatsProjectId, False)).read())
  except: fail('Could not get sample attribute from the alignstats project')
  if 'message' in data: fail('Could not get sample attribute from the alignstats project. API returned message "' + str(data['message']) + '"')

  # Store the attribute ids
  for attribute in data:
    if attribute['name'].endswith('Z-score (Alignstats)'): zscoreAttributes[attribute['name']] = attribute['id']
    elif attribute['name'].endswith('(Alignstats)'): attributes[attribute['id']] = attribute['name']

  # Return the list of attribute Ids
  return attributes, zscoreAttributes

# Get the values for the specified sample attribute
def calculateZscores(args, projectIds, sampleProjects, attributes, zscoreAttributes):
  global mosaicConfig
  global alignstatsProjectId
  attributeValues = {}
  valuesForMean   = {}
  failedSamples   = {}
  toImport        = []
  projectAttributeIds = {}

  # Populate attributeValues with all the necessary attribute ids
  for attributeId in attributes:
    attributeValues[attributeId] = {}
    valuesForMean[attributeId]   = []

    # Define the name of the z-score attribute for this attribute and check if it exists in the alignstats project. If not,
    # create it
    zscoreAttribute = attributes[attributeId].replace('(Alignstats)', 'Z-score (Alignstats)')
    zscoreAttribute = str(args.collection_name) + ' ' + zscoreAttribute
    if zscoreAttribute not in zscoreAttributes: zscoreAttributes[zscoreAttribute] = createZscoreAttribute(zscoreAttribute)

  # Loop over all of the projects in the collection
  for projectId in projectIds:
    projectAttributeIds[projectId] = {}

    # Get all the attribute information for the project
    try: data = json.loads(os.popen(api_sa.getSampleAttributes(mosaicConfig, projectId, True)).read())
    except: fail('Could not get attribute values for attribute id: ' + str(attributes[attribute]))
    if 'message' in data: fail('Could not get attribute values for attribute id: ' + str(attributes[attribute]) + '. API returned the message "' + data['message'] + '"')

    # Loop over all of the returned attributes and consider only those listed in the attributes dictionary
    for attribute in data:

      # Store all the attribute ids that are present in the project
      projectAttributeIds[projectId][attribute['id']] = []
      for sample in attribute['values']: projectAttributeIds[projectId][attribute['id']].append(sample['sample_id'])

      # Proceed with alignstats attributes
      if attribute['id'] in attributes:
        zscoreAttribute = attributes[attribute['id']].replace('(Alignstats)', 'Z-score (Alignstats)')
        zscoreAttribute = str(args.collection_name) + ' ' + zscoreAttribute

        # Loop over the project samples and store the values
        for sampleInfo in attribute['values']:
          attributeValues[attribute['id']][sampleInfo['sample_id']] = sampleInfo['value']
          valuesForMean[attribute['id']].append(sampleInfo['value'])

  # Process all the data for each attribute
  for attributeId in attributes:

    # Get the id of the associated z-score attribute
    zscoreAttribute   = attributes[attributeId].replace('(Alignstats)', 'Z-score (Alignstats)')
    zscoreAttribute   = str(args.collection_name) + ' ' + zscoreAttribute
    zscoreAttributeId = zscoreAttributes[zscoreAttribute]

    # Calculate the mean and standard deviation of the values
    mean = statistics.mean(valuesForMean[attributeId])
    sd   = statistics.stdev(valuesForMean[attributeId], mean)

    # Loop over all of the samples and calculate their z-scores
    for sampleId in attributeValues[attributeId]:
      if sd == 0: zScore = 0.
      else: zScore = float((attributeValues[attributeId][sampleId] - mean) / sd)
      projectId = sampleProjects[sampleId]

      # If the z-score attribute is not in the project, import it
      if zscoreAttributeId not in projectAttributeIds[projectId]:
        importAttribute(projectId, zscoreAttributeId, zscoreAttribute)
        projectAttributeIds[projectId][zscoreAttributeId] = []

      # Add or update the z-score value
      if sampleId in projectAttributeIds[projectId][zscoreAttributeId]: updateZscore(projectId, sampleId, zscoreAttributeId, zScore)
      else: addZscore(projectId, sampleId, zscoreAttributeId, zScore)

      # Determine if the z-score is outside of the pass/fail threshold
      if args.cutoff:
        if abs(zScore) > float(args.cutoff):
          if sampleId not in failedSamples: failedSamples[sampleId] = attributeId
          else: failedSamples[sampleId] = str(failedSamples[sampleId]) + ',' + str(attributeId)

  # Return the list of failed samples
  return failedSamples

# Create a z-score attribute in the alignstats project
def createZscoreAttribute(zscoreAttribute):
  global mosaicConfig
  global alignstatsProjectId

  # Create a new attribute
  try: data = json.loads(os.popen(api_sa.postSampleAttribute(mosaicConfig, zscoreAttribute, 'float', 'Null', 'true', 'Z-score', 'Sample Count', alignstatsProjectId)).read())
  except: fail('Failed to create new attribute: ' + str(zscoreAttribute))
  if 'message' in data: fail('Failed to create new sample attribute (' + str(zscoreAttribute) + '). API returned message "' + str(data['message']) + '"')

  # Return the id of the created attribute
  return data['id']

## Check if a project has a sample attribute and if not, import it
def importAttribute(projectId, attributeId, zscoreAttribute):
  global mosaicConfig

  try: data = json.loads(os.popen(api_sa.postImportSampleAttribute(mosaicConfig, attributeId, projectId)).read())
  except: fail('Failed to import attribute ' + str(zscoreAttribute))
  if 'message' in data: fail('Failed to import attribute ' + str(zscoreAttribute) + '. API returned message "' + str(data['message']) + '"')

# Add a value for a sample attribute
def addZscore(projectId, sampleId, attributeId, value):
  global mosaicConfig

  try: data = json.loads(os.popen(api_sa.postUpdateSampleAttribute(mosaicConfig, value, projectId, sampleId, attributeId)).read())
  except: fail('Failed to update (POST) sample ' + str(sampleId) + ' with value for attribute ' + str(attributeId))
  if 'message' in data: fail('Failed to update (POST) sample ' + str(sampleId) + ' with value for attribute ' + str(attributeId) + '. API returned message "' + str(data['message']) + '"')

# Update the Z-score attribute for a sample
def updateZscore(projectId, sampleId, attributeId, value):
  global mosaicConfig

  try: data = json.loads(os.popen(api_sa.putSampleAttributeValue(mosaicConfig, projectId, sampleId, attributeId, value)).read())
  except: fail('Failed to update (PUT) sample ' + str(sampleId) + ' with value for attribute ' + str(attributeId))
  if 'message' in data: fail('Failed to update (PUT) sample ' + str(sampleId) + ' with value for attribute ' + str(attributeId) + '. API returned message "' + str(data['message']) + '"')

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables
mosaicConfig = {}
alignstatsProjectId = False

if __name__ == "__main__":
  main()
