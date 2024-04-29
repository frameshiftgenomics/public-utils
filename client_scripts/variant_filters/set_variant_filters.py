import os
import argparse
import json
import math
import glob
import importlib
import sys

from os.path import exists
from pprint import pprint
from sys import path

def main():

  # Parse the command line
  args = parseCommandLine()

  # Import the api client
  path.append(args.api_client)
  from mosaic import Mosaic, Project, Store
  apiStore  = Store(config_file = args.client_config)
  apiMosaic = Mosaic(config_file = args.client_config)

  # Open an api client project object for the defined project
  project = apiMosaic.get_project(args.project_id)

  # Check if this is a collection
  data = project.get_project()
  if data['is_collection']:
    project_ids = []
    for sub_project in data['collection_projects']:
      project_ids.append(sub_project['child_project_id'])
  else:
    project_ids = [args.project_id]

  # Loop over all the projects (for a collection) and apply the filters
  for project_id in project_ids:
    project = apiMosaic.get_project(project_id)
    print('Setting filters for project ', project.name, ' (id:', project_id,')', sep = '')

    # Get information on the sample available in the Mosaic project. Some variant filters require filtering on genotype. The variant filter
    # description will contain terms like "Proband": "alt". Therefore, the term Proband needs to be converted to a Mosaic sample id. If
    # genotype based filters are being omitted, this can be skipped
    samples    = {}
    hasProband = False
    proband    = False
    if not args.no_genotype_filters: 
      samples = {}
      for sample in project.get_samples():
        samples[sample['name']] = {'id': sample['id'], 'relation': False}
        for attribute in project.get_attributes_for_sample(sample['id']):
          if attribute['uid'] == 'relation':
            for value in attribute['values']:
              if value['sample_id'] == sample['id']:
                samples[sample['name']]['relation'] = value['value']
                if value['value'] == 'Proband':
                  if hasProband: fail('Multiple samples in the Mosaic project are listed as the proband')
                  hasProband = True
                  proband    = sample['name']
                break
  
    # Get all of the annotations in the current project. When creating a filter, the project will be checked to ensure that it has all of the
    # required annotations before creating the filter
    annotations    = {}
    annotationUids = {}
    for annotation in project.get_variant_annotations():
  
      # Loop over the annotation versions and get the latest (highest id)
      annotation_version_id = False
      for annotation_version in annotation['annotation_versions']:
        if not annotation_version_id:
          annotation_version_id = annotation_version['id']
        elif annotation_version['id'] > annotation_version_id:
          annotation_version_id = annotation_version['id']
  
      annotations[annotation['name']] = {'id': annotation['id'], 'annotation_version_id': annotation_version_id, 'uid': annotation['uid'], 'type': annotation['value_type'], 'privacy_level': annotation['privacy_level']}
    for annotation in annotations:
      annotationUids[annotations[annotation]['uid']] = {'name': annotation, 'type': annotations[annotation]['type'], 'annotation_version_id': annotations[annotation]['annotation_version_id']}
  
  
  #  for annotation in project.get_variant_annotations():
  #    annotations[annotation['name']] = {'id': annotation['id'], 'uid': annotation['uid'], 'type': annotation['value_type'], 'privacy_level': annotation['privacy_level']}
  #  for annotation in annotations:
  #    annotationUids[annotations[annotation]['uid']] = {'name': annotation, 'type': annotations[annotation]['type']}
  
    # Get HPO terms from Mosaic
    hpoTerms = []
    for hpoTerm in project.get_sample_hpo_terms(samples[proband]['id']):
      hpoTerms.append({'hpo_id': hpoTerm['hpo_id'], 'label': hpoTerm['label']})
  
    # Determine all of the variant filters that are to be added; remove any filters that already exist with the same name; fill out variant
    # filter details not in the json (e.g. the uids of private annotations); create the filters; and finally update the project settings to
    # put the filters in the correct category and sort order. Note that the filters to be applied depend on the family structure. E.g. de novo
    # filters won't be added to projects without parents
    sampleMap                 = createSampleMap(samples)
    annotationMap             = createAnnotationMap(annotations)
    filtersInfo               = readVariantFiltersJson(args.variant_filters)
    filterCategories, filters = getFilterCategories(filtersInfo)
    filters                   = getFilters(filtersInfo, filterCategories, filters, samples, sampleMap, annotations, annotationUids, annotationMap, annotationUids, hpoTerms)
  
    # Get all of the filters that exist in the project, and check which of these share a name with a filter to be created
    deleteFilters(project, args.project_id, filters)
  
    # Create all the required filters and update their categories and sort order in the project settings
    createFilters(project, args.project_id, annotations, annotationUids, filterCategories, filters)

