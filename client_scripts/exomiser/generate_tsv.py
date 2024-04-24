from os.path import exists
from pprint import pprint
from sys import path

import argparse
import os
import sys

def main():

  # Parse the command line
  args = parseCommandLine()

  # Import the api client
  path.append(args.api_client)
  from mosaic import Mosaic, Project, Store
  apiStore  = Store(config_file = args.client_config)
  apiMosaic = Mosaic(config_file = args.client_config)

  # Open an api client project object for the defined project
  project = apiMosaic.get_project(args.project_id)

  # Variant filters will be added to the project and we need to define the annotation ids for the displayed columns. This will be
  # the Exomiser annotations just created as well as ClinVar and the gene symbol, the consequence and the genotypes. We need to
  # get the ids for some of these columns
  existing_annotations = {}
  for annotation in project.get_variant_annotations():
    existing_annotations[annotation['name']] = {'id': annotation['id'], 'uid': annotation['uid'], 'privacy_level': annotation['privacy_level']}

  # The following private variant annotations need to be created in Mosaic. These need to be private as they
  # are ranks or scores that are specific to the project they are run in - the same variant could have a 
  # different rank in a different project, and so these cannot be public, as only one value would be allowed
  # across projects
  annotations = {}
  annotations = create_annotation(project, existing_annotations, annotations, 'Rank', 'float')
  annotations = create_annotation(project, existing_annotations, annotations, 'p-value', 'float')
  annotations = create_annotation(project, existing_annotations, annotations, 'Gene Combined Score', 'float')
  annotations = create_annotation(project, existing_annotations, annotations, 'Gene Phenotype Score', 'float')
  annotations = create_annotation(project, existing_annotations, annotations, 'Gene Variant Score', 'float')
  annotations = create_annotation(project, existing_annotations, annotations, 'Variant Score', 'float')
  annotations = create_annotation(project, existing_annotations, annotations, 'MOI', 'string')

  # Open the output tsv file
  output_tsv = open(args.output_tsv, 'w')
  print('CHROM', 'START', 'END', 'REF', 'ALT', \
    annotations['Rank']['uid'], \
    annotations['p-value']['uid'], \
    annotations['Gene Combined Score']['uid'], \
    annotations['Gene Phenotype Score']['uid'], \
    annotations['Gene Variant Score']['uid'], \
    annotations['Variant Score']['uid'], \
    annotations['MOI']['uid'], \
    sep = '\t', file = output_tsv)

  # Store the variants information
  variants    = {}
  variantInfo = {}

  # Check that the exomiser output file exists and open it for parsing
  if not exists(args.input_tsv): fail('The file ' + str(args.input_tsv) + ' was not found')
  input_tsv = open(args.input_tsv, 'r')
  for i, variant in enumerate(input_tsv.readlines()):

    # Skip the header line
    if variant.startswith('#'): continue

    # Split the line on tab and extract the values of interest
    fields = variant.rstrip().split('\t')
    chrom  = fields[14]
    start  = int(fields[15])
    end    = int(fields[16]) + 1
    rank   = fields[0]
    variantInfo[i] = {'chrom': chrom, 
                   'start': start,
                   'end': end,
                   'ref': fields[17],
                   'alt': fields[18],
                   'rank': rank,
                   'gene': fields[2],
                   'pvalue': fields[5],
                   'comb': fields[6],
                   'pheno': fields[7],
                   'geneVar': fields[8],
                   'variant': fields[9],
                   'moi': fields[4]}

    # If the ref or alt allele are 'N', change them to '*'
    if variantInfo[i]['ref'] == 'N': variantInfo[i]['ref'] = '*'
    if variantInfo[i]['alt'] == 'N': variantInfo[i]['alt'] = '*'

    # Multiple variants can have the same rank, and the same variant can have multiple ranks (e.g. based on different modes
    # of inheritance). Store the variant information so that these can be consolidated before being exported
    if chrom not in variants: variants[chrom] = {}
    if start not in variants[chrom]: variants[chrom][start] = {}
    if end not in variants[chrom][start]:
      variants[chrom][start][end] = {'ref': variantInfo[i]['ref'], 'alt': variantInfo[i]['alt'], 'rank': rank, 'pvalue': variantInfo[i]['pvalue'], 'comb': variantInfo[i]['comb'], 'pheno': variantInfo[i]['pheno'], 'geneVar': variantInfo[i]['geneVar'], 'variant': variantInfo[i]['variant'], 'moi': variantInfo[i]['moi']}
    else:
      variants[chrom][start][end]['rank']    = variants[chrom][start][end]['rank'] + ',' + rank
      variants[chrom][start][end]['pvalue']  = variants[chrom][start][end]['pvalue'] + ',' + variantInfo[i]['pvalue']
      variants[chrom][start][end]['comb']    = variants[chrom][start][end]['comb'] + ',' + variantInfo[i]['comb']
      variants[chrom][start][end]['pheno']   = variants[chrom][start][end]['pheno'] + ',' + variantInfo[i]['pheno']
      variants[chrom][start][end]['geneVar'] = variants[chrom][start][end]['geneVar'] + ',' + variantInfo[i]['geneVar']
      variants[chrom][start][end]['variant'] = variants[chrom][start][end]['variant'] + ',' + variantInfo[i]['variant']
      variants[chrom][start][end]['moi']     = variants[chrom][start][end]['moi'] + ',' + variantInfo[i]['moi']

  # Loop over all variants and write them to file
  for chrom in variants:
    for start in variants[chrom]:
      for end in variants[chrom][start]:
         print(chrom, start, end, variants[chrom][start][end]['ref'], variants[chrom][start][end]['alt'], variants[chrom][start][end]['rank'], variants[chrom][start][end]['pvalue'], variants[chrom][start][end]['comb'], variants[chrom][start][end]['pheno'], variants[chrom][start][end]['geneVar'], variants[chrom][start][end]['variant'], variants[chrom][start][end]['moi'], sep = '\t', file = output_tsv)

  # Close the input and output files
  input_tsv.close()
  output_tsv.close()

