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
  global integrationProjectId
  global integrationAttributes
  global integrationName
  global includeFullCohort
  global cohorts

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {'MOSAIC_TOKEN': {'value': args.token, 'desc': 'An access token', 'long': '--token', 'short': '-t'},
                    'MOSAIC_URL': {'value': args.url, 'desc': 'The api url', 'long': '--url', 'short': '-u'},
                    'MOSAIC_ATTRIBUTES_PROJECT_ID': {'value': args.attributes_project, 'desc': 'The public attribtes project id', 'long': '--attributes_project', 'short': '-a'},
                    'ALIGNSTATS_ATTRIBUTES_PROJECT_ID': {'value': args.alignstats_project, 'desc': 'The alignstats project id', 'long': '--alignstats_project', 'short': '-l'}}
  mosaicConfig = mosaic_config.parseConfig(args.config, mosaicRequired)

###################
###################
################### GENERALIZE
###################
###################
  # Define the integrations project id
  integrationProjectId = mosaicConfig['ALIGNSTATS_ATTRIBUTES_PROJECT_ID']
  integrationName = 'Alignstats'

  # Get a list of all projects in the collection
  print('Getting collection projects...')
  getProjects(args.collection_id)

  # Get all of the attributes from the project for this integration for which z-scores will be calculated
  print('Getting integration attributes...')
  getIntegrationAttributes(integrationName)

  # If a json file was supplied describing how to subset samples, read in the information and build the cohorts
  print('Building cohorts to calculate Z-scores for')
  if args.sample_cohorts:
    getSampleCohortData(args.sample_cohorts)
    buildProjectAttributeCohorts(cohorts, args.collection_id)
    if includeFullCohort: buildFullCohort()
    addAttributeValuesToCohorts()
    addCohortIds()

  # Loop over all of the projects in the collection, get the sample attributes, loop over the attributes associated
  # with this integration and get the values for all the samples, store them and build a list of values to calculate
  # the mean and standard deviation of every attribute for all the required cohorts
  print('Processing all samples for all projects and attributes')
  processAllSamples()

  # Calculate the mean and standard deviation for every attribute and cohort
  print('Calculating the mean and standard deviation for all attributes and cohorts')
  calculateMeanAndSd()

  # Loop back over all of the attributes now that the mean and standard deviation are known are calculate all the Z-scores
  print('Calculating Z-scores')
  calculateZscores()

  # Write out all failure information
  print('Writing out failures')
  writeFailures(args.project_id)
  exit(0)





















  # Get a list of all projects in the collection, If this is not a collection, fail
  projects, projectSamples, sampleProjects = getSubProjects(args)

  # Check that the specified project is in the collection (or is 0)
  checkProjectId(args, projects)

  # Get all of the Alignstats attributes from the Alignstats project
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
  #parser.add_argument('--collection_name', '-n', required = True, metavar = 'string', help = 'A name to identify the collection used to generate z-scores')

  # Include the path to a json describing how to subset samples
  parser.add_argument('--sample_cohorts', '-s', required = False, metavar = 'string', help = 'A json file describing how to subset samples to calculate Z-scores')

  # Include an optional pass/fail cutoff. Samples whose z-scores fall out of this range will be flagged
  #parser.add_argument('--cutoff', '-f', required = False, metavar = 'integer', help = 'Z-score cutoff. Samples whose Z-score falls outside this range will be flagged')

  # Version
  parser.add_argument('--version', '-v', action="version", version='Alignstats integration version: ' + str(version))

  return parser.parse_args()

# Get a list of all projects in the collection
def getProjects(collectionId):
  global mosaicConfig
  global projectIds
  global sampleNames
  global failures
  global noFailures

  # Get all project information for the collection
  try: data = json.loads(os.popen(api_p.getCollectionProjects(mosaicConfig, collectionId)).read())
  except: fail('Could not get collection projects')
  if 'message' in data: fail('Could not get collection projects. API returned the message' + str(data['message']) + '"')

  # Loop over the collection projects and store the ids
  for project in data:
    projectId = project['id']
    projectIds[projectId] = []

    # Get all of the samples in the project
    try: samplesData = json.loads(os.popen(api_s.getSamples(mosaicConfig, projectId)).read())
    except: fail('Could not get samples for project ' + str(projectId))
    if 'message' in samplesData: fail('Could not get samples for project ' + str(projectId) + '. API returned the message "' + str(samplesData['message']) + '"')

    # Loop over the samples in the project and attach their ids to the project. Also populate
    # the failures dictionary with all the sample ids. This is used to keep track of all Z-scores
    # outside of the cutoffs for each sample
    for sample in samplesData:
      projectIds[projectId].append(sample['id'])
      sampleNames[sample['id']] = sample['name']
      failures[sample['id']]    = {}
      noFailures[sample['id']]  = {}

  # This script is only for collections. If there are no sub-projects, fail
  if len(projectIds) == 0: fail('The defined collection_id must be associated with a collection')

