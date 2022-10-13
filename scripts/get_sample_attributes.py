#!/usr/bin/python

from __future__ import print_function

import os
import argparse
import json

def main():

  # Parse the command line
  args = parseCommandLine()

  # Check the supplied arguments are consistent
  checkArgs(args)

  # Get all the sample attributes in the project
  getSampleAttributeIds(args)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Standard args
  parser.add_argument('--token', '-t', required = True, metavar = "string", help = "The Mosaic authorization token")
  parser.add_argument('--apiCommands', '-a', required = True, metavar = "string", help = "The path to the directory of api commands")
  parser.add_argument('--url', '-u', required = True, metavar = "string", help = "The base url for Mosaic curl commands, up to an including \"api\". Do NOT include a trailing /")

  # Custom args
  parser.add_argument('--project', '-p', required = True, metavar = "integer", help = "The Mosaic project id to upload attributes to")
  parser.add_argument('--public', '-b', required = False, action = 'store_true', help = "If set, only print out public attributes")
  parser.add_argument('--private', '-v', required = False, action = 'store_true', help = "If set, only print out private attributes")

  return parser.parse_args()

# Check that -b and -v aren't simultaneously set
def checkArgs(args):
  if args.public and args.private:
    print("The --public and --private arguments cannot be set simultaneously. --public will print out public attributes,")
    print("--private will print out private attributes. If neither are set, all attributes are printed out.")
    exit(1)

# Get all the sample attributes in the project
def  getSampleAttributeIds(args):
  global sampleAttributeIds

  # Get the first page of conversations
  command = args.apiCommands + "/get_sample_attributes.sh " + str(args.token) + " \"" + str(args.url) + "\" " + str(args.project)
  data    = json.loads(os.popen(command).read())

  # Store the attribute ids
  for attribute in data: sampleAttributeIds[attribute["name"]] = {"id": attribute["id"], "uid": attribute["uid"], "is_public": attribute["is_public"]}

  # Print out attributes, accounting for whether all, public, or private were requested
  for attribute in sampleAttributeIds:
    if sampleAttributeIds[attribute]["is_public"]:
      if not args.private: print(attribute, sampleAttributeIds[attribute]["id"], sampleAttributeIds[attribute]["uid"], sampleAttributeIds[attribute]["is_public"], sep = "\t")
    else:
      if not args.public: print(attribute, sampleAttributeIds[attribute]["id"], sampleAttributeIds[attribute]["uid"], sampleAttributeIds[attribute]["is_public"], sep = "\t")

# Initialise global variables

# Store the ids of the projects in the collection
sampleAttributeIds = {}

if __name__ == "__main__":
  main()
