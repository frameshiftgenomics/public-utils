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
  global alignstatsProjectId
  global hasSampleAttributes
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {"token": True, "url": True, "attributesProjectId": True}
  mosaicConfig   = mosaic_config.parseConfig(args, mosaicRequired)

  # Check the integration status, e.g. if the required attributes exist or need to be created
  checkStatus(args)

  # Get the attributes names to be populated
  parseAttributes(args)

  # Get any alignstats files attached to the project samples
  #test = get_mosaic_data.getSampleFiles(mosaicConfig, args.project, "alignstats.json")
  #print(test)
  #exit(0)

  # If the alignstatsProjectId is False, the project needs to be created along with all the Alignstats attributes
  if not alignstatsProjectId:
    createProject(args)
    createAttributes(args)

  # Import the attributes into the project with Alignstats data
  getAttributeIds(args)

  # Check if the attributes already exist in the target project
  checkAttributesExist(args)

  ###### MAKE SURE ERROR REPORTING IS DONE. PROJECT VARIABLE SHOULD BE SET TO PASS / FAIL WHERE POSSIBLE
  # Each sample has a separate json file. Get the names of all the files and the sample names
  if not getSampleFiles(args): outputErrors(1)

  # Read the json files for each sample and store the attributes
  passed = readJsonFiles(args)

  # If this step failed, the alignstats json files were not successfully processed. The project attribute 
  # "Alignstats Data" should still be imported into the project and set to Fail. Otherwise the alignstats
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
  #outputErrors(0)

# Input options
def parseCommandLine():
  global version

  parser = argparse.ArgumentParser(description='Process the command line arguments')

# Required arguments
  parser.add_argument('--reference', '-r', required = True, metavar = "string", help = "The reference genome to use. Allowed values: '37', '38'")
  parser.add_argument('--input_files', '-i', required = True, metavar = "file", action = "append", help = "The input json files (this can be set multiple times - once file per sample")
  parser.add_argument('--project', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")

  # Optional pipeline arguments
  parser.add_argument('--attributes_file', '-f', required = False, metavar = "file", help = "The input file listing the Peddy attributes")
  parser.add_argument('--output', '-o', required = False, metavar = "file", help = "The output file containing the values to upload")

  # Optional mosaic arguments
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "The config file for Mosaic")
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic")
  parser.add_argument('--attributes_project', '-a', required = False, metavar = "integer", help = "The Mosaic project id that contains public attributes")

  # Version
  parser.add_argument('--version', '-v', action="version", version='Alignstats integration version: ' + str(version))

  return parser.parse_args()

# Check if the Alignstats attributes have already been created or if then need to be created
def checkStatus(args):
  global alignstatsProjectId

  # Check the public attributes project for the project attribute indicating that the alignstats integration
  # has been run before
  data = json.loads(os.popen(api_pa.getProjectAttributes(mosaicConfig, mosaicConfig["attributesProjectId"])).read())

  # Loop over all the project attributes and look for attribute "Alignstats Integration xa545Ihs"
  alignstatsProjectId = False
  for attributeName in data:
    if attributeName["name"] == "Alignstats Integration xa545Ihs":

      # There should be a value in the json object corresponding to the value in this project. Check this is the case
      alignstatsProjectId = attributeName["values"][0]["value"]
      break

# Parse the tsv file containing the Mosaic attributes
def parseAttributes(args):
  global errors
  global sampleNames
  global sampleAttributes
  global projectAttributes
  global integrationStatus

  # If the attributes file was not specified on the command line, use the default version
  if not args.attributes_file: args.attributes_file = os.path.dirname(os.path.abspath(__file__)) + "/mosaic.atts.alignstats.tsv"

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
    # False for now. These will be read from the Alignstats Attributes project if it already exists, or will
    # be assigned when the attributes are created, if this is the first running of the Alignstats integration.
    # Get the value type (string or float) from the file
    if attributes[0] == "project": projectAttributes[attributes[1]] = {"id": False, "uid": False, "type": attributes[2], "values": False}

    # With sample attributes, we need both the attribute id and uid which will be determined later. For now,
    # set the id and uid to False, and read in the value type
    elif attributes[0] == "sample":
      sampleAttributes[attributes[1]] = {"id": False, "uid": False, "type": attributes[2], "name": attributes[3], "xlabel": attributes[4], "ylabel": attributes[5], "values": {}, "processed": False, "present": False}
      sampleNames[attributes[3]]      = attributes[1]

    # If the attribute is not correctly defined, add the line to the errors
    else:
      integrationStatus = "Incomplete"
      errors.append("Unknown attribute in line " + str(lineNo) + " of file " + args.attributes)

