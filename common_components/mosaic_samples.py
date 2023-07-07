import os

# Get all samples in a Mosaic project and store the required sample attributes
def getMosaicSamples(mosaicConfig, api_s, api_sa, projectId):
  mosaicSamples   = {}
  mosaicSampleIds = api_s.getSampleNamesAndIds(mosaicConfig, projectId)
  for sample in mosaicSampleIds:
    mosaicSamples[sample] = {'id': mosaicSampleIds[sample], 'relation': False}

    # Loop over the sample attributes and store what is required
    data = api_sa.getAttributesForSample(mosaicConfig, projectId, mosaicSampleIds[sample])
    for attribute in data:
      if attribute['name'] == 'Relation':
        for value in attribute['values']:
          if value['sample_id'] == mosaicSampleIds[sample]:
            mosaicSamples[sample]['relation'] = value['value']
            break

  # Return the sample information
  return mosaicSamples

# If the proband is defined with a sample attribute, determine the proband
def getProband(mosaicConfig, mosaicSamples):
  proband   = False
  for sample in mosaicSamples:
    if mosaicSamples[sample]['relation'] == 'Proband':
      if proband: fail('Multiple samples in the Mosaic project are listed as the proband')
      else: proband = sample

  # Return the name and id of the proband
  return proband

# If the script fails, provide an error message and exit
def fail(message):
  print(message, sep = "")
  exit(1)
