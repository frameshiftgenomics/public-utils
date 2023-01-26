#!/usr/bin/python

from __future__ import print_function
from os.path import exists
import argparse

# Parse the config file and get the Mosaic token and url
def parseConfig(configFilename, required):
  config = {}

  # Check the config file exists, if it was defined
  if configFilename:
    if not exists(configFilename): fail('Config file "' + str(configFilename) + '" does not exist')

    # Parse the config file and store the token and url
    try: configFile = open(configFilename, "r")
    except: fail('Failed to open config file "' + str(configFilename) + '"')
    for line in configFile.readlines():
      fields            = line.rstrip().split("=")
      config[fields[0]] = fields[1]

  # Loop over the required arguments and overwrite the config file if values are provided
  for requiredConfig in required:
    if required[requiredConfig]['value']: config[requiredConfig] = required[requiredConfig]['value']
    if requiredConfig not in config: config[requiredConfig] = required[requiredConfig]['value']

    # Check that values are set for the required arguments
    if not config[requiredConfig]:
      print(required[requiredConfig]['desc'], ' is required. You can either supply this with "', required[requiredConfig]['long'], ' (', required[requiredConfig]['short'], ')" or', sep = '')
      print("supply a config file '--config (-c)' which includes the line:")
      print('  ', requiredConfig, '=<VALUE>', sep = '')
      exit(1)

  # The api routines expect the keys 'token' and 'url' to be used, so update config
  config['token'] = config.pop('MOSAIC_TOKEN')
  config['url']   = config.pop('MOSAIC_URL')

  # Ensure the url terminates with a '/'
  if not config['url'].endswith("/"): config['url'] += "/"

  # Return the values
  return config

# If problems are found with the templates, fail
def fail(text):
  print(text)
  exit(1)