# Create a project to hold all the Alignstats attributes
def createProject(args):
  global alignstatsProjectId
  global mosaicConfig

  # Define the curl command
  command  = api_p.postProject(mosaicConfig, "Alignstats Attributes", args.reference)
  jsonData = json.loads(os.popen(command).read())
  alignstatsProjectId = jsonData["id"]

  # Add a project attribute to the Public attributes project with this id as the value
  command  = api_pa.postProjectAttribute(mosaicConfig, "Alignstats Integration xa545Ihs", "float", str(alignstatsProjectId), "false", mosaicConfig["attributesProjectId"])
  jsonData = json.loads(os.popen(command).read())

# If the Alignstats attributes project was created, create all the required attributes                                                                                         
def createAttributes(args):                                                                                                                                               
  global alignstatsProjectId
  global projectAttributes
  global sampleAttributes
  global mosaicConfig

  # Create all the project attributes required for Alignstats integration
  for attribute in projectAttributes:
    attType  = projectAttributes[attribute]["type"]
    command  = api_pa.postProjectAttribute(mosaicConfig, attribute, attType, "Null", "true", alignstatsProjectId)
    jsonData = json.loads(os.popen(command).read())
                  
  # Create all the sample attributes required for Alignstats integration
  for attribute in sampleAttributes:
    attType  = sampleAttributes[attribute]["type"]
    xlabel   = sampleAttributes[attribute]["xlabel"]
    ylabel   = sampleAttributes[attribute]["ylabel"]
    jsonData = json.loads(os.popen(api_sa.postSampleAttribute(mosaicConfig, attribute, attType, "Not Set", "true", xlabel, ylabel, alignstatsProjectId)).read())

# Import the attributes into the current project
def getAttributeIds(args):
  global errors
  global alignstatsProjectId
  global projectAttributes
  global sampleAttributes
  global mosaicConfig

  # First, get all the project attribute ids from the Alignstats Attributes project
  try: jsonData = json.loads(os.popen(api_pa.getProjectAttributes(mosaicConfig, alignstatsProjectId)).read())
  except: fail('Couldn\'t get project attributes')

  # Loop over the project attributes and store the ids                                                 
  for attribute in jsonData:
    projectAttributes[str(attribute["name"])]["id"]  = attribute["id"]
    projectAttributes[str(attribute["name"])]["uid"] = attribute["uid"]

  # Get all the sample attribute ids from the Alignstats Attributes project
  try: jsonData = json.loads(os.popen(api_sa.getSampleAttributes(mosaicConfig, alignstatsProjectId, 'false')).read())
  except: fail('Couldn\'t get sample attriubtes')

  # Loop over the sample attributes and store the ids                                                
  for attribute in jsonData:                                                                          

    # Only include custom attributes (e.g. ignore global default attributes like Median Read Coverage that are
    # added to all Mosaic projects
    if str(attribute["is_custom"]) == "True":

      # Only set the values for attributes that exist in alignstats tsv file. The Alignstats Attributes
      # project may contain more attributes than the tsv. This could be the case if we are just trying
      # to update a subset of attributes, or if the alignstats output has been updated
      if str(attribute["name"]) in sampleAttributes:
        sampleAttributes[str(attribute["name"])]["id"]        = attribute["id"]
        sampleAttributes[str(attribute["name"])]["uid"]       = attribute["uid"]
        sampleAttributes[str(attribute["name"])]["processed"] = True

      # Store the names of any attributes that exist in Mosaic, but are not being updated
      else: errors.append("Mosaic attribute \"" + str(attribute["name"]) + "\" was not included in the alignstats tsv and was thus not updated")

  # Loop over the sampleAttributes (e.g. all the attributes that were defined in the alignstats tsv, representing
  # all attributes to be included. If any of these attributes were not "processed" above, there is no attribute in
  # the Mosaic Alignstats Attributes project and it needs to be created
  for attribute in sampleAttributes:
    if not sampleAttributes[attribute]["processed"]:
      attType  = sampleAttributes[attribute]["type"]
      xlabel   = sampleAttributes[attribute]["xlabel"]
      ylabel   = sampleAttributes[attribute]["ylabel"]
      try: jsonData = json.loads(os.popen(api_sa.postSampleAttribute(mosaicConfig, attribute, attType, 'Null', 'true', xlabel, ylabel, alignstatsProjectId)).read())
      except: fail('Could not create sample attribute: ' + str(attribute))

      # If an error was thrown, inform the user and quit
      if 'message' in jsonData: fail('Failed to create sample attribute (' + str(attribute) + '. Error message was: ' + str(jsonData['message']))

      # Store information about the created attribute
      sampleAttributes[str(jsonData["name"])]["id"]        = jsonData["id"]
      sampleAttributes[str(jsonData["name"])]["uid"]       = jsonData["uid"]
      sampleAttributes[str(jsonData["name"])]["processed"] = True