# Get all of the attributes from the project for this integration for which z-scores will be calculated
def getIntegrationAttributes(integrationName):
  global mosaicConfig
  global integrationProjectId
  global integrationAttributes

  # Attributes associated with this integration will end with the integration name in parentheses. Define this string for searching
  nameEnd = '(' + str(integrationName) + ')'

  # Get all the sample attribute data for the project connected to this integration
  try: data = json.loads(os.popen(api_sa.getSampleAttributes(mosaicConfig, integrationProjectId, False)).read())
  except: fail('Could not get sample attribute from the ' + str(integrationName) + ' project')
  if 'message' in data: fail('Could not get sample attribute from the ' + str(integrationName) + ' project. API returned message "' + str(data['message']) + '"')

  # Store the attribute ids, ignoring attributes with 'Z-score' in the name
  for attribute in data:
    if attribute['name'].endswith(nameEnd) and str('Z-score') not in attribute['name']: integrationAttributes[attribute['id']] = attribute['name']
 
# If a json file was supplied describing how to subset samples, read in the information
def getSampleCohortData(cohortFile):
  global cohorts
  global includeFullCohort

  # Get the json data
  try: jsonFile = open(cohortFile, 'r')
  except: fail('Could not open the json file: ' + cohortFile)
  try: jsonData = json.loads(jsonFile.read())
  except: fail('Json file ' + cohortFile + ' is not valid')

  # Check the entries are valid and complete, and determine if project attributes need to be read in
  for cohort in jsonData:

    # The 'type' field is necessary to determine if this subset is the full cohort, based on a sample or
    # project attribute
    try: cohortType = jsonData[cohort]['type']
    except: fail('The field "type" is not present in the input json file for sample cohort "' + cohort + '"')

    # Each cohort needs the cutoff defined. Any samples whose absolute Z-score value is greated than the cutoff fail
    try: cutoff = jsonData[cohort]['cutoff']
    except: fail('The field "cutoff" is not present in the input json file for sample cohort "' + cohort + '"')

    # If the type is "project", get the project attribute id and value to subset the samples
    if cohortType == 'project':
      try: attributeId = jsonData[cohort]['project_attribute']
      except: fail('Cohort ' + cohort + ' is based on a project attribute, but the "project_attribute" field is not provided')

      # The project attribute value can be a string, a number, or a Boolean. Depending on the type,
      # different values and comparisons will be required
      if 'string' in jsonData[cohort]: fail('Have not handled string comparisons')
      elif 'number' in jsonData[cohort]: fail('Have not handled numerical comparisons')
      elif 'boolean' in jsonData[cohort]:
        if type(jsonData[cohort]['boolean']) != bool: fail('Cohort ' + str(cohort) + ' is determined with a Boolean project attribute, but the provided value (' + str(jsonData[cohort]['boolean']) + ') is not Boolean')
        cohorts[cohort] = {'cutoff': cutoff, 'cohortType': 'project', 'attributeId': attributeId, 'type': 'bool', 'value': jsonData[cohort]['boolean']}

    # If the type is "sample", get the sample attribute id and value to subset the samples
    elif cohortType == 'sample': fail('Not implemented subsetting on samples yet')

    # If the type is "all", no additional information is required, but it is noted that z-scores for the full
    # cohort are required
    elif cohortType == 'all':
      includeFullCohort = True
      cohorts['all'] = {'cutoff': cutoff}

    # If a different value is provided for the "type" field, fail
    else: fail('Cohort type "' + cohortType + '" is not valid')

# Build the cohorts that are constructed based on project attributes
def buildProjectAttributeCohorts(cohorts, collectionId):
  global mosaicConfig

  # Get information on all of the project attributes associated with the collection
  try: attributeData = json.loads(os.popen(api_pa.getProjectAttributes(mosaicConfig, collectionId)).read())
  except: fail('Could not get project attribute data for the collection')
  if 'message' in attributeData: fail('Could not get project attribute data for the collection. API returned the message "' + str(attributeData['message']) + '"')

  # Get a list of all the project attribute ids that are listed in the input json files. These will
  # be used to build a list of samples that need to be in each cohort
  for cohort in cohorts:
    if cohort == 'all': continue
    if cohorts[cohort]['cohortType'] == 'project':

      # Get the attribute id for the project attribute used to build the cohort, and the data type (e.g. int, string, bool) of the attribute
      isCohortBuilt = False
      attributeId   = cohorts[cohort]['attributeId']
      dataType      = cohorts[cohort]['type']

      # Loop through the attribute data to find the attribute with this attribute id
      hasAttribute = False
      for attribute in attributeData:
        if int(attribute['id']) == int(attributeId):
          hasAttribute = True
          break

      # If the attribute was not in the collection, fail
      if not hasAttribute: fail('Attribute with id ' + str(attributeId) + ' was not in the collection and so the cohort ' + str(cohort) + ' could not be built')

      # Build the cohort based on the data type
      if dataType == 'bool': buildBooleanProjectCohort(attribute['values'], cohort, attributeId, cohorts[cohort]['value'])
      else: fail('Cannot build a cohort with a ' + str(dataType) + ' project attribute')

