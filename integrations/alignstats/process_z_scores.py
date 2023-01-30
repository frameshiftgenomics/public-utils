#!/usr/bin/python

from __future__ import print_function
from os.path import exists
from random import random

import argparse
import json
import math
import os
import statistics

import datetime
from sys import path
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-2]) + "/api_commands")
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-2]) + "/common_components")
import mosaic_config
import api_sample_attributes as api_sa
import api_samples as api_s
import api_projects as api_p
import api_project_attributes as api_pa
import api_project_conversations as api_pc

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
  print('Getting collection projects...')
  projects, projectSamples, sampleProjects = getSubProjects(args)

  # Check that the specified project is in the collection (or is 0)
  checkProjectId(args, projects)

  # Get all of the Alignstats attributes from the Alignstats project
  print('Getting alignstats attriubtes...')
  attributes, zscoreAttributes = getSampleAttributes(args)

  # Calculate and assign the Z-scores
  failedSamples, failedAttributeId = calculateZscores(args, projects, projectSamples, sampleProjects, attributes, zscoreAttributes)

  # Post results to conversations
  print('Posting results...')
  processFailedSamples(args, projects, sampleProjects, failedSamples, failedAttributeId)
  print('Complete')

# Input options
def parseCommandLine():
  global version

  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Arguments related to the config file
  parser.add_argument('--config', '-c', required = False, metavar = 'string', help = 'A config file containing token / url information')
  parser.add_argument('--token', '-t', required = False, metavar = 'string', help = 'The Mosaic authorization token')
  parser.add_argument('--url', '-u', required = False, metavar = 'string', help = 'The base url for Mosaic curl commands, up to an including "api". Do NOT include a trailing "')
  parser.add_argument('--attributes_project', '-a', required = False, metavar = 'integer', help = 'The Mosaic project id that contains public attributes')
  parser.add_argument('--alignstats_project', '-l', required = False, metavar = 'integer', help = 'The Mosaic project id that contains alignstats attributes')

  # The collection to calculate z-scores for and the project being updated
  parser.add_argument('--collection_id', '-d', required = True, metavar = 'integer', help = 'The Mosaic collection id to generate z-scores for')
  parser.add_argument('--project_id', '-p', required = True, metavar = 'integer', help = 'The Mosaic project to update. If set to 0, z-scores for all samples in the collection will be calculated and their projects updated. Otherwise, only the specifid project will be processed')

  # The name to define the collection used for generating Z-scores. The same project could be in multiple collections and so
  # Z-scores could be calculated for different groups of samples. The Z-score attributes must therefore include some text to
  # indicate the collection they are associated with
  parser.add_argument('--collection_name', '-n', required = True, metavar = 'string', help = 'A name to identify the collection used to generate z-scores')

  # Include an optional pass/fail cutoff. Samples whose z-scores fall out of this range will be flagged
  parser.add_argument('--cutoff', '-f', required = False, metavar = 'integer', help = 'Z-score cutoff. Samples whose Z-score falls outside this range will be flagged')

  # Version
  parser.add_argument('--version', '-v', action="version", version='Alignstats integration version: ' + str(version))

  return parser.parse_args()

# Get a list of all projects in the collection
def getSubProjects(args):
  global mosaicConfig
  projects       = []
  sampleProjects = {}
  projectSamples = {}

  # Get all project information for the collection
  try: data = json.loads(os.popen(api_p.getCollectionProjects(mosaicConfig, args.collection_id)).read())
  except: fail('Could not get collection projects')
  if 'message' in data: fail('Could not get collection projects. API returned the message' + str(data['message']) + '"')
  for project in data:
    projectId                 = project['id']
    projectSamples[projectId] = []
    projects.append(projectId)

    # Get all of the samples in the project
    try: samplesData = json.loads(os.popen(api_s.getSamples(mosaicConfig, projectId)).read())
    except: fail('Could not get samples for project ' + str(projectId))
    if 'message' in samplesData: fail('Could not get samples for project ' + str(projectId) + '. API returned the message "' + str(samplesData['message']) + '"')

    # Store the project for every sample and vice versa
    for sample in samplesData:
      sampleProjects[sample['id']] = {'projectId': projectId, 'name': sample['name']}
      projectSamples[projectId].append(sample['id'])

  # This script is only for collections. If there are no sub-projects, fail
  if len(projects) == 0: fail('The defined collection_id must be associated with a collection')

  # Return the list of projects
  return projects, projectSamples, sampleProjects

