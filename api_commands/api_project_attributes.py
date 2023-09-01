import os
import json
import math

# The first section of this file contains routines to execute the API routes and acts as a layer between the
# calling script and the Pythonized API routes. This will check for errors, deal with looping over pages of 
# results etc and return data objects. The API routes themselves occur later in this file

######
###### Execute the GET routes
######

# Return all project attribute information for a project
def getProjectAttributes(config, projectId):
  try: data = json.loads(os.popen(getProjectAttributesCommand(config, projectId)).read())
  except: fail('Failed to GET project attributes for project: ' + str(projectId))
  if 'message' in data: fail('Failed to GET project attributes for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Return all the data
  return data

# Return all project attribute information for a project as a dictionary keyed on the name
def getProjectAttributesDictName(config, projectId):
  atts = {}
  try: data = json.loads(os.popen(getProjectAttributesCommand(config, projectId)).read())
  except: fail('Failed to GET project attributes for project: ' + str(projectId))
  if 'message' in data: fail('Failed to GET project attributes for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))
  for att in data: atts[att['name']] = att

  # Return all the data
  return atts

# Return project attribute ids for a project as a dictionary keyed on the name
def getProjectAttributesDictNameId(config, projectId):
  atts = {}
  try: data = json.loads(os.popen(getProjectAttributesCommand(config, projectId)).read())
  except: fail('Failed to GET project attributes for project: ' + str(projectId))
  if 'message' in data: fail('Failed to GET project attributes for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))
  for att in data: atts[att['name']] = att['id']

  # Return all the data
  return atts

# Return a dictionary of all project attribute information for a project keyed by the id
def getProjectAttributesDictId(config, projectId):
  ids = {}
  try: data = json.loads(os.popen(getProjectAttributesCommand(config, projectId)).read())
  except: fail('Failed to GET project attributes for project: ' + str(projectId))
  if 'message' in data: fail('Failed to GET project attributes for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))
  for attribute in data: ids[attribute['id']] = attribute

  # Return all the data
  return ids

# Return a dictionary of project attributes for a project with the name as key, and id, and uid as values
def getProjectAttributesNameIdUid(config, projectId):
  atts = {}

  # Get the data
  try: data = json.loads(os.popen(getProjectAttributesCommand(config, projectId)).read())
  except: fail('Failed to GET project attributes for project: ' + str(projectId))
  if 'message' in data: fail('Failed to GET project attributes for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))
  for att in data: atts[att['name']] = {'id': att['id'], 'uid': att['uid']}

  # Return all the data
  return atts

# Return a dictionary of project attributes for a project with the id as key, and name, and uid as values
def getProjectAttributesIdNameUid(config, projectId):
  atts = {}

  # Get the data
  try: data = json.loads(os.popen(getProjectAttributesCommand(config, projectId)).read())
  except: fail('Failed to GET project attributes for project: ' + str(projectId))
  if 'message' in data: fail('Failed to GET project attributes for project: ' + str(projectId) + '. API returned the message: ' + str(data['message']))
  for att in data: atts[att['id']] = {'name': att['name'], 'uid': att['uid']}

  # Return all the data
  return atts

# Return a list of public attributes, including only the id and name
def getPublicProjectAttributesNameIdUid(mosaicConfig):
  limit = 100
  page  = 1
  pAtts = []

  # Get the first page of attributes
  try: data = json.loads(os.popen(getPublicProjectAttributesCommand(mosaicConfig, limit, page)).read())
  except: fail('Failed to GET public project attributes')
  if 'message' in data: fail('Failed to GET public project attributes')

  # Store the required data
  for record in data['data']: pAtts.append({'name': record['name'], 'id': record['id'], 'uid': record['uid']})

  # Calculate the number of pages
  noPages = math.ceil(int(data['count']) / int(limit))

  # Loop over all pages of public attributes and store information to return
  for page in range(2, noPages + 1):
    try: data = json.loads(os.popen(getPublicProjectAttributesCommand(mosaicConfig, limit, page)).read())
    except: fail('Failed to GET public project attributes')
    if 'message' in data: fail('Failed to GET public project attributes')
    for record in data['data']: pAtts.append({'name': record['name'], 'id': record['id'], 'uid': record['uid']})

  # Return the data
  return pAtts

# Get all attributes that the user has access to
def getUserPublicProjectAttributes(config):
  pAtts = {}

  # Get the attributes
  try: data = json.loads(os.popen(getUserProjectAttributesCommand(config)).read())
  except: fail('Failed to get public project attributes for the user')
  if 'message' in data: fail('Failed to GET public project attributes')

  # Loop over all the attributes and return
  for pAtt in data:
    if pAtt['is_public']: pAtts[pAtt['id']] = {'uid': pAtt['uid'], 'name': pAtt['name'], 'value_type': pAtt['value_type'], 'original_project_id': pAtt['original_project_id'], 'projects': {}}
    for project in pAtt['values']: pAtts[pAtt['id']]['projects'][project['project_id']] = project['value']

  # Return the information
  return pAtts

# Get all timestamp attributes
def getTimestampsDictNameId(config, projectId):
  attributes = {}

  # Get the attributes
  try: data = json.loads(os.popen(getProjectAttributesCommand(config, projectId)).read())
  except: fail('Failed to get project attributes for project ' + str(projectId))
  if 'message' in data: fail('Failed to get project attributes for project' + str(projectId))

  # Loop over all the attributes and return
  for attribute in data:
    if attribute['value_type'] == 'timestamp': attributes[attribute['name']] = attribute['id']

  # Return the information
  return attributes

######
###### Execute POST routes
######

# Create a project attribute
def createProjectAttribute(config, projectId, name, description, value, valueType, isPublic):

  # Check that the description is under 255 characters as this is the max allowed
  if len(description) > 255: fail('Description for attribute "' + str(name) + '" is greater than the maximum of 255 characters')
  try: data = json.loads(os.popen(postProjectAttributeCommand(config, name, description, valueType, value, isPublic, projectId)).read())
  except: fail('Failed to create a project attribute for project ' + str(projectId))
  if 'message' in data: fail('Failed to create a project attribute for project ' + str(projectId) + '. API returned the message: ' + str(data['message']))

  # Return the id of the new project attribute
  return data['id']

# Import a project attribute
def importProjectAttribute(config, projectId, attId, value):
  try: data = json.loads(os.popen(postImportProjectAttributeCommand(config, attId, value, projectId)).read())
  except: fail('Failed to import a project attribute for project ' + str(projectId))
  if 'message' in data: fail('Failed to import a project attributes for project ' + str(projectId) + '. API returned the message: ' + str(data['message']))

######
###### Execute the PUT routes
######

# Update a project attribute
def updateProjectAttribute(config, projectId, attId, value):
  try: data = json.loads(os.popen(putProjectAttributeCommand(config, value, projectId, attId)).read())
  except: fail('Failed to update a project attribute for project ' + str(projectId))
  if 'message' in data: fail('Failed to update a project attributes for project ' + str(projectId) + '. API returned the message: ' + str(data['message']))

# Update the predefined list of values for a project attribute
def updateProjectAttributePredefined(config, projectId, attId, values):
  try: data = json.loads(os.popen(putProjectAttributePredefinedCommand(config, values, projectId, attId)).read())
  except: fail('Failed to update project attribute (' + str(attId) + ') for project ' + str(projectId))
  if 'message' in data: fail('Failed to update project attribute (' + str(attId) + ') for project ' + str(projectId) + '. API returned the message: ' + str(data['message']))

######
###### Execute the DELETE route
######

# Delete a project attribute
def deleteProjectAttribute(config, projectId, attributeId):
  try: data = os.popen(deleteProjectAttributeCommand(config, projectId, attributeId)).read()
  except: fail('Failed to delete project attribute ' + str(attributeId) + ' for project ' + str(projectId))
  if 'message' in data: fail('Failed to delete project attribute ' + str(attributeId) + ' for project ' + str(projectId) + '. API returned the message: ' + str(json.loads(data)['message']))

#################
#################
################# Following are the API routes for variant filters (mirrors the API docs)
#################
#################

# This contains API routes for project attributes (mirrors the API docs)

######
###### GET routes
######

# Get the project attributes for the defined project
def getProjectAttributesCommand(mosaicConfig, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" ' 
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/attributes' + '"'

  return command

# Get all public project attributes
def getPublicProjectAttributesCommand(mosaicConfig, limit, page):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/attributes?limit=' + str(limit) + '&page=' + str(page) + '"'

  return command

# Get the project attributes for the all projects the user has access to
def getUserProjectAttributesCommand(mosaicConfig):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" ' 
  command += '"' + str(url) + 'api/v1/user/projects/attributes' + '"'

  return command

######
###### POST routes
######

# Create a new project attribute
def postProjectAttributeCommand(mosaicConfig, name, description, valueType, value, isPublic, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"name": "' + str(name) + '", "value_type": "' + str(valueType) + '", "description": "' + str(description) + '", "is_public": "' + str(isPublic)
  if value == 'null': command += '", "value": null}\' '
  else: command += '", "value": "' + str(value) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/attributes' + '"'

  return command

# Import a project attribute
def postImportProjectAttributeCommand(mosaicConfig, attributeId, value, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"attribute_id": "' + str(attributeId) + '", "value": '

  # If the value is null, it should not be enclosed in quotation marks
  if value == 'null': command += 'null}\' '
  else: command += '"' + str(value) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/attributes/import' + '"'

  return command

######
###### PUT routes
######

# Update the value of a project attribute
def putProjectAttributeCommand(mosaicConfig, value, projectId, attributeId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  # Check if the value contains a ' or " character. Some values are comments that may reasonably contain these, but they
  # will break the curl command, so they should be escaped. Timestamps should not be checked, only string attributes
  if type(value) == str:
    if "'" in value: value = value.replace("'", "'\\''")
    elif '"' in value: value = value.replace('"', '\\"')

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  if value == 'null': command += '-d \'{"value": null}\' '
  else: command += '-d \'{"value": "' + str(value) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/attributes/' + str(attributeId) + '"'

  return command

# Update the predfined values of a project attribute
def putProjectAttributePredefinedCommand(mosaicConfig, predefinedValues, projectId, attributeId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"predefined_values": ['
  for i, value in enumerate(predefinedValues):
    text = 'null' if value == 'null' else '"' + str(value) + '"'
    if i == 0: command += str(text)
    else: command += ', ' + str(text)
  command += ']}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/attributes/' + str(attributeId) + '"'

  return command

######
###### DELETE routes
######

# Delete a project attribute
def deleteProjectAttributeCommand(mosaicConfig, projectId, attributeId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X DELETE -H "Authorization: Bearer ' + str(token) + '" '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/attributes/' + str(attributeId) + '"'

  return command

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)