# Build a cohort using a Boolean project attribute
def buildBooleanProjectCohort(attributeValues, cohort, attributeId, value):
  global projectIds
  global cohorts

  # If "sampleIds" already exists in the cohorts dictionary, this routine has already been run for this cohort and so there
  # must be a conflict somewhere
  if 'sampleIds' in cohorts[cohort]: fail('The cohorts dictionary already contains sample ids for cohort ' + str(cohort))
  cohorts[cohort]['sampleIds'] = []

  # Check that the number of projects in the collection - len(projectsIds) - is equal to the number of projects that have values in
  # this collection - len(attributeValues). If these values are different, not all projects in the collection have values for this
  # project attribute, and so the cohort cannot be build
  if len(projectIds) != len(attributeValues): fail('Not all projects in the collection have values for project id ' + str(attributeId))

  # Loop over all of the projects with values (i.e. all projects in the collection), check that the value for that project is a
  # Boolean and add them to the cohort if it is the correct value
  for project in attributeValues:
    projectId    = project['project_id']
    projectValue = project['value']

    # If the project has the correct Boolean value, loop over the project samples and add them to the cohort
    if str(projectValue) == str(value):
      for sampleId in projectIds[projectId]: cohorts[cohort]['sampleIds'].append(sampleId)

# Build the cohort including all samples
def buildFullCohort():
  global projectIds
  global cohorts
  cohorts['all']['sampleIds'] = []

  # Loop over all projects and add all sample ids to the full cohort
  for projectId in projectIds:
    for sampleId in projectIds[projectId]: cohorts['all']['sampleIds'].append(sampleId)

# Add the ids of all of the integration attributes to each of the cohorts. This is where the sample attribute values
# for each of the samples will be stored
def addAttributeValuesToCohorts():
  global cohorts
  global integrationAttributes

  for cohort in cohorts:
    cohorts[cohort]['attributes'] = {}
    for attributeId in integrationAttributes:
      cohorts[cohort]['attributes'][attributeId] = {}
      cohorts[cohort]['attributes'][attributeId]['values'] = []
      cohorts[cohort]['attributes'][attributeId]['mean']   = False
      cohorts[cohort]['attributes'][attributeId]['sd']     = False

# Add ids to all of the cohorts
def addCohortIds():
  global cohorts

  # If the 'all' cohort is included, set it's name to "All Samples" and give it the id 1
  idValue = 1
  if 'all' in cohorts:
    cohorts['all']['name'] = 'All Samples'
    cohorts['all']['id']   = 1
    idValue = 2

  # Loop over all of the cohorts
  for cohort in cohorts:
    if cohort == 'all': continue
    cohorts[cohort]['name'] = cohort
    cohorts[cohort]['id']   = idValue
    idValue += 1

# Loop over all of the projects in the collection, get the sample attributes, loop over the attributes associated
# with this integration and get the values for all the samples, store them and build a list of values to calculate
# the mean and standard deviation of every attribute for all the required cohorts
def processAllSamples():
  global sampleAttributeValues
  global projectIds
  global integrationAttributes
  global integrationName
  global cohorts
  global missingSamples

  # First define a dictionary to store the values
  for projectId in projectIds:

    # Get all the sample attribute information for the project
    try: data = json.loads(os.popen(api_sa.getSampleAttributes(mosaicConfig, projectId, True)).read())
    except: fail('Could not get sample attribute values for project id: ' + str(projectId))
    if 'message' in data: fail('Could not get sample attribute values for project id: ' + str(projectId) + '. API returned the message "' + data['message'] + '"')

    # Loop over all of the returned attributes and consider only those listed in the attributes dictionary
    noIntegrationAttributes = 0
    for attribute in data:
      attributeId = attribute['id']
      if attributeId not in sampleAttributeValues: sampleAttributeValues[attributeId] = {}
      if attributeId not in missingSamples: missingSamples[attributeId] = []

      # Proceed with alignstats attributes. All other attributes in the project are not part of this integration and do not need
      # Z-scores calculating
      if attributeId in integrationAttributes:
        noIntegrationAttributes += 1

        # Check that the samples in the project all have values for this attribute. If not, store the missing samples so that they
        # can be skipped when calculating Z-scores
        if len(attribute['values']) != len(projectIds[projectId]): print('Warning: not all samples in project ', projectId, ' have values for attribute ', attribute['id'], sep = '')
        for sampleId in projectIds[projectId]: missingSamples[attributeId].append(sampleId)

        # Loop over the samples in the project that have a value for this attribute
        for sample in attribute['values']:
          sampleId    = sample['sample_id']
          sampleValue = sample['value']

          # Remove the sample ids of samples that have values, leaving only those missing values
          missingSamples[attributeId].remove(sampleId)

          # Store the value for this sample and attribute. This will be needed once the cohort means and standard deviations are known
          # to calculate the Z-scores.
          sampleAttributeValues[attributeId][sampleId] = sampleValue

          # Loop over all of the cohorts. If this sample is in the cohort, append the value to the list of values in this cohort for 
          # calculating the mean and standard deviation.
          for cohort in cohorts:
            if sampleId in cohorts[cohort]['sampleIds']: cohorts[cohort]['attributes'][attributeId]['values'].append(sampleValue)

    # If the number of sample attributes associated with this integration that are seen in this project is not equal to
    # the expected number of attributes, fail
    if noIntegrationAttributes != len(integrationAttributes):
      text =  'Project ' + str(projectId) + ' has ' + str(noIntegrationAttributes) + ' of the expected ' + str(len(integrationAttributes)) + ' sample attributes. '
      text += 'Ensure that the ' + str(integrationName) + ' integration has been run on this project'
      fail(text)

