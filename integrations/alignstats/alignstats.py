#!/usr/bin/python

from __future__ import print_function

import sys
import os
import math
import argparse
import json
from random import random
from os.path import exists

# Add the path of the common functions and import them
from sys import path
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-2]) + "/common_components")
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-2]) + "/api_commands")
import mosaic_config
import api_attributes as api_a
import api_dashboards as api_d
import api_projects as api_p
import api_project_attributes as api_pa
import api_samples as api_s
import api_sample_attributes as api_sa
import api_sample_files as api_sf

def main():
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {'MOSAIC_TOKEN': {'value': args.token, 'desc': 'An access token', 'long': '--token', 'short': '-t'},
                    'MOSAIC_URL': {'value': args.url, 'desc': 'The api url', 'long': '--url', 'short': '-u'},
                    'MOSAIC_ATTRIBUTES_PROJECT_ID': {'value': args.attributes_project, 'desc': 'The public attribtes project id', 'long': '--attributes_project', 'short': '-a'},
                    'ALIGNSTATS_ATTRIBUTES_PROJECT_ID': {'value': args.alignstats_project, 'desc': 'The alignstats project id', 'long': '--alignstats_project', 'short': '-l'}}
  mosaicConfig   = mosaic_config.mosaicConfigFile(args.config)
  mosaicConfig   = mosaic_config.commandLineArguments(mosaicConfig, mosaicRequired)

  # Define the alignstats project id
  alignstatsProjectId = mosaicConfig['ALIGNSTATS_ATTRIBUTES_PROJECT_ID']

  # Get any alignstats files that are attached to the project
  samples = api_s.getSampleNameId(mosaicConfig, args.project_id)
  for sample in samples:
    sample['mosaicFiles'] = {}
    sample['files']       = {}
    sampleFiles = api_sf.getSampleFiles(mosaicConfig, args.project_id, sample['id'], 'alignstats.json')
    for fileId in sampleFiles: sample['mosaicFiles'][sampleFiles[fileId]['name']] = sampleFiles[fileId]['uri']

  # If input files are specified on the command line, determine which samples have files specified. Files
  # specified on the command line will be given precedence over those attached to the project
  if args.input_files: getInputFiles(args, samples)

  # Check that there exists one unambiguous alignstats files to use for each sample. If there is a single
  # file specified on the command line for a sample, this is the file that will be used. If no file is
  # specified on the command line, there must be one and only one "alignstats.json" file associated with
  # the Mosaic project
  samples = checkInputFiles(samples)

  # Get the attributes names to be populated
  parseAttributes(args)

  # Import the attributes into the project with Alignstats data
  getAttributeIds(args, alignstatsProjectId)

  # Read the json files for each sample and store the attributes
  readJsonFiles(args, samples)

  # Generate a file to output to Mosaic
  tsvFile = outputToMosaic(samples)

  # Import the attributes into the current project and upload the values
  importAttributes(args, tsvFile)

  # Create an attribute set
  #createAttributeSet(args)

  # Remove the created files
  os.remove(tsvFile)

# Input options
def parseCommandLine():
  global version

  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Required arguments
  parser.add_argument('--input_files', '-i', required = False, metavar = "file", action = "append", help = "The input json files (this can be set multiple times - once file per sample")
  parser.add_argument('--project_id', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")

  # Optional pipeline arguments
  parser.add_argument('--attributes_file', '-f', required = False, metavar = "file", help = "The input file listing the Peddy attributes")

  # Optional mosaic arguments
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "The config file for Mosaic")
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic")
  parser.add_argument('--attributes_project', '-a', required = False, metavar = "integer", help = "The Mosaic project id that contains public attributes")
  parser.add_argument('--alignstats_project', '-l', required = False, metavar = "integer", help = "The Mosaic project id that contains alignstats attributes")

  # Version
  parser.add_argument('--version', '-v', action="version", version='Alignstats integration version: ' + str(version))

  return parser.parse_args()

