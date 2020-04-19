#!/bin/bash
echo "Starting Filebeat custom startup script"

set -euo pipefail

until curl -s -f "${ELASTIC_HOST}" > /dev/null; do
      echo "Waiting for elasticsearch..."
      sleep 5
done

until curl -s "${KIBANA_HOST}/login" | grep "Loading Kibana" > /dev/null; do
      echo "Waiting for kibana..."
      sleep 5
done

echo "Setting up dashboards..."
# https://www.elastic.co/guide/en/beats/filebeat/current/filebeat-template.html#load-template-manually
filebeat setup \
    --index-management \
    --pipelines \
    --modules ${FILEBEAT_MODULES} \
    -E output.logstash.enabled=false \
    -E 'output.elasticsearch.hosts=["${ELASTIC_HOST}"]' \
    --strict.perms=false

echo "Done Filebeat custom startup script"
