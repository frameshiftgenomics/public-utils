#!/usr/bin/python

# This contains API routes for charts (mirrors the API docs)

######
###### GET routes
######

######
###### POST routes
######

# Add users as watchers to a conversation
def postConversationWatcher(mosaicConfig, userIds, conversationId, projectId):
  token = mosaicConfig['MOSAIC_TOKEN']
  url   = mosaicConfig['MOSAIC_URL']

  command  = 'curl -S -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer ' + str(token) + '" '
  command += '-d \'{"user_ids": "' + str(userIds) + '"}\' '
  command += '"' + str(url) + 'api/v1/projects/' + str(projectId) + '/conversations/' + str(conversationId) + '/watchers' + '"'

  return command

######
###### PUT routes
######

######
###### DELETE routes
######
