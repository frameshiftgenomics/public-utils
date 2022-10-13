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
import get_mosaic_data
import api_attributes as api_a
import api_dashboards as api_d
import api_samples as api_s
import api_projects as api_p
import api_project_attributes as api_pa
import api_sample_attributes as api_sa

def main():
  global fastpProjectId
  global hasSampleAttributes
  global mosaicConfig
  global samples

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {"token": True, "url": True, "attributesProjectId": True}
  mosaicConfig   = mosaic_config.parseConfig(args, mosaicRequired)

  # Check the integration status, e.g. if the required attributes exist or need to be created
  checkStatus(args)

  # Get the attributes names to be populated
  parseAttributes(args)

  # If the fastpProjectId is False, the project needs to be created along with all the Fastp attributes
  if not fastpProjectId: createProject(args)
  createAttributes(args)

  # Import the attributes into the project with Alignstats data
  getAttributeIds(args)

  # Get all the samples in the project
  #samples = get_mosaic_data.getSamples(mosaicConfig, args.project)

  # Check if the attributes already exist in the target project
  checkAttributesExist(args)

  # Read the json file and store the attributes
  passed = readJsonFile(args)

  # If this step failed, the fastp json file was not successfully processed. The project attribute 
  # "Fastp Data" should still be imported into the project and set to Fail. Otherwise the fastp
  # data should be processed
  if passed:
    hasSampleAttributes = True

    # Generate a file to output to Mosaic
    outputToMosaic(args)

  # Import the attributes into the current project and upload the values
  importAttributes(args)

  # Create an attribute set
  createAttributeSet(args)

  # Remove the created files
  removeFiles(args)

  # Output the observed errors.
  outputErrors(0)

# Input options
def parseCommandLine():
  global version

  parser = argparse.ArgumentParser(description='Process the command line arguments')

# Required arguments
  parser.add_argument('--input', '-i', required = True, metavar = "file", help = "The input json file")
  parser.add_argument('--project', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")

  # Optional pipeline arguments
  parser.add_argument('--attributes_file', '-f', required = False, metavar = "file", help = "The input file listing the Peddy attributes")
  parser.add_argument('--output', '-o', required = False, metavar = "file", help = "The output file containing the values to upload")

  # Optional mosaic arguments
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "The config file for Mosaic")
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic")
  parser.add_argument('--attributes_project', '-a', required = False, metavar = "integer", help = "The Mosaic project id that contains public attributes")

  return parser.parse_args()

# Check if the Fastp attributes have already been created or if then need to be created
def checkStatus(args):
  global fastpProjectId

  # Check the public attributes project for the project attribute indicating that the fastp integration
  # has been run before
  try: data = json.loads(os.popen(api_pa.getProjectAttributes(mosaicConfig, mosaicConfig["attributesProjectId"])).read())
  except: fail("Failed to get public attributes. API message: " + os.popen(api_pa.getProjectAttributes(mosaicConfig, mosaicConfig["attributesProjectId"])).read())

  # Loop over all the project attributes and look for attribute "Fastp Integration xa545Ihs"
  fastpProjectId = False
  for attributeName in data:
    if attributeName["name"] == "Fastp Integration xa545Ihs":

      # There should be a value in the json object corresponding to the value in this project. Check this is the case
      fastpProjectId = attributeName["values"][0]["value"]
      break

