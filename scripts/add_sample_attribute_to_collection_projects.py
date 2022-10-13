#!/usr/bin/python

from __future__ import print_function

import os
import argparse
import json

def main():

  # Parse the command line
  args = parseCommandLine()

  # Get the id for the conversation to update
  getProjectIds(args)

  # Get the id of the attribute to import
  attributeId = getAttributeId(args)

  # Get the sample ids for samples in the projects
  getSampleIds(args)

  # Get the values for each project
  getValues(args)

  # Import the sample attribute into each project, then set the value for each sample
  importAttributes(args, attributeId)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Standard args
  parser.add_argument('--token', '-t', required = True, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--apiCommands', '-a', required = True, metavar = "string", help = "The path to the directory of api commands")
  parser.add_argument('--url', '-u', required = True, metavar = "string", help = "The base url for Mosaic curl commands, up to an including \"api\". Do NOT include a trailing /")
  parser.add_argument('--inputFile', '-i', required = True, metavar = "string", help = "The input tsv file linking project name to value")

  # Custom args
  parser.add_argument('--project', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")
  parser.add_argument('--attribute', '-b', required = True, metavar = "string", help = "The attribute uid to import")

  return parser.parse_args()

# Get the id for the conversation to update
def  getProjectIds(args):
  global projectIds

  # Get the first page of conversations
  command = args.apiCommands + "/get_collection_projects.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(args.project)
  data    = json.loads(os.popen(command).read())

  # Store the project ids
  for project in data: projectIds[project["name"]] = {"id": project["id"], "samples": [], "value": False}

# Get the id of the attribute to import
def getAttributeId(args):

  # Get the first page of conversations
  command = args.apiCommands + "/get_sample_attributes.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(args.project)
  data    = json.loads(os.popen(command).read())

  # Loop over the attributes and find the correct attribute
  attributeId = False
  for attribute in data:
    if attribute["uid"] == args.attribute:
      attributeId = attribute["id"]
      continue

  # Fail if the attribute wasn't found
  if not attributeId:
    print("Attribute with Mosaic uid ", args.attribute, " was not found in the collection. Make sure the attribute is imported into at least one project", sep = "")
    exit(1)

  return attributeId

# Get the sample ids
def getSampleIds(args):
  global projectIds

  # Loop over all the projects
  for project in projectIds:
    projectId = projectIds[project]["id"]

    # Get the sample ids for each project
    command = args.apiCommands + "/get_samples.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(projectId)
    data    = json.loads(os.popen(command).read())

    # Loop over the samples and add to the projectIds
    for sample in data: projectIds[project]["samples"].append(sample["id"])

# Get the values for each project
def getValues(args):
  global projectIds

  # Open the input file
  inputFile = open(args.inputFile, "r")
  for line in inputFile.readlines():
    values  = line.rstrip().split("\t")
    project = values[0]
    value   = values[1]
    projectIds[project]["value"] = value

# Import the sample attribute into each project, then set the value for each sample
def importAttributes(args, attributeId):
  global projectIds

  # Loop over each project
  for project in projectIds:
    projectId = projectIds[project]["id"]
    value     = projectIds[project]["value"]
    samples   = projectIds[project]["samples"]

    # Import the required attribute
    importCommand = args.apiCommands + "/import_sample_attribute.sh " + str(args.token) + " \"" + str(args.url) + "\" \"" + str(projectId) + "\" \"" + str(attributeId) + "\""
    importData    = json.loads(os.popen(importCommand).read())

    # PUT the value for each sample in the project
    for sample in samples:
      putCommand = args.apiCommands + "/put_sample_attribute_value.sh " + str(args.token) + " \"" + str(args.url) + "\" \"" + str(projectId) + "\" \"" + str(sample) + "\" \"" + str(attributeId) + "\" \"" + str(value) + "\""
      putData    = json.loads(os.popen(putCommand).read())

# Initialise global variables

# Store the ids of the projects in the collection
projectIds = {}

if __name__ == "__main__":
  main()
