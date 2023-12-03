from os.path import exists

import os
import argparse
import sys

from sys import path
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/api_commands")
import api_attributes as api_a
import api_conversations as api_c
import api_dashboards as api_d
import api_genes as api_g
import api_projects as api_p
import api_project_roles as api_pr
import api_project_attributes as api_pa
import api_project_interval_attributes as api_pia
import api_project_conversations as api_pc
import api_project_settings as api_ps
import api_sample_attributes as api_sa

def main():
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Define the mosaicConfig object
  mosaicConfig = {}
  mosaicConfig['MOSAIC_TOKEN'] = args.token
  mosaicConfig['MOSAIC_URL']   = args.url

  # Get all the information about the template and target projects, including what is pinned to the dashboard:
  # Project attributes and timing information (e.g. intervals)
  templateProjectAttributes, templateEvents = getProjectAttributes(args.template_project_id)
  projectAttributes, projectEvents          = getProjectAttributes(args.project_id)
  templateIntervals = api_pia.getIntervalsIdToName(mosaicConfig, args.template_project_id)
  projectIntervals  = api_pia.getIntervalsIdToName(mosaicConfig, args.project_id)

  # Sample attributes
  templateSampleAttributes = api_sa.getSampleAttributesDictName(mosaicConfig, args.template_project_id)
  sampleAttributes         = api_sa.getSampleAttributesIdList(mosaicConfig, args.project_id)

  # Conversations information
  templateConversations    = getProjectConversations(args.template_project_id)
  projectConversations     = getProjectConversations(args.project_id)

  # Dashboard setup
  templateProjectAttributes, templateConversations = dashboard(args.template_project_id, templateProjectAttributes, templateConversations)
  projectAttributes, projectConversations = dashboard(args.project_id, projectAttributes, projectConversations)

  # Get the table and chart defaults
  templateDefaults = getTableChartDefaults(args.template_project_id)

  # Now update the project with the information from the template
  updateSampleAttributes(args.project_id, templateSampleAttributes, sampleAttributes)
  updateProjectAttributes(args.project_id, templateProjectAttributes, projectAttributes)
  updateTiming(args.project_id, templateEvents, templateIntervals, projectEvents, projectIntervals)
  updateConversations(args.project_id, templateConversations, projectConversations)

  # Update the project defaults
  updateSampleAttributesDefaults(args.project_id, templateDefaults)
  updateVariantsTable(args.project_id, templateDefaults)

  # Get any gene sets from the template and create them in the target
  recreateGeneSets(args.template_project_id, args.project_id)
  exit(0)

  # Import the "Assigned Template" project attribute and set the value to Template:version
  assignTemplateAttribute(args.project_id, args.template, projectAttributes, assignedTemplateId)

