#!/usr/bin/python

from __future__ import print_function

import os
import math
import argparse
import json
from random import random

def main():

  # Parse the command line
  args = parseCommandLine()

  # Get the id for the conversation to update
  conversationId = getConversationID(args)

  # Add the comment to the conversation
  addComment(args, conversationId)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')
  parser.add_argument('--token', '-t', required = True, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--project', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")
  parser.add_argument('--apiCommands', '-a', required = True, metavar = "string", help = "The path to the directory of api commands")
  parser.add_argument('--url', '-u', required = True, metavar = "string", help = "The base url for Mosaic curl commands, up to an including \"api\". Do NOT include a trailing /")
  parser.add_argument('--conversationTitle', '-c', required = True, metavar = "string", help = "The title of the conversation to update")
  parser.add_argument('--comment', '-m', required = True, metavar = "string", help = "The comment to add to the conversation")

  return parser.parse_args()

# Get the id for the conversation to update
def  getConversationID(args):

  # Get the first page of conversations
  command = args.apiCommands + "/get_conversations.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(args.project) + " 1"
  data    = json.loads(os.popen(command).read())

  # Determine the number of pages
  noPages = int( math.ceil( float(data["count"]) / float(25.) ) )

  # Loop over all necessary pages
  conversationId = False
  for i in range(0, noPages):
    command = args.apiCommands + "/get_project_conversations.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(args.project) + " " + str(i + 1)
    data    = json.loads(os.popen(command).read())

    # Loop over the conversations from all the templates and create then
    for conversation in data["data"]:
      if str(conversation["title"]) == str(args.conversationTitle):
        conversationId = conversation["id"]
        continue

    # Break the loop if the conversation has been found
    if conversationId: continue

  return conversationId

# Add the comment to the conversation
def addComment(args, conversationId):

# Initialise global variables

if __name__ == "__main__":
  main()
