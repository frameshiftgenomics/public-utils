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
  projects = getSubProjects(args)

  # Get all of the Alignstats attributes from the Alignstats project
  attributes, zscoreAttributes = getSampleAttributes(args)

  # Get all of the samples in the collection
  samples, projectIds = getProjectSamples(args, projects)

  # Calculate and assign the Z-scores
  failedSamples = calculateZscores(args, samples, projectIds, attributes, zscoreAttributes)
  print(failedSamples)

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
  projects = []

  # Get all project information for the collection
  try: data = json.loads(os.popen(api_p.getCollectionProjects(mosaicConfig, args.project_id)).read())
  except: fail('Could not get collection projects')
  for project in data: projects.append(project['id'])

  # This script is only for collections. If there are no sub-projects, fail
  if len(projects) == 0: fail('The defined project_id must be associated with a collection')

  # Return the list of projects
  return projects

# Get all of the sample attributes from the Alignstats project. Z-scores will be calulcated for all of these attributes
def getSampleAttributes(args):
  global mosaicConfig
  global alignstatsProjectId
  attributes       = {}
  zscoreAttributes = {}

  try: data = json.loads(os.popen(api_sa.getSampleAttributes(mosaicConfig, alignstatsProjectId, False)).read())
  except: fail('Could not get sample attribute from the alignstats project')

  # Store the attribute ids
  for attribute in data:
    if attribute['name'].endswith('Z-score (Alignstats)'): zscoreAttributes[attribute['name']] = attribute['id']
    elif attribute['name'].endswith('(Alignstats)'): attributes[attribute['name']] = attribute['id']

  # Return the list of attribute Ids
  return attributes, zscoreAttributes

# Loop over all projects in the collection and determine their samples
def getProjectSamples(args, projects):
  global mosaicConfig
  samples    = {}
  projectIds = {}

  # Loop over the projects and extract all samples from the project
  for projectId in projects:
    try: data = json.loads(os.popen(api_s.getSamples(mosaicConfig, projectId)).read())
    except: fail('Couldn\'t get samples for project ' + str(projectId))
    for sample in data:
      samples[sample['id']] = {'name': sample['name'], 'projectId': projectId}
      if projectId not in projectIds: projectIds[projectId] = [sample['id']]
      else: projectIds[projectId].append(sample['id'])

  # Return the samples and projectIds
  return samples, projectIds

# Get the values for the specified sample attribute
def calculateZscores(args, samples, projectIds, attributes, zscoreAttributes):
  global mosaicConfig
  global alignstatsProjectId
  failedSamples = {}

  # Loop over the alignstats attributes
  for attribute in attributes:

    # Define the name of the z-score attribute for this attribute and check if it exists in the alignstats project. If not,
    # create it
    zscoreAttribute = attribute.replace('(Alignstats)', 'Z-score (Alignstats)')
    zscoreAttribute = str(args.collection_name) + ' ' + zscoreAttribute
    if zscoreAttribute not in zscoreAttributes: attributeId = createZscoreAttribute(zscoreAttribute, attribute)
    else: attributeId = zscoreAttributes[zscoreAttribute]

    # Loop over all the projects and import the zscore attribute if necessary
    for projectId in projectIds: importAttribute(projectId, attributeId, zscoreAttribute)

    # Reset the array of values for the samples in the collection
    attributeValues = {}
    values          = []

    # Loop over all the constituent projects and get the values for all samples
    for projectId in projectIds:
      try: data = json.loads(os.popen(api_sa.getSpecifiedSampleAttributes(mosaicConfig, projectId, True, [attributes[attribute]])).read())
      except: fail('Could not get attribute values for attribute id: ' + str(attributes[attribute]))

      # Check that the data object only contains one value
      if len(data) != 1: fail('Number of sample attributes is incorrect')

      # Loop over the values for this attribute in this project and store the values
      for valueObject in data[0]['values']:
        if valueObject['sample_id'] not in projectIds[projectId]: fail('Unknown sample')
        attributeValues[valueObject['sample_id']] = {'value': valueObject['value'], 'projectId': projectId}
        values.append(valueObject['value'])

    # Calculate the mean and standard deviation of the values
    mean = statistics.mean(values)
    sd   = statistics.stdev(values, mean)

    # Loop over all of the samples and calculate the z-score
    for sampleId in attributeValues:
      if sd == 0: zScore = 0.
      else: zScore = float((attributeValues[sampleId]['value'] - mean) / sd)
      projectId = attributeValues[sampleId]['projectId']
      updateZscore(projectId, sampleId, attributeId, zScore)
      if args.cutoff:
        if abs(zScore) > float(args.cutoff):
          if zscoreAttribute not in failedSamples: failedSamples[zscoreAttribute] = {}
          failedSamples[zscoreAttribute][sampleId] = {'zscore': zScore, 'projectId': projectId}

  # Return the list of failed samples
  return failedSamples

