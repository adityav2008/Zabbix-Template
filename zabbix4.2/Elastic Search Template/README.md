# zabbix-elasticsearch

This repository provides a script and multiple templates to monitor Elasticsearch clusters and nodes using Zabbix. It's inspired by the awesome work of Elastic's [Untergeek](https://github.com/untergeek/zabbix-grab-bag/tree/master/Elasticsearch).

## zbx_es.py
To query the exposed Elasticsearch API's we use a script called zbx_es.py. It's a simple script which takes two mandatory arguments:
 - which API to use
 - the key to retrieve

At this time I've only tested the script with the following API's which provide me with enough information to properly monitor the nodes and cluster:
  - cluster.health
  - cluster.stats
  - nodes.stats
 
Other nodes.* and cluster.* API's should work as well, others are currently not honored by the script as I haven't had time to test any of them. 

#### Requirements
The script is written in Python and requires the following libraries:
  - [elasticsearch-py](https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/index.html)
  - [kaptan](https://github.com/emre/kaptan)
 
#### Command-line usage
The script can be used in combination with the Zabbix Agent, but can be run from the commandline just as well. The first argument is the API class to call. The second argument is the key to the value you want to retrieve.

For example, if you look at the output of the [Cluster Stats](https://www.elastic.co/guide/en/elasticsearch/reference/2.0/cluster-stats.html) api:

```
{
   "timestamp": 1439326129256,
   "cluster_name": "elasticsearch",
   "status": "green",
   "indices": {
      "count": 3,
      "shards": {
         "total": 35,
         "primaries": 15,
         "replication": 1.333333333333333,
         "index": {
            "shards": {
               "min": 10,
               "max": 15,
               "avg": 11.66666666666666
            },
            ....
```

To retrieve the total number of shards the commandline would be:

```sh
$ ./zbx_es.py cluster.stats indices.shards.total
35
```

An example to get the cluster health status:
```sh
$ ./zbx_es.py cluster.health status
green
```
Or to get the indices total size of node IronMan:
```sh
$ ./zbx_es.py nodes.stats nodes.IronMan.indices.store.size_in_bytes
9670758
```
Or to get the total numer of indices in the cluster:

```sh
$ ./zbx_es.py cluster.stats indices.count
3
```
#### Script notes
My goal for the script was to have it as generic as possible. I did build in some logic however, because the way the Elasticsearch API identifies nodes is not using the configured nodename, but with a generated node_id. 

Take this output for example:

```
{
  "cluster_name" : "my-aweseome-cluster",
  "nodes" : {
    "ZmTYPyuXEATDIE7m9GThDrBA" : {
      "timestamp" : 1443693895783,
      "name" : "my-node-1",
      "transport_address" : "inet[/10.10.10.10:9300]",
      "host" : "ahiruyaki.example.com",
      "ip" : [ "inet[/10.10.10.10:9300]", "NONE" ],
      "indices" : {
        "docs" : {
          "count" : 1660154,
          "deleted" : 0
        },
```
Let's say you want the value of the docs count. To get to this value you'd have to use:
```sh
$ ./zbx_es.py nodes.stats nodes.ZmTYPyuXEATDIE7m9GThDrBA.indicies.docs.count
1660154
```
Which works, but you probably remember you named your node "my-node-1" and have never seen the node id "ZmTYPyuXEATDIE7m9GThDrBA" before.

Some logic in the script is capable of replacing the node-name with the node-id at runtime. So you can actually retrieve the data like this:

```sh
$ ./zbx_es.py nodes.stats nodes.my-node-1.indicies.docs.count
1660154
```
Internally the script will look up the node-id of the node called "my-node-1" and replace "my-node-1" with "ZmTYPyuXEATDIE7m9GThDrBA" before searching for the value. 

## Zabbix integration
To use the script for sending metrics to Zabbix it's recommended to deploy it on a Elasticsearch (cluster) node and then let the Zabbix Agent call it using a UserParameter.

The script and templates are tested on Zabbix 2.4.

#### Zabbix Agent configuration
Deploy the script to the Elasticserver node and add the following line to the Zabbix agent configuration:
````
UserParameter=zbx_es[*],/etc/zabbix/scripts/zbx_es.py $1 $2
````
Be sure to modify the script path to a proper value! After that, restart the agent.
#### Using the Zabbix template
Note: These templates are based on the ones from [Untergeek's zabbix-grab-bag](https://github.com/untergeek/zabbix-grab-bag) and have the same name and items. However, they are not compatible because of the way we interact with the API.

Before importing the zbx_es_templates.xml file be sure to create a value map called "ES Cluster State" which maps the proper values, like:
  - 0 = Green
  - 1 = Yellow
  - 2 = Red
  
Once the value map is in place you can import the zbx_es_templates.xml file. It will provide two templates:
- Elasticsearch Node & Cache (which is for node-level monitoring)
- Elasticsearch Cluster (cluster state, shard-level monitoring, record count, storage sizes, etc.)

Please note that the templates expect a {$NODENAME} host-level macro to be in place.

The following items are included by the templates:

* ES Cluster (11 Items)
  - Cluster-wide records indexed per second
  - Cluster-wide storage size
  - ElasticSearch Cluster Status
  - Number of active primary shards
  - Number of active shards
  - Number of data nodes
  - Number of initializing shards
  - Number of nodes
  - Number of relocating shards
  - Number of unassigned shards
  - Total number of records
* ES Cache (2 Items)
  - Node Field Cache Size
  - Node Filter Cache Size
* ES Node (2 Items)
  - Node Storage Size
  - Records indexed per second

## TODO
  - Make the script even more generic and accept any API call
  - Better error handling (debug mode?)
