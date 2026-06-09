#!/usr/bin/env bash
# Generate nextflow_schema with updated basecaller enumerations
#
# This script uses `nextflow config` to obtain the basecaller container,
# creates JSON arrays of the models using the container's list-models script
# and injects them with jq to create nextflow_schema.json.new.
set -euo pipefail

TARGET=$1

get_artifactory "${WHALEFISH_ARTIFACTORY_METADATA_ROOT}/dorado/latest/models.json"

# Yummy delicious models.json - slurp it up and get simplex and modbase out, 
# and place them into their respective enums in nextflow_schema.json
jq \
  --indent 4 \
  --slurpfile models models.json \
  '(.definitions.basecalling_options.properties.basecaller_cfg.enum) = $models[0].simplex |
   (.definitions.basecalling_options.properties.remora_cfg.enum) = $models[0].modbase' \
  ${TARGET}/nextflow_schema.json > ${TARGET}/nextflow_schema.json.new

echo "# Updated schema generated, you should inspect it before adopting it!"
echo "diff ${TARGET}/nextflow_schema.json ${TARGET}/nextflow_schema.json.new"
echo "mv ${TARGET}/nextflow_schema.json.new ${TARGET}/nextflow_schema.json"