# Create a z-score attribute in the alignstats project
def createZscoreAttribute(zscoreAttribute, attribute):
  global mosaicConfig
  global alignstatsProjectId

  # Create a new attribute
  try: data = json.loads(os.popen(api_sa.postSampleAttribute(mosaicConfig, zscoreAttribute, 'float', 'Null', 'true', 'Z-score', 'Sample Count', alignstatsProjectId)).read())
  except: fail('Failed to create new attribute: ' + str(zscoreAttribute))

  # Check if the api call failed with a message
  if 'message' in data: fail('Failed to create new sample attribute (' + str(zscoreAttribute) + '). API returned message "' + str(data['message']) + '"')

  # Return the id of the created attribute
  return data['id']

# Check if a project has a sample attribute and if not, import it
def importAttribute(projectId, attributeId, zscoreAttribute):
  global mosaicConfig

  # Get the sample attributes in the project
  try: data = json.loads(os.popen(api_sa.getSampleAttributes(mosaicConfig, projectId, False)).read())
  except: fail('Failed to get sample attributes for project ' + str(projectId))
  if 'message' in data: fail('Failed to get sample attributes for project ' + str(projectId) + '. API returned the error "' + str(data['message']) + '"')
  hasAttribute = False
  for attribute in data:
    if int(attribute['id']) == int(attributeId):
      hasAttribute = True
      break

  # Import the attribute
  if not hasAttribute:
    try: data = json.loads(os.popen(api_sa.postImportSampleAttribute(mosaicConfig, attributeId, projectId)).read())
    except: fail('Failed to import attribute ' + str(zscoreAttribute))
    if 'message' in data: fail('Failed to import attribute ' + str(zscoreAttribute) + '. API returned message "' + str(data['message']) + '"')

# Update the Z-score attribute for a sample
def updateZscore(projectId, sampleId, attributeId, value):
  global mosaicConfig
  hasSample = False

  # Check if the sample has this attribute. If so, use the PUT route to update the value, and if not, use the POST route
  # to add a value
  try: data = json.loads(os.popen(api_sa.getSpecifiedSampleAttributes(mosaicConfig, projectId, True, [attributeId])).read())
  except: fail('Failed to get attribute information for attribute ' + str(attributeId))
  if 'message' in data: fail('Failed to get attribute information for attribute ' + str(attributeId) + '. API returned message "' + str(data['message']))
  if len(data) != 1: fail('Unexpected number of records returned for a single attribute')

  # Check if the sample has a value
  for a in data[0]['values']:
    if a['sample_id'] == sampleId:
      hasSample = True
      break

  # If the sample already has a value, update the value with the PUT route
  if hasSample:
    try: data = json.loads(os.popen(api_sa.putSampleAttributeValue(mosaicConfig, projectId, sampleId, attributeId, value)).read())
    except: fail('Failed to update (PUT) sample ' + str(sampleId) + ' with value for attribute ' + str(attributeId))
    if 'message' in data: fail('Failed to update (PUT) sample ' + str(sampleId) + ' with value for attribute ' + str(attributeId) + '. API returned message "' + str(data['message']))

  # Otherwise, use the POST route to add a value for the sample
  else:
    try: data = json.loads(os.popen(api_sa.postUpdateSampleAttribute(mosaicConfig, value, projectId, sampleId, attributeId)).read())
    except: fail('Failed to update (POST) sample ' + str(sampleId) + ' with value for attribute ' + str(attributeId))
    if 'message' in data: fail('Failed to update (POST) sample ' + str(sampleId) + ' with value for attribute ' + str(attributeId) + '. API returned message "' + str(data['message']))

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables
mosaicConfig = {}
alignstatsProjectId = False

if __name__ == "__main__":
  main()
