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
  global includeFullCohort

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {'MOSAIC_TOKEN': {'value': args.token, 'desc': 'An access token', 'long': '--token', 'short': '-t'},
                    'MOSAIC_URL': {'value': args.url, 'desc': 'The api url', 'long': '--url', 'short': '-u'},
                    'MOSAIC_ATTRIBUTES_PROJECT_ID': {'value': args.attributes_project, 'desc': 'The public attribtes project id', 'long': '--attributes_project', 'short': '-a'}}
  mosaicConfig = mosaic_config.parseConfig(args.config, mosaicRequired)

  # Check all information on the integration is available
  checkIntegration(args.integration_name)

  # Get a list of all projects in the collection
  print('Getting collection projects...')
  getProjects(args.collection_id)

  # Get all of the attributes from the project for this integration for which z-scores will be calculated
  print('Getting integration attributes...')
  getIntegrationAttributes()

  # Read in information from the supplied json file describing how to subset samples etc.
  print('Building cohorts to calculate Z-scores for')
  parseJsonInput(args.sample_cohorts)
  buildProjectAttributeCohorts(args.collection_id)
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

  # Store the number of failed attributes for each sample and cohort
  print('Updating failures counts in Mosaic')
  storeFailureCounts(args.name)

  # Write out all failure information
  print('Writing out failures')
  writeFailures(args.project_id)
  print('Complete')

# Input options
def parseCommandLine():
  global version
  global allowedIntegrations

  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Arguments related to the config file
  parser.add_argument('--config', '-c', required = False, metavar = 'string', help = 'A config file containing token / url information')
  parser.add_argument('--token', '-t', required = False, metavar = 'string', help = 'The Mosaic authorization token')
  parser.add_argument('--url', '-u', required = False, metavar = 'string', help = 'The base url for Mosaic curl commands, up to an including "api". Do NOT include a trailing "')
  parser.add_argument('--attributes_project', '-a', required = False, metavar = 'integer', help = 'The Mosaic project id that contains public attributes')

  # Define the integration name. This will be used to find the project containing integration parameters and for naming etc.
  parser.add_argument('--integration_name', '-i', required = True, metavar = 'string', help = 'The name of the integration. Allowed values include:\n' + str(', '.join(allowedIntegrations)))

  # The collection to calculate z-scores for and the project being updated
  parser.add_argument('--collection_id', '-d', required = True, metavar = 'integer', help = 'The Mosaic collection id to generate z-scores for')
  parser.add_argument('--project_id', '-p', required = True, metavar = 'integer', help = 'The Mosaic project to update. If set to 0, z-scores for all samples in the collection will be calculated and their projects updated. Otherwise, only the specifid project will be processed')

  # Include the path to a json describing how to subset samples
  parser.add_argument('--sample_cohorts', '-s', required = True, metavar = 'string', help = 'A json file describing how to subset samples to calculate Z-scores')

  # Include a name that will be included in the names of the created attributes
  parser.add_argument('--name', '-n', required = True, metavar = 'string', help = 'A name that will be included in the created sample attributes that identifies which collection they are associated with. It is recommended to keep this short, and use the collection nickname if appropriate')

  # Version
  parser.add_argument('--version', '-v', action="version", version='Z-score processor version: ' + str(version))

  return parser.parse_args()

# Check all information on the integration is available
def checkIntegration(name):
  global allowedIntegrations
  global integrationName
  global integrationProjectId

  # Fail if the defined integration is not recognised
  if name not in allowedIntegrations: fail('Integration "' + str(name) + '" is not a recognized integration. Allowed integrations are: ' + str(', '.join(allowedIntegrations)))

  # Define the integration name and project id
  integrationName      = name
  try: integrationProjectId = mosaicConfig[str(name.upper()) + '_ATTRIBUTES_PROJECT_ID']
  except: fail('The project id for integration ' + name + ' must be included in the config file as "' + str(name.upper()) + '_ATTRIBUTES_PROJECT_ID=<ID>"')

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
def getIntegrationAttributes():
  global mosaicConfig
  global integrationProjectId
  global integrationAttributes
  global integrationName
  global failedIntegrationAttributes

  # Attributes associated with this integration will end with the integration name in parentheses. Define this string for searching
  nameEnd = '(' + str(integrationName) + ')'

  # Get all the sample attribute data for the project connected to this integration
  try: data = json.loads(os.popen(api_sa.getSampleAttributes(mosaicConfig, integrationProjectId, False)).read())
  except: fail('Could not get sample attribute from the ' + str(integrationName) + ' project')
  if 'message' in data: fail('Could not get sample attribute from the ' + str(integrationName) + ' project. API returned message "' + str(data['message']) + '"')

  # Store the attribute ids, ignoring attributes with 'Z-score' in the name
  for attribute in data:
    if attribute['name'].endswith(nameEnd) and str('Z-score') not in attribute['name']: integrationAttributes[attribute['id']] = attribute['name']
    if attribute['name'].startswith('Failed ' + str(integrationName)): failedIntegrationAttributes[attribute['id']] = attribute['name']
 
