#!/usr/bin/python

from __future__ import print_function

import os
import math
import argparse
import json
from random import random

def main():
  global peddyProjectId
  global hasSampleAttributes

  # Parse the command line
  args = parseCommandLine()

  # Check the integration status, e.g. if the required attributes exist or need to be created
  checkStatus(args)

  # Get the attributes names and where they are found in the Peddy html file.
  parseAttributes(args)

  # If the peddyProjectId is False, the project needs to be created along with all the Peddy attributes
  if not peddyProjectId:
    createProject(args)
    createAttributes(args)

  # Import the attributes into the project with Peddy data
  getAttributeIds(args)

  # Read through the Peddy file
  passed = readPeddyHtml(args)

  # If this step failed, the peddy html could not be found. The project attribute "Peddy data" should still be
  # imported into the project and set to Fail. Otherwise the peddy data should be processed
  if passed:
    hasSampleAttributes = True

    # Build additional attributes
    buildAttributes()

    # Generate a file to output to Mosaic
    outputToMosaic(args)

  # Import the attributes into the current project and upload the values
  importAttributes(args)

  # In order to build the ancestry chart, the background data needs to be posted to the project
  backgroundsId = postBackgrounds(args)
  buildChart(args, backgroundsId)

  # Output the observed errors.
  outputErrors(0)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')
  parser.add_argument('--token', '-t', required = True, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = True, metavar = "string", help = "The base url for Mosaic curl commands, up to an including \"api/\"")
  parser.add_argument('--path', '-d', required = True, metavar = "string", help = "The path where the tsv will be generated")
  parser.add_argument('--apiCommands', '-c', required = True, metavar = "string", help = "The path to the directory of api commands")
  parser.add_argument('--attributesFile', '-f', required = True, metavar = "file", help = "The input file listing the Peddy attributes")
  parser.add_argument('--attributesProject', '-a', required = True, metavar = "integer", help = "The Mosaic project id that contains public attributes")
  parser.add_argument('--reference', '-r', required = True, metavar = "string", help = "The genome reference for the project")
  parser.add_argument('--input', '-i', required = True, metavar = "file", help = "The html file output from Peddy")
  parser.add_argument('--output', '-o', required = True, metavar = "file", help = "The output file containing the values to upload")
  parser.add_argument('--project', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")
  parser.add_argument('--background', '-b', required = True, metavar = "file", help = "The output json containing background ancestry information")

  return parser.parse_args()

# Check if the Peddy attributes have already been created or if then need to be created
def checkStatus(args):
  global errors
  global peddyProjectId

  # Check the public attributes project for the project attribute indicating that the peddy integration
  # has been run before
  command = args.apiCommands + "/get_project_attributes.sh " + args.token + " " + args.url + " " + args.attributesProject
  data = json.loads(os.popen(command).read())

  # If the public attributse project doesn't exist, terminate
  if "message" in data:
    errors.append("Public attributes project (" + args.attributesProject + ") does not exist. Create a Public Attributes project before executing integrations")
    outputErrors(1)

  # Loop over all the project attributes and look for attribute "Peddy Integration xa545Ihs"
  peddyProjectId = False
  for attributeName in data:
    if attributeName["name"] == "Peddy Integration xa545Ihs":

      # There should be a value in the json object corresponding to the value in this project. Check this is the case
      peddyProjectId = attributeName["values"][0]["value"]
      break

# Parse the tsv file containing the Mosaic attributes
def parseAttributes(args):
  global errors
  global projectAttributes
  global sampleAttributes
  global integrationStatus

  # Get all the attributes to be added
  try: attributesInput = open(args.attributesFile, "r")

  # If there is no attributes file, no data can be processed.
  except:
    integrationStatus= "Fail"
    errors.append("File: " + args.attributesFile + " does not exist")
    return False

  lineNo = 0
  for line in attributesInput.readlines():
    lineNo += 1
    line = line.rstrip()
    attributes = line.split("\t")

    # Put all project attributes into the projectAttributes dictionary. Set the Mosaic id and uid to
    # False for now. These will be read from the Peddy Attributes project if it already exists, or will
    # be assigned when the attributes are created, if this is the first running of the Peddy integration.
    # Get the value type (string or float) from the file
    if attributes[0] == "project": projectAttributes[attributes[1]] = {"id": False, "uid": False, "type":attributes[2], "values": False}
      
    # With sample attributes, we need both the attribute id and uid which will be determined later, and where
    # the value will be found in the Peddy html file. For, now set the id and uid to False, and read in the
    # value type, and Peddy html location
    elif attributes[0] == "sample":

      # Put the attributes in the correct array.
      location = str(attributes[4]) + "/" + str(attributes[5])
      sampleAttributes[attributes[1]] = {"id": False, "uid": False, "type": attributes[2], "html": location, "xlabel": attributes[3], "ylabel": "", "values": {}}
  
    # If the attribute is not correctly defined, add the line to the errors
    else:
      integrationStatus = "Incomplete"
      errors.append("Unknown attribute in line " + str(lineNo) + " of file " + args.attributes)

# Create a project to hold all the Peddy attributes
def createProject(args):
  global peddyProjectId

  # Define the curl command
  command  = args.apiCommands + "/create_project.sh " + args.token + " \"" + args.url + "\" \"Peddy Attributes\" \"" + args.reference + "\""
  jsonData = json.loads(os.popen(command).read())
  peddyProjectId = jsonData["id"]

  # Add a project attribute to the Public attributes project with this id as the value
  command  = args.apiCommands + "/create_project_attribute.sh " + args.token + " \"" + args.url + "\" "
  command += args.attributesProject + " \"Peddy Integration xa545Ihs\" float " + str(peddyProjectId) + " false"
  jsonData = json.loads(os.popen(command).read())

# If the Peddy attributes project was created, create all the required attributes
def createAttributes(args):
  global peddyProjectId
  global projectAttributes
  global sampleAttributes

  # Create all the project attributes required for Peddy integration
  command = args.apiCommands + "/create_project_attribute.sh " + args.token + " \"" + args.url + "\" " + str(peddyProjectId)
  for attribute in projectAttributes:
    attType  = projectAttributes[attribute]["type"]
    body     = " \"" + str(attribute) + "\" \"" + str(attType) + "\" Null true"
    jsonData = json.loads(os.popen(command + body).read())

  # Create all the sample attributes required for Peddy integration
  command = args.apiCommands + "/create_sample_attribute.sh " + args.token + " \"" + args.url + "\" " + str(peddyProjectId)
  for attribute in sampleAttributes:
    attType  = sampleAttributes[attribute]["type"]
    xlabel   = sampleAttributes[attribute]["xlabel"]
    ylabel   = sampleAttributes[attribute]["ylabel"]
    body     = " \"" + str(attribute) + "\" \"" + str(attType) + "\" \"" + xlabel + "\" \"" + ylabel + "\" Null true"
    jsonData = json.loads(os.popen(command + body).read())

# Import the attributes into the current project
def getAttributeIds(args):
  global peddyProjectId
  global projectAttributes
  global sampleAttributes

  # First, get all the project attribute ids from the Peddy Attributes project
  command  = args.apiCommands + "/get_project_attributes.sh " + args.token + " " + args.url + " " + str(peddyProjectId)
  jsonData = json.loads(os.popen(command).read())

  # Loop over the project attributes and store the ids
  for attribute in jsonData:
    projectAttributes[str(attribute["name"])]["id"]  = attribute["id"]
    projectAttributes[str(attribute["name"])]["uid"] = attribute["uid"]

  # Get all the sample attribute ids from the Peddy Attributes project
  command  = args.apiCommands + "/get_sample_attributes.sh " + args.token + " " + args.url + " " + str(peddyProjectId)
  jsonData = json.loads(os.popen(command).read())

  # Loop over the project attributes and store the ids
  for attribute in jsonData:

    # Only include custom attributes (e.g. ignore global default attributes like Median Read Coverage that are
    # added to all Mosaic projects
    if str(attribute["is_custom"]) == "True":
      sampleAttributes[str(attribute["name"])]["id"]  = attribute["id"]
      sampleAttributes[str(attribute["name"])]["uid"] = attribute["uid"]

# Read through the peddy html and pull out the data json
def readPeddyHtml(args):
  global samples
  global errors
  global integrationStatus
  global projectAttributes

  # Open the file
  try: peddyHtml = open(args.input, "r")

  # If the file cannot be found, fail
  except:
    integrationStatus = "Fail"
    errors.append("File: " + args.input + " does not exist")
    return False

  # Loop over the file and extract the data
  for line in peddyHtml.readlines():
    line = line.rstrip()

    # Get the data from the "het_data" variable.
    if line.startswith("var het_data"):
      hetData = json.loads(line.split("= ")[1])
      for record in hetData:
        sample = record["sample_id"]
        if sample not in samples: samples.append(sample)

        # Loop over all the Peddy het_data attributes
        for attribute in record:

          # Find the attribute in sampleAttributes
          if str(attribute) != "sample_id":
            for sampleAttribute in sampleAttributes:
              peddyVar  = sampleAttributes[sampleAttribute]["html"].split("/")[0]
              peddyName = sampleAttributes[sampleAttribute]["html"].split("/")[1]

              # Add the value for this sample into the sampleAttributes
              if str(peddyVar) == "het_data" and str(peddyName) == str(attribute): sampleAttributes[sampleAttribute]["values"][sample] = record[attribute]

    # Get "sex_data"
    elif line.startswith("var sex_data"):
      sexData = json.loads(line.split("= ")[1])
      for record in sexData:
        sample = record["sample_id"]

        # Loop over all the Peddy sex_data attributes
        for attribute in record:

          # Find the attribute in sampleAttributes
          if str(attribute) != "sample_id":
            for sampleAttribute in sampleAttributes:
              peddyVar  = sampleAttributes[sampleAttribute]["html"].split("/")[0]
              peddyName = sampleAttributes[sampleAttribute]["html"].split("/")[1]

              # Add the value for this sample into the sampleAttributes
              if str(peddyVar) == "sex_data" and str(peddyName) == str(attribute): sampleAttributes[sampleAttribute]["values"][sample] = record[attribute]

    # Get "pedigree" data
    elif line.startswith("var pedigree"):
      pedData = json.loads(line.split("= ")[1])
      for record in pedData:
        sample = record["sample_id"]

        # Loop over all the Peddy sex_data attributes
        for attribute in record:

          # Find the attribute in sampleAttributes
          if str(attribute) != "sample_id":
            for sampleAttribute in sampleAttributes:
              peddyVar  = sampleAttributes[sampleAttribute]["html"].split("/")[0]
              peddyName = sampleAttributes[sampleAttribute]["html"].split("/")[1]

              # Add the value for this sample into the sampleAttributes
              if str(peddyVar) == "pedigree" and str(peddyName) == str(attribute): sampleAttributes[sampleAttribute]["values"][sample] = record[attribute]

    # Get the background data
    elif line.startswith("var background_pca"):
      background = json.loads(line.split("= ")[1])

      # The background file contains information for some known attriubtes. Change the name of the
      # attributes to the Mosaic uid.
      pc1      = sampleAttributes["Ancestry PC1 (Peddy)"]["uid"]
      pc2      = sampleAttributes["Ancestry PC2 (Peddy)"]["uid"]
      #pc3      = sampleAttributes["Ancestry PC3 (Peddy)"]["uid"]
      #pc4      = sampleAttributes["Ancestry PC4 (Peddy)"]["uid"]
      ancestry = sampleAttributes["Ancestry Prediction (Peddy)"]["uid"]
      for info in background:
        info[pc1]      = info.pop("PC1")
        info[pc2]      = info.pop("PC2")
        #info[pc3]      = info.pop("PC3")
        #info[pc4]      = info.pop("PC4")
        info[ancestry] = info.pop("ancestry")

      backgroundFile = open(args.background, "w")
      print(json.dumps(background), file = backgroundFile)
      backgroundFile.close()

  return True

# Construct some new attributes
def buildAttributes():
  global samples
  global sampleAttributes

  # Generate a sex attribute. Define a female as 0, and a male as 1. The attribute will
  # be a random number between -0.25 < x < 0.25 for female and 0.75 < x < 1.25 for male
  for sample in samples:
    ran = float((random() - 0.5)/ 2)
    sex = sampleAttributes["Sex (Peddy)"]["values"][sample]
    if sex == "male": sampleAttributes["Sex Spread (Peddy)"]["values"][sample] = float ( 1 + ran)
    elif sex == "female": sampleAttributes["Sex Spread (Peddy)"]["values"][sample] = ran
    else: print("Unknown gender for sample ", sample, ": \"", sex, "\"", sep = ""); exit(1)

# Print out data for import into Mosaic
def outputToMosaic(args):
  global samples
  global sampleAttributes

  # Open the output file
  outFile = open(args.output, "w")

  # Output the header line
  line = "SAMPLE_NAME"
  for attribute in sorted(sampleAttributes.keys()): line += "\t" + str(sampleAttributes[attribute]["uid"])
  print(line, file = outFile)
  
  # Loop over the samples and output the required information
  for sample in samples:
    line = sample
    for attribute in sorted(sampleAttributes.keys()):
      try: value = sampleAttributes[attribute]["values"][sample]
      except: value = "-"
      line += "\t" + str(value)
    print(line, sep = "\t", file = outFile)

  # Close the output file
  outFile.close()

# Import attributes into the current project and upload the tsv values file
def importAttributes(args):
  global integrationStatus
  global errors
  global projectAttributes
  global sampleAttributes
  global hasSampleAttributes

  # Set the Peddy Data project attribute value to the value stored in integrationStatus
  projectAttributes["Peddy Data"]["values"] = integrationStatus

  # Begin with the import and setting of project attributes
  command = args.apiCommands + "/import_project_attribute.sh " + args.token + " \"" + args.url + "\" \"" + str(args.project) + "\" "
  for attribute in projectAttributes:
    attributeId = projectAttributes[attribute]["id"]
    value       = projectAttributes[attribute]["values"]
    body        = "\"" + str(attributeId) + "\" \"" + str(value) + "\""
    jsonData    = json.loads(os.popen(command + body).read())

  # Loop over all the defined sample attributes and import them, but only if the parsing of the peddy
  # html was successful
  if hasSampleAttributes:
    command = args.apiCommands + "/import_sample_attribute.sh " + str(args.token) + " \"" + str(args.url) + "\" \"" + str(args.project) + "\" "
    for attribute in sampleAttributes:
      attributeId = sampleAttributes[attribute]["id"]
      body        = "\"" + str(attributeId) + "\""
      jsonData    = json.loads(os.popen(command + body).read())
  
    # Upload the sample attribute values tsv
    command  = args.apiCommands + "/upload_sample_attribute_tsv.sh " + str(args.token) + " \"" + str(args.url) + "\" \"" + str(args.project) + "\" \""
    command += str(args.path) + "/" + str(args.output) + "\""
    data     = os.popen(command)

# Post the background data
def postBackgrounds(args):

  # Build the command to POST
  command  = args.apiCommands + "/post_backgrounds.sh " + str(args.token) + " \"" + str(args.url) + "\" \"" + str(args.project) + "\" "
  command += "\"Ancestry Backgrounds\" " + str(args.background)
  try: data = json.loads(os.popen(command).read())
  except:
    print("Failed to post backgrounds")
    exit(1)

  if "id" not in data:
    print("Failed to post backgrounds")
    exit(1)

  return data["id"]

# Build the ancestry chart
def buildChart(args, backgroundsId):
  global sampleAttributes

  # Get the ids of the PC1 and PC2 attributes
  pc1     = sampleAttributes["Ancestry PC1 (Peddy)"]["id"]
  pc2     = sampleAttributes["Ancestry PC2 (Peddy)"]["id"]
  colorBy = sampleAttributes["Ancestry Prediction (Peddy)"]["id"]

  # Build the command to post a chart
  command  = args.apiCommands + "/post_backgrounds_chart.sh " + str(args.token) + " \"" + str(args.url) + "\" \"" + str(args.project) + "\" "
  command += "\"" + str(pc2) + "\" \"" + str(backgroundsId) + "\" \"Ancestry (Peddy)\" \"" + str(colorBy) + "\" \"" + str(pc1) + "\" "
  command += "\"Ancestry PC2 (Peddy)\""

  try: data = json.loads(os.popen(command).read())
  except:
    print("Failed to post chart")
    exit(1)

  # Get the id of the chart that was created
  try: chartId = data["id"]
  except:
    print("Failed to get id of chart")
    exit(1)

  # Pin the chart to the dashboard
  command = args.apiCommands + "/pin_chart.sh " + str(args.token) + " \"" + str(args.url) + "\" \"" + str(args.project) + "\" \"" + str(chartId) + "\""

  try: data = json.loads(os.popen(command).read())
  except:
    print("Failed to pin chart")
    exit(1)

###############
###############
############### Add errors to a conversation / health?
############### Integration status value needs to be sent to the project attribute
###############
###############
# Output all the errors seen while processing
def outputErrors(errorCode):
  global errors

  for line in errors: print(line)
  exit(errorCode)





# Initialise global variables

# The id of the project holding Peddy attributes
peddyProjectId = False

# Dictionaries to match Peddy attribute names to their location in the html file
projectAttributes = {}
sampleAttributes  = {}

# Keep a list of all errors seen, and the status of the processing
errors            = []
integrationStatus = "Pass"

# Keep track of the samples in the project
samples  = []

# Record if sample attributes are successfully processed
hasSampleAttributes = False

if __name__ == "__main__":
  main()
