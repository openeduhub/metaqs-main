#!/usr/bin/zsh


curl -XGET "10.254.1.31:9200/workspace/_search" -o output.json

# get entries with replicationsource
curl -XGET "10.254.1.31:9200/workspace/_search&filter_path=hits.hits._source.properties.ccm:replicationsource" -o output_sources.json


curl -XGET "10.254.1.31:9200/workspace/_search&filter_path=hits.hits._source.properties" -o output_properties.json
curl -XGET "10.254.1.31:9200/workspace/_search&filter_path=hits.hits._source.i18n" -o output_i18n.json
curl -XGET '10.254.1.31:9200/workspace/_search&filter_path=hits.hits' -o output.json


curl -XGET '10.254.1.31:9200/workspace/_count?pretty' # 361274,


curl -XGET '10.254.1.31:9200/workspace/_search?pretty' -H "Content-Type: application/json" -d @elastic.json
curl -XGET '10.254.1.31:9200/workspace/_count?pretty' -H "Content-Type: application/json" -d @elastic.json