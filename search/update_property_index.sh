curl "http://localhost:8983/solr/properties/update?stream.body=<delete><query>*:*</query></delete>"
curl "http://localhost:8983/solr/properties/update?stream.body=<commit/>"
curl "http://localhost:8983/solr/properties/update/csv?stream.file=hunchkin/property_index.csv&stream.contentType=text/plain;charset=utf-8&separator=%7c&commit=true"
