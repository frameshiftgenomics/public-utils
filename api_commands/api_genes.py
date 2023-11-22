import os
import json
import math

# The first section of this file contains routines to execute the API routes and acts as a layer between the
# calling script and the Pythonized API routes. This will check for errors, deal with looping over pages of 
# results etc and return data objects. The API routes themselves occur later in this file

######
###### Execute the GET routes
######

# Get all gene sets in a project
def getGeneSets(mosaicConfig, projectId):
  try: data = json.loads(os.popen(getGeneSetsCommand(mosaicConfig, projectId)).read())
  except: fail('Failed to get the gene sets')
  if 'message' in data: fail('Failed to get the gene sets. API returned the message: ' + str(data['message']))

  # Return all the data
  return data

# Get all gene sets in a project as a dictionary keyed on the set name
def getGeneSetsDictName(mosaicConfig, projectId):
  geneSets = {}
  try: data = json.loads(os.popen(getGeneSetsCommand(mosaicConfig, projectId)).read())
  except: fail('Failed to get the gene sets')
  if 'message' in data: fail('Failed to get the gene sets. API returned the message: ' + str(data['message']))
  for geneSet in data: geneSets[geneSet['name']] = geneSet

  # Return all the data
  return geneSets

######
###### Execute POST routes
######

# Create a gene set based on a list of gene ids
def postGeneSetByIds(mosaicConfig, projectId, name, description, genes):

  # Add the existing genes to the gene set
  try: data  = json.loads(os.popen(postGeneSetByIdCommand(mosaicConfig, projectId, name, description, genes)).read())
  except: fail('Failed to create the gene set: ' + str(name))
  if 'message' in data: fail('Failed to create the gene set: ' + str(name) + '. API returned the message: ' + str(data['message']))

  # Return all the data
  return data['id']

# Create a gene set based on a list of gene names
def postGeneSetByName(mosaicConfig, projectId, name, description, genes, organism):
  genesToAdd  = []
  genesToSkip = []

  # Loop over the supplied list of genes and determine if they exist in Mosaic. A list of failed genes will be
  # returned
  for gene in genes:
    data = os.popen(getGeneSearchCommand(mosaicConfig, gene)).read()

    # Loop over the search results and check for an exact match. If the result of the search is a failure, the
    # resulting data object with be html code. Skip these
    isMatch = False
    if data and not data.startswith('<html'):
      for existingGene in json.loads(data)['data']:
        if existingGene['gene_name'] == gene and existingGene['organism'] == organism:
          isMatch = True
          break
      if isMatch: genesToAdd.append(gene)
      else: genesToSkip.append(gene)

  # Add the existing genes to the gene set
  try: data  = json.loads(os.popen(postGeneSetByNameCommand(mosaicConfig, projectId, name, description, genesToAdd)).read())
  except: fail('Failed to create the gene set: ' + str(name))
  if 'message' in data: fail('Failed to create the gene set: ' + str(name) + '. API returned the message: ' + str(data['message']))

  # Return all the data
  return data['id'], genesToSkip

######
###### Execute the PUT routes
######

######
###### Execute the DELETE route
######

#################
#################
################# Following are the API routes for variant filters (mirrors the API docs)
#################
#################

# This contains API routes for project attributes (mirrors the API docs)

######
###### GET routes
######

# Search for a specific gene
def getGeneSearchCommand(mosaicConfig, gene):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" ' 
  command += '"' + str(url) + 'api/v1/genes?search=' + str(gene) + '"'

  return command

# Get all gene sets
def getGeneSetsCommand(mosaicConfig, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X GET -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" ' 
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/genes/sets' + '"'

  return command

######
###### POST routes
######

# Post a gene set using a list of gene ids
def postGeneSetByIdCommand(mosaicConfig, projectId, name, description, genes):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" ' 
  command += '-d \'{"name": "' + str(name) + '", "description": "' + str(description) + '", "is_public_to_project": "true", "gene_ids": ' + str(genes) + '}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/genes/sets' + '"'

  return command

# Post a gene set using a list of gene names
def postGeneSetByNameCommand(mosaicConfig, projectId, name, description, genes):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" ' 
  command += '-d \'{"name": "' + str(name) + '", "description": "' + str(description) + '", "is_public_to_project": "true", "gene_names": ['
  for i, gene in enumerate(genes):
    if i == 0: command += '"' + str(gene) + '"'
    else: command += ',"' + str(gene) + '"'
  command += ']}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/genes/sets' + '"'

  return command

######
###### PUT routes
######

######
###### DELETE routes
######

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = '')
  exit(1)
