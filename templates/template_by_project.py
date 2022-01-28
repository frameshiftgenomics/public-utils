#!/usr/bin/python

from __future__ import print_function
from os.path import exists

import os
import argparse
import json
import math

def main():
  global startingAttributes

  # Parse the command line
  args = parseCommandLine()

  # Check the api directory is correct
  checkApi(args)

  # Get all of the available template projects from the Attribute project
  getAvailableTemplates(args)

  # Check that the requested template exists, and if so, determine if this template contains links
  # to other templates
  templateOrder = checkTemplate(args)

  # Add the requested template to the end of the list. This is the last template to be processed and supersedes
  # all others
  templateOrder.append(args.template)

  # Determine the starting status of the project
  getStartingAttributes(args)

  # Get a list of users for the project
  getProjectUserIds(args)

  # Loop over the templates and pull in the relevant information
  for template in templateOrder: processTemplateProject(args, template)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line')
  parser.add_argument('--token', '-t', required = True, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = True, metavar = "string", help = "The base url for Mosaic curl commands, up to an including \"api\". Do NOT include a trailing /")
  parser.add_argument('--apiCommands', '-c', required = True, metavar = "string", help = "The path to the directory of api commands")
  parser.add_argument('--attributesProject', '-a', required = True, metavar = "integer", help = "The Mosaic project id that contains public attributes")
  parser.add_argument('--project', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")
  parser.add_argument('--template', '-m', required = True, metavar = "string", help = "The template to run")

  return parser.parse_args()

# Check the api directory is correct
def checkApi(args):

  # Check that all the api commands used in this script exist.
  apiCommands = {}
  apiCommands["get_project_attributes.sh"] = True
  apiCommands["get_user_project_attributes.sh"] = True
  apiCommands["put_project_attribute_value.sh"] = True
  apiCommands["import_project_attribute.sh"] = True
  apiCommands["pin_attribute.sh"] = True
  apiCommands["get_dashboard.sh"] = True
  apiCommands["post_conversation.sh"] = True
  apiCommands["get_project_conversations.sh"] = True

  isMissing = False
  for command in apiCommands:
    if not exists(args.apiCommands + "/" + command):
      isMissing = True
      apiCommands[command] = False

  # If any of the api commands are missing fail
  if isMissing:
    print("The following api commands were not found. Please check the supplied path, and that the public-utils repo is up to date.")
    for command in apiCommands:
      if not apiCommands[command]: print("  ", args.apiCommands + "/" + command)
    print()
    fail("Terminated as a result of missing api commands")

# Find all templates from the Attributes project. Look through all public attributes and identify
# those that begin with "Template". The value associated with these attributes is the mosaic project
# id for the template to emulate.
def getAvailableTemplates(args):
  global availableTemplates
  global templateAttributes
  global templateProjects
  global templateOrder

  # Get all the project attributes
  command  = args.apiCommands + "/get_project_attributes.sh " + str(args.token) + " " + str(args.url) + " " + str(args.attributesProject)
  jsonData = json.loads(os.popen(command).read())

  # Loop over all the attributes and identify the templates
  for attribute in jsonData:
    if attribute["name"].startswith("Template "):
      templateName = attribute["name"].split(" ")[1]
      attributeId  = attribute["id"]

      # Loop over the values for the attribute for the different projects it is in
      for project in attribute["values"]:
        if int(project["project_id"]) == int(args.attributesProject):
          availableTemplates[templateName]    = {"projectId": project["value"], "attributeId": attribute["id"], "contains_templates": []}
          templateAttributes[attribute["id"]] = templateName
          templateProjects[project["value"]]  = templateName

  # Get the values for the template attributes across all projects
  command  = args.apiCommands + "/get_user_project_attributes.sh " + str(args.token) + " " + str(args.url)
  jsonData = json.loads(os.popen(command).read())
  for attribute in jsonData:

    # Check if this attribute is a template attribute
    if attribute["id"] in templateAttributes:
      templateName = templateAttributes[attribute["id"]]

      # Loop over the projects that have this public attribute (this assumes that the user running this script has
      # access to all necessary projects - this script should be run by admins)
      for project in attribute["values"]:

        # Ignore this entry if the project_id is that of the public attributes project. All template attributes
        # are in the public attributes project by design
        if int(project["project_id"]) != int(args.attributesProject):

          # Get the name of the template this template attribute appears in, then store this template along with the order it
          # should be processed in with this template
          appearsIn = templateProjects[project["project_id"]]
          availableTemplates[appearsIn]["contains_templates"].append({"template": templateName, "order": project["value"]})

# Check that the requested template exists. If so, determine all the nested templates, ensure there are not problems
# with the nesting structure, and determine the order in which templates should be implemented.
def checkTemplate(args):
  global availableTemplates

  if args.template not in availableTemplates:
    print("Requested template (", args.template, ") does not exist")
    exit(1)

  # Get the templates contained within the requested template and check that no two contained templates contain the
  # same value. This value is used to determine the order in which the templates are processed, so they must be unique
  # integers
  completeTemplateOrder = processNestedTemplates(args.template)

  # Now loop over the list of contained templates and determine if they also contained nested templates to build up
  # the complete order of templates to be processed
  processTemplates  = []
  observedTemplates = []
  for template in completeTemplateOrder:
    processTemplates.append(template)
    observedTemplates.append(template)

  # Loop until all nested templates have been processed
  while len(processTemplates) > 0:
    nextTemplate  = processTemplates.pop(0)
    templateOrder = processNestedTemplates(nextTemplate)

    # Append the additional templates to the list of templates to process. If a template has already been seen, the
    # templates form an infinite loop e.g. template1 contains template2, which itself contains template1. If this
    # is the case, fail.
    for observedTemplate in templateOrder:
      if observedTemplate in observedTemplates:
        print("Template ", observedTemplate, " has been seen multiple times, so creates a nesting problem", sep = "")
        exit(1)
      else:
        observedTemplates.append(observedTemplate)
        completeTemplateOrder.insert(0, observedTemplate)
        processTemplates.insert(0, observedTemplate)

  return completeTemplateOrder

# Get the order of nested templates for a specific template
def processNestedTemplates(template):
  global availableTemplates

  observedOrder = {}
  templateOrder = []
  for template in availableTemplates[template]["contains_templates"]:
    if template["order"] in observedOrder:
      print("Template ", template, " contains multiple template project attributes with the same value", sep = "")
      exit(1)

    # Check that the order is an integer
    if type(template["order"]) != int:
      print("Template ", template, " contains a non-integer template project attribute: ", template["order"], sep = "")
      exit(1)

    # Store the order of this template
    observedOrder[template["order"]] = template["template"]

  # Loop over the sorted order of the contained templates and add to a list in the correct order
  for order in sorted(observedOrder.keys()): templateOrder.append(observedOrder[order])

  return templateOrder

# Get all the proect attributes in the working project prior to running the template. If the template is run on an
# existing project, existing attributes will not be overwritten
def getStartingAttributes(args):
  global startingAttributes

  # Get all the project attributes
  command  = args.apiCommands + "/get_project_attributes.sh " + str(args.token) + " " + str(args.url) + " " + str(args.project)
  jsonData = json.loads(os.popen(command).read())

  # Loop over the attributes
  for attribute in jsonData: startingAttributes.append(attribute["id"])

# Get a list of users for the project
def getProjectUserIds(args):
  global projectUserIds

  # Get the number of users attached to the project
  command = args.apiCommands + "/get_project_roles.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(args.project) + " 1 1"
  data    = json.loads(os.popen(command).read())

  # This action will have failed in the user has insufficient role
  if "message" in data: fail(data["message"])

  # Determine the number of pages of results, given 100 users per page
  noPages = int( math.ceil( float(data["count"]) / float(100.) ) )

  # Loop over all necessary pages
  for i in range(0, noPages):
    command = args.apiCommands + "/get_project_roles.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(args.project) + " 100 " + str(i + 1)
    data    = json.loads(os.popen(command).read())

    # Loop over the users and get the ids
    for user in data["data"]: projectUserIds.append(user["user_id"])

# Extract all the information from a project and import into the new project
def processTemplateProject(args, template):
  global availableTemplates
  global privateProjectAttributes

  # Reset the privateProjectAttributes to only include attributes for this project
  privateProjectAttributes = {}

  # Get the project id of the template being processed
  projectId = availableTemplates[template]["projectId"]

  # Process the dashboard, e.g. pinning objects
  pinnedAttributes, pinnedConversations = processDashboard(args, template, projectId)

  # Process project attributes
  processProjectAttributes(args, template, projectId, pinnedAttributes)

  # Process conversations
  processProjectConversations(args, template, projectId, pinnedConversations)

# Take the public project attributes from a template and make available in the working project
def processProjectAttributes(args, template, projectId, pinnedAttributes):
  global templateAttributes
  global projectAttributes
  global startingAttributes

  # Begin by getting all the public attributes from the project
  command = args.apiCommands + "/get_project_attributes.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(projectId)
  data    = json.loads(os.popen(command).read())

  # If the same object is pinned to the dashboard multiple times, it will appear on the dashboard multiple times. Get
  # the attributes that are pinned to the working project to make sure no double pinning takes place
  pinnedProjectAttributes, pinnedProjectConversations = processDashboard(args, template, args.project)

  # Loop over the attributes
  for attribute in data:
    attributeId    = attribute["id"]
    attributeValue = attribute["values"][0]["value"]

    # Ignore template attributes and attributes that were already in the project. If the template is rerun on a project,
    # the values in the project should not be overwritten.
    if (attributeId not in templateAttributes) and (attributeId not in startingAttributes):
      isPublic = attribute["is_public"]

      # If the project was imported from a nested template, then the value should be updated. Nested templates are
      # ordered so that the values assigned to the last template to be processed should be used. Updating values
      # only occurs for nested templates - if the project already had the attribute, it is not updated.
      if attributeId in projectAttributes:
        command    = str(args.apiCommands) + "/put_project_attribute_value.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(args.project)
        command   += " " + str(attributeId) + " \"" + str(attributeValue) + "\""
        updateData = json.loads(os.popen(command).read())

      # If the attribute has not yet been seen, and is a public attribute import it.
      elif isPublic:
        projectAttributes.append(attributeId)
        command    = str(args.apiCommands) + "/import_project_attribute.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(args.project) 
        command   += " " + str(attributeId) + " \"" + str(attributeValue) + "\""
        importData = json.loads(os.popen(command).read())

      #  If this is a private attribute, store it. These attributes can be used to provide directions for the template
      elif not isPublic: privateProjectAttributes[attribute["name"]] = attribute

      # If the attribute needs to be pinned to the dashboard, pin in
      if attributeId in pinnedAttributes and attributeId not in pinnedProjectAttributes:
        command = str(args.apiCommands) + "/pin_attribute.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(args.project) + " " + str(attributeId)
        pinData = json.loads(os.popen(command).read())
  
# Determine the status of objects on the dashboard in the template project and replicate in the working project
def processDashboard(args, template, projectId):
  pinnedAttributes    = []
  pinnedConversations = []

  # Get the dashboard information
  command = str(args.apiCommands) + "/get_dashboard.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(projectId) 
  data    = json.loads(os.popen(command).read())

  for dashboardObject in data:

    # Ignore all default items. These can't be modified
    if not dashboardObject["is_default"]:

      # Store the ids of the objects that should pinned to the dashboard. The only objects returned by GET dashboard are
      # the objects that are pinned, so no check is required for if they are pinned
      if dashboardObject["type"] == "project_attribute": pinnedAttributes.append(dashboardObject["attribute_id"])
      elif dashboardObject["type"] == "conversation": pinnedConversations.append(dashboardObject["project_conversation_id"])

  return pinnedAttributes, pinnedConversations

# Take the conversations from a template and make available in the working project
def processProjectConversations(args, template, projectId, pinnedConversations):
  global templateAttributes
  global projectConversations
  global projectUserIds

  # If a template is run on an existing project, conversations may already exist from the previously applied template.
  # Get all the conversations in the working project and do not duplicate conversations with the same name.
  conversations = getConversations(args, args.project)
  existingConvs = []
  for conversation in conversations: existingConvs.append(conversation["title"])

  # Get all of the conversations in the template and add into the working project
  conversations = getConversations(args, projectId)

  # Check if any conversations should have users set as watchers
  watchers = getWatchers(args, projectId)

  for conversation in conversations:
    title          = conversation["title"]
    description    = conversation["description"]
    conversationId = conversation["id"]
    isWatcher = True if title in watchers else False

    # The description might contain multiple lines which will break the curl command. Replace all newlines with \n
    if "\n" in description: description = description.replace("\n", "\\n")

    # Build the command to create the conversation if a conversation of the same title doesn't already exist
    if title not in existingConvs:
      command   = args.apiCommands + "/post_conversation.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(args.project)
      command  += " \"" + str(title) + "\" \"" + str(description) + "\""
      postData  = json.loads(os.popen(command).read())
      createdId = postData["id"]

      # Pin the conversation to the dashboard if requested
      if conversationId in pinnedConversations:
        command = str(args.apiCommands) + "/pin_conversation.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(args.project) + " " + str(createdId)
        pinData = json.loads(os.popen(command).read())

      # If the conversation is listed as a watcher, add all users in the project as watchers
      if isWatcher:
        command  = str(args.apiCommands) + "/post_conversation_watchers.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(args.project) + " \""
        command += str(conversationId) + "\" \"" + str(projectUserIds) + "\"" 
        data     = json.loads(os.popen(command).read())

# Check if any conversations should have users set as watchers
def getWatchers(args, projectId):
  global privateProjectAttributes
  conversations = []

  # Loop over the private project attributes
  for attribute in privateProjectAttributes:

    # If watchers are to be automatically assigned to any conversations, the conversation names
    # will be stored in the "Watchers" attribute
    if attribute == "Watchers": 
      for values in privateProjectAttributes[attribute]["values"]:
        if values["project_id"] == projectId:
          for conversation in values["value"].split(","): conversations.append(conversation)

  # Return the names of the conversations that every user should be a watcher on
  return conversations

# Return all conversations in a project
def getConversations(args, projectId):

  # Begin by getting all the conversations from the project. The resulting object is paginated, so determine the number of conversations
  # and consequently the number of pages of conversations that need to be returned
  command = args.apiCommands + "/get_project_conversations.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(projectId) + " 1"
  data    = json.loads(os.popen(command).read())

  # Determine the number of pages
  noPages = int( math.ceil( float(data["count"]) / float(25.) ) )

  # Loop over all necessary pages
  conversations = []
  for i in range(0, noPages):
    command = args.apiCommands + "/get_project_conversations.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(projectId) + " " + str(i + 1)
    data    = json.loads(os.popen(command).read())

    # Loop over the conversations from all the templates and create then
    for conversation in data["data"]: conversations.append(conversation)

  # Return the list of conversations in the project
  return conversations

# If problems are found with the templates, fail
def fail(text):
  print(text)
  exit(1)

# Initialise global variables

# Store the ids of the project attributes present on the dashboard prior to running the template
startingAttributes = []

# Store the project ids of the available templates
availableTemplates = {}
templateAttributes = {}
templateProjects   = {}

# Store the ids of the public attributes and conversations in the project being set up
projectAttributes    = []
projectConversations = []

# Store information on private project attributes in the templates. These attributes can be used
# to provde information on actions to be taken as part of the template.
privateProjectAttributes = {}

# Store a list of user_ids for all users in the project
projectUserIds = []

if __name__ == "__main__":
  main()
