#!/usr/bin/python

from __future__ import print_function

import os
import math
import argparse
import json
from random import random

def main():
  global alignstatsProjectId
  global hasSampleAttributes

  # Parse the command line
  args = parseCommandLine()

  # Get the attributes names to be populated
  parseAttributes(args)

  # Check the integration status, e.g. if the required attributes exist or need to be created
  checkStatus(args)

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

  exit(0)

  # Output the observed errors.
  outputErrors(0)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Typically unchanged parameters for a Mosaic instance
  parser.add_argument('--token', '-t', required = True, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = True, metavar = "string", help = "The base url for Mosaic curl commands, up to an including \"api\". Do NOT include a trailing /")
  parser.add_argument('--apiCommands', '-c', required = True, metavar = "string", help = "The path to the directory of api commands")
  parser.add_argument('--attributesFile', '-f', required = True, metavar = "file", help = "The input file listing the Alignstats attributes")
  parser.add_argument('--attributesProject', '-a', required = True, metavar = "integer", help = "The Mosaic project id that contains public attributes")

  # Dynamic parameters
  parser.add_argument('--reference', '-r', required = True, metavar = "string", help = "The genome reference for the project")
  parser.add_argument('--input', '-i', required = True, metavar = "file", help = "The input file listing samples and json files")
  parser.add_argument('--path', '-d', required = True, metavar = "string", help = "The path where the tsv will be generated")
  parser.add_argument('--output', '-o', required = True, metavar = "file", help = "The output file containing the values to upload. Extension must be tsv")
  parser.add_argument('--project', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")

  return parser.parse_args()

# Check if the Alignstats attributes have already been created or if then need to be created
def checkStatus(args):
  global alignstatsProjectId

  # Check the public attributes project for the project attribute indicating that the alignstats integration
  # has been run before
  command = args.apiCommands + "/get_project_attributes.sh " + args.token + " \"" + args.url + "\" " + args.attributesProject
  data    = json.loads(os.popen(command).read())

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

  # Define the curl command
  command  = args.apiCommands + "/create_project.sh " + args.token + " \"" + args.url + "\" \"Alignstats Attributes\" \"" + args.reference + "\""
  jsonData = json.loads(os.popen(command).read())
  alignstatsProjectId = jsonData["id"]

  # Add a project attribute to the Public attributes project with this id as the value
  command  = args.apiCommands + "/create_project_attribute.sh " + args.token + " \"" + args.url + "\" "
  command += args.attributesProject + " \"Alignstats Integration xa545Ihs\" float " + str(alignstatsProjectId) + " false"
  jsonData = json.loads(os.popen(command).read())

# If the Alignstats attributes project was created, create all the required attributes                                                                                         
def createAttributes(args):                                                                                                                                               
  global alignstatsProjectId
  global projectAttributes
  global sampleAttributes

  # Create all the project attributes required for Alignstats integration
  command = args.apiCommands + "/create_project_attribute.sh " + args.token + " \"" + args.url + "\" " + str(alignstatsProjectId)
  for attribute in projectAttributes:
    attType  = projectAttributes[attribute]["type"]
    body     = " \"" + str(attribute) + "\" \"" + str(attType) + "\" Null true"
    jsonData = json.loads(os.popen(command + body).read())
                  
  # Create all the sample attributes required for Alignstats integration
  command = args.apiCommands + "/create_sample_attribute.sh " + args.token + " \"" + args.url + "\" " + str(alignstatsProjectId)
  for attribute in sampleAttributes:
    attType  = sampleAttributes[attribute]["type"]
    xlabel   = sampleAttributes[attribute]["xlabel"]
    ylabel   = sampleAttributes[attribute]["ylabel"]
    body     = " \"" + str(attribute) + "\" \"" + str(attType) + "\" \"" + str(xlabel) + "\" \"" + str(ylabel) + "\" Null true"
    jsonData = json.loads(os.popen(command + body).read())

# Import the attributes into the current project
def getAttributeIds(args):
  global errors
  global alignstatsProjectId
  global projectAttributes
  global sampleAttributes

  # First, get all the project attribute ids from the Alignstats Attributes project
  command  = args.apiCommands + "/get_project_attributes.sh " + str(args.token) + " " + str(args.url) + " " + str(alignstatsProjectId)
  jsonData = json.loads(os.popen(command).read())

  # Loop over the project attributes and store the ids                                                 
  for attribute in jsonData:
    projectAttributes[str(attribute["name"])]["id"]  = attribute["id"]
    projectAttributes[str(attribute["name"])]["uid"] = attribute["uid"]

  # Get all the sample attribute ids from the Alignstats Attributes project
  command  = args.apiCommands + "/get_sample_attributes.sh " + args.token + " \"" + args.url + "\" " + str(alignstatsProjectId)
  jsonData = json.loads(os.popen(command).read())

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
      command  = args.apiCommands + "/create_sample_attribute.sh " + args.token + " \"" + args.url + "\" " + str(alignstatsProjectId)
      attType  = sampleAttributes[attribute]["type"]
      xlabel   = sampleAttributes[attribute]["xlabel"]
      ylabel   = sampleAttributes[attribute]["ylabel"]
      body     = " \"" + str(attribute) + "\" \"" + str(attType) + "\" \"" + str(xlabel) + "\" \"" + str(ylabel) + "\" Null true"
      jsonData = json.loads(os.popen(command + body).read())
      sampleAttributes[str(jsonData["name"])]["id"]        = jsonData["id"]
      sampleAttributes[str(jsonData["name"])]["uid"]       = jsonData["uid"]
      sampleAttributes[str(jsonData["name"])]["processed"] = True

# Check if the attributes already exist in the target project and check if the Alignstats integration has
# already been run (attributes could have been deleted, so both checks are required)
def checkAttributesExist(args):
  global sampleAttributes
  global projectAttributes
  global hasRun

  for attribute in projectAttributes:
    if attribute == "Alignstats Data": alignstatsId = projectAttributes[attribute]["id"]

  # Get all the project attributes in the target project
  command  = args.apiCommands + "/get_project_attributes.sh " + str(args.token) + " " + str(args.url) + " " + str(args.project)
  jsonData = json.loads(os.popen(command).read())
  for attribute in jsonData:
    if attribute["name"] == "Alignstats Data" and attribute["id"] == alignstatsId: hasRun = True

  # Get all the sample attributes in the target project
  command  = args.apiCommands + "/get_sample_attributes.sh " + str(args.token) + " " + str(args.url) + " " + str(args.project)
  jsonData = json.loads(os.popen(command).read())
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

  # Get the samples and the json files
  try: inputFile = open(args.input, "r")
  except:
    integrationStatus= "Fail"
    errors.append("File: " + args.input + " does not exist")
    return False

  # Read each line and get the file names
  for line in inputFile.readlines():
    line = line.rstrip()
    samples[line.split("\t")[0]] = line.split("\t")[1]

  # Close the input file
  inputFile.close()

  return True

# Read through the Alignstats json files for each sample and store the information
def readJsonFiles(args):
  global integrationStatus
  global errors
  global samples
  global sampleNames
  global sampleAttributes

  # Loop over the samples, and open and read the associated json files
  for sample in samples:
    try: sampleFile = open(samples[sample], 'r')
    except:
      integrationStatus= "Fail"
      errors.append("File: " + args.input + " does not exist")
      return False

    # Read through the alignstats file
    try: sampleData = json.loads(sampleFile.read())
    except:
      integrationStatus= "Fail"
      errors.append("File: " + args.input + " is not a well formed json")
      return False

    # Loop over all the attributes in the
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
    sampleFile.close()

  # If the files were successfully processed, return True
  return True

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

  # Set the Alignstats Data project attribute value to the value stored in integrationStatus
  projectAttributes["Alignstats Data"]["values"] = integrationStatus

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
    command = args.apiCommands + "/import_sample_attribute.sh " + args.token + " \"" + args.url + "\" \"" + str(args.project) + "\" "
    for attribute in sampleAttributes:
      attributeId = sampleAttributes[attribute]["id"]
      body        = "\"" + str(attributeId) + "\""
      jsonData    = json.loads(os.popen(command + body).read())
  
    # Upload the sample attribute values tsv
    command  = args.apiCommands + "/upload_sample_attribute_tsv.sh " + args.token + " \"" + args.url + "\" \"" + str(args.project) + "\" \""
    command += str(args.path) + "/" + str(args.output) + "\""
    data     = os.popen(command)

# Create an attribute set
def createAttributeSet(args):
  global sampleAttributes

  # Get any existing attribute sets
  command = args.apiCommands + "/get_attribute_sets.sh " + str(args.token) + " \"" + str(args.url) + "\" \"" + str(args.project) + "\""
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
    command  = args.apiCommands + "/delete_attribute_set.sh " + str(args.token) + " \"" + str(args.url) + "\" \"" + str(args.project) + "\" "
    command += "\"" + str(setId) + "\""
    try: data = os.popen(command).read()
    except: print("Failed to delete attribute set with id:", setId, sep = "")

  # Create the attribute set from these ids
  if createSet:
    command  = args.apiCommands + "/post_attribute_set.sh " + str(args.token) + " \"" + str(args.url) + "\" \"" + str(args.project) + "\" "
    command += "\"Alignstats\" \"Imported Alignstats attributes\" true \"" + str(attributeIds) + "\" \"sample\""

    try: data = json.loads(os.popen(command).read())
    except:
      print("Failed to create attribute set")
      exit(1)

# Output errors
def outputErrors(errorCode):
  global errors

# Initialise global variables

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
integrationStatus = "Pass"

# Keep track of the samples in the project
samples  = {}

# Record if sample attributes are successfully processed
hasSampleAttributes = False

if __name__ == "__main__":
  main()
