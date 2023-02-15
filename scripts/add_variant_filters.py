#!/usr/bin/python

from __future__ import print_function
from os.path import exists

import os
import math
import argparse
import json
from random import random

from sys import path
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/api_commands")
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/common_components")
import mosaic_config
import api_samples as api_s
import api_project_settings as api_ps
import api_variant_annotations as api_va
import api_variant_filters as api_vf

def main():
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {'MOSAIC_TOKEN': {'value': args.token, 'desc': 'An access token', 'long': '--token', 'short': '-t'},
                    'MOSAIC_URL': {'value': args.url, 'desc': 'The api url', 'long': '--url', 'short': '-u'}}
  mosaicConfig   = mosaic_config.mosaicConfigFile(args.config)
  mosaicConfig   = mosaic_config.commandLineArguments(mosaicConfig, mosaicRequired)

  # Define the sample ids and available annotation uids for this project. For other scripts that call this 
  # script, it is assumed that this information is known, and so those scripts will call the addVariantFilters
  # routine directly. When executed from the  command line, these ids must be provided.
  sampleIds = api_s.getSampleIds(mosaicConfig, args.project_id)
  uids      = api_va.getAnnotationUidsWithNamesTypes(mosaicConfig, args.project_id)

  ############ NEED TO GET FROM COMMAND LINE
  sampleMap     = {}
  annotationMap = {}

  # Add all the filters to the project
  addVariantFilters(mosaicConfig, args.filter_json, args.project_id, sampleIds, uids, sampleMap, annotationMap)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Arguments related to the config file
  parser.add_argument('--token', '-t', required = False, metavar = 'string', help = 'The Mosaic authorization token')
  parser.add_argument('--url', '-u', required = False, metavar = 'string', help = 'The base url for Mosaic curl commands, up to an including "api". Do NOT include a trailing ')
  parser.add_argument('--config', '-c', required = False, metavar = 'string', help = 'A config file containing token / url information')

  # The project id to which the filter is to be added is required
  parser.add_argument('--project_id', '-p', required = True, metavar = 'integer', help = 'The Mosaic project id to add variant filters to')

  # Arguments related to the file to add
  parser.add_argument('--filter_json', '-f', required = True, metavar = 'string', help = 'The json file defining all of the variant filters to add')

  return parser.parse_args()

##########################
##########################
########################## Scripts calling this script will skip everything above here and directly call addVariantFilters
##########################
##########################

# Perform all steps necessary to add variant filters
def addVariantFilters(mosaicConfig, jsonFilename, projectId, sampleIds, uids, sampleMap, annotationMap):
  filterInformation = {}

  # Get all filters that currently exist in the project
  existingFilters = api_vf.getVariantFilterNamesIds(mosaicConfig, projectId)

  # Read the json
  filters = readJson(jsonFilename)

  # The path to the files must be provided
  if 'path_to_files' not in filters: fail('The json file describing variant filters is missing the "path_to_files" section')
  filterPath = str(filters['path_to_files']) if filters['path_to_files'].endswith('/') else str(filters['path_to_files']) + '/'

  # Loop over the categories and validate all information
  if 'categories' not in filters: fail('The json file describing variant filters is missing the "categories" section')
  for category in filters['categories']:
    observedSortPositions = []

    # Loop over the filters in the category
    if 'filters' not in filters['categories'][category]: fail('The json file describing variant filters is missing the "filters" section for the category: ' + str(category))
    for vFilter in filters['categories'][category]['filters']:

      # Check that the filter does not contain the same sort position as another filter in this category and the get
      # the information on this variant filter
      observedSortPositions = checkSort(filters['categories'][category]['filters'][vFilter], category, vFilter, observedSortPositions)
      filterFile            = getFilterFile(filters['categories'][category]['filters'][vFilter], filterPath, category, vFilter)
      data                  = readJson(filterFile)
      checkFilters(data, vFilter)
      data = checkGenotypeFilters(data, vFilter, sampleIds, sampleMap)
      checkAnnotationFilters(data, vFilter, uids, annotationMap)
      filterInformation[vFilter] = data

  # Loop over the categories again and create all the filters
  sortedFilters = []
  for category in filters['categories']:
    filterIds = {}
    for vFilter in filters['categories'][category]['filters']:

      # If the filter doesn't exist, create it, otherwise use the id of the existing filter
      if vFilter in existingFilters: filterId = existingFilters[vFilter]
      else: filterId = api_vf.createVariantFilter(mosaicConfig, projectId, vFilter, category, filterInformation[vFilter]['filters'])

      # Store the sort position of this filter id
      filterIds[filters['categories'][category]['filters'][vFilter]['sort_position']] = filterId

    # Populate the object used to update the Mosaic project settings
    record = {'category': category, 'sortOrder': []}
    for i in sorted(filterIds.keys()): record['sortOrder'].append(str(filterIds[i]))
    sortedFilters.append(record)

  # Set the sort orders for all the categories
  api_ps.setVariantFilterSortOrder(mosaicConfig, projectId, sortedFilters)

# Read the input json file to get all of the filters and their categories and sort orders
def readJson(filename):

  # Check that the file defining the filters exists
  if not exists(filename): fail('Could not find the json file ' + str(filename))

  # The file describing the variant filters should be in json format. Fail if the file is not valid
  try: jsonFile = open(filename, "r")
  except: fail('Could not open the json file: ' + str(filename))
  try: data = json.load(jsonFile)
  except: fail('Could not read contents of json file ' + str(filename) + '. Check that this is a valid json')

  # Return the json information
  return data

