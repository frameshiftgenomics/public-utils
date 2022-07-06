#!/usr/bin/python

from __future__ import print_function

import sys
import os
import math
import argparse
import json
from random import random

# Add the path of the common functions and import them
from sys import path
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-2]) + "/common_components")
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-2]) + "/api_commands")
import mosaic_config
import api_attributes as api_a
import api_charts as api_c
import api_dashboards as api_d
import api_projects as api_p
import api_project_attributes as api_pa
import api_project_backgrounds as api_pb
import api_sample_attributes as api_sa

def main():
  global peddyProjectId
  global hasSampleAttributes
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {"token": True, "url": True, "attributeProjectId": True}
  mosaicConfig   = mosaic_config.parseConfig(args, mosaicRequired)

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

  # Check if the attributes already exist in the target project
  checkAttributesExist(args)

  # Read through the Peddy file
  passed = readPeddyHtml(args)

  # Set the output file if one wasn't specified
  if not args.output: args.output = "peddy_mosaic_upload.tsv"

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

  # Create an attribute set
  createAttributeSet(args)

  # In order to build the ancestry chart, the background data needs to be posted to the project
  backgroundsId = postBackgrounds(args)
  buildChart(args, backgroundsId)

  # Remove the created files
  removeFiles(args)

  # Output the observed errors.
  outputErrors(0)

# Input options
def parseCommandLine():
  global version

  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Required arguments
  parser.add_argument('--reference', '-r', required = True, metavar = "string", help = "The reference genome to use. Allowed values: '37', '38'")
  parser.add_argument('--input_html', '-i', required = True, metavar = "file", help = "The html file output from Peddy")
  parser.add_argument('--project', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")

  # Optional pipeline arguments
  parser.add_argument('--attributes_file', '-f', required = False, metavar = "file", help = "The input file listing the Peddy attributes")
  parser.add_argument('--output', '-o', required = False, metavar = "file", help = "The output file containing the values to upload")
  parser.add_argument('--background', '-b', required = False, metavar = "file", help = "The output json containing background ancestry information")

  # Optional mosaic arguments
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "The config file for Mosaic")
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic")
  parser.add_argument('--attributes_project', '-a', required = False, metavar = "integer", help = "The Mosaic project id that contains public attributes")

  # Version
  parser.add_argument('--version', '-v', action="version", version='Peddy integration version: ' + str(version))

  return parser.parse_args()

# Check if the Peddy attributes have already been created or if then need to be created
def checkStatus(args):
  global errors
  global peddyProjectId
  global mosaicConfig

  # Check the public attributes project for the project attribute indicating that the peddy integration
  # has been run before
  command = api_pa.getProjectAttributes(mosaicConfig, mosaicConfig["attributesProjectId"])
  data    = json.loads(os.popen(command).read())

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

  # If the attributes file was not specified on the command line, use the default version
  if not args.attributes_file: args.attributes_file = os.path.dirname(os.path.abspath(__file__)) + "/mosaic.atts.peddy.tsv"

  # Get all the attributes to be added
  try: attributesInput = open(args.attributes_file, "r")

  # If there is no attributes file, no data can be processed.
  except:
    integrationStatus= "Fail"
    errors.append("File: " + args.attributes_file + " does not exist")
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
      sampleAttributes[attributes[1]] = {"id": False, "uid": False, "type": attributes[2], "html": location, "xlabel": attributes[3], "ylabel": "", "values": {}, "present": False}
  
    # If the attribute is not correctly defined, add the line to the errors
    else:
      integrationStatus = "Incomplete"
      errors.append("Unknown attribute in line " + str(lineNo) + " of file " + args.attributes_file)

# Create a project to hold all the Peddy attributes
def createProject(args):
  global peddyProjectId
  global mosaicConfig

  # Define the curl command
  command  = api_p.postProject(mosaicConfig, "Peddy Attributes", args.reference)
  jsonData = json.loads(os.popen(command).read())
  peddyProjectId = jsonData["id"]

  # Add a project attribute to the Public attributes project with this id as the value
  command  = api_pa.postProjectAttribute(mosaicConfig, "Peddy Integration xa545Ihs", "float", str(peddyProjectId), False, mosaicConfig["attributesProjectId"])
  jsonData = json.loads(os.popen(command).read())

