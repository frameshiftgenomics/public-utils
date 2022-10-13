#!/usr/bin/python

from os.path import exists

import os
import json
import math

from sys import path
import api_samples as api_s
import api_sample_files as api_sf

# Get all samples in a Mosaic project
def getSamples(mosaicConfig, projectId):

  # Define the samples object
  samples = {}

  # Get the samples and populate the samples object
  jsonData = json.loads(os.popen(api_s.getSamples(mosaicConfig, projectId)).read())
  for record in jsonData: samples[record["name"]] = {"id": record["id"], "uid": record["uid"]}

  return samples

# Get all sample files with a specific extension
def getSampleFiles(mosaicConfig, projectId, extension):
  limit = 10
  page  = 1
  sampleFiles = {}

  # Get all files associated with the project
  jsonData = json.loads(os.popen(api_sf.getAllSampleFiles(mosaicConfig, projectId, limit, page)).read())
  noPages  = int( math.ceil( float(jsonData["count"]) / float(limit) ) )

  # Loop over all the files and search for those with the correct extension
  for sampleFile in jsonData['data']:
    if sampleFile['type'] == 'alignstats.json': sampleFiles[sampleFile['name']] = {"id": sampleFile['id'], "name": sampleFile['name'], "sample_id": sampleFile['sample_id']}

  # Loop over any additional pages of files
  for page in range(1, noPages):
    jsonData = json.loads(os.popen(api_sf.getAllSampleFiles(mosaicConfig, projectId, limit, page + 1)).read())
    for sampleFile in jsonData['data']:
      if sampleFile['type'] == 'alignstats.json': sampleFiles[sampleFile['name']] = {"id": sampleFile['id'], "uri": sampleFile['uri'], "sample_id": sampleFile['sample_id']}

  # Return the files
  return sampleFiles

# If problems are found with the templates, fail
def fail(text):
  print(text)
  exit(1)
