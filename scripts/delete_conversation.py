#!/usr/bin/python

from __future__ import print_function
from os.path import exists

import os
import math
import argparse
import json
from random import random

from sys import path
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/api_commands")
path.append("/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]) + "/common_components")
import mosaic_config
import api_project_conversations as api_pc

def main():
  global mosaicConfig

  # Parse the command line
  args = parseCommandLine()

  # Parse the mosaic configuration file
  mosaicRequired = {'MOSAIC_TOKEN': {'value': args.token, 'desc': 'An access token', 'long': '--token', 'short': '-t'},
                    'MOSAIC_URL': {'value': args.url, 'desc': 'The api url', 'long': '--url', 'short': '-u'}}
  mosaicConfig = mosaic_config.parseConfig(args.config, mosaicRequired)

  # Get all the conversations in the project
  if not args.conversation_id: getConversations(args)

  # Delete the specified conversation
  deleteConversation(args)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Arguments related to the config file
  parser.add_argument('--token', '-t', required = False, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--url', '-u', required = False, metavar = "string", help = "The base url for Mosaic curl commands, up to an including \"api\". Do NOT include a trailing /")
  parser.add_argument('--config', '-c', required = False, metavar = "string", help = "A config file containing token / url information")

  # The project id to which the filter is to be added is required
  parser.add_argument('--project_id', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")

  # Arguments related to the file to add
  parser.add_argument('--conversation_id', '-v', required = False, metavar = "string", help = "The conversation id to be deleted. If not included, a list of conversation ids will be presented")

  return parser.parse_args()

# Delete the file
def getConversations(args):
  global mosaicConfig
  limit = 100
  page  = 1

  # Get all the conversations
  try: data = json.loads(os.popen(api_pc.getCoversations(mosaicConfig, limit, 1, args.project_id)).read())
  except: fail('Could not get project conversations for project ' + str(projectId))
  if 'message' in data: fail('Could not get project conversations for project ' + str(projectId) + '. API returned the message "' + str(data['message']) + '"')

  # Get the number of pages of conversations
  noPages = math.ceil(float(data['count']) / float(limit))

  # Loop over the conversations and look for one with the name 'Alignstats information'
  for conversation in data['data']: print(conversation['id'], ': ', conversation['title'])

  # Loop over remaining pages of files if the conversation has not been found
  if noPages > 1 and not conversationId:
    for i in range(1, noPages, 1):
      try: data = json.loads(os.popen(api_pc.getCoversations(mosaicConfig, limit, i + 1, args.project_id)).read())
      except: fail('Could not get project conversations for project ' + str(projectId))
      if 'message' in data: fail('Could not get project conversations for project ' + str(projectId) + '. API returned the message "' + str(data['message']) + '"')
      for conversation in data['data']: print(conversation['id'], ': ', conversation['title'])

  # After outputting the conversations ids, finish
  exit(0)

# Delete the conversation
def deleteConversation(args):
  global mosaicConfig

  try: data = os.popen(api_pc.deleteCoversation(mosaicConfig, args.project_id, args.conversation_id))
  except: fail('Could not delete conversation')
  if 'message' in data: fail('Could not delete conversation. API returned the message "' + str(data['message']) + '"')

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

# Initialise global variables
mosaicConfig = {}

# Attributes from the config file
apiUrl              = False
token               = False

if __name__ == "__main__":
  main()
