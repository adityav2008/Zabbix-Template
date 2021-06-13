#!/usr/bin/env python

import sys
import kaptan
from elasticsearch import *

# Define the fail message
def zbx_fail():
  print "ZBX_NOTSUPPORTED"
  sys.exit(2)

# Default returnval
returnval = None

# __main__
#
# We need to have two command-line arguments:
# sys.argv[1]: API to use
# sys.argv[2]: The key to retrieve
#
# Supported API's:
#
# cluster.*
# nodes.*
#
# Examples:
#
# zbx_elasticsearch.py cluster.health indices.count
# zbx_elasticsearch.py nodes.stats nodes.ironman.indices.store.size_in_bytes

# Handle command-line arguments
if len(sys.argv) < 4:
  zbx_fail()

if '.' not in sys.argv[1]:
  zbx_fail()

# Split the API argument 
api = sys.argv[1].split(".")
es_host = sys.argv[3]
# Try to establish a connection to elasticsearch
try:
  conn = Elasticsearch([es_host])
except Exception, e:
  zbx_fail()

# Kaptan config object 
config = kaptan.Kaptan()

if "cluster" in sys.argv[1]:
  config.import_config(getattr(conn.cluster, api[1])())
  returnval = config.get(sys.argv[2])

elif "nodes" in sys.argv[1]:
  nodestats = getattr(conn.nodes, api[1])()
  config.import_config(nodestats)

  # Map node_id to node_name  
  node_names = {}
  for node_id in nodestats['nodes']:
    node_name = nodestats['nodes'][node_id]['name']
    node_names[node_name] = node_id

  # Replace the node name with node ID if possible
  key_string = sys.argv[2]
  for node in sorted(node_names, key=len, reverse=True):
    if node in key_string:
      key_string = key_string.replace(node, node_names[node])
      break

  # Get the value
  returnval = config.get(key_string)

else:
  zbx_fail()

# Return a value or fail state
if returnval is None:
  zbx_fail()
else:
  # Map status green/yellow/red to integers
  if returnval == 'green':
    returnval = 0
  elif returnval == 'yellow':
    returnval = 1
  elif returnval == 'red':
    returnval = 2

  print returnval

# End