# Input options
def parseCommandLine():
  global version

  parser = argparse.ArgumentParser(description='Process the command line')

  # Required arguments
  parser.add_argument('--project_id', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")
  parser.add_argument('--template_project_id', '-m', required = True, metavar = "integer", help = "The Mosaic project id of the template to run")
  parser.add_argument('--token', '-t', required = True, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = True, metavar = "string", help = "The base url for Mosaic")

  # Store the version
  parser.add_argument('--version', '-v', action="version", version='Mosaic templates version: ' + str(version))

  return parser.parse_args()

# Get all the information about a projects attributes
def getProjectAttributes(projectId):
  global mosaicConfig
  generalAttributes = {}
  timingAttributes  = {}

  # Get all the attributes
  data = api_pa.getProjectAttributes(mosaicConfig, projectId)
  for attribute in data:

    # Get the attribute value associated with this project
    attributeValue = False
    for value in attribute['values']:
      if int(value['project_id']) == int(projectId):
        attributeValue = value['value']
        break

    # Store the information
    if attribute['value_type'] == 'timestamp': timingAttributes[attribute['id']] = {'name': attribute['name'], 'value': attributeValue, 'isPublic': attribute['is_public']}
    else: generalAttributes[attribute['id']] = {'name': attribute['name'], 'value': attributeValue, 'isPinned': False, 'isNamePinned': False, 'isPublic': attribute['is_public']}

  # Return the attributes
  return generalAttributes, timingAttributes

# Get all the existing conversations
def getProjectConversations(projectId):
  global mosaicConfig

  # Get all the conversations from the project and add the isPinned flag as false
  conversations = api_pc.getConversationsIdToTitleDesc(mosaicConfig, projectId)
  for convId in conversations: conversations[convId]['isPinned'] = False

  # Return the list of conversations in the project
  return conversations

# Determine what is pinned to the project dashboard
def dashboard(projectId, projectAttributes, projectConversations):
  global mosaicConfig

  # Get the dashboard information
  data = api_d.getDashboard(mosaicConfig, projectId)
  for dashboardObject in data:

    # Ignore all default items. These can't be modified
    if not dashboardObject['is_default']:

      # For project attributes, update the stored attributes to indicate that they need to be pinned to the dashboard and whether
      # they should be pinned with or without the attribute name.
      if dashboardObject['type'] == 'project_attribute':
        attributeId = dashboardObject['attribute_id']
        if attributeId not in projectAttributes: fail('Project attribute ' + str(attributeId) + ' was not found in the supplied attributes dictionary for project ' + str(projectId))

        # Check if the name should be pinned, then update the attribute
        projectAttributes[attributeId]['isPinned'] = True
        projectAttributes[attributeId]['isNamePinned'] = True if dashboardObject['should_show_name_in_badge'] else False

      # For conversations
      elif dashboardObject['type'] == 'conversation':
        conversationId = dashboardObject['project_conversation_id']
        if conversationId not in projectConversations: fail('Conversation ' + str(conversationId) + ' was not found in the supplied conversations dictionary for project ' + str(projectId))
        projectConversations[conversationId]['isPinned'] = True

  # Return the information
  return projectAttributes, projectConversations

# Use the project settings to get the table and chart defaults for the template project
def getTableChartDefaults(projectId):
  global mosaicConfig
  defaults = {}

  # Get all the project settings
  projectSettings = api_ps.getProjectSettings(mosaicConfig, projectId)

  # Samples table columns
  defaults['sampleAttributesColumnIds'] = projectSettings['selected_sample_attribute_column_ids']
  defaults['variantAnnotationIds']      = projectSettings['selected_variant_annotation_ids']
  defaults['geneAnnotationIds']         = projectSettings['selected_gene_annotation_ids']
  defaults['sampleAttributeChartIds']   = projectSettings['selected_sample_attribute_chart_data']['chart_ids']

  # Return the project settings
  return defaults

# Update the sample attributes
def updateSampleAttributes(projectId, templateAttributes, sampleAttributes):
  global mosaicConfig

  # Loop over all of the template sample attributes
  for attribute in templateAttributes:

    # Ignore all attributes that are not public and check if any of these remaining attributes
    # are present in the current project
    if templateAttributes[attribute]['is_public']:
      attributeId = templateAttributes[attribute]['id']
      if attributeId not in sampleAttributes: api_sa.importSampleAttribute(mosaicConfig, projectId, attributeId)

# Update the project attributes based on the template
def updateProjectAttributes(projectId, templateAttributes, projectAttributes):
  global mosaicConfig

  # Loop over all of the template attributes
  for attributeId in templateAttributes:
    name         = templateAttributes[attributeId]['name']
    value        = templateAttributes[attributeId]['value']
    isPublic     = templateAttributes[attributeId]['isPublic']
    isPinned     = templateAttributes[attributeId]['isPinned']
    isNamePinned = 'true' if templateAttributes[attributeId]['isNamePinned'] else 'false'

    # If there is no value, set it to null
    if not value: value = 'null'

    # Only import the attribute if it doesn't already exist in the project being updated and is public
    if attributeId not in projectAttributes and isPublic:
      importData = api_pa.importProjectAttribute(mosaicConfig, projectId, attributeId, value)

      # Store the project attribute. This attribute was just imported and so is not currently pinned
      projectAttributes[attributeId] = {'name': name, 'value': value, 'isPinned': False, 'isNamePinned': isNamePinned, 'isPublic': isPublic}

    # If the attribute should be pinned, and isn't already pinned, pin it
    if isPinned and not projectAttributes[attributeId]['isPinned']: api_d.pinProjectAttribute(mosaicConfig, projectId, attributeId, isNamePinned)

# Update the timing information for the project
def updateTiming(projectId, templateEvents, templateIntervals, projectEvents, projectIntervals):
  global mosaicConfig

  # Loop over all the events in the template
  for eventId in templateEvents:
    name  = templateEvents[eventId]['name']
    value = templateEvents[eventId]['value']
    if not value: value = 'null'

    # Only add events that are not already in the project
    if eventId not in projectEvents: api_pa.importProjectAttribute(mosaicConfig, projectId, eventId, value)
  
  # Now add the intervals
  for intervalId in templateIntervals:
    name = templateIntervals[intervalId]['name']

    # Only import intervals that are not already in the project
    if intervalId not in projectIntervals: api_pia.importInterval(mosaicConfig, projectId, intervalId)

# Update the conversations
def updateConversations(projectId, templateConversations, projectConversations):
  global mosaicConfig

  # Get the titles of all conversations that exist in the project being updated
  existingTitles = []
  for convId in projectConversations: existingTitles.append(projectConversations[convId]['title'])

  # Loop over the conversations in the template
  for convId in templateConversations:
    title       = templateConversations[convId]['title']
    description = templateConversations[convId]['description']
    isPinned    = templateConversations[convId]['isPinned']

    # The description might contain multiple lines which will break the curl command. Replace all newlines with \n
    if description:
      if "\n" in description: description = description.replace("\n", "\\n")

    # Only create the conversation if a conversations of the same name does not already exist
    if title not in existingTitles:
      createdConvId = api_pc.createConversation(mosaicConfig, projectId, title, description)

      # Pin the conversation if required
      if isPinned: api_d.pinConversation(mosaicConfig, projectId, createdConvId)

# Update the samples table to show the correct columns in the correct order
def updateSampleAttributesDefaults(projectId, defaults):
  global mosaicConfig

  columnIds = defaults['sampleAttributesColumnIds']
  chartIds  = defaults['sampleAttributeChartIds']
  api_ps.setDefaultTableAndCharts(mosaicConfig, projectId, columnIds, chartIds)

# Update the variants table to include the correct annotations
def updateVariantsTable(projectId, defaults):
  global mosaicConfig

  annotationIds = defaults['variantAnnotationIds']
  api_ps.setDefaultVariantAnnotations(mosaicConfig, projectId, annotationIds)

# Get any saved gene sets from the template
def recreateGeneSets(templateId, projectId):
  global mosaicConfig

  # Get the gene sets in the target project
  existingSets = []
  geneSets     = api_g.getGeneSets(mosaicConfig, projectId)
  for geneSet in geneSets: existingSets.append(geneSet['name'])

  # Get the gene sets from the template and add any that don't exist to the target project
  geneSets = api_g.getGeneSets(mosaicConfig, templateId)
  for geneSet in geneSets:
    name        = geneSet['name']
    description = geneSet['description']
    genes       = geneSet['gene_ids']
    if name not in existingSets: geneSetId = api_g.postGeneSetByIds(mosaicConfig, projectId, name, description, genes)

# Import the "Assigned Template" project attribute and set the value to Template:version
def assignTemplateAttribute(projectId, templateName, projectAttributes, attributeId):
  global mosaicConfig
  global version

  # Define the attribute value as Template:version
  value = str(templateName) + ":" + str(version)

  # If the 'Assigned Template' attribute id was not found, fail
  if not attributeId: fail('Could not find the "Assigned Template" attribute in the public attributes project')

  # If the Assigned Template attribute is not already in the project, import it, otherwise, update the value
  if attributeId not in projectAttributes: api_pa.importProjectAttribute(mosaicConfig, projectId, attributeId, value)
  else: api_pa.updateProjectAttribute(mosaicConfig, projectId, attributeId, value)

# If problems are found with the templates, fail
def fail(text):
  print(text)
  exit(1)

# Initialise global variables

# Attributes from the config file
mosaicConfig = {}

# Store the version
version = "1.05"

if __name__ == "__main__":
  main()
