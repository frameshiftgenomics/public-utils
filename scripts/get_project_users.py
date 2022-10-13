#!/usr/bin/python

from __future__ import print_function

import os
import argparse
import json
import math

def main():

  # Parse the command line
  args = parseCommandLine()

  # Get all the sample attributes in the project
  getUsers(args)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Standard args
  parser.add_argument('--token', '-t', required = True, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--apiCommands', '-a', required = True, metavar = "string", help = "The path to the directory of api commands")
  parser.add_argument('--url', '-u', required = True, metavar = "string", help = "The base url for Mosaic curl commands, up to an including \"api\". Do NOT include a trailing /")

  # Custom args
  parser.add_argument('--project', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")

  return parser.parse_args()

# Get all the sample attributes in the project
def getUsers(args):

  # Get the number of users attached to the project
  command = args.apiCommands + "/get_project_roles.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(args.project) + " 1 1"
  data    = json.loads(os.popen(command).read())

  # Determine the number of pages of results, given 100 users per page
  noPages = int( math.ceil( float(data["count"]) / float(100.) ) )

  # Loop over all necessary pages
  userIds = []
  for i in range(0, noPages):
    command = args.apiCommands + "/get_project_roles.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(args.project) + " 100 " + str(i + 1)
    data    = json.loads(os.popen(command).read())

    # Loop over the users and get the ids
    for user in data["data"]: userIds.append(user["user_id"])

  print(userIds)

# Initialise global variables

if __name__ == "__main__":
  main()