# If the Peddy attributes project was created, create all the required attributes
def createAttributes(args):
  global peddyProjectId
  global projectAttributes
  global sampleAttributes
  global mosaicConfig

  # Create all the project attributes required for Peddy integration
  for attribute in projectAttributes:
    attType  = projectAttributes[attribute]["type"]
    command  = api_pa.postProjectAttribute(mosaicConfig, attribute, attType, "Null", True, peddyProjectId)
    jsonData = json.loads(os.popen(command).read())

  # Create all the sample attributes required for Peddy integration
  for attribute in sampleAttributes:
    attType  = sampleAttributes[attribute]["type"]
    xlabel   = sampleAttributes[attribute]["xlabel"]
    ylabel   = sampleAttributes[attribute]["ylabel"]
    command  = api_sa.postSampleAttribute(mosaicConfig, attribute, attType, xlabel, ylabel, "Null", True, peddyProjectId)
    jsonData = json.loads(os.popen(command).read())

# Get the attributes to be imported into the current project
def getAttributeIds(args):
  global peddyProjectId
  global projectAttributes
  global sampleAttributes
  global mosaicConfig

  # First, get all the project attribute ids from the Peddy Attributes project
  command  = api_pa.getProjectAttributes(mosaicConfig, peddyProjectId)
  jsonData = json.loads(os.popen(command).read())

  # Loop over the project attributes and store the ids
  for attribute in jsonData:
    projectAttributes[str(attribute["name"])]["id"]  = attribute["id"]
    projectAttributes[str(attribute["name"])]["uid"] = attribute["uid"]

  # Get all the sample attribute ids from the Peddy Attributes project
  command  = api_sa.getSampleAttributes(mosaicConfig, peddyProjectId)
  jsonData = json.loads(os.popen(command).read())

  # Loop over the sample attributes and store the ids
  for attribute in jsonData:

    # Only include custom attributes (e.g. ignore global default attributes like Median Read Coverage that are
    # added to all Mosaic projects
    if str(attribute["is_custom"]) == "True":
      sampleAttributes[str(attribute["name"])]["id"]  = attribute["id"]
      sampleAttributes[str(attribute["name"])]["uid"] = attribute["uid"]

# Check if the attributes already exist in the target project and check if the Peddy integration has
# already been run (attributes could have been deleted, so both checks are required)
def checkAttributesExist(args):
  global sampleAttributes
  global projectAttributes
  global mosaicConfig
  global hasRun

  for attribute in projectAttributes:
    if attribute == "Peddy Data": peddyId = projectAttributes[attribute]["id"]

  # Get all the project attributes in the target project
  command  = api_pa.getProjectAttributes(mosaicConfig, args.project)
  jsonData = json.loads(os.popen(command).read())
  for attribute in jsonData: 
    if attribute["name"] == "Peddy Data" and attribute["id"] == peddyId: hasRun = True

  # Get all the sample attributes in the target project
  command  = api_sa.getSampleAttributes(mosaicConfig, args.project)
  jsonData = json.loads(os.popen(command).read())
  projectSampleAttributes = []
  for attribute in jsonData: projectSampleAttributes.append(attribute["id"])

  # Loop over the sample attributes and check if they exist in the target project
  for attribute in sampleAttributes:
    if sampleAttributes[attribute]["id"] in projectSampleAttributes: sampleAttributes[attribute]["present"] = True

# Read through the peddy html and pull out the data json
def readPeddyHtml(args):
  global samples
  global errors
  global integrationStatus
  global projectAttributes

  # Open the file
  try: peddyHtml = open(args.input_html, "r")

  # If the file cannot be found, fail
  except:
    integrationStatus = "Fail"
    errors.append("File: " + args.input_html + " does not exist")
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
      htmlBackground = json.loads(line.split("= ")[1])

      # The background file contains information for some known attriubtes. Change the name of the
      # attributes to the Mosaic uid.
      pc1      = sampleAttributes["Ancestry PC1 (Peddy)"]["uid"]
      pc2      = sampleAttributes["Ancestry PC2 (Peddy)"]["uid"]
      pc3      = sampleAttributes["Ancestry PC3 (Peddy)"]["uid"]
      pc4      = sampleAttributes["Ancestry PC4 (Peddy)"]["uid"]
      ancestry = sampleAttributes["Ancestry Prediction (Peddy)"]["uid"]
      for info in htmlBackground:
        info[pc1]      = info.pop("PC1")
        info[pc2]      = info.pop("PC2")
        info[ancestry] = info.pop("ancestry")

        # Remove the pc3 and pc4 info
        info.pop("PC3")
        info.pop("PC4")

      # Create a json object with the background name defined, and add the background data as the payload
      background = json.loads('{"name":"Ancestry Backgrounds","payload":[]}')
      background["payload"] = htmlBackground
      if not args.background: args.background = "peddy_backgrounds.json"
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
  global mosaicConfig

  # Set the Peddy Data project attribute value to the value stored in integrationStatus
  projectAttributes["Peddy Data"]["values"] = integrationStatus

  # Begin with the import and setting of project attributes
  for attribute in projectAttributes:
    attributeId = projectAttributes[attribute]["id"]
    value       = projectAttributes[attribute]["values"]
    command  = api_pa.postImportProjectAttribute(mosaicConfig, attributeId, value, args.project)
    jsonData = json.loads(os.popen(command).read())

  # Loop over all the defined sample attributes and import them, but only if the parsing of the peddy
  # html was successful
  if hasSampleAttributes:
    for attribute in sampleAttributes:

      # Only import the attribute if it wasn't already in the project
      if not sampleAttributes[attribute]["present"]:
        attributeId = sampleAttributes[attribute]["id"]
        command     = api_sa.postImportSampleAttribute(mosaicConfig, attributeId, args.project)
        jsonData    = json.loads(os.popen(command).read())
  
    # Upload the sample attribute values tsv
    command = api_sa.postUploadSampleAttribute(mosaicConfig, args.output, args.project)
    data    = os.popen(command)

