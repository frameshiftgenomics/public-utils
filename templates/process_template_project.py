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
import api_dashboards as api_d
import api_projects as api_p
import api_project_attributes as api_pa
import api_sample_attributes as api_sa

def main():
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {'MOSAIC_TOKEN': {'value': args.token, 'desc': 'An access token', 'long': '--token', 'short': '-t'},
                    'MOSAIC_URL': {'value': args.url, 'desc': 'The api url', 'long': '--url', 'short': '-u'},
                    'MOSAIC_ATTRIBUTES_PROJECT_ID': {'value': args.attributes_project, 'desc': 'The public attributes project id', 'long': '--attributes_project', 'short': '-a'}}
  mosaicConfig   = mosaic_config.mosaicConfigFile(args.config)
  mosaicConfig   = mosaic_config.commandLineArguments(mosaicConfig, mosaicRequired)

  # Open the json describing the template and ensure it is valid
  templateData = openJson(args.template)

  # Get the template name, then get all the existing template projects in Mosaic and determine if the requested
  # template exists
  name       = templateData['name'] if 'name' in templateData else fail('Field "name" is missing from the template json')
  templateId = getExistingTemplates(name)

  # Get all of the sample and projects attributes in the public attributes project and in the template project
  sampleAttributes  = api_sa.getSampleAttributesDictNameId(mosaicConfig, mosaicConfig['MOSAIC_ATTRIBUTES_PROJECT_ID'])
  projectAttributes = api_pa.getProjectAttributesDictNameId(mosaicConfig, mosaicConfig['MOSAIC_ATTRIBUTES_PROJECT_ID'])
  templateSampleAttributes  = api_sa.getSampleAttributesDictNameId(mosaicConfig, templateId)
  templateProjectAttributes = api_pa.getProjectAttributesDictNameId(mosaicConfig, templateId)

  # Get information on the template project dashboard
  dashboard = api_d.getDashboard(mosaicConfig, templateId)

  # Loop over all of the sample and project attributes listed in the json and check if they exist in the public
  # attributes project. If so, import them into the template (unless they are already present in the template project).
  # If not, create the attributes in the public attributes project and import them
  for attribute in templateData['sample_attributes']:
    if attribute not in sampleAttributes: attributeId = createAttribute('sample', attribute, templateData['sample_attributes'][attribute])
    else: attributeId = sampleAttributes[attribute]
    if attribute not in templateSampleAttributes: api_sa.importSampleAttribute(mosaicConfig, templateId, attributeId)
  for attribute in templateData['project_attributes']:
    if attribute not in projectAttributes: attributeId = createAttribute('project', attribute, templateData['project_attributes'][attribute])
    else: attributeId = projectAttributes[attribute]
    if attribute not in templateProjectAttributes: api_pa.importProjectAttribute(mosaicConfig, templateId, attributeId, templateData['project_attributes'][attribute]['value'])
    importProjectAttribute(templateId, templateProjectAttributes, dashboard, attribute, attributeId, templateData['project_attributes'][attribute])

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Arguments related to the config file
  parser.add_argument('--config', '-c', required = False, metavar = 'string', help = 'A config file containing token / url information')
  parser.add_argument('--token', '-t', required = False, metavar = 'string', help = 'The Mosaic authorization token')
  parser.add_argument('--url', '-u', required = False, metavar = 'string', help = 'The base url for Mosaic curl commands, up to an including "api". Do NOT include a trailing /')
  parser.add_argument('--attributes_project', '-a', required = False, metavar = 'integer', help = 'The Mosaic project id that contains public attributes')

  # Arguments related to the event
  parser.add_argument('--template', '-m', required = True, metavar = 'string', help = 'The json describing the template')

  return parser.parse_args()

# Open the json describing the template and ensure it is valid
def openJson(template):

  # Check that the file defining the filters exists
  if not exists(template): fail('Could not find the json file ' + str(template))

  # The file describing the template should be in json format. Fail if the file is not valid
  try: jsonFile = open(template, "r")
  except: fail('Could not open the json file: ' + str(template))
  try: data = json.load(jsonFile)
  except: fail('Could not read contents of json file ' + str(template) + '. Check that this is a valid json')
  jsonFile.close()

  # Return the json data
  return data

# Get all existing Mosaic templates
def getExistingTemplates(name):
  global mosaicConfig
  existingTemplates = {}
  templateName      = 'Template ' + str(name)

  # Get the existing projects and extract those that begin with 'Template'
  existingProjects = api_p.getProjectsDictNameId(mosaicConfig)
  for template in existingProjects:
    if template.startswith('Template '): existingTemplates[template] = existingProjects[template]

  # Check if the requested template exists. If not, create the template and store the id

########################
########################
######################## IF CREATING TEMPLATE - NEED TO ADD ATTRIBUTE TO PUBLIC ATTRIBUTES
########################
########################
  if templateName in existingTemplates: templateId = existingTemplates[templateName]
  else: templateId = api_p.createProject(mosaicConfig, name, 'Template project', 'GRCh38', 'protected')

  # Return the template id
  return templateId

# Create a new public project attribute
def createAttribute(attributeType, attribute, attributeInfo):
  global mosaicConfig

  # Create the new attribute
  description = str(attributeInfo['description'])
  value       = attributeInfo['value']
  valueType   = str(attributeInfo['type'])
  if (valueType != 'string') and (valueType != 'float'): fail('Project attribute ' + str(attribute) + ' has type "' + valueType + '". Allowed values are "string", "float"')
  if attributeType == 'sample': return api_sa.createPublicSampleAttribute(mosaicConfig, mosaicConfig['MOSAIC_ATTRIBUTES_PROJECT_ID'], attribute, value, valueType, '', '')
  elif attributeType == 'project': return api_pa.createProjectAttribute(mosaicConfig, mosaicConfig['MOSAIC_ATTRIBUTES_PROJECT_ID'], attribute, description, value, valueType, 'true')

# Import a public project attribute into the template project and pin to the dashboard if required
def importProjectAttribute(templateId, templateAttributes, dashboard, attribute, attributeId, attributeInfo):
  global mosaicConfig

  # Get the value to apply as the default for the project attribute in the template as well as whether
  # this attribute needs to be pinned to the dashboard
  value  = attributeInfo['value']
  pinned = attributeInfo['pinned'] if 'pinned' in attributeInfo else False

  # Check if the attribute has already been imported into the template and import if necessary. If the attribute is
  # already in the template project, check if it has been pinned to the dashboard. If it has, we do not want to pin
  # it again
  isPinned = False
  #if attributeId not in templateAttributes: api_pa.importProjectAttribute(mosaicConfig, templateId, attributeId, value)
  #else:
  for record in dashboard:
    if record['type'] == 'project_attribute' and record['attribute_id'] == attributeId and record['is_active']: isPinned = True

  # Pin the attribute if required. First check if the attribute is already pinned
  if pinned and not isPinned:
    if str(pinned) == 'value': api_d.pinProjectAttribute(mosaicConfig, templateId, attributeId, 'false')
    elif str(pinned) == 'name_value': api_d.pinProjectAttribute(mosaicConfig, templateId, attributeId, 'true')
    else: fail('Project attribute "' + str(attribute) + '" has value "' + str(pinned) + '" for its pinned status. Allowed values are "value" and "name_value"')

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables
mosaicConfig = {}

if __name__ == "__main__":
  main()