# Input options
def parseCommandLine():
  global version
  parser = argparse.ArgumentParser(description='Process the command line')

  # Required arguments
  parser.add_argument('--client_config', '-c', required = True, metavar = 'string', help = 'The ini config file for Mosaic')
  parser.add_argument('--api_client', '-a', required = True, metavar = 'string', help = 'The api_client directory')
  parser.add_argument('--project_id', '-p', required = True, metavar = 'string', help = 'The project id that variants will be uploaded to')
  parser.add_argument('--variant_filters', '-f', required = True, metavar = 'string', help = 'The json file describing the variant filters to apply to each project')

  # Optional mosaic arguments
  parser.add_argument('--no_genotype_filters', '-n', required = False, action = "store_true", help = 'If set, all filters that include genotypes will be omitted')

  # Version
  parser.add_argument('--version', '-v', action="version", version='Calypso annotation pipeline version: ' + str(version))

  return parser.parse_args()

## Create a mapping from the sample relation to a Mosaic sample id. The json file describing the filter
## can include fields for requiring specific genotypes for family members, e.g. Proband must be an alt,
## in order to be general for any project. These need to be converted to sample ids for Mosaic
def createSampleMap(samples):
  sampleMap = {}
  for sample in samples:
    if not samples[sample]['relation']:
      fail('Sample attribute "Relation" must be present and populated for all samples (no value exists for "' + str(sample) + '")')
    sampleMap[samples[sample]['relation'].lower()] = samples[sample]['id']

  # Return the sample map
  return sampleMap

# Create an annotation map that links general names for annotations to the specific annotation available
# in the project. For example, clinVar annotations can be regularly updated - when the filter is created,
# it needs to point to the clinVar annotation available in that project
def createAnnotationMap(annotations):
  annotationMap = {}
  clinVar       = []

  # Loop over all annotations in the project
  for annotation in annotations:

    # ClinVar can be regurlarly updated, so the filter can include the term 'clinvar_latest'. If this is
    # encountered, the filter should use the clinVar annotation available in the project
    if 'clinvar' in annotation.lower():
      clinVar.append(annotation)

    # Private annotations will be referred to in the json by name, so these need to be included in the map
    if annotations[annotation]['privacy_level'] == 'private':
      annotationMap[annotation] = annotations[annotation]['uid']

  # If there is a single available clinVar annotation use this
  if len(clinVar) == 1:
    annotationMap['clinvar_latest'] = annotations[clinVar[0]]['uid']
  else:
    fail('public-utils/common_components/variant_filters.py: Multiple ClinVar annotations exist in project. No logic exists to select the correct annotation')

  # Return the annotation map
  return annotationMap

# Process the json file describing the filters to apply
def readVariantFiltersJson(variantFiltersJson):

  # Check that the file defining the filters exists
  if not exists(variantFiltersJson):
    fail('Could not find the json file ' + str(variantFiltersJson))

  # The file describing the variant filters should be in json format. Fail if the file is not valid
  try:
    jsonFile = open(variantFiltersJson, 'r')
  except:
    fail('Could not open the json file: ' + str(variantFiltersJson))
  try:
    filtersInfo = json.load(jsonFile)
  except:
    fail('Could not read contents of json file ' + str(variantFiltersJson) + '. Check that this is a valid json')

  # Close the file
  jsonFile.close()

  # Return the json information
  return filtersInfo

