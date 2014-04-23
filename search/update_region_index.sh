curl "http://localhost:8983/solr/collection1/update?stream.body=<delete><query>*:*</query></delete>"
curl "http://localhost:8983/solr/collection1/update?stream.body=<commit/>"
curl "http://localhost:8983/solr/collection1/update/csv?stream.file=hunchkin/region_index.csv&stream.contentType=text/plain;charset=utf-8&separator=%7c&commit=true"
