from __future__ import print_function
from os.path import exists

import os
import argparse
import json
import math
import sys

# Add the path of the common functions and import them
from sys import path
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/common_components")
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/api_commands")
import mosaic_config
import api_attributes as api_a
import api_conversations as api_c
import api_dashboards as api_d
import api_projects as api_p
import api_project_roles as api_pr
import api_project_attributes as api_pa
import api_project_interval_attributes as api_pia
import api_project_conversations as api_pc
import api_sample_attributes as api_sa

def main():
  global startingAttributes
  global mosaicConfig
  print('TEST')
  print(sys.version)
  exit(0)

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {'MOSAIC_TOKEN': {'value': args.token, 'desc': 'An access token', 'long': '--token', 'short': '-t'},
                    'MOSAIC_URL': {'value': args.url, 'desc': 'The api url', 'long': '--url', 'short': '-u'},
                    'MOSAIC_ATTRIBUTES_PROJECT_ID': {'value': args.attributes_project, 'desc': 'The public attribtes project id', 'long': '--attributes_project', 'short': '-a'}}
  mosaicConfig   = mosaic_config.mosaicConfigFile(args.config)
  mosaicConfig   = mosaic_config.commandLineArguments(mosaicConfig, mosaicRequired)

  # Get all of the available template projects from the Attribute project
  availableTemplates, assignedTemplateId = getAvailableTemplates(args)

  # If the requested template does not exist, fail
  templateId = availableTemplates[args.template] if args.template in availableTemplates else fail('Requested template (' + args.template + ') does not exist')

  # Get all the information about the template project, including what is pinned to the dashboard
  templateAttributes, templateEvents = getProjectAttributes(templateId)
  templateIntervals     = api_pia.getIntervalsIdToName(mosaicConfig, templateId)
  templateConversations = getProjectConversations(templateId)
  templateAttributes, templateConversations = dashboard(templateId, templateAttributes, templateConversations)

  # Get information about the project to which the template will be applied. This will be used to ensure data is
  # not overwritten as part of the template application
  projectAttributes, projectEvents = getProjectAttributes(args.project_id)
  projectIntervals     = api_pia.getIntervalsIdToName(mosaicConfig, args.project_id)
  projectConversations = getProjectConversations(args.project_id)
  projectAttributes, projectConversations = dashboard(args.project_id, projectAttributes, projectConversations)

  # Update the project with the information from the template
  updateAttributes(args.project_id, templateAttributes, projectAttributes)
  updateTiming(args.project_id, templateEvents, templateIntervals, projectEvents, projectIntervals)
  updateConversations(args.project_id, templateConversations, projectConversations)

  # Import the "Assigned Template" project attribute and set the value to Template:version
  assignTemplateAttribute(args.project_id, args.template, projectAttributes, assignedTemplateId)

# Input options
def parseCommandLine():
  global version

  parser = argparse.ArgumentParser(description='Process the command line')

  # Required arguments
  parser.add_argument('--project_id', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")
  parser.add_argument('--template', '-m', required = True, metavar = "string", help = "The template to run")

  # Optional pipeline arguments
  parser.add_argument('--attributes_file', '-f', required = False, metavar = "file", help = "The input file listing the Peddy attributes")
  parser.add_argument('--output', '-o', required = False, metavar = "file", help = "The output file containing the values to upload")
  parser.add_argument('--background', '-b', required = False, metavar = "file", help = "The output json containing background ancestry information")

  # Optional mosaic arguments
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "The config file for Mosaic")
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic")
  parser.add_argument('--attributes_project', '-a', required = False, metavar = "integer", help = "The Mosaic project id that contains public attributes")

  # Store the version
  parser.add_argument('--version', '-v', action="version", version='Mosaic templates version: ' + str(version))

  return parser.parse_args()

# Find all templates from the Attributes project. Look through all public attributes and identify
# those that begin with "Template". The value associated with these attributes is the mosaic project
# id for the template to emulate.
def getAvailableTemplates(args):
  global mosaicConfig
  availableTemplates = {}

  # Get all the project attributes
  data = api_pa.getProjectAttributes(mosaicConfig, mosaicConfig['MOSAIC_ATTRIBUTES_PROJECT_ID'])

  # Loop over all the attributes and identify the templates
  for attribute in data:

    # Look for attributes that point to template projects
    if attribute['name'].startswith('Template '):
      templateName = attribute['name'].split(' ')[1]

      # Loop over the values for the attribute for the different projects it is in
      for project in attribute['values']:
        if int(project['project_id']) == int(mosaicConfig['MOSAIC_ATTRIBUTES_PROJECT_ID']): availableTemplates[templateName] = project['value']

    # Also look for an attribute called 'Assigned Template'. For every project where a template is run, this attribute is set to the
    # name of the executed template
    elif attribute['name'] == 'Assigned Template': assignedTemplateId = attribute['id']

  # Return the available templates
  return availableTemplates, assignedTemplateId

# Get all the information about a projects attributes
def getProjectAttributes(projectId):
  global mosaicConfig
  generalAttributes = {}
  timingAttributes  = {}

  # Get all the attributes
  data = api_pa.getProjectAttributes(mosaicConfig, projectId)

  # Store information on the attributes
  for attribute in data:

    # Get the attribute value associated with this project
    attributeValue = False
    for value in attribute['values']:
      if value['project_id'] == projectId: attributeValue = value['value']

    # Store the information
    if attribute['value_type'] == 'timestamp': timingAttributes[attribute['id']] = {'name': attribute['name'], 'value': attributeValue, 'isPublic': attribute['is_public']}
    else: generalAttributes[attribute['id']] = {'name': attribute['name'], 'value': attributeValue, 'isPinned': False, 'isNamePinned': False, 'isPublic': attribute['is_public']}

  # Return the attributes
  return generalAttributes, timingAttributes

