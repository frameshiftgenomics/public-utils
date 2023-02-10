#!/usr/bin/python

# This contains API routes for project settings (mirrors the API docs)

######
###### GET routes
######

# Get the project settings
def getProjectSettings(mosaicConfig, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/settings' + '"'

  return command

######
###### POST routes
######

######
###### PUT routes
######

# Set a variant annotation as a default
def putDefaultAnnotations(mosaicConfig, projectId, annotationIds):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"selected_variant_annotation_ids": ' + str(annotationIds) + '}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/settings' + '"'

  return command

# Set the sort order of variant filters and annotations
def putDefaultAnnotations(mosaicConfig, projectId, annotationIds):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"selected_variant_annotation_ids": ' + str(annotationIds) + '}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/settings' + '"'

  return command

#{
#  sorted_annotations: {
#    variant_filters: [['VARIANT_FILTERS|Custom Cat 2', [4, 3]], ['VARIANT_FILTERS|Custom Cat 1', [1, 2]]],
#    variant_annotations: // same as above [['ENTITY_ENUM|Category Name', [...sortedEntityIds]]]
#  }
#}

######
###### DELETE routes
######
