#!/usr/bin/python

from __future__ import print_function

import os
import argparse
import json

def main():
  global templates

  # Parse the command line
  args = parseCommandLine()

  # Parse the template json
  parseTemplate(args.templatePath, args.template)

  # If this template called for additional templates to be included, parse these templates and store
  # their requirements
  if len(templates) > 0: 
    for template in templates: parseTemplate(args.templatePath, template)

  # Get all the public attributes in Mosaic
  getPublicAttributes(args)

  # Create conversations and import the project attributes
  createConversations(args)
  importAttributes(args)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line')
  parser.add_argument('--template', '-m', required = True, metavar = "string", help = "The template to run")
  parser.add_argument('--templatePath', '-l', required = True, metavar = "string", help = "The path to the template json files")
  #parser.add_argument('--input', '-i', required = True, metavar = "file", help = "The html file output from Peddy")
  #parser.add_argument('--attributesFile', '-f', required = True, metavar = "file", help = "The input file listing the Peddy attributes")
  #parser.add_argument('--output', '-o', required = True, metavar = "file", help = "The output file containing the values to upload")
  #parser.add_argument('--attributesProject', '-a', required = True, metavar = "integer", help = "The Mosaic project id that contains public attributes")
  parser.add_argument('--token', '-t', required = True, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = True, metavar = "string", help = "The base url for Mosaic curl commands, up to an including \"api\". Do NOT include a trailing /")
  parser.add_argument('--project', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")
  parser.add_argument('--path', '-c', required = True, metavar = "string", help = "The path where the api calls scripts live")
  #parser.add_argument('--background', '-b', required = True, metavar = "file", help = "The output json containing background ancestry information")

  return parser.parse_args()

# Read in the template json and determine what needs to be created
def parseTemplate(path, template):
  global templates
  global projectAttributes
  global conversations

  # Open the json file
  try: templateFile = open(path + template + ".json", "r")
  except:
    print("No template: ", path + template, sep = "")
    exit(1)

  # Extract the json information
  try: templateData = json.loads(templateFile.read())
  except:
    print("Not valid json")
    exit(1)

  # Store the name of the template. If a template includes itself as a template, or
  # contains another template taht contains itself, this could create an infinte
  # loop. If this template has already been seen, terminate to avoid an infinite loop
  if template in seenTemplates:
    print("Infinite loop")
    exit(1)
  seenTemplates.append(template)

  # Loop over other templates that need to run
  if "templates" in templateData:
    if type(templateData["templates"]) == list:
      for template in templateData["templates"]: templates.append(template)
    else:
      print(mosaicObject, " is not of the required type. ", type(data[mosaicObject]), " instead of ", objectType, sep = "")
      exit(1)

  # Loop over the project attributes and store them. Prior to assigning the value to the
  # attribute, check if there is already a value assigned. The hierarchy is such that
  # the first template seen takes precedence.
  if "project attributes" in templateData:
    for attribute in templateData["project attributes"]:
      if attribute not in projectAttributes:
        try: value = templateData["project attributes"][attribute]["value"]
        except: fail("Fail: project attribute " + attribute)
        try: pin = templateData["project attributes"][attribute]["pin"]
        except: fail("Fail: project attribute " + attribute)
        projectAttributes[attribute] = {"value": value, "pin": pin}

  # Loop over the conversations and store them
  if "conversations" in templateData:
    for conversation in templateData["conversations"]:
      if conversation not in conversations:
        try: description = templateData["conversations"][conversation]["description"]
        except: fail("Fail conversation " + conversation)
        try: pin = templateData["conversations"][conversation]["pin"]
        except: fail("Fail conversation " + conversation)
        conversations[conversation] = {"description": description, "pin": pin}

# Get all the public attributes in Mosaic and associate the id with the uid
def getPublicAttributes(args):
  global publicAttributes

  # Get all the public attributes
  command = args.path + "/get_public_attributes.sh " + args.token + " \"" + args.url + "\""
  data    = json.loads(os.popen(command).read())

  # Loop over all the attributes and store the id for each uid
  for record in data["data"]: publicAttributes[record["uid"]] = record["id"]

# Create all of the required conversations
def createConversations(args):
  global conversations

  # Loop over the conversations from all the templates and create then
  for conversation in conversations:
    description = conversations[conversation]["description"]
    pin         = conversations[conversation]["pin"]

    # Build the command to create the conversation
    command     = args.path + "/create_conversation.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(args.project)
    command    += " \"" + str(conversation) + "\" \"" + str(description) + "\""
    createData  = json.loads(os.popen(command).read())

    # Pin the conversation to the dashboard if requested
    if pin:
      conversationId = createData["id"]
      command        = str(args.path) + "/pin_conversation.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(args.project) + " " + str(conversationId)
      pinData        = json.loads(os.popen(command).read())

# Import the project attributes and assign values
def importAttributes(args):
  global publicAttributes
  global projectAttributes

  # Loop over the project attributes, import them into the project and assign the values
  for attribute in projectAttributes:
    try: attributeId = publicAttributes[attribute]
    except: fail("Unknown attribute uid :" + attribute)

    # Get the value to assign to the attribute, and whether it should be pinned to the dashboard
    value = projectAttributes[attribute]["value"]
    pin   = projectAttributes[attribute]["pin"]

    # Build the command to import the attribute
    command    = str(args.path) + "/import_project_attribute.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(args.project) 
    command   += " " + str(attributeId) + " \"" + str(value) + "\""
    importData = json.loads(os.popen(command).read())

    # Pin the attribute to the dashboard if requested
    if pin:
      command = str(args.path) + "/pin_attribute.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(args.project) + " " + str(attributeId)
      pinData = json.loads(os.popen(command).read())

# If problems are found with the templates, fail
def fail(text):
  print(text)
  exit(1)


# Initialise global variables

# Store the different Mosaic objects from the template
templates         = []
projectAttributes = {}
conversations     = {}

# Store the names of the templates that have been seen
seenTemplates = []

# Store all public attributes available in Mosaic
publicAttributes = {}

if __name__ == "__main__":
  main()
