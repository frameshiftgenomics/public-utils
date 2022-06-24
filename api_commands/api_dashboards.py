#!/usr/bin/python

# Pin a chart to the dashboard
def pinChart(mosaicConfig, chartId, projectId):
  token = mosaicConfig["token"]
  url   = mosaicConfig["url"]

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"type": "chart", "chart_id": "' + str(chartId) + '", "is_active": "true"}\' '
  command += str(url) + 'api/v1/projects/' + str(projectId) + '/dashboard'

  return command

