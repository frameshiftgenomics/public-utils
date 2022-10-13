#!/bin/bash

TOKEN=$1
PROJECT_ID=$2
FILECHECK=$3

# Paths
UTILS=/uufs/chpc.utah.edu/common/HIPAA/u0991467/programs/public-utils

# Parameters
URL="https://mosaic.chpc.utah.edu/api"
CONFIG=/uufs/chpc.utah.edu/common/HIPAA/u0991467/programs/public-utils/config.txt

# Get the path to the project files
PROJECT_PATH="/"`$UTILS/api_commands/get_all_sample_files.sh $TOKEN $URL $PROJECT_ID 1 1 \
| python -m json.tool | \
grep uri | \
cut -d "\"" -f 4 | \
cut -c 8- | \
rev | \
cut -d '/' -f 4- | \
rev`

echo "The path to the project files is: "$PROJECT_PATH

# Get the reference genome
REF=`echo $PROJECT_PATH | rev | cut -d '/' -f 1 | rev`

echo "The reference genome used is: "$REF

# Get the ped file and the sample names
PED=$PROJECT_PATH/Reports/*.ped
SAMPLES=()
while read line; do
  SAMPLE=`echo -e "$line" | cut -f 2`
  if [[ ${SAMPLE} != "Sample_ID" ]]; then
    SAMPLES+=($SAMPLE)
  fi
done < $PED

# Get the peddy html file
LENGTH=1000
FILEBASE=`echo $PROJECT_PATH | rev | cut -d '/' -f 3 | rev`
for file in $PROJECT_PATH/Reports/peddy/$FILEBASE*.html; do
  if [[ "${#file}" -lt "$LENGTH" ]]; then
    LENGTH=${#file}
    PEDDY_FILE=$file
  fi
done

# Get the project identifier
PROJECT_NAME=`echo $FILEBASE | cut -d '-' -f 1`

# Get the alignstats files
AS_FILES=""
for SAMPLE in "${SAMPLES[@]}"; do 
  AS_FILES=$AS_FILES" -i $PROJECT_PATH/Reports/alignstats/$SAMPLE*json"
done

# If requested, just print out the files to be used
if [ $FILECHECK -eq 0 ]; then
  echo "Project:    "$PROJECT_NAME
  echo "Ref:        "$REF
  echo "PED file:   "`ls $PED`
  echo "Peddy file: "$PEDDY_FILE
  echo "Alignstats files:"
  #more ./$PROJECT_NAME.alignstats.files.txt
  exit
fi

# Apply UDN template
python $UTILS/templates/template_by_project.py \
-c $CONFIG \
-m "UDN" \
-p $PROJECT_ID

# Run the Peddy integration
python $UTILS/integrations/peddy/peddy.py \
-c $CONFIG \
-r $REF \
-i $PEDDY_FILE \
-p $PROJECT_ID \

# Run the alignstats integration
python $UTILS/integrations/alignstats/alignstats.py \
-c $CONFIG \
-r $REF \
$AS_FILES \
-p $PROJECT_ID