# Parse the tsv file containing the Mosaic attributes
def parseAttributes(args):
  global errors
  global sampleNames
  global sampleAttributes
  global projectAttributes
  global integrationStatus

  # If the attributes file was not specified on the command line, use the default version
  if not args.attributes_file: args.attributes_file = os.path.dirname(os.path.abspath(__file__)) + "/mosaic.atts.fastp.tsv"

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
    # False for now. These will be read from the Fastp Attributes project if it already exists, or will
    # be assigned when the attributes are created, if this is the first running of the Fastp integration.
    # Get the value type (string or float) from the file
    if attributes[0] == "project": projectAttributes[attributes[1]] = {"id": False, "uid": False, "type": attributes[2], "values": False}

    # With sample attributes, we need both the attribute id and uid which will be determined later. For now,
    # set the id and uid to False, and read in the value type
    elif attributes[0] == "sample":
      sampleAttributes[attributes[1]] = {"id": False, "uid": False, "type": attributes[2], "name": attributes[3], "xlabel": attributes[4], "ylabel": attributes[5], "value": False, "processed": False, "present": False}
      sampleNames[attributes[3]]      = attributes[1]

    # If the attribute is not correctly defined, add the line to the errors
    else:
      integrationStatus = "Incomplete"
      errors.append("Unknown attribute in line " + str(lineNo) + " of file " + args.attributes)

# Create a project to hold all the Fastp attributes
def createProject(args):
  global fastpProjectId
  global mosaicConfig

  # Create the project
  try: jsonData = json.loads(os.popen(api_p.postProject(mosaicConfig, "Fastp Attributes", args.reference)).read())
  except: fail("Unable to create Fastp Attributes project")
  fastpProjectId = jsonData["id"]

  # Add a project attribute to the Public attributes project with this id as the value
  try: jsonData = json.loads(os.popen(api_pa.postProjectAttribute(mosaicConfig, "Fastp Integration xa545Ihs", "float", str(fastpProjectId), "false", mosaicConfig["attributesProjectId"])).read())
  except: fail("Unable to add project attribute to Fastp attribute project")

# If the Fastp attributes project was created, create all the required attributes                                                                                         
def createAttributes(args):                                                                                                                                               
  global fastpProjectId
  global projectAttributes
  global sampleAttributes
  global mosaicConfig

  # Create all the project attributes required for Fastp integration
  for attribute in projectAttributes:

    # Check if an attribute of this name already exists. If the GET command fails, there are no attributes in
    # the project, so proceed to add the attribute
    addAttribute = True
    for existingAttribute in json.loads(os.popen(api_pa.getProjectAttributes(mosaicConfig, fastpProjectId)).read()):
      if existingAttribute["name"] == attribute: addAttribute = False

    # Add the attribute
    if addAttribute:
      attType = projectAttributes[attribute]["type"]
      try: jsonData = json.loads(os.popen(api_pa.postProjectAttribute(mosaicConfig, attribute, attType, "Null", "true", fastpProjectId)).read())
      except: fail("Failed to create fastp public project attribute: " + attribute)
                  
  # Create all the sample attributes required for Fastp integration
  for attribute in sampleAttributes:

    # Check if the sample attribute exists
    addAttribute = True
    for existingAttribute in json.loads(os.popen(api_sa.getSampleAttributes(mosaicConfig, fastpProjectId)).read()):
      if existingAttribute["name"] == attribute: addAttribute = False

    # Add the attribute
    if addAttribute:
      attType  = sampleAttributes[attribute]["type"]
      xlabel   = sampleAttributes[attribute]["xlabel"]
      ylabel   = sampleAttributes[attribute]["ylabel"]
      try: jsonData = json.loads(os.popen(api_sa.postSampleAttribute(mosaicConfig, attribute, attType, "Not Set", "true", xlabel, ylabel, fastpProjectId)).read())
      except: fail("Failed to create fastp public sample attribute: " + attribute)