# Parse the json file describing how to subset samples etc.
def parseJsonInput(jsonFile):
  global cohorts
  global includeFullCohort
  global primaryAttributes
  global integrationAttributes

  # Get the json data
  try: jsonHandle = open(jsonFile, 'r')
  except: fail('Could not open the json file: ' + jsonFile)
  try: jsonData = json.loads(jsonHandle.read())
  except: fail('Json file ' + jsonFile + ' is not valid')

  # First, check that there is a section describing how to build sample cohorts
  if 'Cohorts' not in jsonData: fail('The json input file (' + str(jsonFile) + ') requires a "Cohorts" section describing how to build sample cohorts')

  # Check the entries are valid and complete, and determine if project attributes need to be read in
  for cohort in jsonData['Cohorts']:

    # The 'type' field is necessary to determine if this subset is the full cohort, based on a sample or
    # project attribute
    try: cohortType = jsonData['Cohorts'][cohort]['type']
    except: fail('The field "type" is not present in the input json file for sample cohort "' + cohort + '"')

    # Each cohort needs the cutoff defined. Any samples whose absolute Z-score value is greated than the cutoff fail
    try: cutoff = jsonData['Cohorts'][cohort]['cutoff']
    except: fail('The field "cutoff" is not present in the input json file for sample cohort "' + cohort + '"')

    # If the type is "project", get the project attribute id and value to subset the samples
    if cohortType == 'project':
      try: attributeId = jsonData['Cohorts'][cohort]['project_attribute']
      except: fail('Cohort ' + cohort + ' is based on a project attribute, but the "project_attribute" field is not provided')

      # The project attribute value can be a string, a number, or a Boolean. Depending on the type,
      # different values and comparisons will be required
      if 'string' in jsonData['Cohorts'][cohort]: fail('Have not handled string comparisons')
      elif 'number' in jsonData['Cohorts'][cohort]: fail('Have not handled numerical comparisons')
      elif 'boolean' in jsonData['Cohorts'][cohort]:
        if type(jsonData['Cohorts'][cohort]['boolean']) != bool: fail('Cohort ' + str(cohort) + ' is determined with a Boolean project attribute, but the provided value (' + str(jsonData['Cohorts'][cohort]['boolean']) + ') is not Boolean')
        cohorts[cohort] = {'cutoff': cutoff, 'cohortType': 'project', 'attributeId': attributeId, 'type': 'bool', 'value': jsonData['Cohorts'][cohort]['boolean']}

    # If the type is "sample", get the sample attribute id and value to subset the samples
    elif cohortType == 'sample': fail('Not implemented subsetting on samples yet')

    # If the type is "all", no additional information is required, but it is noted that z-scores for the full
    # cohort are required
    elif cohortType == 'all':
      includeFullCohort = True
      cohorts['all'] = {'cutoff': cutoff}

    # If a different value is provided for the "type" field, fail
    else: fail('Cohort type "' + cohortType + '" is not valid')

  # Check if there is a "Primary_attributes" section in the json file. This is used to prioritize attributes in the
  # resulting conversation posted to Mosaic. Check that the supplied attributes are valid and store their ids
  if 'Primary_attributes' in jsonData:
    attributeNames = []
    attributeIds   = {}
    for attribute in jsonData['Primary_attributes']: attributeNames.append(attribute)

    # Loop over the attribute ids available for this integration and check that the supplied attributes are valid
    for attributeId in integrationAttributes:
      if integrationAttributes[attributeId] in attributeNames: attributeIds[integrationAttributes[attributeId]] = attributeId

    # If there are any attributes left in the attributeNames list, these are not valid
    if len(attributeNames) != len(attributeIds):
      text = 'The following primary attributes were not recognised. Ensure the input json contains valid attributes:\n'
      for attribute in attributeNames:
        if attribute not in attributeIds: text += '  ' + str(attribute) + '\n'
      fail(text)

    # Store the primary attribute ids in the order they appeared in the json
    for attribute in attributeNames: primaryAttributes.append(attributeIds[attribute])

