#!/usr/bin/python

from __future__ import print_function
from os.path import exists
import argparse

# If a config file was provided, extract everything into the config dictionary
def mosaicConfigFile(configFilename):
  config = {}

  # If no config file was provided, return an empty dictionary. This will need to be populated
  # by individual command line arguments, or the script will fail
  if not configFilename: return config

  # Check the config file exists, if it was defined
  if not exists(configFilename): fail('Config file "' + str(configFilename) + '" does not exist')

  # Parse the config file and store the token and url
  try: configFile = open(configFilename, "r")
  except: fail('Failed to open config file "' + str(configFilename) + '"')

  # Store everything from the config file
  for line in configFile.readlines():
    fields            = line.rstrip().split("=")
    config[fields[0]] = fields[1]

  # Return the config information
  return config

# If command line arguments are supplied, overwrite the necessary fields read in from the config file, and/or
# supplement with anything not included in the config file
def commandLineArguments(config, required):

  # The required dictonary lists all of the information required along with any command line arguments set
  # by the calling script. Check that everything that is required was either supplied in a config file, or
  # was specified on the command line. If a command line argument explicitly set a value that was also in 
  # the config file, use the value provided on the command line
  for field in required:

    # Get the value for the field. If the value is set, add this to the config, or overwrite the existing value
    value = required[field]['value']

    # If the required field was not provided via a config file, or the command line, fail
    if not value and not field in config:
      if 'short' in required[field]: print(required[field]['desc'], ' is required. You can either supply this with "', required[field]['long'], ' (', required[field]['short'], ')" or', sep = '')
      else: print(required[field]['desc'], ' is required. You can either supply this with "', required[field]['long'], '" or', sep = '')
      print("supply a config file '--config (-c)' which includes the line:")
      print('  ', field, '=<VALUE>', sep = '')
      exit(1)

    # If the field was not set on the command line, but was in the config, continue
    elif not value and field in config: continue

    # If the field was set on the command line, update the config with this value, overwriting any existing value
    else: config[field] = value

  # Return the config information
  return config

############
############
############ Move all scripts over to the new routines, then delete this
############
############
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
