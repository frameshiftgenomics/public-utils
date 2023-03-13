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
                    'PEDDY_ATTRIBUTES_PROJECT_ID': {'value': args.peddy_project_id, 'desc': 'The peddy project id', 'long': '--peddy_project_id', 'short': '-d'}}
  mosaicConfig   = mosaic_config.mosaicConfigFile(args.config)
  mosaicConfig   = mosaic_config.commandLineArguments(mosaicConfig, mosaicRequired)

  # Define the alignstats project id
  peddyProjectId = mosaicConfig['PEDDY_ATTRIBUTES_PROJECT_ID']

  # Get any peddy files that are attached to the project
  samples = api_s.getSampleNameId(mosaicConfig, args.project_id)
  if args.input_html: inputFile = args.input_html
  else: inputFile = checkMosaicFiles(args, samples)

  # Get the attributes names and where they are found in the Peddy html file.
  parseAttributes(args)

  # Import the attributes into the project with Peddy data
  getAttributeIds(args, peddyProjectId)

  # Check if the attributes already exist in the target project
  #checkAttributesExist(args)

  # Read through the Peddy file
  backgroundFile = readPeddyHtml(samples, inputFile)

  # Build additional attributes
  buildAttributes(samples)

  # Generate a file to output to Mosaic
  tsvFile = outputToMosaic(samples)

  # Import the attributes into the current project and upload the values
  importAttributes(args, tsvFile)

  # Create an attribute set
  #createAttributeSet(args)

  # In order to build the ancestry chart, the background data needs to be posted to the project
  backgroundsId = api_pb.uploadBackgroundData(mosaicConfig, args.project_id, backgroundFile)
  #backgroundsId = postBackgrounds(args)
  buildChart(args, backgroundsId)

  # Remove the created files
  os.remove(backgroundFile)
  os.remove(tsvFile)

# Input options
def parseCommandLine():
  global version

  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Required arguments
  parser.add_argument('--project_id', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")

  # Optional pipeline arguments
  parser.add_argument('--input_html', '-i', required = False, metavar = "file", help = "The html file output from Peddy")
  parser.add_argument('--attributes_file', '-f', required = False, metavar = "file", help = "The input file listing the Peddy attributes")

  # Optional mosaic arguments
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "The config file for Mosaic")
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic")
  parser.add_argument('--attributes_project', '-a', required = False, metavar = 'integer', help = 'The Mosaic project id that contains public attributes')
  parser.add_argument('--peddy_project_id', '-d', required = False, metavar = 'integer', help = 'The Mosaic project id that contains peddy attributes')

  # Version
  parser.add_argument('--version', '-v', action="version", version='Peddy integration version: ' + str(version))

  return parser.parse_args()

# Check that all project samples are associated with the same peddy file
def checkMosaicFiles(args, samples):
  inputFiles = []

  # Loop over all samples in the project and get any associated peddy html files
  for sample in samples:
    sampleFiles = api_sf.getSampleFiles(mosaicConfig, args.project_id, sample['id'], 'peddy.html')
    for fileId in sampleFiles:
      filename = sampleFiles[fileId]['uri']
      if filename.startswith('file:/'): filename = filename[6:]
      if filename not in inputFiles: inputFiles.append(filename)

  # If there are no, or more than one peddy html files associated with the project, fail. No files
  # have been set on the command line (or this routine would not be executed), so there must be one
  # and only one peddy html file available
  if len(inputFiles) == 0: fail('No Peddy html files are associated with project ' + str(args.project_id) + ' and no files were specified on the command line')
  elif len(inputFiles) > 1: fail('More than one Peddy htlm files are associated with project ' + str(args.project_id))

  # Return the name and path of the Peddy html file
  return inputFiles[0]

# Parse the tsv file containing the Mosaic attributes
def parseAttributes(args):
  global projectAttributes
  global sampleAttributes

  # If the attributes file was not specified on the command line, use the default version
  if not args.attributes_file: args.attributes_file = os.path.dirname(os.path.abspath(__file__)) + '/mosaic.atts.peddy.tsv'

  # Get all the attributes to be added
  try: attributesInput = open(args.attributes_file, 'r')

  # If there is no attributes file, no data can be processed.
  except: fail('File ' + str(args.attributes_file) + ' cannot be found')

  lineNo = 0
  for line in attributesInput.readlines():
    lineNo += 1
    line = line.rstrip()
    attributes = line.split('\t')

    # Put all project attributes into the projectAttributes dictionary. Set the Mosaic id and uid to
    # False for now. These will be read from the Peddy Attributes project if it already exists, or will
    # be assigned when the attributes are created, if this is the first running of the Peddy integration.
    # Get the value type (string or float) from the file
    if attributes[0] == 'project': projectAttributes[attributes[1]] = {'id': False, 'uid': False, 'type':attributes[2], 'values': False}
      
    # With sample attributes, we need both the attribute id and uid which will be determined later, and where
    # the value will be found in the Peddy html file. For, now set the id and uid to False, and read in the
    # value type, and Peddy html location
    elif attributes[0] == 'sample':

      # Put the attributes in the correct array.
      location = str(attributes[4]) + '/' + str(attributes[5])
      sampleAttributes[attributes[1]] = {'id': False, 'uid': False, 'type': attributes[2], 'html': location, 'xlabel': attributes[3], 'ylabel': '', 'values': {}, 'present': False}
  
    # If the attribute is not correctly defined, add the line to the errors
    else: fail('Unknown attribute')

