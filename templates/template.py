#!/usr/bin/python

from __future__ import print_function
from os.path import exists

import os
import argparse
import json
import math

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

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {"token": True, "url": True, "attributesProjectId": True}
  mosaicConfig   = mosaic_config.parseConfig(args, mosaicRequired)

  # Get all of the available template projects from the Attribute project
  availableTemplates = getAvailableTemplates(args)

  # If the requested template does not exist, fail
  templateId = availableTemplates[args.template] if args.template in availableTemplates else fail("Requested template (" + args.template + ") does not exist")

  # Get all the information about the template project, including what is pinned to the dashboard
  templateAttributes, templateEvents = getProjectAttributes(templateId)
  templateIntervals     = getProjectIntervals(templateId)
  templateConversations = getProjectConversations(templateId)
  templateAttributes, templateConversations = dashboard(templateId, templateAttributes, templateConversations)

  # Get information about the project to which the template will be applied. This will be used to ensure data is
  # not overwritten as part of the template application
  projectAttributes, projectEvents = getProjectAttributes(args.project)
  projectIntervals     = getProjectIntervals(args.project)
  projectConversations = getProjectConversations(args.project)
  projectAttributes, projectConversations = dashboard(args.project, projectAttributes, projectConversations)

  # Update the project with the information from the template
  updateAttributes(args.project, templateAttributes, projectAttributes)
  updateTiming(args.project, templateEvents, templateIntervals, projectEvents, projectIntervals)
  updateConversations(args.project, templateConversations, projectConversations)

  # Import the "Assigned Template" project attribute and set the value to Template:version
  assignTemplateAttribute(args.project, args.template, projectAttributes)

