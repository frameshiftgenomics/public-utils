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
  global mosaicConfig
  global somalierProjectId
  global hasSampleAttributes

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {"token": True, "url": True, "attributeProjectId": True}
  mosaicConfig   = mosaic_config.parseConfig(args, mosaicRequired)

  # Check the integration status, e.g. if the required attributes exist or need to be created
  checkStatus(args)

  # Get the attributes names and where they are found in the Peddy html file.
  parseAttributes(args)

  # If the somalierProjectId is False, the project needs to be created along with all the Peddy attributes
  if not somalierProjectId:
    createProject(args)
    createAttributes(args)

  # Import the attributes into the project with Somalier data
  getAttributeIds(args)

  # Check if the attributes already exist in the target project
  checkAttributesExist(args)

  # Set the output file if one wasn't specified
  if not args.output: args.output = "somalier_mosaic_upload.tsv"

  # Read through the Somalier relatedness samples file, if provided
  passed = readSomalierRelatednessSamples(args)

  # If this step failed, the Somalier files could not be found. The project attribute "Somalier data" should still be
  # imported into the project and set to Fail. Otherwise the Somalier data should be processed
  if passed:
    hasSampleAttributes = True

    # Generate a file to output to Mosaic
    outputToMosaic(args)

  # Import the attributes into the current project and upload the values
  importAttributes(args)

  # Create an attribute set
  #createAttributeSet(args)

  # In order to build the ancestry chart, the background data needs to be posted to the project
  #backgroundsId = postBackgrounds(args)
  #buildChart(args, backgroundsId)

  # Remove the created files
  #removeFiles(args)

  # Output the observed errors.
  outputErrors(0)

# Input options
def parseCommandLine():
  global version

  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Required arguments
  parser.add_argument('--reference', '-r', required = True, metavar = "string", help = "The reference genome to use. Allowed values: '37', '38'")
  parser.add_argument('--relatedness_samples', '-s', required = True, metavar = "file", help = "The Somalier tsv file containing information about each sample")
  parser.add_argument('--project', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")

  # Optional pipeline arguments
  parser.add_argument('--attributes_file', '-f', required = False, metavar = "file", help = "The input file listing the Peddy attributes")
  parser.add_argument('--output', '-o', required = False, metavar = "file", help = "The output file containing the values to upload")
  #parser.add_argument('--background', '-b', required = False, metavar = "file", help = "The output json containing background ancestry information")

  # Optional mosaic arguments
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "The config file for Mosaic")
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic")
  parser.add_argument('--attributes_project', '-a', required = False, metavar = "integer", help = "The Mosaic project id that contains public attributes")

  # Version
  parser.add_argument('--version', '-v', action="version", version='Somalier integration version: ' + str(version))

  return parser.parse_args()

# Check if the Peddy attributes have already been created or if then need to be created
def checkStatus(args):
  global errors
  global somalierProjectId
  global mosaicConfig

  # Check the public attributes project for the project attribute indicating that the peddy integration
  # has been run before
  data = json.loads(os.popen(api_pa.getProjectAttributes(mosaicConfig, mosaicConfig["attributesProjectId"])).read())

  # If the public attributse project doesn't exist, terminate
  if "message" in data:
    errors.append("Public attributes project (" + args.attributesProject + ") does not exist. Create a Public Attributes project before executing integrations")
    outputErrors(1)

  # Loop over all the project attributes and look for attribute "Somalier Integration xa545Ihs"
  somalierProjectId = False
  for attributeName in data:
    if attributeName["name"] == "Somalier Integration xa545Ihs":

      # There should be a value in the json object corresponding to the value in this project. Check this is the case
      somalierProjectId = attributeName["values"][0]["value"]
      break

# Parse the tsv file containing the Mosaic attributes
def parseAttributes(args):
  global errors
  global projectAttributes
  global sampleAttributes
  global integrationStatus

  # If the attributes file was not specified on the command line, use the default version
  if not args.attributes_file: args.attributes_file = os.path.dirname(os.path.abspath(__file__)) + "/mosaic.atts.somalier.tsv"

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
    attributes = line.rstrip().split("\t")

    # Put all project attributes into the projectAttributes dictionary. Set the Mosaic id and uid to
    # False for now. These will be read from the Somalier Attributes project if it already exists, or will
    # be assigned when the attributes are created, if this is the first running of the Somalier integration.
    # Get the value type (string or float) from the file
    if attributes[0] == "project": projectAttributes[attributes[1]] = {"id": False, "uid": False, "type":attributes[2], "values": False}
      
    # With sample attributes, we need both the attribute id and uid which will be determined later. For now,
    # set the id and uid to False, and read in the value type.
    elif attributes[0] == "sample":
      sampleAttributes[attributes[1]] = {"id": False, "uid": False, "type": attributes[2], "name": attributes[3], "xlabel": attributes[4], "ylabel": attributes[5], "values": {}, "column": False, "processed": False, "present": False}

    # If the attribute is not correctly defined, add the line to the errors
    else:
      integrationStatus = "Incomplete"
      errors.append("Unknown attribute in line " + str(lineNo) + " of file " + args.attributes_file)