# Get the attributes to be imported into the current project
def getAttributeIds(args, projectId):
  global mosaicConfig
  global projectAttributes
  global sampleAttributes

  # First, get all the project attribute ids from the Peddy Attributes project
  projectAttributes = api_pa.getProjectAttributesNameIdUid(mosaicConfig, projectId)

  # Get all the sample attribute ids from the Peddy Attributes project
  data = api_sa.getSampleAttributes(mosaicConfig, projectId)

  # Loop over the sample attributes and store the ids
  for attribute in data:

    # Only include custom attributes (e.g. ignore global default attributes like Median Read Coverage that are
    # added to all Mosaic projects
    if str(attribute['is_custom']) == 'True':

      # Ignore attributes that begin with 'Failed Peddy'. These are attributes created as part of Z-score calculations
      if not attribute['name'].startswith('Failed Peddy'):
        sampleAttributes[str(attribute['name'])]['id']  = attribute['id']
        sampleAttributes[str(attribute['name'])]['uid'] = attribute['uid']

# Read through the peddy html and pull out the data json
def readPeddyHtml(samples, inputFile):
  global sampleAttributes
  global projectAttributes

  # Open the file
  try: peddyHtml = open(inputFile, 'r')
  except: fail('Could not open file ' + str(inputFile))

  # Loop over the file and extract the data
  for line in peddyHtml.readlines():
    line = line.rstrip()

    # Get the data from the "het_data" variable.
    if line.startswith('var het_data'):
      hetData = json.loads(line.split('= ')[1])
      for record in hetData:
        sample = record['sample_id']

        # Loop over all the Peddy het_data attributes
        for attribute in record:

          # Find the attribute in sampleAttributes
          if str(attribute) != 'sample_id':
            for sampleAttribute in sampleAttributes:
              peddyVar  = sampleAttributes[sampleAttribute]['html'].split('/')[0]
              peddyName = sampleAttributes[sampleAttribute]['html'].split('/')[1]

              # Add the value for this sample into the sampleAttributes
              if str(peddyVar) == 'het_data' and str(peddyName) == str(attribute): sampleAttributes[sampleAttribute]['values'][sample] = record[attribute]

    # Get "sex_data"
    elif line.startswith('var sex_data'):
      sexData = json.loads(line.split('= ')[1])
      for record in sexData:
        sample = record['sample_id']

        # Loop over all the Peddy sex_data attributes
        for attribute in record:

          # Find the attribute in sampleAttributes
          if str(attribute) != 'sample_id':
            for sampleAttribute in sampleAttributes:
              peddyVar  = sampleAttributes[sampleAttribute]['html'].split('/')[0]
              peddyName = sampleAttributes[sampleAttribute]['html'].split('/')[1]

              # Add the value for this sample into the sampleAttributes
              if str(peddyVar) == 'sex_data' and str(peddyName) == str(attribute): sampleAttributes[sampleAttribute]['values'][sample] = record[attribute]

    # Get "pedigree" data
    elif line.startswith('var pedigree'):
      pedData = json.loads(line.split('= ')[1])
      for record in pedData:
        sample = record['sample_id']

        # Loop over all the Peddy sex_data attributes
        for attribute in record:

          # Find the attribute in sampleAttributes
          if str(attribute) != 'sample_id':
            for sampleAttribute in sampleAttributes:
              peddyVar  = sampleAttributes[sampleAttribute]['html'].split('/')[0]
              peddyName = sampleAttributes[sampleAttribute]["html"].split("/")[1]

              # Add the value for this sample into the sampleAttributes
              if str(peddyVar) == 'pedigree' and str(peddyName) == str(attribute): sampleAttributes[sampleAttribute]['values'][sample] = record[attribute]

    # Get the background data
    elif line.startswith('var background_pca'):
      htmlBackground = json.loads(line.split('= ')[1])

      # The background file contains information for some known attriubtes. Change the name of the
      # attributes to the Mosaic uid.
      pc1      = sampleAttributes['Ancestry PC1 (Peddy)']['uid']
      pc2      = sampleAttributes['Ancestry PC2 (Peddy)']['uid']
      pc3      = sampleAttributes['Ancestry PC3 (Peddy)']['uid']
      pc4      = sampleAttributes['Ancestry PC4 (Peddy)']['uid']
      ancestry = sampleAttributes['Ancestry Prediction (Peddy)']['uid']
      for info in htmlBackground:
        info[pc1]      = info.pop('PC1')
        info[pc2]      = info.pop('PC2')
        info[ancestry] = info.pop('ancestry')

        # Remove the pc3 and pc4 info
        info.pop('PC3')
        info.pop('PC4')

      # Create a json object with the background name defined, and add the background data as the payload
      background            = json.loads('{"name":"Ancestry Backgrounds","payload":[]}')
      background['payload'] = htmlBackground
      backgroundFile        = 'peddy_backgrounds.json'
      backgroundHandle      = open(backgroundFile, "w")
      print(json.dumps(background), file = backgroundHandle)
      backgroundHandle.close()

  # Close the Peddy file
  peddyHtml.close()

  # Return the name of the background file
  return backgroundFile