# Extract all the variant filter categories from the json file
def getFilterCategories(filtersInfo):
  categories = {}
  filters    = {}

  # The json should contain a "categories" section which includes the name of all the categories that filters
  # can be assigned to as well as the order of filters within the categories. Loop over the categories and validate all information
  if 'categories' not in filtersInfo:
     fail('public-utils/common_components/variant_filters.py: The json file describing variant filters is missing the "categories" section')
  for category in filtersInfo['categories']:

    # For each category, loop over the names of the filters, and store their sort order. Check that there are no
    # duplicated sort positions
    categories[category] = {}
    for name in filtersInfo['categories'][category]:
      position = filtersInfo['categories'][category][name]
      if position in categories[category]:
        fail('public-utils/common_components/variant_filters.py: Filter ' + str(name) + ' in category ' + str(category) + ' has the same sort position as a different filter')
      categories[category][position] = name
      if name in filters:
        fail('public-utils/common_components/variant_filters.py: Filter "' + str(name) + '" appears multiple times in the filter description json')
      filters[name] = {'category': category, 'sortPosition': position}

  # Return the categories information
  return categories, filters

# Process all the information on the individual filters
def getFilters(filtersInfo, categories, filters, samples, sampleMap, annotations, annotationUids, annotationMap, uids, hpoTerms):

  # Check all required sections and no others are present
  for section in filtersInfo:
    if section == 'categories':
      pass
    elif section == 'filters':
      pass
    else:
      fail('Unknown section (' + str(section) + ') in the variant filters json')
  if 'filters' not in filtersInfo:
    fail('public-utils/common_components/variant_filters.py: The json file describing variant filters is missing the "filters" section')

  # Now check that all of the filters defined for each category are described in detail in the "filters" section of the json
  # Loop over all of the filters in the category and add them to the filterNames list. Check if any of the filters in
  # the categories section do not have a description in the 'filters' section
  filterNames = []
  for category in categories:
    for position in categories[category]:
      name = categories[category][position]
      if name not in filtersInfo['filters']:
        fail('public-utils/common_components/variant_filters.py: Filter "' + str(name) + '" appears in filter category "' + str(category) + '", but is not described in the "filters" section')
      filterNames.append(categories[category][position])

  # If there are any filters that are uncategorized, throw an error
  for name in filtersInfo['filters']:
    if name not in filterNames:
      fail('public-utils/common_components/variant_filters.py: Filter "' + str(name) + '" is not included in any category. Please include in a category')

  # Loop over the filters are process
  for category in categories:
    for position in categories[category]:
      name = categories[category][position]

      # Check if this filter has any requirements, for example, does it require that the case has parents (for e.g. de novo filters)    
      filters[name]['useFilter'] = checkRequirements(filtersInfo['filters'][name], sampleMap, hpoTerms)

      # If this filter is not to be applied to the project, the rest of the filter information can be ignored - e.g. if this is a
      # filter that requires the parents to be present, but they are not
      if filters[name]['useFilter']:
        filters[name]['info'] = filtersInfo['filters'][name]

        # Check the genotype information for the filter
        if 'genotypes' in filters[name]['info']:
          filters[name]['info'] = checkGenotypeFilters(filters[name]['info'], name, list(samples.keys()), sampleMap)

        # Check all of the annotation filters
        filters[name]['info'] = checkAnnotationFilters(filters[name]['info'], name, annotations, annotationUids, annotationMap, uids)

        # Check for any HPO information
        if 'hpo_filters' in filters[name]['info']['filters']:
          filters[name]['info'] = checkHpo(filters[name]['info'], name, hpoTerms)

        # Now check if display is present. If so, this will describe how to update the variant table if this filter is applied. The only
        # allowable fields in this section are 'columns' which defines which column should show in the variant table, and 'sort' which
        # determines which annotation should be sorted on and how (ascending / descending). Set the "setDisplay" flag if this is required
        if 'display' in filtersInfo['filters'][name]:
          filters[name]['setDisplay'] = True
          for field in filtersInfo['filters'][name]['display']:

            # Process the "columns" field. This must contain a list of available annotation uids
            if field == 'column_uids':

              # Create a new list as some uids will need to be replaced in the list, but the order needs to be preserved
              orderedUids = []
              filters[name]['columnUids'] = filtersInfo['filters'][name]['display'][field]
              for uid in filters[name]['columnUids']: 
                if uid not in uids:
                  if uid in annotationMap:
                    orderedUids.append(annotationMap[uid])
                  else:
                    fail('public_utils/common_components/variant_filters.py: Unknown uid (' + str(uid) + ') in "display" > "column_uids" for variant filter ' + str(name))
                else:
                  orderedUids.append(uid)
              filters[name]['columnUids'] = orderedUids

            # Process the "sort" field which defines the annotation to sort the table on
            elif field == 'sort':
              if 'column_uid' not in filtersInfo['filters'][name]['display']['sort']:
                fail('public_utils/common_components/variant_filters.py: Field "column_uid" is missing from the "display" > "sort" section for filter ' + str(name))
              if 'direction' not in filtersInfo['filters'][name]['display']['sort']:
                fail('public_utils/common_components/variant_filters.py: Field "direction" is missing from the "display" > "sort" section for filter ' + str(name))

              # Check the column to sort on is a valid uid, or is defined in the annotation map
              sortUid = filtersInfo['filters'][name]['display'][field]['column_uid']
              if sortUid not in uids:
                if sortUid in annotationMap:
                  uid = annotationMap[sortUid]
                else:
                  fail('public_utils/common_components/variant_filters.py: Unknown uid (' + str(sortUid) + ') in "display" > "sort" > "column_uid" for variant filter ' + str(name))
              else:
                uid = filtersInfo['filters'][name]['display'][field]['column_uid']
              filters[name]['sortColumnUid'] = uid 

              # Check that the sort direction is valid
              filters[name]['sortDirection'] = filtersInfo['filters'][name]['display'][field]['direction']
              if filters[name]['sortDirection'] != 'ascending' and filters[name]['sortDirection'] != 'descending':
                fail('public_utils/common_components/variant_filters.py: Sort direction must be "ascending" or "descending" for filter ' + str(name))

            else:
              fail('public_utils/common_components/variant_filters.py: Unknown field in the "display" section for filter ' + str(name))
        else:
          filters[name]['setDisplay'] = False

  # Return the filter information
  return filters