# Build the cohorts that are constructed based on project attributes
def buildProjectAttributeCohorts(collectionId):
  global mosaicConfig
  global cohorts

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

  # Count the number of projects that are in this cohort
  noProjects = 0

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
      noProjects += 1
      for sampleId in projectIds[projectId]: cohorts[cohort]['sampleIds'].append(sampleId)

  # Store the number of projects associated with this cohort
  cohorts[cohort]['numberOfProjects'] = noProjects

# Build the cohort including all samples
def buildFullCohort():
  global projectIds
  global cohorts
  cohorts['all']['sampleIds'] = []

  # Loop over all projects and add all sample ids to the full cohort
  for projectId in projectIds:
    for sampleId in projectIds[projectId]: cohorts['all']['sampleIds'].append(sampleId)

  # Store the number of projects in the full cohort
  cohorts['all']['numberOfProjects'] = len(projectIds)

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
  global failedIntegrationAttributes
  global failedAttributesInProject

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

      # Proceed with all integration attributes. All other attributes in the project are not part of this integration and do not need
      # Z-scores calculating
      if attributeId in integrationAttributes:

        # Skip integration attributes that start with "Failed <integrationName>". These are counts of failed attributes and not integration attributes themselves
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

      # Also store information on the number of failed attributes
      elif attributeId in failedIntegrationAttributes:
        if projectId not in failedAttributesInProject: failedAttributesInProject[projectId] = {}
        if attributeId not in failedAttributesInProject[projectId]: failedAttributesInProject[projectId][attributeId] = []
        for sample in attribute['values']: failedAttributesInProject[projectId][attributeId].append(sample['sample_id'])

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

# Store the number of failed attributes by cohort for each sample
def storeFailureCounts(name):
  global mosaicConfig
  global projectIds
  global noFailures
  global cohorts
  global failedIntegrationAttributes
  global integrationName
  global integrationProjectId
  global sampleAttributeValues
  global failedAttributesInProject

  # Loop over all of the samples,in all of the projects,  import the failed attributes as required 
  for projectId in projectIds:
    attributeInProject = {}
    for sampleId in projectIds[projectId]:
      for cohort in cohorts:
        value         = 0
        attributeName = 'Failed ' + str(integrationName) +  ' attributes for ' + str(name) + ' ' + str(cohorts[cohort]['name'])

        # Check if this attribute exists in the integration project. If not, create it
        attributeId = False
        for integrationId in failedIntegrationAttributes:
          if str(attributeName) == str(failedIntegrationAttributes[integrationId]):
            attributeId = integrationId
            break

        # Create the attribute
        if not attributeId:
          try: data = json.loads(os.popen(api_sa.postSampleAttribute(mosaicConfig, attributeName, 'float', 'Null', 'true', 'Failed Attributes', 'Sample Count', integrationProjectId)).read())
          except: fail('Failed to create new attribute: ' + str(zscoreAttribute))
          if 'message' in data: fail('Failed to create new sample attribute (' + str(zscoreAttribute) + '). API returned message "' + str(data['message']) + '"')
          attributeId = data['id']

        # If the attribute is already in the project, it will be stored in the failedAttributesInProject dictionary
        if attributeId not in attributeInProject: attributeInProject[attributeId] = False
        if projectId in failedAttributesInProject:
          if attributeId in failedAttributesInProject[projectId]: attributeInProject[attributeId] = True

        # Only proceed if this sample is a member of the cohort
        if sampleId in cohorts[cohort]['sampleIds']:
          if sampleId not in noFailures: value = 0
          elif cohort not in noFailures[sampleId]: value = 0
          else: value = noFailures[sampleId][cohort]

          # Update the number of failed attributes in Mosaic for this sample and cohort
          # If the attribute is not in the project, import it
          if not attributeInProject[attributeId]: 
            importAttribute(projectId, attributeId, value)
            addValue(projectId, sampleId, attributeId, value)
            attributeInProject[attributeId] = True

          # If the attribute is in the project, but this sample does not have a value, POST a value
          elif projectId not in failedAttributesInProject: addValue(projectId, sampleId, attributeId, value)
          elif attributeId not in failedAttributesInProject[projectId]: addValue(projectId, sampleId, attributeId, value)
          elif sampleId not in failedAttributesInProject[projectId][attributeId]: addValue(projectId, sampleId, attributeId, value)

          # If the sample already has a value, update (PUT) it
          else: updateValue(projectId, sampleId, attributeId, value)

