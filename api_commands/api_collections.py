import os
import json

# The first section of this file contains routines to execute the API routes and acts as a layer between the
# calling script and the Pythonized API routes. This will check for errors, deal with looping over pages of 
# results etc and return data objects. The API routes themselves occur later in this file

######
###### Execute GET routes
######

######
###### Execute POST routes
######

# Add projects to a collection
def addProjectsToCollection(mosaicConfig, collectionId, projectIds, roleType):
  try: data = json.loads(os.popen(postSubProjectsCommand(mosaicConfig, collectionId, projectIds, roleType)).read())
  except: fail('Failed to add projects to the collection')
  if 'message' in data: fail('Failed to add projects to the collection. API returned the message: ' + str(data['message']))

######
###### Execute DELETE routes
######

#################
#################
################# Following are the API routes for variant filters (mirrors the API docs)
#################
#################

######
###### GET routes
######

######
###### POST routes
######

# Add projects to a collection
def postSubProjectsCommand(mosaicConfig, collectionId, projectIds, roleType):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"collection_projects": [' + str(','.join(map(str,projectIds))) + '], '
  command += '"role_type_id": ' + str(roleType) + '}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(collectionId) + '/sub-projects' + '"'

  return command

######
###### PUT routes
######

######
###### DELETE routes
######

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)