# Check if this filter has any requirements, for example, does it require that the case has parents (for e.g. de novo filters)    
def checkRequirements(filtersInfo, sampleMap, hpoTerms):
  useFilter = True

  # Check if parents are required for this filter. If so, check if they are present in the sample map. If not, this filter
  # should not be included in the project
  if 'requires_mother' in filtersInfo: 
    if filtersInfo['requires_mother'] and 'mother' not in sampleMap:
      useFilter = False
  if 'requires_father' in filtersInfo: 
    if filtersInfo['requires_father'] and 'father' not in sampleMap:
      useFilter = False

  # If this filter requires HPO terms and none are available, the filter should be skipped
  if 'hpo_filters' in filtersInfo['filters'] and not hpoTerms:
    useFilter = False

  # Return whether this filter passes all requirements
  return useFilter

# Get information on the genotype filters and check they are valid
def checkGenotypeFilters(data, name, sampleIds, sampleMap):

  # Store the allowed genotype options for saved filters
  genotypeOptions = []
  genotypeOptions.append('ref_samples')
  genotypeOptions.append('alt_samples')
  genotypeOptions.append('het_samples')
  genotypeOptions.append('hom_samples')

  # Check what genotype filters need to be applied and that the supplied genotypes are valid
  for genotype in data['genotypes']:
    if genotype not in genotypeOptions:
      fail('Mosaic variant filter with the name ' + str(name) + ', contains an unknown genotype option: ' + str(genotype))
    if not data['genotypes'][genotype]:
      continue

    # Check which samples need to have the requested genotype and add to the command. Use the supplied sampleIds
    # list to check that these samples are in the project
    sampleList = []
    if type(data['genotypes'][genotype]) != list:
      fail('Mosaic variant filter with the name ' + str(name) + ' has an invalid genotypes section')
    for sample in data['genotypes'][genotype]:

      # The genotype filter must either contain a valid sample id for the project, or the value in the json (e.g. proband)
      # must be present in the sampleMap and point to a valid sample id for this project
      sampleId = sampleMap[sample] if sample in sampleMap else False
      if not sampleId:
        try:
          sampleId = int(sample)
        except:
          fail('Mosaic variant filter ' + str(name) + ' references a sample with a non-integer id: ' + str(sample))
        if int(sampleId) not in sampleIds:
          fail('Mosaic variant filter ' + str(name) + ' references sample ' + str(sample) + ' which is not in the requested project')
      sampleList.append(sampleId)

    # Add the genotype filter to the filters listed in the json
    data['filters'][genotype] = sampleList

  # Return the updated data
  return data

