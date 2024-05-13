import os
import argparse

from datetime import datetime
from pprint import pprint
from sys import path

def main():

  # Parse the command line
  args = parseCommandLine()

  # Import the api client
  path.append(args.api_client)
  from mosaic import Mosaic, Project, Store
  apiStore  = Store(config_file = args.client_config)
  apiMosaic = Mosaic(config_file = args.client_config)

  # Get the project settings
  job_statuses = args.status if args.status else None
  per_status_start = args.per_status_start if args.per_status_start else None
  per_status_end = args.per_status_end if args.per_status_end else None
  for job in apiMosaic.get_queue_status(per_status_start = per_status_start, per_status_end = per_status_end)['jobs']:

    # If only jobs of a particular status are to be output, check if the job has this status and only
    # output if it does
    if args.status:
      if str(args.status) == str(job['status']):
        print_job_info(job)

    # Otherwise output all jobs
    else:
      print_job_info(job)

# Input options
def parseCommandLine():
  parser = argparse.ArgumentParser(description='Process the command line arguments')

  # Define the location of the api_client and the ini config file
  parser.add_argument('--client_config', '-c', required = True, metavar = 'string', help = 'The ini config file for Mosaic')
  parser.add_argument('--api_client', '-a', required = True, metavar = 'string', help = 'The api_client directory')

  # Optional arguments
  parser.add_argument('--status', '-s', required = False, metavar = 'string', help = 'Only show jobs with this status. Options are: waiting, active, failed, completed')
  parser.add_argument('--per_status_start', '-t', required = False, metavar = 'integer', help = 'The start value of the job range to return')
  parser.add_argument('--per_status_end', '-e', required = False, metavar = 'integer', help = 'The end value of the job range to return')

  return parser.parse_args()

# Print information about the job
def print_job_info(job):
  print(job['redis_job_id'], ', id: ', job['id'], ', status: ', job['status'], ', type: ', job['job_type'], ', project: ', job['project_id'], ', submitted at: ', datetime.fromtimestamp(job['timestamp'] / 1000), sep = '')

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)

if __name__ == "__main__":
  main()