# Calculate the mean and standard deviation for every attribute and cohort
def calculateMeanAndSd():
  global cohorts

  # Loop over all of the cohorts
  for cohort in cohorts:

    # Loop over all of the attribute ids and calculate the mean and standard deviation
    for attributeId in cohorts[cohort]['attributes']:
      mean = statistics.mean(cohorts[cohort]['attributes'][attributeId]['values'])
      sd   = statistics.stdev(cohorts[cohort]['attributes'][attributeId]['values'], mean)
      cohorts[cohort]['attributes'][attributeId]['mean'] = mean
      cohorts[cohort]['attributes'][attributeId]['sd']   = sd

# Loop back over all of the attributes now that the mean and standard deviation are known are calculate all the Z-scores
def calculateZscores():
  global cohorts
  global sampleAttributeValues
  global missingSamples
  global failures
  global noFailures

  # Loop over all of the cohorts. Z-scores need to be calculated for every sample, for every attribute in each
  # of the cohorts
  for cohort in cohorts:

    # Get the cutoff value for this cohort 
    cutoff = cohorts[cohort]['cutoff']

    # Loop over all of the attributes associated with the integration
    for attributeId in cohorts[cohort]['attributes']:
      mean = cohorts[cohort]['attributes'][attributeId]['mean']
      sd   = cohorts[cohort]['attributes'][attributeId]['sd']

      # Loop over all of the samples and determine the Z-score
      for sampleId in cohorts[cohort]['sampleIds']:

        # If this sample was missing a value for this attribute, skip the zscore calculation
        if sampleId in missingSamples[attributeId]: continue
        if sd == 0: zscore = 0.
        else: zscore = float((sampleAttributeValues[attributeId][sampleId] - mean) / sd)

        # Check if the Z-score falls outside of the cohort cutoff. If so, store the Z-score and keep
        # count of how many attributes have failed the cutoff for this sample and cohort
        if abs(zscore) > float(cutoff):
          if attributeId not in failures[sampleId]: failures[sampleId][attributeId] = {}
          failures[sampleId][attributeId][cohort] = round(zscore, 2)

          # Keep track of the number of failures
          if sampleId not in noFailures: noFailures[sampleId] = {}
          if cohort not in noFailures[sampleId]: noFailures[sampleId][cohort] = 1
          else: noFailures[sampleId][cohort] += 1

# Write out all failure information
def writeFailures(updateProjectId):
  global projectIds
  global failures
  global noFailures
  global cohorts
  global integrationName

  # Define the title of the conversation used to house information on failed samples
  title = str(integrationName) + ' information'

  # The conversation description begins with the date and basic information about what Z-scores were calculated for
  description  = '**' + str(integrationName) + ' information** posted on ' + str(datetime.date.today())
  description += '\\nZ-scores were calulated for the following sample cohorts:'

  # If all projects are to have project conversations updated, the supplied projectId must be 0. Otherwise, only update
  # the conversation for the provided projectId
  if updateProjectId == 0:

    # Loop over all the projects to write out the failures for each sample in the project
    for projectId in projectIds: updateProjectConversation(projectId, description)
  else: updateProjectConversation(updateProjectId, title, description)