# Process the annotation filters
def checkAnnotationFilters(data, name, annotations, annotationUids, annotationMap, uids):

  # Make sure the annotation_filters section exists
  if 'annotation_filters' not in data['filters']:
    fail('public_utils/common_components/variant_filters.py: Annotation filter ' + str(name) + ' does not contain the required "annotation_filters" section')

  # Check the filters provided in the json. The annotation filters need to extract the uids for the annotations, so
  # ensure that each annotation has a valid uid (e.g. it is present in the project), and that supporting information
  # e.g. a minimum value cannot be supplied for a string annotation, is valid
  for aFilter in data['filters']['annotation_filters']:

    # The json file must contain either a valid uid for a project annotation, the name of a valid private annotation, or
    # have a name in the annotation map to relate a name to a uid. This is used for annotations (e.g. ClinVar) that are
    # regularly updated, so the template does not need to be updated for updating annotations.
    if 'uid' in aFilter:
      uid = aFilter['uid']
    elif 'name' in aFilter:

      # Loop over the annotations in the annotation map and see if the requested annotation name is the beginning of any
      # available annotations. For example, the filter could include an annotation name of "GQ Proband", but the project
      # will have an annotation of the name "GQ Proband SAMPLE_NAME". As long as only a single annotation matches, this
      # will be the annotation to use
      matchedAnnotations = []
      for annotation in annotationMap:
        if aFilter['name'] in annotation:
          matchedAnnotations.append(annotation)
      if len(matchedAnnotations) == 1:
        aFilter['uid'] = annotationMap[matchedAnnotations[0]]
        del aFilter['name']

      ## Check if this name is in the annotationMap and if so, use the mapped uid
      #if aFilter['name'] in annotationMap:
      #  aFilter['uid'] = annotationMap[aFilter['name']]
      #  del aFilter['name']

      # If the name is not in the annotationMap, check if a private annotation with this name exists in the project
      else:
        for annotation in annotations:
          if str(annotation) == str(aFilter['name']):
            aFilter['uid'] = annotations[annotation]['uid']
            del aFilter['name']
            break

    # Store the uid and check that it exists
    uid = aFilter['uid'] if 'uid' in aFilter else False
    if not uid:
      fail('public_utils/common_components/variant_filters.py: variant filter "' + str(name) + '" uses an unknown annotation: ' + str(aFilter['name']))
    if uid not in uids:
      fail('public_utils/common_components/variant_filters.py: variant filter "' + str(name) + '" uses an unknown annotation uid: ' + str(uid))

    # Check that the filter defines whether or not to include null values
    if 'include_nulls' not in aFilter:
      fail('public_utils/common_components/variant_filters.py: Annotation filter ' + str(name) + ' contains a filter with no "include_nulls" section')

    # If the annotation is a string, the "values" field must be present
    if uids[uid]['type'] == 'string':
      if 'values' not in aFilter:
        fail('public_utils/common_components/variant_filters.py: Annotation filter ' + str(name) + ' contains a string based filter with no "values" section')
      if type(aFilter['values']) != list:
        fail('public_utils/common_components/variant_filters.py: Annotation filter ' + str(name) + ' contains a string based filter with a "values" section that is not a list')

    # If the annotation is a float, check that the specified operation is valid
    elif uids[uid] == 'float':

      # Loop over all the fields for the filter and check that they are valid
      hasRequiredValue = False
      for value in aFilter:
        if value == 'uid':
          continue
        elif value == 'include_nulls':
          continue

        # The filter can define a minimum value
        elif value == 'min':
          try:
            float(aFilter[value])
          except:
            fail('Annotation filter ' + str(name) + ' has a "min" that is not a float')
          hasRequiredValue = True

        # The filter can define a minimum value
        elif value == 'max':
          try:
            float(aFilter[value])
          except:
            fail('Annotation filter ' + str(name) + ' has a "max" that is not a float')
          hasRequiredValue = True

        # Other fields are not recognised
        else:
          fail('public_utils/common_components/variant_filters.py: Annotation filter ' + str(name) + ' contains an unrecognised field: ' + str(value))

      # If no comparison fields were provided, fail
      if not hasRequiredValue:
        fail('public_utils/common_components/variant_filters.py: Annotation filter ' + str(name) + ' contains a filter based on a float, but no comparison operators have been included')

    # Include annotation_version_id for the selected uid
    aFilter['annotation_version_id'] = annotationUids[aFilter['uid']]['annotation_version_id']

  # Return the updated annotation information
  return data