# Check if a project has a sample attribute and if not, import it
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

# Update a value for a sample attribute
def updateValue(projectId, sampleId, attributeId, value):
  global mosaicConfig

  try: data = json.loads(os.popen(api_sa.putSampleAttributeValue(mosaicConfig, projectId, sampleId, attributeId, value)).read())
  except: fail('Failed to update (PUT) sample ' + str(sampleId) + ' with value for attribute ' + str(attributeId))
  if 'message' in data: fail('Failed to update (PUT) sample ' + str(sampleId) + ' with value for attribute ' + str(attributeId) + '. API returned message "' + str(data['message']) + '"')

# Write out all failure information
def writeFailures(updateProjectId):
  global projectIds
  global failures
  global noFailures
  global cohorts
  global integrationName
  global primaryAttributes

  # Define the title of the conversation used to house information on failed samples
  title = str(integrationName) + ' information'

  # The conversation description begins with the date and basic information about what Z-scores were calculated for
  description  = '**' + str(integrationName) + ' information** posted on ' + str(datetime.date.today())
  description += '\\nZ-scores were calulated for the following sample cohorts:'

  # If all projects are to have project conversations updated, the supplied projectId must be 0. Otherwise, only update
  # the conversation for the provided projectId
  if int(updateProjectId) == 0:

    # Loop over all the projects to write out the failures for each sample in the project
    for projectId in projectIds: updateProjectConversation(projectId, title, description)
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
    if i == 0: projectDescription += ' **' + str(cohortName) + '** (' + str(len(cohorts[cohort]['sampleIds'])) + ' samples in ' + str(cohorts[cohort]['numberOfProjects']) + ' projects)'
    else: projectDescription += ', **' + str(cohortName) + '** (' + str(len(cohorts[cohort]['sampleIds'])) + ' samples in ' + str(cohorts[cohort]['numberOfProjects']) + ' projects)'
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
              projectDescription += str(sampleNames[sampleId]) + ' had ' + str(noFailures[sampleId][cohort]) + ' failures'
              firstSample = False
            else: projectDescription += ', ' + str(sampleNames[sampleId]) + ' had ' + str(noFailures[sampleId][cohort]) + ' failures'

    # If primary attributes were specified, include failures associated with these attributes first, then note that others failed
    projectDescription += '\\n'
    if len(primaryAttributes) != 0: projectDescription = primaryFailures(projectId, projectDescription)
    projectDescription = nonPrimaryFailures(projectId, projectDescription)

  # Get the id of the conversation to update
  conversationId, isNew = getConversationId(projectId)

  # Truncate the description if it is too long to fit in a Mosaic conversation
  if len(projectDescription) > 4999: projectDescription = projectDescription[0:4900] + '...\\n\\nOutput truncated'

  # Update the conversation description
  try: data = json.loads(os.popen(api_pc.putUpdateCoversation(mosaicConfig, str(title), str(projectDescription), str(projectId), conversationId)).read())
  except: fail('Could not update project conversation with title "' + str(title) + '" in project ' + str(projectId))
  if 'message' in data: fail('Could not update project conversation with title "' + str(title) + '" in project ' + str(projectId) + '. API returned the message "' + str(data['message']) + '"')