# Generate information for a project conversation and update it
def updateProjectConversation(projectId, title, description):
  global projectIds
  global sampleNames
  global failures
  global noFailures
  global cohorts
  global integrationName
  global integrationAttributes

  # Determine the total number of failing attributes by cohort and in total for the project
  noProjectFailures   = {}
  includedInCohorts   = {}
  projectDescription  = description
  noTotalFailures     = 0
  projectId = int(projectId)

  # Loop over all the samples in the project and determine the number of failures for each cohort (and in total)
  for sampleId in projectIds[projectId]:

    # Loop over all the sample cohorts, determine if samples from this project are in the cohort, and process any errors
    # if they are
    for cohort in cohorts:

      # Determine if this project was a part of this cohort, e.g. if samples from this project appear in the cohort list.
      if sampleId in cohorts[cohort]['sampleIds']: includedInCohorts[cohort] = True

      # Check if any samples failed, e.g. the Z-score exceeded the cutoff for any attribute
      if cohort in noFailures[sampleId]:
        if cohort not in noProjectFailures: noProjectFailures[cohort] = noFailures[sampleId][cohort]
        else: noProjectFailures[cohort] += noFailures[sampleId][cohort]
        noTotalFailures += noFailures[sampleId][cohort]

  # Loop over the cohorts that the project was included in and update the description to be written to the project
  # conversation. This includes a summary of each of the cohorts the project was in followed by a break down of the
  # of the failing attributes by sample
  for i, cohort in enumerate(includedInCohorts):
    cohortName = cohorts[cohort]['name']
    if i == 0: projectDescription += ' **' + str(cohortName) + '** (' + str(len(cohorts[cohort]['sampleIds'])) + ' samples)'
    else: projectDescription += ', **' + str(cohortName) + '** (' + str(len(cohorts[cohort]['sampleIds'])) + ' samples)'
  projectDescription += '\\n\\n'

  # If there were no failures in the project, include this in the decription
  if noTotalFailures == 0: projectDescription += 'Z-scores for all attributes and all samples were within the defined cutoffs'

  # If there were any failures loop over the cohorts and write out information for each cohort
  else:

    # Give the overall cohort summaries before a break down of individual attributes
    for cohort in noProjectFailures:
      cohortName = cohorts[cohort]['name']
      cohortId   = cohorts[cohort]['id']
      if noProjectFailures[cohort] == 0: projectDescription += '  **' + str(cohorts[cohort]['name']) + '**: All samples passed all attributes\\n'
      else: 
        projectDescription += '  **' + str(cohorts[cohort]['name']) + ' (id: ' + str(cohortId) + ')**: '
        firstSample = True
        for sampleId in projectIds[projectId]:
          if cohort in noFailures[sampleId]:
            if firstSample:
              projectDescription += str(sampleNames[sampleId]) + ' had ' + str(noFailures[sampleId][cohort]) + ' failures\\n'
              firstSample = False
            else: projectDescription += ', ' + str(sampleNames[sampleId]) + ' had ' + str(noFailures[sampleId][cohort]) + ' failures\\n'

    # Now give the full break down of failing sample attributes.
    #projectDescription += '\n**Following is a break down of all failing attributes for all samples**\n'
    for sampleId in projectIds[projectId]:

      # If this sample has failures, include a title line for this sample in the description, then get the failing attriubtes
      if len(failures[sampleId]) > 0:
        projectDescription += '\\n**Sample ' + str(sampleNames[sampleId]) + '**:\\n'
        for attributeId in failures[sampleId]:
          projectDescription += str(integrationAttributes[attributeId]) + ': '
          for i, cohort in enumerate(failures[sampleId][attributeId]):
            if i == 0: projectDescription += str(cohorts[cohort]['id']) + ' (' + str(failures[sampleId][attributeId][cohort]) + ')'
            else: projectDescription += ', ' + str(cohorts[cohort]['id']) + ' (' + str(failures[sampleId][attributeId][cohort]) + ')'
          projectDescription += '\\n'

  # Get the id of the conversation to update
  conversationId, isNew = getConversationId(projectId)

  # Update the conversation description
  try: data = json.loads(os.popen(api_pc.putUpdateCoversation(mosaicConfig, str(title), str(projectDescription), str(projectId), conversationId)).read())
  except: fail('Could not update project conversation with title "' + str(title) + '" in project ' + str(projectId))
  if 'message' in data: fail('Could not update project conversation with title "' + str(title) + '" in project ' + str(projectId) + '. API returned the message "' + str(data['message']) + '"')

# Get the conversation id of the conversation to update
def getConversationId(projectId):
  global mosaicConfig
  global integrationName
  conversationId = False
  isNew          = False
  limit          = 100
  title          = integrationName + ' information'

  # All z-score results are posted to a conversation in the project called 'Alignstats information'. If this conversation does
  # not exist, create it
  try: data = json.loads(os.popen(api_pc.getCoversations(mosaicConfig, limit, 1, projectId)).read())
  except: fail('Could not get project conversations for project ' + str(projectId))
  if 'message' in data: fail('Could not get project conversations for project ' + str(projectId) + '. API returned the message "' + str(data['message']) + '"')

  # Get the number of pages of conversations
  noPages = math.ceil(float(data['count']) / float(limit))

  # Loop over the conversations and look for one with the name 'Alignstats information'
  for conversation in data['data']:
    if str(conversation['title']) == str(title):
      conversationId = conversation['id']
      break

  # Loop over remaining pages of files if the conversation has not been found
  if noPages > 1 and not conversationId:
    for i in range(1, noPages, 1):
      try: data = json.loads(os.popen(api_pc.getCoversations(mosaicConfig, limit, i + 1, projectId)).read())
      except: fail('Could not get project conversations for project ' + str(projectId))
      if 'message' in data: fail('Could not get project conversations for project ' + str(projectId) + '. API returned the message "' + str(data['message']) + '"')
      for conversation in data['data']:
        if str(conversation['title']) == str(title):
          conversationId = conversation['id']
          break

  # If the conversation doesn't exist, create it
  if not conversationId:

    # Create a new conversation with a blank description. This will be populated with information in another routine
    try: data = json.loads(os.popen(api_pc.postCoversation(mosaicConfig, title, '', projectId)).read())
    except: fail('Could not create a new alignstats conversation')
    if 'message' in data: fail('Could not create a new conversation. API returned the message "' + str(data['message']) + '"')
    conversationId = data['id']
    isNew          = True

  # Return the conversation id
  return conversationId, isNew



