# Import the attributes into the current project
def getAttributeIds(args):
  global errors
  global fastpProjectId
  global projectAttributes
  global sampleAttributes
  global mosaicConfig

  # First, get all the project attribute ids from the Fastp Attributes project
  jsonData = json.loads(os.popen(api_pa.getProjectAttributes(mosaicConfig, fastpProjectId)).read())

  # Loop over the project attributes and store the ids                                                 
  for attribute in jsonData:
    projectAttributes[str(attribute["name"])]["id"]  = attribute["id"]
    projectAttributes[str(attribute["name"])]["uid"] = attribute["uid"]

  # Get all the sample attribute ids from the Fastp Attributes project
  jsonData = json.loads(os.popen(api_sa.getSampleAttributes(mosaicConfig, fastpProjectId)).read())

  # Loop over the sample attributes and store the ids                                                
  for attribute in jsonData:                                                                          

    # Only include custom attributes (e.g. ignore global default attributes like Median Read Coverage that are
    # added to all Mosaic projects
    if str(attribute["is_custom"]) == "True":

      # Only set the values for attributes that exist in fastp tsv file. The Fastp Attributes
      # project may contain more attributes than the tsv. This could be the case if we are just trying
      # to update a subset of attributes, or if the alignstats output has been updated
      if str(attribute["name"]) in sampleAttributes:
        sampleAttributes[str(attribute["name"])]["id"]        = attribute["id"]
        sampleAttributes[str(attribute["name"])]["uid"]       = attribute["uid"]
        sampleAttributes[str(attribute["name"])]["processed"] = True

      # Store the names of any attributes that exist in Mosaic, but are not being updated
      else: fail("Mosaic attribute \"" + str(attribute["name"]) + "\" was not included in the fastp tsv and was thus not updated")

# Check if the attributes already exist in the target project and check if the fastp integration has
# already been run (attributes could have been deleted, so both checks are required)
def checkAttributesExist(args):
  global sampleAttributes
  global projectAttributes
  global hasRun
  global mosaicConfig

  for attribute in projectAttributes:
    if attribute == "Fastp Data": fastpId = projectAttributes[attribute]["id"]

  # Get all the project attributes in the target project
  jsonData = json.loads(os.popen(api_pa.getProjectAttributes(mosaicConfig, args.project)).read())
  for attribute in jsonData:
    if attribute["name"] == "Fastp Data" and attribute["id"] == fastpId: hasRun = True

  # Get all the sample attributes in the target project
  jsonData = json.loads(os.popen(api_sa.getSampleAttributes(mosaicConfig, args.project)).read())
  projectSampleAttributes = []
  for attribute in jsonData: projectSampleAttributes.append(attribute["id"])

  # Loop over the sample attributes and check if they exist in the target project
  for attribute in sampleAttributes:
    if sampleAttributes[attribute]["id"] in projectSampleAttributes: sampleAttributes[attribute]["present"] = True

# Read through the Alignstats json file and store the information
def readJsonFile(args):
  global integrationStatus
  global errors
  global sampleNames
  global sampleAttributes

  # Open the input file
  try: jsonFile = open(args.input, "r")
  except:
    integrationStatus = "Fail"
    errors.append("File: " + args.input + " was not found")
    return False

  # Read through the alignstats file
  try: fastpData = json.loads(jsonFile.read())
  except:
    integrationStatus= "Fail"
    errors.append("File: " + args.input + " is not a well formed json")
    return False

  # Loop over all attributes to be imported
  for attribute in sampleNames:

    # If the attribute contains pipes, this is a nested object in the json, so break this up
    attributePath = attribute.split("|") if "|" in attribute else [attribute]

    # Check that this attribute is present in the json and extract the value
    value = False
    while len(attributePath) > 0:
      marker = attributePath.pop(0)

      # If value is False, this is the first step, so the value must be extracted from the fastpData
      if not value:
        try: value = fastpData[marker]
        except:
          print("Attribute: \"" + attribute + "\" could not be processed")
          break

      # Otherwise, value has already been populated and the required value is within this object
      else:
        try: value = value[marker]
        except:
          print("Attribute: \"" + attribute + "\" could not be processed")
          break

    # Store the value
    sampleAttributes[sampleNames[attribute]]["value"] = value

  # If the files were successfully processed, return True
  return True