# Input options
def parseCommandLine():
  global version

  parser = argparse.ArgumentParser(description='Process the command line')

  # Required arguments
  parser.add_argument('--project', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")
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
  jsonData = json.loads(os.popen(api_pa.getProjectAttributes(mosaicConfig, mosaicConfig["attributesProjectId"])).read())

  # Loop over all the attributes and identify the templates
  for attribute in jsonData:
    if attribute["name"].startswith("Template "):
      templateName = attribute["name"].split(" ")[1]
      attributeId  = attribute["id"]

      # Loop over the values for the attribute for the different projects it is in
      for project in attribute["values"]:
        if int(project["project_id"]) == int(mosaicConfig["attributesProjectId"]):
          availableTemplates[templateName] = project["value"]

  # Return the available templates
  return availableTemplates

# Get all the information about a projects attributes
def getProjectAttributes(projectId):
  global mosaicConfig
  generalAttributes = {}
  timingAttributes  = {}

  # Get all the attributes
  data = json.loads(os.popen(api_pa.getProjectAttributes(mosaicConfig, projectId)).read())

  # Store information on the attributes
  for attribute in data:
    attributeId     = attribute['id']
    attributeName   = attribute['name']
    attributePublic = attribute['is_public']

    # Get the attribute value associated with this project
    attributeValue = False
    for value in attribute['values']:
      if value['project_id'] == projectId: attributeValue = value['value']

    # Store the information
    if attribute['value_type'] == "timestamp": timingAttributes[attributeId] = {'name': attributeName, 'value': attributeValue, 'isPublic': attributePublic}
    else: generalAttributes[attributeId] = {'name': attributeName, 'value': attributeValue, 'isPinned': False, 'isNamePinned': False, 'isPublic': attributePublic}

  return generalAttributes, timingAttributes

# Get all of the timing intervals
def getProjectIntervals(projectId):
  global mosaicConfig
  intervals = {}

  # Get all project intervals
  data = json.loads(os.popen(api_pia.getProjectIntervalAttributes(mosaicConfig, projectId)).read())
  for interval in data:
    intervalId   = interval['id']
    intervalName = interval['name']
    intervals[intervalId] = {'name': intervalName}

  # Return the project intervals
  return intervals

# Get all the existing conversations
def getProjectConversations(projectId):
  global mosaicConfig
  conversations = {}

  # Begin by getting all the conversations from the project. The resulting object is paginated, so determine the number of conversations
  # and consequently the number of pages of conversations that need to be returned
  data = json.loads(os.popen(api_pc.getCoversations(mosaicConfig, 100, 1, projectId)).read())

  # Determine the number of pages
  noPages = int( math.ceil( float(data["count"]) / float(100.) ) )

  # Loop over all necessary pages
  for i in range(0, noPages):
    data = json.loads(os.popen(api_pc.getCoversations(mosaicConfig, 100, i + 1, projectId)).read())

    # Loop over the conversations from all the templates and create then
    for conversation in data["data"]: 
      id          = conversation['id']
      title       = conversation['title']
      description = conversation['description']
      conversations[id] = {'title': title, 'description': description, 'isPinned': False}

  # Return the list of conversations in the project
  return conversations

# Determine what is pinned to the project dashboard
def dashboard(projectId, projectAttributes, projectConversations):
  global mosaicConfig

  # Get the dashboard information
  data = json.loads(os.popen(api_d.getDashboard(mosaicConfig, projectId)).read())

  for dashboardObject in data:

    # Ignore all default items. These can't be modified
    if not dashboardObject["is_default"]:

      # For project attributes, update the stored attributes to indicate that they need to be pinned to the dashboard and whether
      # they should be pinned with or without the attribute name.
      if dashboardObject['type'] == "project_attribute":
        attributeId = dashboardObject['attribute_id']
        if attributeId not in projectAttributes: fail("Project attribute " + str(attributeId) + " was not found in the supplied attributes dictionary for project " + str(projectId))

        # Check if the name should be pinned, then update the attribute
        projectAttributes[attributeId]['isPinned'] = True
        projectAttributes[attributeId]['isNamePinned'] = True if dashboardObject['should_show_name_in_badge'] else False

      # For conversations
      elif dashboardObject['type'] == 'conversation':
        conversationId = dashboardObject['project_conversation_id']
        if conversationId not in projectConversations: fail("Conversation " + str(conversationId) + " was not found in the supplied conversations dictionary for project " + str(projectId))
        projectConversations[conversationId]['isPinned'] = True

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
      try: importData = json.loads(os.popen(api_pa.postImportProjectAttribute(mosaicConfig, attributeId, value, projectId)).read())
      except: fail("Couldn't add attribute " + str(name) + " to the project")

      # If the attribute should be pinned, pin it
      if isPinned:
        try: pinData = json.loads(os.popen(api_d.postPinAttribute(mosaicConfig, attributeId, isNamePinned, projectId)).read())
        except: fail("Couldn't pin attribute " + str(name) + "to the project")

# Update the timing information for the project
def updateTiming(projectId, templateEvents, templateIntervals, projectEvents, projectIntervals):
  global mosaicConfig

  # Loop over all the events in the template
  for eventId in templateEvents:
    name  = templateEvents[eventId]['name']
    value = templateEvents[eventId]['value']

    # Only add events that are not already in the project
    if eventId not in projectEvents:
      try: importData = json.loads(os.popen(api_pa.postImportProjectAttribute(mosaicConfig, eventId, value, projectId)).read())
      except: fail("Couldn't add event " + str(name) + " to the project")
  
  # Now add the intervals
  for intervalId in templateIntervals:
    name = templateIntervals[intervalId]['name']

    # Only import intervals that are not already in the project
    if intervalId not in projectIntervals:
      try: importData = json.loads(os.popen(api_pia.postImportProjectIntervalAttribute(mosaicConfig, intervalId, projectId)).read())
      except: fail("Couldn't import interval " + str(name) + " to the project")

# Update the conversations
def updateConversations(projectId, templateConversations, projectConversations):
  global mosaicConfig

  # Get the titles of all conversations that exist in the project being updated
  existingTitles = []
  for conversationId in projectConversations: existingTitles.append(projectConversations[conversationId]['title'])

  # Loop over the conversations in the template
  for conversationId in templateConversations:
    title       = templateConversations[conversationId]['title']
    description = templateConversations[conversationId]['description']
    isPinned    = templateConversations[conversationId]['isPinned']

    # The description might contain multiple lines which will break the curl command. Replace all newlines with \n
    if description:
      if "\n" in description: description = description.replace("\n", "\\n")

    # Only create the conversation if a conversations of the same name does not already exist
    if title not in existingTitles:
      try: postData = json.loads(os.popen(api_pc.postCoversation(mosaicConfig, title, description, projectId)).read())
      except: fail("Couldn't create conversation with the title " + str(title))

      # Get the id of the created conversation. This will be required to pin the conversation
      createdConversationId = postData['id']

      # Pin the conversation if required
      if isPinned:
        try: pinData = json.loads(os.popen(api_d.postPinConversation(mosaicConfig, createdConversationId, projectId)).read())
        except: fail("Couldn't pin conversations with title " + str(title))
    
# Import the "Assigned Template" project attribute and set the value to Template:version
def assignTemplateAttribute(projectId, templateName, projectAttributes):
  global mosaicConfig
  global version

  # Define the attribute value as Template:version
  value = str(templateName) + ":" + str(version)

  # Get the id of the "Assigned Template" attribute from the public attributes project
  try: data = json.loads(os.popen(api_pa.getProjectAttributes(mosaicConfig, mosaicConfig['attributesProjectId'])).read())
  except: fail("Couldn't get attributes from the public attributes project")
  attributeId = False
  for attribute in data:
    if attribute['name'] == "Assigned Template": attributeId = attribute['id']

  # If the attribute id was not found, fail
  if not attributeId: fail("Couldn't find the \"Assigned Template\" attribute in the public attributes project")

  # If the Assigned Template attribute is not already in the project, import it, otherwise, update the value
  if attributeId not in projectAttributes: data = json.loads(os.popen(api_pa.postImportProjectAttribute(mosaicConfig, attributeId, value, projectId)).read())
  else: data = json.loads(os.popen(api_pa.putProjectAttribute(mosaicConfig, value, projectId, attributeId)).read())

# If problems are found with the templates, fail
def fail(text):
  print(text)
  exit(1)

# Initialise global variables

# Attributes from the config file
mosaicConfig = {}

# Store the version
version = "1.01"

if __name__ == "__main__":
  main()