# Print a summary of primary attributes that failed
def primaryFailures(projectId, projectDescription):
  global projectIds
  global failures
  global primaryAttributes
  global hasPrimaryFailure
  global sampleNames
  hasPrimaryFailure = False
  sampleFailures    = {}

  # Loop over all samples in the project
  for sampleId in projectIds[projectId]:
    sampleFailures[sampleId] = False

    # Determine if any of the failing attributes are primary attributes
    if len(failures[sampleId]) > 0:
      for attributeId in failures[sampleId]:
        if attributeId in primaryAttributes:
          hasPrimaryFailure        = True
          sampleFailures[sampleId] = True

  # If the sample has failures in the primary attributes, include them in the description
  if not hasPrimaryFailure: projectDescription += '**All samples passed all primary attributes**'
  else:
    projectDescription += '### Failed primary attributes\\n'
    for sampleId in projectIds[projectId]:
      if not sampleFailures[sampleId]: projectDescription += '**Sample ' + str(sampleNames[sampleId]) + ' passed all attributes**\\n'
      else:
        projectDescription += '**Sample ' + str(sampleNames[sampleId]) + '**:\\n'
        for attributeId in failures[sampleId]:
          if attributeId in primaryAttributes:
            projectDescription += '&nbsp;&nbsp;' + str(integrationAttributes[attributeId]) + ': '
            for i, cohort in enumerate(failures[sampleId][attributeId]):
              if i == 0: projectDescription += str(cohorts[cohort]['id']) + ' (' + str(failures[sampleId][attributeId][cohort]) + ')'
              else: projectDescription += ', ' + str(cohorts[cohort]['id']) + ' (' + str(failures[sampleId][attributeId][cohort]) + ')'
            projectDescription += '\\n'

  projectDescription += '\\n'

  # Return the updated description
  return projectDescription

# Print a summary of non primary attributes that failed
def nonPrimaryFailures(projectId, projectDescription):
  global projectIds
  global failures
  global sampleNames
  global primaryAttributes

  # Provide a title
  if len(primaryAttributes) == 0: projectDescription += '### Failed attributes\\n'
  else: projectDescription += '### Failed non-primary attributes\\n'

  # Loop over all samples in the project
  for sampleId in projectIds[projectId]:

    # Determine if any of the failing attributes are primary attributes
    if len(failures[sampleId]) > 0:
      projectDescription += '**Sample ' + str(sampleNames[sampleId]) + '** failed:\\n'
      for attributeId in failures[sampleId]:
        if attributeId not in primaryAttributes:
          projectDescription += '&nbsp;&nbsp;' + str(integrationAttributes[attributeId]) + ': '
          for i, cohort in enumerate(failures[sampleId][attributeId]):
            if i == 0: projectDescription += str(cohorts[cohort]['id']) + ' (' + str(failures[sampleId][attributeId][cohort]) + ')'
            else: projectDescription += ', ' + str(cohorts[cohort]['id']) + ' (' + str(failures[sampleId][attributeId][cohort]) + ')'
          projectDescription += '\\n'

  # Return the updated description
  return projectDescription

# Get the conversation id of the conversation to update
def getConversationId(projectId):
  global mosaicConfig
  global integrationName
  conversationId = False
  isNew          = False
  limit          = 100
  title          = integrationName + ' information'

  # All z-score results are posted to a conversation in the project called '<INTEGRATION> information'. If this conversation does
  # not exist, create it
  try: data = json.loads(os.popen(api_pc.getCoversations(mosaicConfig, limit, 1, projectId)).read())
  except: fail('Could not get project conversations for project ' + str(projectId))
  if 'message' in data: fail('Could not get project conversations for project ' + str(projectId) + '. API returned the message "' + str(data['message']) + '"')

  # Get the number of pages of conversations
  noPages = math.ceil(float(data['count']) / float(limit))

  # Loop over the conversations and look for one with the name '<INTEGRATION> information'
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
    except: fail('Could not create a new conversation')
    if 'message' in data: fail('Could not create a new conversation. API returned the message "' + str(data['message']) + '"')
    conversationId = data['id']
    isNew          = True

  # Return the conversation id
  return conversationId, isNew

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables

# The mosaic config is used to request data from Mosaic
mosaicConfig = {}

# Define the list of allowed integrations
allowedIntegrations = ['Alignstats', 'Peddy']

# The integrationProjectId defines the project that contains all of the attributes for this integration. Also
# store the attribute ids of all the sample attributes associated with the integration
integrationProjectId        = False
integrationAttributes       = {}
integrationName             = False
failedIntegrationAttributes = {}
failedAttributesInProject   = {}

# Store all of the project ids in the collection, along with the samples
projectIds = {}

# Store the list of samples in each cohort. Also determine if the cohort of all samples is required
cohorts           = {}
includeFullCohort = False

# Store primary attributes
primaryAttributes = []
hasPrimaryFailure = False

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
version = "0.0.4"

if __name__ == "__main__":
  main()