# Print out data for import into Mosaic
def outputToMosaic(args):
  global samples
  global sampleAttributes

  # Open the output file
  if not args.output: args.output = "fastp_mosaic_upload.tsv"
  outFile = open(args.output, "w")

  # Output the header line
  line = "SAMPLE_NAME"
  for attribute in sorted(sampleAttributes.keys()): line += "\t" + str(sampleAttributes[attribute]["uid"])
  print(line, file = outFile)
  
  line = "BOB"
  for attribute in sorted(sampleAttributes.keys()):
    try: value = sampleAttributes[attribute]["value"]
    except: value = "" 
    line += "\t" + str(value)
  print(line, sep = "\t", file = outFile)
  exit(0)

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

  # Set the Alignstats Data project attribute value to the value stored in integrationStatus
  projectAttributes["Alignstats Data"]["values"] = integrationStatus

  # Begin with the import and setting of project attributes
  for attribute in projectAttributes:                                                                           
    attributeId = projectAttributes[attribute]["id"]                                                            
    value       = projectAttributes[attribute]["values"]                                                        
    command     = api_pa.postImportProjectAttribute(mosaicConfig, attributeId, value, args.project)
    jsonData    = json.loads(os.popen(command).read())

  # Loop over all the defined sample attributes and import them, but only if the parsing of the peddy           
  # html was successful     
  if hasSampleAttributes:   
    for attribute in sampleAttributes:
      attributeId = sampleAttributes[attribute]["id"]
      command     = api_sa.postImportSampleAttribute(mosaicConfig, attributeId, args.project)
      jsonData    = json.loads(os.popen(command).read())
  
    # Upload the sample attribute values tsv
    command = api_sa.postUploadSampleAttribute(mosaicConfig, args.output, args.project)
    data     = os.popen(command)

# Create an attribute set
def createAttributeSet(args):
  global sampleAttributes
  global mosaicConfig

  # Get any existing attribute sets
  command = api_a.getProjectAttributeSets(mosaicConfig, args.project)
  data    = json.loads(os.popen(command).read())

  # Loop over the existing attribute sets and see if the Alignstats set already exists
  setId = False
  existingIds = []
  for attributeSet in data:
    if attributeSet["name"] == "Alignstats":
      setId       = attributeSet["id"]
      existingIds = attributeSet["attribute_ids"]

  # Loop over the imported attributes and create a string of all the ids. Count the number of attributes to go into the set
  attributeIds = []
  for attribute in sampleAttributes: attributeIds.append(sampleAttributes[attribute]["id"])

  # If there already exists a Alignstats attribute set, check that the attribute string is the same. If not, replace the existing set
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
    command = api_a.postProjectAttributeSet(mosaicConfig, "Alignstats", "Imported Alignstats attributes", True, attributeIds, "scatterplot", args.project)
    try: data = json.loads(os.popen(command).read())
    except:
      print("Failed to create attribute set")
      exit(1)

# Remove the created files
def removeFiles(args):

  # Remove the tsv file
  if args.output: os.remove(args.output)

# Output errors
def outputErrors(errorCode):
  global errors

  for error in errors: print(error)

# Fail
def fail(message):
  print(message)
  exit(1)

# Initialise global variables

# Store mosaic info, e.g. the token, url etc.
mosaicConfig = {}

# The id of the project holding alignstats attributes
fastpProjectId = False
  
# Record if the Alignstats integration has previously run
hasRun = False

# Dictionaries to match Alignstats attribute names to their location in the html file
projectAttributes = {}
sampleAttributes  = {}

# sampleAttributes uses the Mosaic name as the key, but there are occasions where
# the key needs to be the Alignstats name. SampleNames provides this
sampleNames = {}

# Keep a list of all errors seen, and the status of the processing
errors            = []
integrationStatus = "Pass"

# Keep track of the samples in the project
samples  = {}

# Record if sample attributes are successfully processed
hasSampleAttributes = False

if __name__ == "__main__":
  main()