# Check that the specified project is in the collection (or is 0)
def checkProjectId(args, projects):

  # The supplied project_id must be an integer
  try: projectId = int(args.project_id)
  except: fail('The project_id (' + str(args.project_id) + ') needs to be 0 (update all projects), or the id of a project in the collection')

  # If the project_id is 0, this means all projects need to be updated
  if int(args.project_id) == 0: pass

  # Otherwise, the project_id must be a project in the collection
  elif projectId in projects: pass

  # Otherwise, fail
  else: fail('The project_id (' + str(args.project_id) + ') needs to be 0 (update all projects), or the id of a project in the collection')

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
def calculateZscores(args, projectIds, projectSamples, sampleProjects, attributes, zscoreAttributes):
  global mosaicConfig
  global alignstatsProjectId
  attributeValues = {}
  valuesForMean   = {}
  failedSamples   = {}
  toImport        = []
  projectAttributeIds = {}

  # Populate attributeValues with all the necessary attribute ids
  print('Checking and creating Z-score attributes...')
  for attributeId in attributes:
    attributeValues[attributeId] = {}
    valuesForMean[attributeId]   = []

    # Define the name of the z-score attribute for this attribute and check if it exists in the alignstats project. If not,
    # create it
    zscoreAttribute = attributes[attributeId].replace('(Alignstats)', 'Z-score (Alignstats)')
    zscoreAttribute = str(args.collection_name) + ' ' + zscoreAttribute
    if zscoreAttribute not in zscoreAttributes: zscoreAttributes[zscoreAttribute] = createZscoreAttribute(zscoreAttribute)

  # Get the id of the failed attributes id
  failedAttributeId = False
  for attributeId in attributes:
    if attributes[attributeId] == 'Failed Attributes (Alignstats)': failedAttributeId = attributeId
  if not failedAttributeId: fail('The Alignstats project does not contain the "Failed Attributes (Alignstats)" sample attribute. Ensure this public attribute exists.')

  # Loop over all of the projects in the collection
  print('Getting attributes for project:')
  for projectId in projectIds:
    hasFailedAttribute             = False
    projectAttributeIds[projectId] = {}

    # Get all the attribute information for the project
    try: data = json.loads(os.popen(api_sa.getSampleAttributes(mosaicConfig, projectId, True)).read())
    except: fail('Could not get attribute values for attribute id: ' + str(attributes[attribute]))
    if 'message' in data: fail('Could not get attribute values for attribute id: ' + str(attributes[attribute]) + '. API returned the message "' + data['message'] + '"')

    # Loop over all of the returned attributes and consider only those listed in the attributes dictionary
    for attribute in data:

      # Check if this is the attribute that records the number of failed attributes
      if attribute['name'] == 'Failed Attributes (Alignstats)': hasFailedAttribute = True

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

    # If the attribute that records the number of failed attributes is not present in the project, import it and set the value
    # to zero for all project samples
    if not hasFailedAttribute:
      importAttribute(projectId, failedAttributeId, 'Failed Attributes (Alignstats)')
      for sampleId in projectSamples[projectId]: addValue(projectId, sampleId, failedAttributeId, 0)

  # Process all the data for each attribute
  print('Calculating Z-scores for attribute:')
  for attributeId in attributes:
    print('  ', attributes[attributeId], sep = '')
    if attributeId == failedAttributeId: continue

    # Get the id of the associated z-score attribute
    zscoreAttribute   = attributes[attributeId].replace('(Alignstats)', 'Z-score (Alignstats)')
    zscoreAttribute   = str(args.collection_name) + ' ' + zscoreAttribute
    zscoreAttributeId = zscoreAttributes[zscoreAttribute]

    # Calculate the mean and standard deviation of the values
    mean = statistics.mean(valuesForMean[attributeId])
    sd   = statistics.stdev(valuesForMean[attributeId], mean)

    # Loop over all of the samples and calculate their z-scores
    for sampleId in attributeValues[attributeId]:
      if sd == 0: zscore = 0.
      else: zscore = float((attributeValues[attributeId][sampleId] - mean) / sd)
      projectId = sampleProjects[sampleId]['projectId']

      # If the z-score attribute is not in the project, import it
      if zscoreAttributeId not in projectAttributeIds[projectId]:
        importAttribute(projectId, zscoreAttributeId, zscoreAttribute)
        projectAttributeIds[projectId][zscoreAttributeId] = []

      # Add or update the z-score value
      if sampleId in projectAttributeIds[projectId][zscoreAttributeId]: updateValue(projectId, sampleId, zscoreAttributeId, zscore)
      else: addValue(projectId, sampleId, zscoreAttributeId, zscore)

      # Determine if the z-score is outside of the pass/fail threshold
      if args.cutoff:
        if abs(zscore) > float(args.cutoff):
          if projectId not in failedSamples: failedSamples[projectId] = {}
          if sampleId not in failedSamples[projectId]: failedSamples[projectId][sampleId] = {}
          failedSamples[projectId][sampleId][attributeId] = {'name': attributes[attributeId], 'value': attributeValues[attributeId][sampleId], 'mean': mean, 'sd': sd, 'zscore': zscore}

  # Return the list of failed samples
  return failedSamples, failedAttributeId

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
def addValue(projectId, sampleId, attributeId, value):
  global mosaicConfig

  try: data = json.loads(os.popen(api_sa.postUpdateSampleAttribute(mosaicConfig, value, projectId, sampleId, attributeId)).read())
  except: fail('Failed to update (POST) sample ' + str(sampleId) + ' with value for attribute ' + str(attributeId))
  if 'message' in data: fail('Failed to update (POST) sample ' + str(sampleId) + ' with value for attribute ' + str(attributeId) + '. API returned message "' + str(data['message']) + '"')

