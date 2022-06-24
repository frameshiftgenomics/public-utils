#!/usr/bin/python

# Get the project attribtes for the defined project
def postProject(mosaicConfig, name, reference):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"name": "' + str(name) + '", "reference": "' + str(reference) + '"}\' ' + str(url) + 'api/v1/projects'

  return command

# Post background data to a project
def postBackgrounds(mosaicConfig, filename, projectId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d "@' + str(filename) + '" ' + str(url) + 'api/v1/projects/' + str(projectId) + '/backgrounds'

  return command

# Post background data to a project
def getProjectCharts(mosaicConfig, projectId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X GET -H "Authorization: Bearer ' + str(token) + '" '
  command += str(url) + 'api/v1/projects/' + str(projectId) + '/charts'

  return command

# Post a chart with background data
def postProjectBackgroundChart(mosaicConfig, name, chartType, attributeId, backgroundId, ylabel, colorId, compareId, projectId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"name": "' + str(name) + '", "chart_type": "' + str(chartType) + '", "attribute_id": "' + str(attributeId)
  command += '", "project_background_id": "' + str(backgroundId) + '", "saved_chart_data": {"x_axis": "attribute", "y_label": "'
  command += str(ylabel) + '", "color_by": "attribute", "color_by_attribute_id": "' + str(colorId) + '", "compare_to_attribute_id": "'
  command += str(compareId) + '"}}\' ' + str(url) + 'api/v1/projects/' + str(projectId) + '/charts'

  return command

# Delete chart
def deleteProjectChart(mosaicConfig, projectId, chartId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X DELETE -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += str(url) + 'api/v1/projects/' + str(projectId) + '/charts/' + str(chartId)

  return command