# Check if the attributes already exist in the target project and check if the Alignstats integration has
# already been run (attributes could have been deleted, so both checks are required)
def checkAttributesExist(args):
  global sampleAttributes
  global projectAttributes
  global hasRun
  global mosaicConfig

  for attribute in projectAttributes:
    if attribute == "Alignstats Data": alignstatsId = projectAttributes[attribute]["id"]

  # Get all the project attributes in the target project
  jsonData = json.loads(os.popen(api_pa.getProjectAttributes(mosaicConfig, args.project)).read())
  for attribute in jsonData:
    if attribute["name"] == "Alignstats Data" and attribute["id"] == alignstatsId: hasRun = True

  # Get all the sample attributes in the target project
  jsonData = json.loads(os.popen(api_sa.getSampleAttributes(mosaicConfig, args.project, 'false')).read())
  projectSampleAttributes = []
  for attribute in jsonData: projectSampleAttributes.append(attribute["id"])

  # Loop over the sample attributes and check if they exist in the target project
  for attribute in sampleAttributes:
    if sampleAttributes[attribute]["id"] in projectSampleAttributes: sampleAttributes[attribute]["present"] = True

# Read the input file to get the names of the json files for all the samples in the project
def getSampleFiles(args):
  global integrationStatus
  global errors
  global samples

  # Get all of the samples in the project
  command  = api_s.getSamples(mosaicConfig, args.project)
  jsonData = json.loads(os.popen(command).read())
  for record in jsonData: samples[record["name"]] = False

  # Loop over the provided input files - there should be one file per sample - and check the files exist
  isSuccess  = True
  for index, filename in enumerate(args.input_files):

    # The file may include the entire path, so extract just the filename
    fileNoPath = filename.split("/")[-1] if "/" in filename else filename

    # See if one, and only one, of the project samples are embedded in the filename
    hasMatch      = False
    matchedSample = False
    for sample in samples:
      if sample in fileNoPath:
        if hasMatch:
          errors.append("File: " + fileNoPath + " contains the names of multiple project samples, so it cannot be determined which samples this file belongs to")
          integrationStatus = "Fail"
          isSuccess         = False
          break
        else:
          hasMatch      = True
          matchedSample = sample

    # If the filename does not contain the name of a sample, it cannot be determined which sample the file belongs to
    if not hasMatch:
      errors.append("File: " + fileNoPath + " does not contain the name of any project samples, so it cannot be determined which samples this file belongs to")
      integrationStatus = "Fail"
      break

    # Otherwise associate this file with the sample, and check it exists
    else:
      try: samples[matchedSample] = {"file": filename, "handle": open(filename, "r")}
      except:
        errors.append("File: " + filename + " could not be opened")
        integrationStatus = "Fail"
        isSuccess = False

  # Only samples with associated files can be processed, so remove all samples without a file, and provide a warning
  toRemove = []
  for sample in samples:
    if not samples[sample]: toRemove.append(sample)
  if len(toRemove) > 0:
    for sample in toRemove: samples.pop(sample)
    print("WARNING: ", len(toRemove), " samples did not have alignstats files associated", sep = "")

  return isSuccess