# Process the HPO filters. These are optional, so the script will not fail if they are not present
def checkHpo(data, name, hpoTerms):

  # Remove the HPO info from the data object. It will be returned in the format expected by Mosaic
  hpoInfo = data['filters'].pop('hpo_filters')

  # If the "hpo_terms" field says proband, use the proband hpo terms
  if 'hpo_terms' not in hpoInfo:
    fail('The hpo_filters for ' + str(name) + ' includes hpo_filters, but has no, "hpo_terms" field')
  if hpoInfo['hpo_terms'] == 'proband':
    data['filters']['hpo_terms'] = hpoTerms
  else:
    fail('Unknown value for the hpo_filters > "hpo_terms" field for filter ' + str(name) + ': ' + str(hpoInfo['hpo_terms']))

  # The number of overlaps is required. If this is set to a larger number than the number of available terms,
  # set the number of overlaps to the number of terms
  if 'hpo_min_overlap' not in hpoInfo:
    fail('The hpo_filters for ' + str(name) + ' includes hpo_filters, but has no, "hpo_min_overlap" field')
  overlaps = hpoInfo['hpo_min_overlap']
  if int(overlaps) > len(hpoTerms):
    overlaps = len(hpoTerms)
  data['filters']['hpo_min_overlap'] = overlaps

  # Return the updated data
  return data

# Get all of the filters that exist in the project, and check which of these share a name with a filter to be created
def deleteFilters(project, projectId, filters):
  for existingFilter in project.get_variant_filters():
    if existingFilter['name'] in filters.keys():
      project.delete_variant_filter(existingFilter['id'])

# Create all the required filters and update their categories and sort order in the project settings
def createFilters(project, projectId, annotations, annotationUids, categories, filters):
  sortedFilters = []
  for category in categories:
    record      = {'category': category, 'sortOrder': []}
    useCategory = False
    for sortId in sorted(categories[category]):
      name = categories[category][sortId]

      # Create the filter, unless it has been marked as not to be added
      if filters[name]['useFilter']:

        # If the variant table display is getting modified, get the ids of the columns to show in the table as an array,
        # the id of the column to sort on and the sort direction
        columnIds    = []
        sortColumnid = None
        sortDirection = None
        if filters[name]['setDisplay']:
          for columnUid in filters[name]['columnUids']:
            columnIds.append(annotationUids[columnUid]['annotation_version_id'])
          sortColumnId = str(annotationUids[filters[name]['sortColumnUid']]['annotation_version_id'])
          if filters[name]['sortDirection'] == 'ascending':
            sortDirection = 'ASC'
          elif filters[name]['sortDirection'] == 'descending':
            sortDirection = 'DESC'

        filterInfo = project.post_variant_filter(name = name, category = category, column_ids = columnIds, sort_column_id = sortColumnId, sort_direction = sortDirection, filter_data = filters[name]['info']['filters'])
        filterId   = filterInfo['id']
        record['sortOrder'].append(str(filterId))
        useCategory = True

    # Populate the object used to update the Mosaic project settings. If no filters from this category passed the
    # requirements to be added, skip this step
    if useCategory:
      sortedFilters.append(record)

  # Set the sort orders for all the categories
  if sortedFilters:
    text = ''
    for i, filters in enumerate(sortedFilters):
      if i == 0:
        text += '["VARIANT_FILTERS|' + str(filters['category']) + '", [' + ','.join(filters['sortOrder']) + ']]'
      else:
        text += ', ["VARIANT_FILTERS|' + str(filters['category']) + '", [' + ','.join(filters['sortOrder']) + ']]'
    sortedAnnotations = {'sorted_annotations' : {}}
    sortedAnnotations['sorted_annotations'] = {'variant_filters': text}
    projectSettings = project.put_project_settings(sorted_annotations = sortedAnnotations)

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables

# Pipeline version
version = "1.1.6"

if __name__ == "__main__":
  main()