# Create a project to hold all the Peddy attributes
def createProject(args):
  global somalierProjectId
  global mosaicConfig

  # Define the curl command
  jsonData = json.loads(os.popen(api_p.postProject(mosaicConfig, "Somalier Attributes", args.reference)).read())
  if "message" in jsonData:
    print(jsonData["message"])
    exit(1)
  somalierProjectId = jsonData["id"]

  # Add a project attribute to the Public attributes project with this id as the value
  jsonData = json.loads(os.popen(api_pa.postProjectAttribute(mosaicConfig, "Somalier Integration xa545Ihs", "float", str(somalierProjectId), "false", mosaicConfig["attributesProjectId"])).read())

# If the Somalier attributes project was created, create all the required attributes
def createAttributes(args):
  global somalierProjectId
  global projectAttributes
  global sampleAttributes
  global mosaicConfig

  # Create all the project attributes required for Somalier integration
  for attribute in projectAttributes:
    attType  = projectAttributes[attribute]["type"]
    jsonData = json.loads(os.popen(api_pa.postProjectAttribute(mosaicConfig, attribute, attType, "Null", "true", somalierProjectId)).read())

  # Create all the sample attributes required for Somalier integration
  for attribute in sampleAttributes:
    attType  = sampleAttributes[attribute]["type"]
    xlabel   = sampleAttributes[attribute]["xlabel"]
    ylabel   = sampleAttributes[attribute]["ylabel"]
    jsonData = json.loads(os.popen(api_sa.postSampleAttribute(mosaicConfig, attribute, attType, "Null", "true", xlabel, ylabel, somalierProjectId)).read())

# Get the attributes to be imported into the current project
def getAttributeIds(args):
  global somalierProjectId
  global projectAttributes
  global sampleAttributes
  global mosaicConfig

  # First, get all the project attribute ids from the Somalier Attributes project
  jsonData = json.loads(os.popen(api_pa.getProjectAttributes(mosaicConfig, somalierProjectId)).read())

  # Loop over the project attributes and store the ids
  for attribute in jsonData:
    projectAttributes[str(attribute["name"])]["id"]  = attribute["id"]
    projectAttributes[str(attribute["name"])]["uid"] = attribute["uid"]

  # Get all the sample attribute ids from the SomalierPeddy Attributes project
  jsonData = json.loads(os.popen(api_sa.getSampleAttributes(mosaicConfig, somalierProjectId)).read())

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
    if attribute == "Somalier Data": somalierId = projectAttributes[attribute]["id"]

  # Get all the project attributes in the target project
  jsonData = json.loads(os.popen(api_pa.getProjectAttributes(mosaicConfig, args.project)).read())
  for attribute in jsonData: 
    if attribute["name"] == "Somalier Data" and attribute["id"] == somalierId: hasRun = True

  # Get all the sample attributes in the target project
  jsonData = json.loads(os.popen(api_sa.getSampleAttributes(mosaicConfig, args.project)).read())
  projectSampleAttributes = []
  for attribute in jsonData: projectSampleAttributes.append(attribute["id"])

  # Loop over the sample attributes and check if they exist in the target project
  for attribute in sampleAttributes:
    if sampleAttributes[attribute]["id"] in projectSampleAttributes: sampleAttributes[attribute]["present"] = True