# Get all the existing conversations
def getProjectConversations(projectId):
  global mosaicConfig

  # Get all the conversations from the project and add the isPinned flag as false
  conversations = api_pc.getConversationsIdToTitleDesc(mosaicConfig, projectId)
  for convId in conversations: conversations[convId]['isPinned'] = False

  # Return the list of conversations in the project
  return conversations

# Determine what is pinned to the project dashboard
def dashboard(projectId, projectAttributes, projectConversations):
  global mosaicConfig

  # Get the dashboard information
  data = api_d.getDashboard(mosaicConfig, projectId)
  for dashboardObject in data:

    # Ignore all default items. These can't be modified
    if not dashboardObject['is_default']:

      # For project attributes, update the stored attributes to indicate that they need to be pinned to the dashboard and whether
      # they should be pinned with or without the attribute name.
      if dashboardObject['type'] == 'project_attribute':
        attributeId = dashboardObject['attribute_id']
        if attributeId not in projectAttributes: fail('Project attribute ' + str(attributeId) + ' was not found in the supplied attributes dictionary for project ' + str(projectId))

        # Check if the name should be pinned, then update the attribute
        projectAttributes[attributeId]['isPinned'] = True
        projectAttributes[attributeId]['isNamePinned'] = True if dashboardObject['should_show_name_in_badge'] else False

      # For conversations
      elif dashboardObject['type'] == 'conversation':
        conversationId = dashboardObject['project_conversation_id']
        if conversationId not in projectConversations: fail('Conversation ' + str(conversationId) + ' was not found in the supplied conversations dictionary for project ' + str(projectId))
        projectConversations[conversationId]['isPinned'] = True

  # Return the information
  return projectAttributes, projectConversations

# Update the project attributes based on the template
def updateAttributes(projectId, templateAttributes, projectAttributes):
  global mosaicConfig

  # Loop over all of the template attributes
  for attributeId in templateAttributes:
    name         = templateAttributes[attributeId]['name']
    value        = templateAttributes[attributeId]['value']
    isPublic     = templateAttributes[attributeId]['isPublic']
    isPinned     = templateAttributes[attributeId]['isPinned']
    isNamePinned = 'true' if templateAttributes[attributeId]['isNamePinned'] else 'false'

    # Only import the attribute if it doesn't already exist in the project being updated and is public
    if attributeId not in projectAttributes and isPublic:
      importData = api_pa.importProjectAttribute(mosaicConfig, projectId, attributeId, value)

      # Store the project attribute. This attribute was just imported and so is not currently pinned
      projectAttributes[attributeId] = {'name': name, 'value': value, 'isPinned': False, 'isNamePinned': isNamePinned, 'isPublic': isPublic}

    # If the attribute should be pinned, and isn't already pined, pin it
    if isPinned and not projectAttributes[attributeId]['isPinned']: api_d.pinProjectAttribute(mosaicConfig, projectId, attributeId, isNamePinned)

# Update the timing information for the project
def updateTiming(projectId, templateEvents, templateIntervals, projectEvents, projectIntervals):
  global mosaicConfig

  # Loop over all the events in the template
  for eventId in templateEvents:
    name  = templateEvents[eventId]['name']
    value = templateEvents[eventId]['value']
    if not value: value = 'null'

    # Only add events that are not already in the project
    if eventId not in projectEvents: api_pa.importProjectAttribute(mosaicConfig, projectId, eventId, value)
  
  # Now add the intervals
  for intervalId in templateIntervals:
    name = templateIntervals[intervalId]['name']

    # Only import intervals that are not already in the project
    if intervalId not in projectIntervals: api_pia.postInterval(mosaicConfig, projectId, intervalId)

# Update the conversations
def updateConversations(projectId, templateConversations, projectConversations):
  global mosaicConfig

  # Get the titles of all conversations that exist in the project being updated
  existingTitles = []
  for convId in projectConversations: existingTitles.append(projectConversations[convId]['title'])

  # Loop over the conversations in the template
  for convId in templateConversations:
    title       = templateConversations[convId]['title']
    description = templateConversations[convId]['description']
    isPinned    = templateConversations[convId]['isPinned']

    # The description might contain multiple lines which will break the curl command. Replace all newlines with \n
    if description:
      if "\n" in description: description = description.replace("\n", "\\n")

    # Only create the conversation if a conversations of the same name does not already exist
    if title not in existingTitles:
      createdConvId = api_pc.createConversation(mosaicConfig, projectId, title, description)

      # Pin the conversation if required
      if isPinned: api_d.pinConversation(mosaicConfig, projectId, createdConvId)
    
# Import the "Assigned Template" project attribute and set the value to Template:version
def assignTemplateAttribute(projectId, templateName, projectAttributes, attributeId):
  global mosaicConfig
  global version

  # Define the attribute value as Template:version
  value = str(templateName) + ":" + str(version)

  # If the 'Assigned Template' attribute id was not found, fail
  if not attributeId: fail('Could not find the "Assigned Template" attribute in the public attributes project')

  # If the Assigned Template attribute is not already in the project, import it, otherwise, update the value
  if attributeId not in projectAttributes: api_pa.importProjectAttribute(mosaicConfig, projectId, attributeId, value)
  else: api_pa.updateProjectAttribute(mosaicConfig, projectId, attributeId, value)

# If problems are found with the templates, fail
def fail(text):
  print(text)
  exit(1)

# Initialise global variables

# Attributes from the config file
mosaicConfig = {}

# Store the version
version = "1.04"

if __name__ == "__main__":
  main()