# Input options
def parseCommandLine():

  parser = argparse.ArgumentParser(description='Process the command line')

  # Define the location of the api_client and the ini config file
  parser.add_argument('--client_config', '-c', required = True, metavar = 'string', help = 'The ini config file for Mosaic')
  parser.add_argument('--api_client', '-a', required = True, metavar = 'string', help = 'The api_client directory')

  # The project id to which the filter is to be added is required
  parser.add_argument('--project_id', '-p', required = True, metavar = 'integer', help = 'The Mosaic project id to add variant filters to')

  # The exomiser output tsv file with the values for the annotations
  parser.add_argument('--input_tsv', '-i', required = True, metavar = 'string', help = 'The exomiser variants.tsv file')

  # The output tsv file
  parser.add_argument('--output_tsv', '-o', required = True, metavar = 'string', help = 'The output tsv file to upload to Mosaic')

  return parser.parse_args()

# Check if the exomiser annotations exist and if not, create them
def create_annotation(project, existing_annotations, annotations, name, value_type):

  # Check if the annotation already exists
  annotations[name] = {}
  if name in existing_annotations:
    annotations[name]['id']  = existing_annotations[name]['id']
    annotations[name]['uid'] = existing_annotations[name]['uid']
  else:
    data = project.post_variant_annotation(name = name, value_type = value_type, privacy_level = 'private', category = 'Exomiser')
    annotations[name]['id']  = data['id']
    annotations[name]['uid'] = data['uid']

  # Return the updated annotations
  return annotations

# If the script fails, provide an error message and exit
def fail(message):
  print('FAIL: ', message, sep = '')
  exit(1)

# Initialise global variables

if __name__ == "__main__":
  main()