# Construct some new attributes
def buildAttributes(samples):
  global sampleAttributes

  # Generate a sex attribute. Define a female as 0, and a male as 1. The attribute will
  # be a random number between -0.25 < x < 0.25 for female and 0.75 < x < 1.25 for male
  for sample in samples:
    ran        = float((random() - 0.5)/ 2)
    sex        = sampleAttributes['Sex (Peddy)']['values'][sample['name']]
    if sex == 'male': sampleAttributes['Sex Spread (Peddy)']['values'][sample['name']] = float ( 1 + ran)
    elif sex == 'female': sampleAttributes['Sex Spread (Peddy)']['values'][sample['name']] = ran
    else: fail('Unknown gender for sample ' + str(sample['name']) + ': "' + str(sex) + '"')

# Print out data for import into Mosaic
def outputToMosaic(samples):
  global sampleAttributes

  # Open the output file
  tsvFile = 'peddy_mosaic_upload.tsv'
  outFile = open(tsvFile, 'w')

  # Output the header line
  line = 'SAMPLE_NAME'
  for attribute in sorted(sampleAttributes.keys()): line += '\t' + str(sampleAttributes[attribute]['uid'])
  print(line, file = outFile)
  
  # Loop over the samples and output the required information
  for sample in samples:
    line = sample['name']
    for attribute in sorted(sampleAttributes.keys()):
      try: value = sampleAttributes[attribute]["values"][sample['name']]
      except: value = "-"
      line += '\t' + str(value)
    print(line, sep = '\t', file = outFile)

  # Close the output file
  outFile.close()

  # Return the name of the output tsv file
  return tsvFile

# Import attributes into the current project and upload the tsv values file
def importAttributes(args, tsvFile):
  global mosaicConfig
  global projectAttributes
  global sampleAttributes
  global version

  # Set the Peddy Data project attribute value to the value stored in integrationStatus
  projectAttributes['Peddy Data']['values'] = 'v' + str(version)

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

# Build the ancestry chart
def buildChart(args, backgroundsId):
  global mosaicConfig
  global sampleAttributes

  # Loop over all the charts in the project and find any charts that use a background
  charts = api_c.getCharts(mosaicConfig, args.project_id)

  # Store the ids of charts that use a background and have the name "Ancestry (Peddy)"
  chartsToRemove = []
  for chart in charts:
    if chart['projectBackgroundId'] != None and chart['name'] == 'Ancestry (Peddy)': chartsToRemove.append(chart['id'])

  # Remove old ancestry charts before adding the new one
  for chartId in chartsToRemove: api_c.deleteChart(mosaicConfig, args.project_id, chartId)

  # Get the ids of the PC1 and PC2 attributes
  pc1      = sampleAttributes['Ancestry PC1 (Peddy)']['id']
  pc2      = sampleAttributes['Ancestry PC2 (Peddy)']['id']
  colourBy = sampleAttributes['Ancestry Prediction (Peddy)']['id']

  # Build the command to post a chart
  chartId = api_c.createScatterChartWithBackgrounds(mosaicConfig, args.project_id, 'Ancestry (Peddy)', pc2, backgroundsId, 'Ancestry PCS (Peddy)', colourBy, pc1)

  # Pin the chart to the dashboard
  api_d.pinChart(mosaicConfig, args.project_id, chartId)

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables

# Store the version
version = "0.1.2"

# Store mosaic info, e.g. the token, url etc.
mosaicConfig = {}

# Dictionaries to match Peddy attribute names to their location in the html file
projectAttributes = {}
sampleAttributes  = {}

if __name__ == "__main__":
  main()
