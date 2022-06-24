#!/usr/bin/python

# Get the project attribtes for the defined project
def getProjectAttributes(mosaicConfig, projectId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" ' + str(url) + "api/v1/projects/" + str(projectId) + "/attributes"

  return command

# Create a new project attribute
def postProjectAttribute(mosaicConfig, name, valueType, value, isPublic, projectId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"name": "' + str(name) + '", "value_type": "' + str(valueType) + '", "value": "' + str(value) + '", "is_public": "' + str(isPublic) + '"}\' '
  command += str(url) + 'api/v1/projects/' + str(projectId) + '/attributes'

  return command

# Import a project attribute
def importProjectAttribute(mosaicConfig, attributeId, value, projectId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"attribute_id": "' + str(attributeId) + '", "value": "' + str(value) + '"}\' '
  command += str(url) + 'api/v1/projects/' + str(projectId) + '/attributes/import'

  return command

# Get all available attribute sets
def getProjectAttributeSets(mosaicConfig, projectId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += str(url) + 'api/v1/projects/' + str(projectId) + '/attributes/sets'

  return command

# Delete an attribute set
def postProjectAttributeSet(mosaicConfig, name, description, isPublic, attributeIds, projectId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"name": "' + str(name) + '", "description": "' + str(description) + '", "is_public_to_project": "' + str(isPublic)
  command += '", "attribute_ids": "' + str(attributeIds) + '", "type": "' + str(valueType) + '"}\' '
  command += str(url) + 'api/v1/projects/' + str(projectId) + '/attributes/sets'

  return command

# Delete an attribute set
def deleteProjectAttributeSet(mosaicConfig, projectId, setId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X DELETE -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += url + 'api/v1/projects/' + str(projectId) + '/attributes/sets/' + str(setId)

  return command