## Get a list of all projects in the collection
#def getSubProjects(args):
#  global mosaicConfig
#  projects       = []
#  sampleProjects = {}
#  projectSamples = {}
#
#  # Get all project information for the collection
#  try: data = json.loads(os.popen(api_p.getCollectionProjects(mosaicConfig, args.collection_id)).read())
#  except: fail('Could not get collection projects')
#  if 'message' in data: fail('Could not get collection projects. API returned the message' + str(data['message']) + '"')
#  for project in data:
#    projectId                 = project['id']
#    projectSamples[projectId] = []
#    projects.append(projectId)
#
#    # Get all of the samples in the project
#    try: samplesData = json.loads(os.popen(api_s.getSamples(mosaicConfig, projectId)).read())
#    except: fail('Could not get samples for project ' + str(projectId))
#    if 'message' in samplesData: fail('Could not get samples for project ' + str(projectId) + '. API returned the message "' + str(samplesData['message']) + '"')
#
#    # Store the project for every sample and vice versa
#    for sample in samplesData:
#      sampleProjects[sample['id']] = {'projectId': projectId, 'name': sample['name']}
#      projectSamples[projectId].append(sample['id'])
#
#  # This script is only for collections. If there are no sub-projects, fail
#  if len(projects) == 0: fail('The defined collection_id must be associated with a collection')
#
#  # Return the list of projects
#  return projects, projectSamples, sampleProjects
#
## Check that the specified project is in the collection (or is 0)
#def checkProjectId(args, projects):
#
#  # The supplied project_id must be an integer
#  try: projectId = int(args.project_id)
#  except: fail('The project_id (' + str(args.project_id) + ') needs to be 0 (update all projects), or the id of a project in the collection')
#
#  # If the project_id is 0, this means all projects need to be updated
#  if int(args.project_id) == 0: pass
#
#  # Otherwise, the project_id must be a project in the collection
#  elif projectId in projects: pass
#
#  # Otherwise, fail
#  else: fail('The project_id (' + str(args.project_id) + ') needs to be 0 (update all projects), or the id of a project in the collection')
#
## Get all of the sample attributes from the Alignstats project. Z-scores will be calulcated for all of these attributes
#def getSampleAttributes(args):
#  global mosaicConfig
#  global alignstatsProjectId
#  attributes       = {}
#  zscoreAttributes = {}
#
#  try: data = json.loads(os.popen(api_sa.getSampleAttributes(mosaicConfig, alignstatsProjectId, False)).read())
#  except: fail('Could not get sample attribute from the alignstats project')
#  if 'message' in data: fail('Could not get sample attribute from the alignstats project. API returned message "' + str(data['message']) + '"')
#
#  # Store the attribute ids
#  for attribute in data:
#    if attribute['name'].endswith('Z-score (Alignstats)'): zscoreAttributes[attribute['name']] = attribute['id']
#    elif attribute['name'].endswith('(Alignstats)'): attributes[attribute['id']] = attribute['name']
#
#  # Return the list of attribute Ids
#  return attributes, zscoreAttributes
#
#
## Get the values for the specified sample attribute
#def calculateZscores(args, projectIds, projectSamples, sampleProjects, attributes, zscoreAttributes):
#  global mosaicConfig
#  global alignstatsProjectId
#  attributeValues = {}
#  valuesForMean   = {}
#  failedSamples   = {}
#  toImport        = []
#  projectAttributeIds = {}
#
#  # Populate attributeValues with all the necessary attribute ids
#  print('Checking and creating Z-score attributes...')
#  for attributeId in attributes:
#    attributeValues[attributeId] = {}
#    valuesForMean[attributeId]   = []
#
#    # Define the name of the z-score attribute for this attribute and check if it exists in the alignstats project. If not,
#    # create it
#    zscoreAttribute = attributes[attributeId].replace('(Alignstats)', 'Z-score (Alignstats)')
#    zscoreAttribute = str(args.collection_name) + ' ' + zscoreAttribute
#    if zscoreAttribute not in zscoreAttributes: zscoreAttributes[zscoreAttribute] = createZscoreAttribute(zscoreAttribute)
#
#  # Get the id of the failed attributes id
#  failedAttributeId = False
#  for attributeId in attributes:
#    if attributes[attributeId] == 'Failed Attributes (Alignstats)': failedAttributeId = attributeId
#  if not failedAttributeId: fail('The Alignstats project does not contain the "Failed Attributes (Alignstats)" sample attribute. Ensure this public attribute exists.')
#
#  # Loop over all of the projects in the collection
#  print('Getting attributes for project:')
#  for projectId in projectIds:
#    hasFailedAttribute             = False
#    projectAttributeIds[projectId] = {}
#
#    # Get all the attribute information for the project
#    try: data = json.loads(os.popen(api_sa.getSampleAttributes(mosaicConfig, projectId, True)).read())
#    except: fail('Could not get attribute values for attribute id: ' + str(attributes[attribute]))
#    if 'message' in data: fail('Could not get attribute values for attribute id: ' + str(attributes[attribute]) + '. API returned the message "' + data['message'] + '"')
#
#    # Loop over all of the returned attributes and consider only those listed in the attributes dictionary
#    for attribute in data:
#
#      # Check if this is the attribute that records the number of failed attributes
#      if attribute['name'] == 'Failed Attributes (Alignstats)': hasFailedAttribute = True
#
#      # Store all the attribute ids that are present in the project
#      projectAttributeIds[projectId][attribute['id']] = []
#      for sample in attribute['values']: projectAttributeIds[projectId][attribute['id']].append(sample['sample_id'])
#
#      # Proceed with alignstats attributes
#      if attribute['id'] in attributes:
#        zscoreAttribute = attributes[attribute['id']].replace('(Alignstats)', 'Z-score (Alignstats)')
#        zscoreAttribute = str(args.collection_name) + ' ' + zscoreAttribute
#
#        # Loop over the project samples and store the values
#        for sampleInfo in attribute['values']:
#          attributeValues[attribute['id']][sampleInfo['sample_id']] = sampleInfo['value']
#          valuesForMean[attribute['id']].append(sampleInfo['value'])
#
#    # If the attribute that records the number of failed attributes is not present in the project, import it and set the value
#    # to zero for all project samples
#    if not hasFailedAttribute:
#      importAttribute(projectId, failedAttributeId, 'Failed Attributes (Alignstats)')
#      for sampleId in projectSamples[projectId]: addValue(projectId, sampleId, failedAttributeId, 0)
#
#  # Process all the data for each attribute
#  print('Calculating Z-scores for attribute:')
#  for attributeId in attributes:
#    print('  ', attributes[attributeId], sep = '')
#    if attributeId == failedAttributeId: continue
#
#    # Get the id of the associated z-score attribute
#    zscoreAttribute   = attributes[attributeId].replace('(Alignstats)', 'Z-score (Alignstats)')
#    zscoreAttribute   = str(args.collection_name) + ' ' + zscoreAttribute
#    zscoreAttributeId = zscoreAttributes[zscoreAttribute]
#
#    # Calculate the mean and standard deviation of the values
#    mean = statistics.mean(valuesForMean[attributeId])
#    sd   = statistics.stdev(valuesForMean[attributeId], mean)
#
#    # Loop over all of the samples and calculate their z-scores
#    for sampleId in attributeValues[attributeId]:
#      if sd == 0: zscore = 0.
#      else: zscore = float((attributeValues[attributeId][sampleId] - mean) / sd)
#      projectId = sampleProjects[sampleId]['projectId']
#
#      # If the z-score attribute is not in the project, import it
#      if zscoreAttributeId not in projectAttributeIds[projectId]:
#        importAttribute(projectId, zscoreAttributeId, zscoreAttribute)
#        projectAttributeIds[projectId][zscoreAttributeId] = []
#
#      # Add or update the z-score value
#      if sampleId in projectAttributeIds[projectId][zscoreAttributeId]: updateValue(projectId, sampleId, zscoreAttributeId, zscore)
#      else: addValue(projectId, sampleId, zscoreAttributeId, zscore)
#
#      # Determine if the z-score is outside of the pass/fail threshold
#      if args.cutoff:
#        if abs(zscore) > float(args.cutoff):
#          if projectId not in failedSamples: failedSamples[projectId] = {}
#          if sampleId not in failedSamples[projectId]: failedSamples[projectId][sampleId] = {}
#          failedSamples[projectId][sampleId][attributeId] = {'name': attributes[attributeId], 'value': attributeValues[attributeId][sampleId], 'mean': mean, 'sd': sd, 'zscore': zscore}
#
#  # Return the list of failed samples
#  return failedSamples, failedAttributeId
#
## Create a z-score attribute in the alignstats project
#def createZscoreAttribute(zscoreAttribute):
#  global mosaicConfig
#  global alignstatsProjectId
#
#  # Create a new attribute
#  try: data = json.loads(os.popen(api_sa.postSampleAttribute(mosaicConfig, zscoreAttribute, 'float', 'Null', 'true', 'Z-score', 'Sample Count', alignstatsProjectId)).read())
#  except: fail('Failed to create new attribute: ' + str(zscoreAttribute))
#  if 'message' in data: fail('Failed to create new sample attribute (' + str(zscoreAttribute) + '). API returned message "' + str(data['message']) + '"')
#
#  # Return the id of the created attribute
#  return data['id']
#
### Check if a project has a sample attribute and if not, import it
#def importAttribute(projectId, attributeId, zscoreAttribute):
#  global mosaicConfig
#
#  try: data = json.loads(os.popen(api_sa.postImportSampleAttribute(mosaicConfig, attributeId, projectId)).read())
#  except: fail('Failed to import attribute ' + str(zscoreAttribute))
#  if 'message' in data: fail('Failed to import attribute ' + str(zscoreAttribute) + '. API returned message "' + str(data['message']) + '"')
#
## Add a value for a sample attribute
#def addValue(projectId, sampleId, attributeId, value):
#  global mosaicConfig
#
#  try: data = json.loads(os.popen(api_sa.postUpdateSampleAttribute(mosaicConfig, value, projectId, sampleId, attributeId)).read())
#  except: fail('Failed to update (POST) sample ' + str(sampleId) + ' with value for attribute ' + str(attributeId))
#  if 'message' in data: fail('Failed to update (POST) sample ' + str(sampleId) + ' with value for attribute ' + str(attributeId) + '. API returned message "' + str(data['message']) + '"')
#
## Update the Z-score attribute for a sample
#def updateValue(projectId, sampleId, attributeId, value):
#  global mosaicConfig
#
#  try: data = json.loads(os.popen(api_sa.putSampleAttributeValue(mosaicConfig, projectId, sampleId, attributeId, value)).read())
#  except: fail('Failed to update (PUT) sample ' + str(sampleId) + ' with value for attribute ' + str(attributeId))
#  if 'message' in data: fail('Failed to update (PUT) sample ' + str(sampleId) + ' with value for attribute ' + str(attributeId) + '. API returned message "' + str(data['message']) + '"')
#
## Post results to project conversations
#def processFailedSamples(args, projects, sampleProjects, failedSamples, failedAttributeId):
#  noProjects = len(projects)
#  noSamples  = len(sampleProjects)
#
#  # If a single project was specified, only update this project, otherwise loop over all projects and post results to them all
#  if int(args.project_id) == 0: 
#    for projectId in projects: processProject(args.cutoff, projectId, sampleProjects, failedSamples, failedAttributeId, noProjects, noSamples)
#  else: processProject(args.cutoff, int(args.project_id), sampleProjects, failedSamples, failedAttributeId, noProjects, noSamples)
#
## Process the z-score results for a project
#def processProject(cutoff, projectId, sampleProjects, failedSamples, failedAttributeId, noProjects, noSamples):
#  global mosaicConfig
#
#  # Get the conversation id of the conversation to update
#  conversationId, isNew = getConversationId(projectId)
#
#  # Determine the number of attributes that failed (e.g. outside the Z-score cutoff) and update the sample attribute
#  if projectId in failedSamples:
#    for sampleId in failedSamples[projectId]: updateValue(projectId, sampleId, failedAttributeId, len(failedSamples[projectId][sampleId]))
#
#  # Generate the conversation description
#  title       = 'Alignstats information'
#  description  = '**Alignstats QC information** (' + str(datetime.date.today()) + ')'
#  description += '\\nZ-scores calculated based on ' + str(noSamples) + ' samples from ' + str(noProjects) + ' projects'
#
#  # If no samples failed, state that in the message
#  if projectId not in failedSamples: description += '\\n\\nNo samples failed. I.e. the Z-score for all samples and all attributes were within ' + str(cutoff) + ' standard deviations of the mean'
#
#  # If some samples failed for some attributes, list the failures
#  else:
#    description += '\\n\\nThe following failures occured:'
#
#    # Get all the sample names to add them to the description in order
#    sampleNames = {}
#    for sampleId in failedSamples[projectId]:
#      sampleNames[sampleProjects[sampleId]['name']] = sampleId
#
#    for sampleName in sorted(sampleNames.keys()):
#      sampleId = sampleNames[sampleName]
#      description += '\\n**Sample ' + sampleProjects[sampleId]['name'] + ':**'
#      for attributeId in failedSamples[projectId][sampleId]: 
#        description += '\\n&nbsp;&nbsp;&nbsp;&nbsp;' + failedSamples[projectId][sampleId][attributeId]['name'] + ': '
#        description += 'value: ' + str(failedSamples[projectId][sampleId][attributeId]['value']) + ', Z-score: ' + str(failedSamples[projectId][sampleId][attributeId]['zscore'])
#
#  # Update the conversation description
#  try: data = json.loads(os.popen(api_pc.putUpdateCoversation(mosaicConfig, title, description, projectId, conversationId)).read())
#  except: fail('Could not update project conversation with title "Alignstats information" in project ' + str(projectId))
#  if 'message' in data: fail('Could not update project conversation with title "Alignstats information" in project ' + str(projectId) + '. API returned the message "' + str(data['message']) + '"')
#

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables

# The mosaic config is used to request data from Mosaic
mosaicConfig = {}

# The integrationProjectId defines the project that contains all of the attributes for this integration. Also
# store the attribute ids of all the sample attributes associated with the integration
integrationProjectId  = False
integrationAttributes = {}
integrationName       = False

# Store all of the project ids in the collection, along with the samples
projectIds = {}

# Store the list of samples in each cohort. Also determine if the cohort of all samples is required
cohorts           = {}
includeFullCohort = False

# Store the names of all samples
sampleNames = {}

# Store the sample ids of samples that do not have values for each attribute
missingSamples = {}

# Store the sample attribute value for all samples and all attributes
sampleAttributeValues = {}

# Also keep track of all failures
failures   = {}
noFailures = {}

# Store the version
version = "0.0.3"

if __name__ == "__main__":
  main()