# Create an attribute set
def createAttributeSet(args):
  global sampleAttributes
  global mosaicConfig

  # Get any existing attribute sets
  command = api_a.getProjectAttributeSets(mosaicConfig, args.project)
  data    = json.loads(os.popen(command).read())

  # Loop over the existing attribute sets and see if the Peddy set already exists
  setId = False
  existingIds = []
  for attributeSet in data:
    if attributeSet["name"] == "Peddy": 
      setId       = attributeSet["id"]
      existingIds = attributeSet["attribute_ids"]

  # Loop over the imported attributes and create a string of all the ids. Count the number of attributes to go into the set
  attributeIds = []
  for attribute in sampleAttributes: attributeIds.append(sampleAttributes[attribute]["id"])

  # If there already exists a Peddy attribute set, check that the attribute string is the same. If not, replace the existing set
  createSet = False
  deleteSet = False
  if setId:
    if sorted(existingIds) != sorted(attributeIds):
      createSet = True
      deleteSet = True

  #  If no attribute set exists, one needs to be created
  else: createSet = True

  # Delete the existing set if necessary
  if deleteSet:
    command = api_a.deleteProjectAttributeSet(mosaicConfig, args.project, setId)
    try: data = os.popen(command).read()
    except: print("Failed to delete attribute set with id:", setId, sep = "")

  # Create the attribute set from these ids
  if createSet:
    command = api_a.postProjectAttributeSet(mosaicConfig, "Peddy", "Imported Peddy attributes", True, attributeIds, "sample", args.project)
    try: data = json.loads(os.popen(command).read())
    except:
      print("Failed to create attribute set")
      exit(1)

# Post the background data
def postBackgrounds(args):
  global mosaicConfig

  # Build the command to POST
  command = api_pb.postBackgrounds(mosaicConfig, args.background, args.project)
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
  global mosaicConfig

  # Loop over all the charts in the project and find any charts that use a background
  command = api_c.getProjectCharts(mosaicConfig, args.project)
  data    = json.loads(os.popen(command).read())

  # Store the ids of charts that use a background and have the name "Ancestry (Peddy)"
  chartsToRemove = []
  for chart in data:
    if chart["project_background_id"] != None and chart["name"] == "Ancestry (Peddy)": chartsToRemove.append(chart["id"])

  # Remove old ancestry charts before adding the new one
  for chartId in chartsToRemove:
    command = api_c.deleteSavedChart(mosaicConfig, args.project, chartId)
    data    = os.popen(command)

  # Get the ids of the PC1 and PC2 attributes
  pc1     = sampleAttributes["Ancestry PC1 (Peddy)"]["id"]
  pc2     = sampleAttributes["Ancestry PC2 (Peddy)"]["id"]
  colorBy = sampleAttributes["Ancestry Prediction (Peddy)"]["id"]

  # Build the command to post a chart
  command = api_pb.postBackgroundChart(mosaicConfig, "Ancestry (Peddy)", "scatterplot", pc2, backgroundsId, "Ancestry PCS (Peddy)", colorBy, pc1, args.project)
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
  command = api_d.postPinChart(mosaicConfig, chartId, args.project)
  try: data = json.loads(os.popen(command).read())
  except:
    print("Failed to pin chart")
    exit(1)

# Remove the created files
def removeFiles(args):

  # Remove the backgrounds json
  os.remove(args.background)

  # Remove the tsv file
  os.remove(args.output)

# Output all the errors seen while processing
def outputErrors(errorCode):
  global errors

  for line in errors: print(line)
  exit(errorCode)

# Initialise global variables

# Store mosaic info, e.g. the token, url etc.
mosaicConfig = {}

# The id of the project holding Peddy attributes
peddyProjectId = False

# Record if the Peddy integration has previously run
hasRun = False

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

# Store the version
version = "0.1.1"

if __name__ == "__main__":
  main()