# Check that the files on the command line contain the name of a sample
def getInputFiles(args, samples):
  for filename in args.input_files:
    noPath = filename.split("/")[-1] if "/" in filename else filename

    # Check to see if this filename contains a sample name
    for sample in samples:
      if sample['name'] in noPath:
        if noPath in sample['files']: fail('Input files for sample ' + str(sample['name']) + ' are specified multiple times on the command line')
        sample['files'][noPath] = filename

  # Check if multiple files were specified for the same sample
  for sample in samples:
    if len(sample['files']) > 1: fail('Input files for sample ' + str(sample['name']) + ' are specified multiple times on the command line')

# Check that there exists one unambiguous alignstats files to use for each sample. If there is a single
# file specified on the command line for a sample, this is the file that will be used. If no file is
# specified on the command line, there must be one and only one "alignstats.json" file associated with
# the Mosaic project
def checkInputFiles(samples):
  for sample in samples:

    # If there are no files specified on the command line
    if len(sample['files']) != 1:
      if len(sample['mosaicFiles']) == 0: fail('No alignstats.json files are assigned in Mosaic, or specified on the command line for sample ' + str(sample['name']))
      if len(sample['mosaicFiles']) > 1: fail('Multiple alignstats.json files are associated with the Mosaic sample ' + str(sample['name']))
      for info in sample['mosaicFiles']:
        sample['filename'] = info
        if sample['mosaicFiles'][info].startswith('file:/'): sample['file'] = sample['mosaicFiles'][info][6:]
        else: sample['file'] = sample['mosaicFiles'][info]

    # If there was a single file specified on the command line
    else:
      for info in sample['files']:
        sample['filename'] = info
        sample['file']     = sample['files'][info]

    # Delete the info on files other than the single file to be used
    del sample['mosaicFiles']
    del sample['files']

    # Check that the file that will be used exists
    if not exists(sample['file']): fail('A specified input file does not exist: ' + str(sample['file']))

  # Return the updated samples
  return samples

# Parse the tsv file containing the Mosaic attributes
def parseAttributes(args):
  global sampleNames
  global sampleAttributes

  # If the attributes file was not specified on the command line, use the default version
  if not args.attributes_file: args.attributes_file = os.path.dirname(os.path.abspath(__file__)) + "/mosaic.atts.alignstats.tsv"

  # Get all the attributes to be added
  try: attributesInput = open(args.attributes_file, "r")

  # If there is no attributes file, no data can be processed.
  except: fail('File: ' + str(args.attributes_file) + ' does not exist')

  lineNo = 0
  for line in attributesInput.readlines():
    lineNo    += 1
    line       = line.rstrip()
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
    else: fail('Unknown attribute in ' + str(args.attributes) + '. Line: ' + str(line))

# Import the attributes into the current project
def getAttributeIds(args, projectId):
  global mosaicConfig
  global projectAttributes
  global sampleAttributes

  # First, get all the project attribute ids from the Alignstats Attributes project
  projectAttributes = api_pa.getProjectAttributesNameIdUid(mosaicConfig, projectId)

  # Get all the sample attribute ids from the Alignstats Attributes project
  data = api_sa.getSampleAttributes(mosaicConfig, projectId)

  # Loop over the sample attributes and store the ids                                                
  for attribute in data:                                                                          

    # Only include custom attributes (e.g. ignore global default attributes like Median Read Coverage that are
    # added to all Mosaic projects
    if str(attribute['is_custom']) == 'True':

      # Only set the values for attributes that exist in alignstats tsv file. The Alignstats Attributes
      # project may contain more attributes than the tsv. This could be the case if we are just trying
      # to update a subset of attributes, or if the alignstats output has been updated
      if str(attribute['name']) in sampleAttributes:
        sampleAttributes[str(attribute['name'])]['id']        = attribute['id']
        sampleAttributes[str(attribute['name'])]['uid']       = attribute['uid']
        sampleAttributes[str(attribute['name'])]['processed'] = True

  # Loop over the sampleAttributes (e.g. all the attributes that were defined in the alignstats tsv, representing
  # all attributes to be included. If any of these attributes were not "processed" above, there is no attribute in
  # the Mosaic Alignstats Attributes project and it needs to be created
  for attribute in sampleAttributes:
    if not sampleAttributes[attribute]['processed']:
      attType  = sampleAttributes[attribute]['type']
      xlabel   = sampleAttributes[attribute]['xlabel']
      ylabel   = sampleAttributes[attribute]['ylabel']
      api_sa.createPublicSampleAttribute(mosaicConfig, alignstatsProjectId, attribute, 'Not Set', attType, xlabel, ylabel)

      # Store information about the created attribute
      sampleAttributes[str(data['name'])]['id']        = jsonData['id']
      sampleAttributes[str(data['name'])]['uid']       = jsonData['uid']
      sampleAttributes[str(data['name'])]['processed'] = True