# Read through the peddy html and pull out the data json
def readSomalierRelatednessSamples(args):
  global samples
  global sampleAttributes
  global projectAttributes
  global integrationStatus
  global errors

  # Open the file
  try: inputFile = open(args.relatedness_samples, "r")

  # If the file cannot be found, fail
  except:
    integrationStatus = "Fail"
    errors.append("File: " + args.relatedness_samples + " does not exist")
    return False

  # Create a list of attributes included in the Mosaic attributes file
  requiredAttributes = {}
  for attribute in sampleAttributes: requiredAttributes[sampleAttributes[attribute]["name"]] = attribute

  # Loop over the file and extract the data
  for line in inputFile.readlines():
    line = line.rstrip()

    # Get the header line and determine the order of the attributes in the file
    if line.startswith("#"):
      fields = line.strip("#").split("\t")
      for i, field in enumerate(fields):
        if field in requiredAttributes: sampleAttributes[requiredAttributes[field]]["column"] = i

    # Then read the values for all samples
    else:
      fields = line.strip("#").split("\t")
      sample = fields[1]

      # Check for duplicate samples
      if sample in samples:
        integrationStatus = "Fail"
        error.append("Sample: " + str(sample) + " appears twice in the file: " + str(args.relatedness_samples))
        return False
      samples.append(sample)

      # Each row in the file corresponds to a sample. For each sample, get the attributes that
      # were listed in the Mosaic attributes file and store them in sampleAttributes
      for attribute in sampleAttributes:
        column = sampleAttributes[attribute]["column"]

        # Some attributes need to be constructed. In this case, the attributes file should include instructions
        # on how to construct the value, and so will not have appear in requiredAttributes as these instructions
        # will not correspond to a column in the header. So, "column" should be False, and the instuctions should
        # begin with "=". If this is not the case, fail.
        if column: sampleAttributes[attribute]["values"][sample] = fields[column]
        elif not column and sampleAttributes[attribute]["name"].startswith("="): sampleAttributes[attribute]["values"][sample] = constructAttribute(requiredAttributes, sample, attribute, fields)
        else:
          print("The Mosaic attributes file has a line that cannot be interpreted for: ", attribute, sep = "")
          exit(1)

  # Close the input file
  inputFile.close()

  return True

# Construct an attribute from other attributes
def constructAttribute(requiredAttributes, sample, attribute, fields):
  global sampleAttributes

  # Get the instructions for constructing the attribute. Operators and attributes are separated by pipes, 
  # so split on these
  instructions = sampleAttributes[attribute]["name"].strip("=").split("|")
  if len(instructions) > 3:
    print("The attribute calculator is very basic and only deals with 1 operator for now:")
    print("  ", sampleAttributes[attribute]["name"], sep = "")
    exit(1)

  # If the result is to be doubled, note it
  factor = 1.
  if instructions[0].startswith("2*"):
    instructions[0] = instructions[0].strip("2*")
    factor = 2.

  # Loop over the fields and check they are all attributes or operators
  operator = False
  columns  = []
  for field in instructions:
    column = False
    if field in requiredAttributes: columns.append(sampleAttributes[requiredAttributes[field]]["column"])
    elif operator:
      print("The attribute calculator is very basic and only deals with 1 operator for now:")
      print("  ", sampleAttributes[attribute]["name"], sep = "")
      exit(1)
    else: operator = field

  # If the operator is a division, generate the new value
  if str(operator) == "/":

    # If the numerator is zero, return zero
    if float(fields[columns[0]]) == 0.: return float(0.)

    # If the denominator is zero, return N/A
    elif float(fields[columns[1]]) == 0.: return "N/A"
    else: return float(factor) * float(fields[columns[0]]) / float(fields[columns[1]])
  else:
    print("Can't handle other operators yet.")
    exit(1)

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

  # Set the Somalier Data project attribute value to the value stored in integrationStatus
  projectAttributes["Somalier Data"]["values"] = integrationStatus

  # Begin with the import and setting of project attributes
  for attribute in projectAttributes:
    attributeId = projectAttributes[attribute]["id"]
    value       = projectAttributes[attribute]["values"]
    jsonData    = json.loads(os.popen(api_pa.postImportProjectAttribute(mosaicConfig, attributeId, value, args.project)).read())

  # Loop over all the defined sample attributes and import them, but only if the parsing of the Somalier
  # files was successful
  if hasSampleAttributes:
    for attribute in sampleAttributes:

      # Only import the attribute if it wasn't already in the project
      if not sampleAttributes[attribute]["present"]:
        attributeId = sampleAttributes[attribute]["id"]
        jsonData    = json.loads(os.popen(api_sa.postImportSampleAttribute(mosaicConfig, attributeId, args.project)).read())
  
    # Upload the sample attribute values tsv
    data = os.popen(api_sa.postUploadSampleAttribute(mosaicConfig, args.output, args.project))

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

# The id of the project holding Somalier attributes
somalierProjectId = False

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
version = "0.0.1"

if __name__ == "__main__":
  main()