# Read through the Alignstats json files for each sample and store the information
def readJsonFiles(args):
  global integrationStatus
  global errors
  global samples
  global sampleNames
  global sampleAttributes

  # Loop over the samples, and open and read the associated json files
  for sample in samples:

    # Read through the alignstats file
    try: sampleData = json.loads(samples[sample]["handle"].read())
    except:
      integrationStatus= "Fail"
      errors.append("File: " + samples[sample]["file"] + " is not a well formed json")
      return False

    # Loop over all the attributes in the json file
    for attribute in sampleData:
      try: attributeName = sampleNames[attribute]
      except:
        errors.append("Attribute \"" +  attribute + "\" not present for sample \"" + sample + "\"")
        continue

      # Store the values for this sample
      try: sampleAttributes[attributeName]["values"][sample] = sampleData[attribute]

      # If the attribute in the json file is not present in Mosaic, flag it
      except: 
      #if attributeName not in sampleAttributes:
        ################
        ################
        ################
        ###########ERROR
        print("ATTRIBUTE MISSING", sample, attributeName, sampleAttributes[attributeName])
        continue

    # Close the sample file
    samples[sample]["handle"].close()

  # If the files were successfully processed, return True
  return True

# Print out data for import into Mosaic
def outputToMosaic(args):
  global samples
  global sampleAttributes

  # Open the output file
  if not args.output: args.output = "alignstats_mosaic_upload.tsv"
  outFile = open(args.output, "w")

  # Output the header line
  line = "SAMPLE_NAME"
  for attribute in sorted(sampleAttributes.keys()): line += "\t" + str(sampleAttributes[attribute]["uid"])
  print(line, file = outFile)
  
  # Loop over the samples and output the required information
  for sample in sorted(samples):
    line = sample
    for attribute in sorted(sampleAttributes.keys()):
      try: value = sampleAttributes[attribute]["values"][sample]
      except: value = "" 
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
  global hasRun
  global mosaicConfig

  # Set the Alignstats Data project attribute value to the value stored in integrationStatus
  projectAttributes["Alignstats Data"]["values"] = integrationStatus

  # Begin with the import and setting of project attributes
  for attribute in projectAttributes:                                                                           
    attributeId = projectAttributes[attribute]["id"]                                                            
    value       = projectAttributes[attribute]["values"]                                                        

    # If the integration has already been run, just update the values, otherwise import them
    if hasRun: jsonData = json.loads(os.popen(api_pa.putProjectAttribute(mosaicConfig, value, args.project, attributeId)).read())
    else: jsonData = json.loads(os.popen(api_pa.postImportProjectAttribute(mosaicConfig, attributeId, value, args.project)).read())

  # Loop over all the defined sample attributes and import them, but only if the parsing of the peddy           
  # html was successful     
  if hasSampleAttributes:   
    for attribute in sampleAttributes:
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

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Output errors
def outputErrors(errorCode):
  global errors

  for error in errors: print(error)

# Initialise global variables

# Store the version
version = "0.1.2"

# Store mosaic info, e.g. the token, url etc.
mosaicConfig = {}

# The id of the project holding alignstats attributes
alignstatsProjectId = False
  
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
integrationStatus = "v" + str(version)

# Keep track of the samples in the project
samples  = {}

# Record if sample attributes are successfully processed
hasSampleAttributes = False

if __name__ == "__main__":
  main()