# Check that the sort_position is present in the definition and that the positions aren't duplicated
def checkSort(data, category, variantFilter, observedSortPositions):

  # Check that the sort_position is present
  if 'sort_position' not in data: fail('The json file describing variant filters is missing "sort_position" for ' + str(variantFilter) + ' in category ' + str(category))
  if data['sort_position'] in observedSortPositions: fail('The json file describing variant filters has multiple filters with the same position in category ' + str(category))
  else: observedSortPositions.append(data['sort_position'])

  # Return the updated list of sort positions
  return observedSortPositions

# Get the json file for this filter and check it is valid
def getFilterFile(data, filterPath, category, variantFilter):
  if 'file' not in data: fail('The json file describing variant filters is missing "file" for ' + str(variantFilter) + ' in category ' + str(category))
  return str(filterPath) + str(data['file'])

# Check the 'filters' section is present in the variant filter json
def checkFilters(data, name):
  if 'filters' not in data: fail('Variant filter json file with the name ' + str(name) + ' does not contain the required "filters" section')

# Get information on the genotype filters
def checkGenotypeFilters(data, name, sampleIds, sampleMap):

  # Only proceed if genotype information is present
  if 'genotypes' in data:

    # Store the allowed genotype options for saved filters
    genotypeOptions = []
    genotypeOptions.append('ref_samples')
    genotypeOptions.append('alt_samples')
    genotypeOptions.append('het_samples')
    genotypeOptions.append('hom_samples')

    # Check what genotype filters need to be applied and that the supplied genotypes are valid
    for genotype in data['genotypes']:
      if genotype not in genotypeOptions: fail('Mosaic variant filter with the name ' + str(name) + ', contains an unknown genotype option: ' + str(genotype))
      if not data['genotypes'][genotype]: continue

      # Check which samples need to have the requested genotype and add to the command. Use the supplied sampleIds
      # list to check that these samples are in the project
      sampleList = []
      if type(data['genotypes'][genotype]) != list: fail('Mosaic variant filter with the name ' + str(name) + ' has an invalid genotypes section')
      for sample in data['genotypes'][genotype]:

        # The genotype filter must either contain a valid sample id for the project, or the value in the json (e.g. proband)
        # must be present in the sampleMap and point to a valid sample id for this project
        sampleId = sampleMap[sample] if sample in sampleMap else False
        if not sampleId:
          try: sampleId = int(sample)
          except: fail('Mosaic variant filter ' + str(name) + ' references a sample with a non-integer id: ' + str(sample))
          if int(sampleId) not in sampleIds: fail('Mosaic variant filter ' + str(name) + ' references sample ' + str(sample) + ' which is not in the requested project')
        sampleList.append(sampleId)

      # Add the genotype filter to the filters listed in the json
      data['filters'][genotype] = sampleList

  # Return the updated data
  return data

# Process the annotation filters
def checkAnnotationFilters(data, name, uids, annotationMap):

  # Make sure the annotation_filters section exists
  if 'annotation_filters' not in data['filters']: fail('Annotation filter ' + str(name) + ' does not contain the required "annotation_filters" section')

  # Check the filters provided in the json. The annotation filters need to extract the uids for the annotations, so
  # ensure that each annotation has a valid uid (e.g. it is present in the project), and that supporting information
  # e.g. a minimum value cannot be supplied for a string annotation, is valid
  for aFilter in data['filters']['annotation_filters']:

    # The json file must contain either a valid uid for a project annotation, the name of a valid private annotation (for
    # projects where private annotations are created, a new filter template shouldn't be required for every project), or
    # have a name in the annotation map to relate a name to a uid. This is used for annotations (e.g. ClinVar) that are
    # regularly updated, so the template does not need to be updated for updating annotations.
    # If a uid is provided, check it is valid
    uid = False
    if 'uid' in aFilter: uid = aFilter['uid']

    # If a name is provided instead of a uid...
    elif 'name' in aFilter:

      # ...check if this name is in the annotationMap and if so, use the mapped uid
      if aFilter['name'] in annotationMap: uid = annotationMap[aFilter['name']]

      # ...or if the name is not in the annotationMap, check if a private annotation with this name exists in the project
      else:
        for pUid in uids:
          if str(uids[pUid]['name']) == str(aFilter['name']):
            uid = pUid
            break

    if not uid: fail('No uid can be determined for annotation filter ' + str(name))
    if 'include_nulls' not in aFilter: fail('Annotation filter ' + str(name) + ' contains a filter with no "include_nulls" section')

    # If the annotation is a string, the "values" field must be present
    if uids[uid]['type'] == 'string':
      if 'values' not in aFilter: fail('Annotation filter ' + str(name) + ' contains a string based filter with no "values" section')
      if type(aFilter['values']) != list: fail('Annotation filter ' + str(name) + ' contains a string based filter with a "values" section that is not a list')

    # If the annotation is a float, check that the specified operation is valid
    elif uids[uid] == 'float':

      # Loop over all the fields for the filter and check that they are valid
      hasRequiredValue = False
      for value in aFilter:
        if value == 'uid': continue
        elif value == 'include_nulls': continue

        # The filter can define a minimum value
        elif value == 'min':
          try: float(aFilter[value])
          except: fail('Annotation filter ' + str(name) + ' has a "min" that is not a float')
          hasRequiredValue = True

        # The filter can define a minimum value
        elif value == 'max':
          try: float(aFilter[value])
          except: fail('Annotation filter ' + str(name) + ' has a "max" that is not a float')
          hasRequiredValue = True

        # Other fields are not recognised
        else: fail('Annotation filter ' + str(name) + ' contains an unrecognised field: ' + str(value))

      # If no comparison fields were provided, fail
      if not hasRequiredValue: fail('Annotation filter ' + str(name) + ' contains a filter based on a float, but no comparison operators have been included')

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables
mosaicConfig = {}

# Attributes from the config file
apiUrl              = False
token               = False

if __name__ == "__main__":
  main()