# Update the Z-score attribute for a sample
def updateValue(projectId, sampleId, attributeId, value):
  global mosaicConfig

  try: data = json.loads(os.popen(api_sa.putSampleAttributeValue(mosaicConfig, projectId, sampleId, attributeId, value)).read())
  except: fail('Failed to update (PUT) sample ' + str(sampleId) + ' with value for attribute ' + str(attributeId))
  if 'message' in data: fail('Failed to update (PUT) sample ' + str(sampleId) + ' with value for attribute ' + str(attributeId) + '. API returned message "' + str(data['message']) + '"')

# Post results to project conversations
def processFailedSamples(args, projects, sampleProjects, failedSamples, failedAttributeId):
  noProjects = len(projects)
  noSamples  = len(sampleProjects)

  # If a single project was specified, only update this project, otherwise loop over all projects and post results to them all
  if int(args.project_id) == 0: 
    for projectId in projects: processProject(args.cutoff, projectId, sampleProjects, failedSamples, failedAttributeId, noProjects, noSamples)
  else: processProject(args.cutoff, int(args.project_id), sampleProjects, failedSamples, failedAttributeId, noProjects, noSamples)

# Process the z-score results for a project
def processProject(cutoff, projectId, sampleProjects, failedSamples, failedAttributeId, noProjects, noSamples):
  global mosaicConfig

  # Get the conversation id of the conversation to update
  conversationId, isNew = getConversationId(projectId)

  # Determine the number of attributes that failed (e.g. outside the Z-score cutoff) and update the sample attribute
  if projectId in failedSamples:
    for sampleId in failedSamples[projectId]: updateValue(projectId, sampleId, failedAttributeId, len(failedSamples[projectId][sampleId]))

  # Generate the conversation description
  title       = 'Alignstats information'
  description  = '**Alignstats QC information** (' + str(datetime.date.today()) + ')'
  description += '\\nZ-scores calculated based on ' + str(noSamples) + ' samples from ' + str(noProjects) + ' projects'

  # If no samples failed, state that in the message
  if projectId not in failedSamples: description += '\\n\\nNo samples failed. I.e. the Z-score for all samples and all attributes were within ' + str(cutoff) + ' standard deviations of the mean'

  # If some samples failed for some attributes, list the failures
  else:
    description += '\\n\\nThe following failures occured:'

    # Get all the sample names to add them to the description in order
    sampleNames = {}
    for sampleId in failedSamples[projectId]:
      sampleNames[sampleProjects[sampleId]['name']] = sampleId

    for sampleName in sorted(sampleNames.keys()):
      sampleId = sampleNames[sampleName]
      description += '\\n**Sample ' + sampleProjects[sampleId]['name'] + ':**'
      for attributeId in failedSamples[projectId][sampleId]: 
        description += '\\n&nbsp;&nbsp;&nbsp;&nbsp;' + failedSamples[projectId][sampleId][attributeId]['name'] + ': '
        description += 'value: ' + str(failedSamples[projectId][sampleId][attributeId]['value']) + ', Z-score: ' + str(failedSamples[projectId][sampleId][attributeId]['zscore'])

  # Update the conversation description
  try: data = json.loads(os.popen(api_pc.putUpdateCoversation(mosaicConfig, title, description, projectId, conversationId)).read())
  except: fail('Could not update project conversation with title "Alignstats information" in project ' + str(projectId))
  if 'message' in data: fail('Could not update project conversation with title "Alignstats information" in project ' + str(projectId) + '. API returned the message "' + str(data['message']) + '"')

