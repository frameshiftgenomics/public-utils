#!/bin/bash

TOKEN=$1
PROJECT_ID=$2

# Paths
UTILS=/uufs/chpc.utah.edu/common/HIPAA/u0991467/programs/public-utils

# Parameters
URL="https://mosaic.chpc.utah.edu/api"

# Get the path to the project files
$UTILS/api_commands/get_all_sample_files.sh $TOKEN $URL $PROJECT_ID 1 1 | python -m json.tool | grep uri | cut -d "\"" -f 4 | cut -c 8- | rev | cut -d '/' -f 4- | rev