# Read through the Alignstats json files for each sample and store the information
def readJsonFiles(args, samples):
  global sampleNames
  global sampleAttributes

  # Loop over the samples, and open and read the associated json files
  for sample in samples:
    filename = sample['file']

    # Read through the alignstats file
    try: fileHandle = open(sample['file'], 'r')
    except: fail('Could not open file ' + str(sample['file']))
    try: sampleData = json.loads(fileHandle.read())
    except: fail('File ' + str(sample['file']) + ' is not a valid json file')

    # Loop over all the attributes in the json file
    for attribute in sampleData:

      # If no attribute exists in the Alignstats annotation project, this isn't a value that needs
      # to be imported
      if attribute in sampleNames:
        attributeName = sampleNames[attribute]
        sampleAttributes[attributeName]['values'][sample['id']] = sampleData[attribute]

    # Close the sample file
    fileHandle.close()

# Print out data for import into Mosaic
def outputToMosaic(samples):
  global sampleAttributes

  # Open the output file
  outFile   = 'alignstats_mosaic_upload.tsv'
  outHandle = open(outFile, 'w')

  # Output the header line
  line = 'SAMPLE_NAME'
  for attribute in sorted(sampleAttributes.keys()): line += '\t' + str(sampleAttributes[attribute]['uid'])
  print(line, file = outHandle)
  
  # Loop over the samples and output the required information
  for sample in samples:
    line = sample['name']
    for attribute in sorted(sampleAttributes.keys()):
      try: value = sampleAttributes[attribute]['values'][sample['id']]
      except: value = ''
      line += '\t' + str(value)
    print(line, sep = '\t', file = outHandle)

  # Close the output file
  outHandle.close()

  # Return the name of the tsv file
  return outFile

# Import attributes into the current project and upload the tsv values file
def importAttributes(args, tsvFile):
  global mosaicConfig
  global projectAttributes
  global sampleAttributes
  global version

  # Set the Alignstats Data project attribute value to the value stored in integrationStatus
  projectAttributes['Alignstats Data']['values'] = 'v' + str(version)

  # Get the sample and project attributes for the current project
  availableProjectAttributes = api_pa.getProjectAttributesNameIdUid(mosaicConfig, args.project_id)
  availableSampleAttributes  = api_sa.getSampleAttributesDictIdName(mosaicConfig, args.project_id)

  # Begin with the import and setting of project attributes
  for attribute in projectAttributes:
    attributeId = projectAttributes[attribute]['id']
    value       = projectAttributes[attribute]['values']

    # Check if this project attribute has already been imported
    isImported = False
    for att in availableProjectAttributes:
      if str(attribute) == str(att):
        isImported = True
        break

    # If the integration has already been run, just update the values, otherwise import them
    if isImported: api_pa.updateProjectAttribute(mosaicConfig, args.project_id, attributeId, value)
    else: api_pa.importProjectAttribute(mosaicConfig, args.project_id, attributeId, value)

  # Loop over all the defined sample attributes and import them
  for attribute in sampleAttributes:
    attributeId = sampleAttributes[attribute]['id']
    if attributeId not in availableSampleAttributes: api_sa.importSampleAttribute(mosaicConfig, args.project_id, attributeId)
  
  # Upload the sample attribute values tsv
  api_sa.uploadSampleAttributes(mosaicConfig, args.project_id, tsvFile)

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

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables

# Store the version
version = "1.0.1"

# Store mosaic info, e.g. the token, url etc.
mosaicConfig = {}

# Dictionaries to match Alignstats attribute names to their location in the html file
projectAttributes = {}
sampleAttributes  = {}
sampleNames       = {}

if __name__ == "__main__":
  main()