# Get the conversation id of the conversation to update
def getConversationId(projectId):
  global mosaicConfig
  conversationId = False
  isNew          = False
  limit          = 100

  # All z-score results are posted to a conversation in the project called 'Alignstats information'. If this conversation does
  # not exist, create it
  try: data = json.loads(os.popen(api_pc.getCoversations(mosaicConfig, limit, 1, projectId)).read())
  except: fail('Could not get project conversations for project ' + str(projectId))
  if 'message' in data: fail('Could not get project conversations for project ' + str(projectId) + '. API returned the message "' + str(data['message']) + '"')

  # Get the number of pages of conversations
  noPages = math.ceil(float(data['count']) / float(limit))

  # Loop over the conversations and look for one with the name 'Alignstats information'
  for conversation in data['data']:
    if conversation['title'] == 'Alignstats information':
      conversationId = conversation['id']
      break

  # Loop over remaining pages of files if the conversation has not been found
  if noPages > 1 and not conversationId:
    for i in range(1, noPages, 1):
      try: data = json.loads(os.popen(api_pc.getCoversations(mosaicConfig, limit, i + 1, projectId)).read())
      except: fail('Could not get project conversations for project ' + str(projectId))
      if 'message' in data: fail('Could not get project conversations for project ' + str(projectId) + '. API returned the message "' + str(data['message']) + '"')
      for conversation in data['data']:
        if conversation['title'] == 'Alignstats information':
          conversationId = conversation['id']
          break

  # If the conversation doesn't exist, create it
  if not conversationId:

    # Create a new conversation with a blank description. This will be populated with information in another routine
    try: data = json.loads(os.popen(api_pc.postCoversation(mosaicConfig, 'Alignstats information', '', projectId)).read())
    except: fail('Could not create a new alignstats conversation')
    if 'message' in data: fail('Could not create a new alignstats conversation. API returned the message "' + str(data['message']) + '"')
    conversationId = data['id']
    isNew          = True

  # Return the conversation id
  return conversationId, isNew

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Store the version
version = "0.0.2"

# Initialise global variables
mosaicConfig = {}
alignstatsProjectId = False

if __name__ == "__main__":
  main()
